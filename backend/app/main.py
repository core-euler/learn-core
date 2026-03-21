from datetime import datetime, timedelta, timezone
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, Cookie, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from .schemas import RegisterRequest, LoginRequest, RegisterResponse, UserOut
from .security import (
    hash_password,
    verify_and_maybe_rehash_password,
    create_access_token,
    make_refresh_token,
    hash_refresh_token,
    decode_access_token,
)
from .database import get_db, Base, engine, SessionLocal
from .entities import User, Session as DbSession
from .course_entities import Module, Lesson, UserLessonProgress, UserModuleProgress
from .progress_service import bootstrap_progress_for_user, complete_lesson_and_unlock_next
from .course_sync import sync_course_catalog_from_index
from .course_schemas import ModuleOut, LessonOut, LessonContentOut
from .ai_entities import AiSession, AiMessage
from .rag_entities import RagChunk, RagIndexState
from .ai_schemas import LectureRequest, ExamStartRequest, ConsultantRequest
from .ai_service import ensure_mode_access, create_ai_session
from .usage_entities import UserUsage
from .limits_service import check_and_increment_usage, DAILY_LIMIT
from .rate_limit_entities import UserRateWindow
from .minute_limit_service import check_minute_limit, MINUTE_LIMIT
from .streaming import build_text_stream
from .llm_provider import DefaultLlmProviderAdapter, LlmPolicy, call_with_fallback, build_llm_adapter
from .retrieval import (
    ChunkMetadata,
    EmbeddedChunk,
    RetrievalQuery,
    build_retriever_from_embedded_chunks,
    compute_curriculum_content_signature,
    embed_curriculum_chunks,
    load_curriculum_chunks,
    StubChunkIndex,
    StubRetriever,
)
from .env import is_test_mode, cookie_secure, cookie_samesite
from .telegram_auth import validate_telegram_payload, resolve_bot_id
from .config import settings
from .content_index import validate_default_content_index, default_index_path
import os
import json

app = FastAPI(title="LLM Handbook MVP Backend")
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.llm_adapter = build_llm_adapter(
    provider=settings.llm_provider,
    comet_api_key=settings.cometapi_api_key,
    comet_base_url=settings.cometapi_base_url,
    comet_chat_model=settings.cometapi_chat_model,
    comet_exam_model=settings.cometapi_exam_model,
)
app.state.retriever = StubRetriever(StubChunkIndex.empty())
app.state.llm_policy = LlmPolicy(
    timeout_seconds=settings.llm_timeout_seconds,
    fallback_lecture=settings.llm_fallback_lecture,
    fallback_consultant=settings.llm_fallback_consultant,
)
app.state.rag_top_k = settings.rag_top_k


@app.get("/healthz")
def healthz(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"ok": True}


@app.on_event("startup")
def on_startup():
    if settings.content_validate_on_startup:
        validate_default_content_index()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        sync_course_catalog_from_index(
            db,
            index_path=default_index_path(),
            repo_root=Path(__file__).resolve().parent.parent,
        )
    app.state.retriever = _build_runtime_retriever()


def _set_auth_cookies(resp: Response, access: str, refresh: str) -> None:
    resp.set_cookie("access_token", access, httponly=True, secure=cookie_secure(), samesite=cookie_samesite())
    resp.set_cookie("refresh_token", refresh, httponly=True, secure=cookie_secure(), samesite=cookie_samesite())


def _issue_csrf_token(resp: Response) -> str:
    token = secrets.token_urlsafe(32)
    resp.set_cookie("csrf_token", token, httponly=False, secure=cookie_secure(), samesite=cookie_samesite())
    return token


def require_csrf(request: Request, csrf_token: str | None = Cookie(default=None)) -> None:
    header_token = request.headers.get("x-csrf-token")
    if not csrf_token or not header_token or header_token != csrf_token:
        raise HTTPException(status_code=403, detail="csrf_failed")


def _extract_embeddings(payload: dict, expected_len: int) -> list[list[float]]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("embeddings_missing_data")

    rows: list[tuple[int, list[float]]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        emb = row.get("embedding")
        idx = row.get("index", 0)
        if isinstance(idx, int) and isinstance(emb, list) and emb:
            rows.append((idx, [float(x) for x in emb]))

    if not rows:
        raise RuntimeError("embeddings_empty")

    rows.sort(key=lambda item: item[0])
    vectors = [vec for _, vec in rows]
    if len(vectors) != expected_len:
        raise RuntimeError("embeddings_length_mismatch")
    return vectors


def _build_embedding_callable():
    adapter = app.state.llm_adapter
    if not hasattr(adapter, "embed_texts"):
        return None

    def _embed_texts(inputs: list[str]) -> list[list[float]]:
        payload = adapter.embed_texts(model=settings.cometapi_embed_model, inputs=inputs)
        if not isinstance(payload, dict):
            raise RuntimeError("embeddings_invalid_payload")
        return _extract_embeddings(payload, expected_len=len(inputs))

    return _embed_texts


def _load_cached_chunks(db: Session, *, content_signature: str) -> list[EmbeddedChunk]:
    rows = db.execute(
        select(RagChunk)
        .where(RagChunk.content_signature == content_signature)
        .order_by(RagChunk.module_id.asc(), RagChunk.lesson_id.asc(), RagChunk.start_char.asc())
    ).scalars().all()
    loaded: list[EmbeddedChunk] = []
    for row in rows:
        embedding: list[float] | None = None
        if row.embedding_json:
            try:
                parsed = json.loads(row.embedding_json)
                if isinstance(parsed, list):
                    embedding = [float(x) for x in parsed]
            except Exception:
                embedding = None
        loaded.append(
            EmbeddedChunk(
                metadata=ChunkMetadata(
                    chunk_id=row.chunk_id,
                    module_id=row.module_id,
                    lesson_id=row.lesson_id,
                    source_path=row.source_path,
                    start_char=row.start_char,
                    end_char=row.end_char,
                ),
                text=row.text,
                embedding=embedding,
            )
        )
    return loaded


def _persist_rag_snapshot(
    db: Session,
    *,
    content_signature: str,
    chunks: list[EmbeddedChunk],
    embeddings_ready: bool,
) -> None:
    db.execute(delete(RagChunk))
    for chunk in chunks:
        db.add(
            RagChunk(
                content_signature=content_signature,
                chunk_id=chunk.metadata.chunk_id,
                module_id=chunk.metadata.module_id,
                lesson_id=chunk.metadata.lesson_id,
                source_path=chunk.metadata.source_path,
                start_char=chunk.metadata.start_char,
                end_char=chunk.metadata.end_char,
                text=chunk.text,
                embedding_json=json.dumps(chunk.embedding) if chunk.embedding else None,
            )
        )

    state = db.get(RagIndexState, 1)
    if not state:
        state = RagIndexState(id=1)
        db.add(state)
    state.content_signature = content_signature
    state.embed_model = settings.cometapi_embed_model
    state.chunk_size_chars = settings.rag_chunk_size_chars
    state.chunk_overlap_chars = settings.rag_chunk_overlap_chars
    state.embeddings_ready = embeddings_ready
    state.updated_at = datetime.now(timezone.utc)
    db.commit()


def _build_runtime_retriever():
    index_path = default_index_path()
    repo_root = Path(__file__).resolve().parent.parent
    embed_fn = _build_embedding_callable()

    try:
        signature = compute_curriculum_content_signature(
            index_path=index_path,
            repo_root=repo_root,
            chunk_size_chars=settings.rag_chunk_size_chars,
            chunk_overlap_chars=settings.rag_chunk_overlap_chars,
            embed_model=settings.cometapi_embed_model,
        )
    except Exception:
        return StubRetriever(StubChunkIndex.empty())

    try:
        with SessionLocal() as db:
            state = db.get(RagIndexState, 1)
            if state and state.content_signature == signature:
                cached = _load_cached_chunks(db, content_signature=signature)
                if cached:
                    # If embeddings were not available previously, allow one-time backfill.
                    if not state.embeddings_ready and embed_fn:
                        embedded_cached, embeddings_ready = embed_curriculum_chunks(
                            chunks=cached,
                            embed_texts=embed_fn,
                            embedding_batch_size=settings.rag_embedding_batch_size,
                        )
                        if embeddings_ready:
                            _persist_rag_snapshot(
                                db,
                                content_signature=signature,
                                chunks=embedded_cached,
                                embeddings_ready=True,
                            )
                            cached = embedded_cached
                    return build_retriever_from_embedded_chunks(chunks=cached, embed_texts=embed_fn)

            chunks = load_curriculum_chunks(
                index_path=index_path,
                repo_root=repo_root,
                chunk_size_chars=settings.rag_chunk_size_chars,
                chunk_overlap_chars=settings.rag_chunk_overlap_chars,
            )
            chunks, embeddings_ready = embed_curriculum_chunks(
                chunks=chunks,
                embed_texts=embed_fn,
                embedding_batch_size=settings.rag_embedding_batch_size,
            )
            _persist_rag_snapshot(
                db,
                content_signature=signature,
                chunks=chunks,
                embeddings_ready=embeddings_ready,
            )
            return build_retriever_from_embedded_chunks(chunks=chunks, embed_texts=embed_fn)
    except Exception:
        return StubRetriever(StubChunkIndex.empty())


def _compose_grounded_message(user_message: str, retrieval_result) -> str:
    if not retrieval_result.chunks:
        return user_message
    chunks = []
    for idx, chunk in enumerate(retrieval_result.chunks, start=1):
        chunks.append(
            f"[chunk {idx}] source={chunk.metadata.source_path} score={chunk.score:.4f}\n{chunk.text}"
        )
    context_block = "\n\n".join(chunks)
    return (
        "Use only the context below to answer. If context is insufficient, say so.\n\n"
        f"CONTEXT:\n{context_block}\n\n"
        f"QUESTION:\n{user_message}"
    )


def _compose_full_name(first_name: str, last_name: str | None) -> str:
    if last_name:
        return f"{first_name} {last_name}".strip()
    return first_name


def _build_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=_compose_full_name(user.first_name, user.last_name),
        auth_method=user.auth_method,
    )


@app.post("/api/auth/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="email_exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.email.split("@")[0],
        auth_method="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    bootstrap_progress_for_user(db, user.id)
    return RegisterResponse(user=_build_user_out(user))


@app.get('/api/auth/telegram/callback')
def auth_telegram_callback(
    id: str,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
    photo_url: str | None = None,
    auth_date: str | None = None,
    hash: str | None = None,
    db: Session = Depends(get_db),
):
    normalized_first_name = first_name.strip()
    normalized_last_name = (last_name or '').strip() or None
    normalized_username = (username or '').strip() or None
    normalized_photo_url = (photo_url or '').strip() or None

    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail='telegram_auth_not_configured')

    payload = {
        'id': id,
        'first_name': normalized_first_name,
        'last_name': normalized_last_name or '',
        'username': normalized_username or '',
        'photo_url': normalized_photo_url or '',
        'auth_date': auth_date or '',
        'hash': hash or '',
    }

    ok = validate_telegram_payload(payload, settings.telegram_bot_token)
    if not ok:
        raise HTTPException(status_code=401, detail='invalid_telegram_auth')

    if settings.telegram_bot_id:
        resolved_bot_id = resolve_bot_id(settings.telegram_bot_token)
        if not resolved_bot_id or resolved_bot_id != settings.telegram_bot_id:
            raise HTTPException(status_code=401, detail='invalid_telegram_bot_binding')

    user = db.execute(select(User).where(User.telegram_id == id)).scalar_one_or_none()
    if not user:
        user = User(
            email=None,
            password_hash=None,
            first_name=normalized_first_name,
            last_name=normalized_last_name,
            auth_method='telegram',
            telegram_id=id,
            telegram_username=normalized_username,
            photo_url=normalized_photo_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        bootstrap_progress_for_user(db, user.id)
    else:
        user.first_name = normalized_first_name
        user.last_name = normalized_last_name
        user.telegram_username = normalized_username
        user.photo_url = normalized_photo_url
        db.commit()
        db.refresh(user)

    access = create_access_token(user.id)
    refresh = make_refresh_token()
    session = DbSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)
    db.commit()

    resp = JSONResponse({'ok': True})
    _set_auth_cookies(resp, access, refresh)
    _issue_csrf_token(resp)
    return resp


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    ok, replacement_hash = verify_and_maybe_rehash_password(payload.password, user.password_hash)
    if not ok:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if replacement_hash:
        user.password_hash = replacement_hash
        db.commit()

    access = create_access_token(user.id)
    refresh = make_refresh_token()
    session = DbSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)
    db.commit()

    resp = JSONResponse({"ok": True})
    _set_auth_cookies(resp, access, refresh)
    _issue_csrf_token(resp)
    return resp


@app.post("/api/auth/refresh")
def refresh(refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing_refresh")

    refresh_hash = hash_refresh_token(refresh_token)
    session = db.execute(select(DbSession).where(DbSession.refresh_token_hash == refresh_hash)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="invalid_refresh")

    # Reuse detection: revoked token reuse means potential theft -> revoke all sessions for user.
    if session.is_revoked:
        user_sessions = db.execute(select(DbSession).where(DbSession.user_id == session.user_id)).scalars().all()
        for s in user_sessions:
            s.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="refresh_reuse_detected")

    exp = session.expires_at
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > exp:
        raise HTTPException(status_code=401, detail="invalid_refresh")

    session.is_revoked = True

    new_refresh = make_refresh_token()
    new_s = DbSession(
        user_id=session.user_id,
        refresh_token_hash=hash_refresh_token(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(new_s)
    db.commit()

    access = create_access_token(session.user_id)
    resp = JSONResponse({"ok": True})
    _set_auth_cookies(resp, access, new_refresh)
    _issue_csrf_token(resp)
    return resp


@app.get("/api/auth/me", response_model=UserOut)
def me(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing_access")
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_access")

    user = db.get(User, payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="invalid_access")

    return _build_user_out(user)


@app.post("/api/auth/logout")
def logout(refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if refresh_token:
        refresh_hash = hash_refresh_token(refresh_token)
        session = db.execute(select(DbSession).where(DbSession.refresh_token_hash == refresh_hash)).scalar_one_or_none()
        if session:
            session.is_revoked = True
            db.commit()

    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    resp.delete_cookie("csrf_token")
    return resp


@app.post("/api/auth/logout-all")
def logout_all(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing_access")
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_access")

    user_id = payload.get("user_id")
    sessions = db.execute(select(DbSession).where(DbSession.user_id == user_id, DbSession.is_revoked == False)).scalars().all()
    for s in sessions:
        s.is_revoked = True
    db.commit()

    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    resp.delete_cookie("csrf_token")
    return resp


@app.post('/_test/reset')
def _test_reset(db: Session = Depends(get_db)):
    if not is_test_mode():
        raise HTTPException(status_code=404, detail='not_found')
    # Keep test DB schema aligned with latest models between test runs.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


@app.post('/_test/reset-minute-window')
def _test_reset_minute_window(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not is_test_mode():
        raise HTTPException(status_code=404, detail='not_found')
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')
    rw = db.execute(select(UserRateWindow).where(UserRateWindow.user_id == user_id)).scalar_one_or_none()
    if rw:
        rw.requests_in_window = 0
        rw.window_start_epoch = 0
        db.commit()
    return {'ok': True}


@app.post('/_test/seed-course')
def _test_seed_course(db: Session = Depends(get_db)):
    if not is_test_mode():
        raise HTTPException(status_code=404, detail='not_found')
    Base.metadata.create_all(bind=engine)
    m1 = Module(slug='m1', title='M1', description='m1', order_index=1, is_published=True)
    m2 = Module(slug='m2', title='M2', description='m2', order_index=2, is_published=True)
    db.add_all([m1, m2])
    db.commit()
    db.refresh(m1)
    db.refresh(m2)
    db.add_all([
        Lesson(module_id=m1.id, slug='l1', title='L1', description='l1', order_index=1, md_file_path='content/m1/l1.md', is_published=True),
        Lesson(module_id=m1.id, slug='l2', title='L2', description='l2', order_index=2, md_file_path='content/m1/l2.md', is_published=True),
        Lesson(module_id=m2.id, slug='l1', title='L3', description='l3', order_index=1, md_file_path='content/m2/l1.md', is_published=True),
    ])
    db.commit()
    return {'ok': True}


@app.get('/api/modules')
def get_modules(db: Session = Depends(get_db)):
    mods = db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()
    out = []
    for m in mods:
        count = db.execute(select(Lesson).where(Lesson.module_id == m.id, Lesson.is_published == True)).scalars().all()
        out.append(ModuleOut(id=m.id, title=m.title, description=m.description, order_index=m.order_index, lessons_count=len(count)).model_dump())
    return {'modules': out}


@app.get('/api/modules/{module_id}')
def get_module(module_id: str, db: Session = Depends(get_db)):
    m = db.get(Module, module_id)
    if not m or not m.is_published:
        raise HTTPException(status_code=404, detail='module_not_found')
    lessons = db.execute(select(Lesson).where(Lesson.module_id == m.id, Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().all()
    return {
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'order_index': m.order_index,
        'lessons': [LessonOut(id=l.id, module_id=l.module_id, title=l.title, description=l.description, order_index=l.order_index).model_dump() for l in lessons]
    }


@app.get('/api/lessons/{lesson_id}')
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    l = db.get(Lesson, lesson_id)
    if not l or not l.is_published:
        raise HTTPException(status_code=404, detail='lesson_not_found')
    return LessonOut(id=l.id, module_id=l.module_id, title=l.title, description=l.description, order_index=l.order_index)


@app.get('/api/lessons/{lesson_id}/content')
def get_lesson_content(lesson_id: str, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')

    l = db.get(Lesson, lesson_id)
    if not l or not l.is_published:
        raise HTTPException(status_code=404, detail='lesson_not_found')

    lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == payload.get('user_id'), UserLessonProgress.lesson_id == lesson_id)).scalar_one_or_none()
    if not lp or lp.status == 'locked':
        raise HTTPException(status_code=403, detail='lesson_locked')

    path = os.path.join(os.path.dirname(__file__), '..', l.md_file_path)
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='content_not_found')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return LessonContentOut(lesson_id=l.id, title=l.title, content=content)


@app.get('/api/progress')
def get_progress(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')

    user_id = payload.get('user_id')
    module_rows = db.execute(select(Module).where(Module.is_published == True).order_by(Module.order_index.asc())).scalars().all()

    out_modules = []
    total_lessons = 0
    completed_lessons = 0
    next_lesson_id = None
    consultant_unlocked = False

    for m in module_rows:
        mp = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id, UserModuleProgress.module_id == m.id)).scalar_one_or_none()
        lesson_rows = db.execute(select(Lesson).where(Lesson.module_id == m.id, Lesson.is_published == True).order_by(Lesson.order_index.asc())).scalars().all()
        lesson_items = []
        for l in lesson_rows:
            lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == l.id)).scalar_one_or_none()
            if not lp:
                continue
            total_lessons += 1
            if lp.status == 'completed':
                completed_lessons += 1
            lesson_items.append({
                'lesson_id': l.id,
                'status': lp.status,
                'exam_score': lp.exam_score,
                'exam_attempts': lp.exam_attempts,
                'completed_at': lp.completed_at.isoformat() if lp.completed_at else None,
            })

        module_status = mp.status if mp else 'locked'
        if module_status == 'completed':
            consultant_unlocked = True

        for item in lesson_items:
            if item['status'] == 'available' and next_lesson_id is None:
                next_lesson_id = item['lesson_id']

        out_modules.append({
            'module_id': m.id,
            'status': module_status,
            'completed_at': mp.completed_at.isoformat() if mp and mp.completed_at else None,
            'lessons': lesson_items,
        })

    overall_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
    return {
        'overall_percent': overall_percent,
        'next_lesson_id': next_lesson_id,
        'consultant_unlocked': consultant_unlocked,
        'modules': out_modules,
    }


@app.get('/api/progress/stats')
def get_progress_stats(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = payload.get('user_id')

    total_lessons = len(db.execute(select(Lesson).where(Lesson.is_published == True)).scalars().all())
    total_modules = len(db.execute(select(Module).where(Module.is_published == True)).scalars().all())
    completed_lessons = len(db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.status == 'completed')).scalars().all())
    completed_modules = len(db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id, UserModuleProgress.status == 'completed')).scalars().all())

    usage = db.execute(select(UserUsage).where(UserUsage.user_id == user_id)).scalar_one_or_none()
    return {
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'total_modules': total_modules,
        'completed_modules': completed_modules,
        'total_ai_requests': usage.total_requests if usage else 0,
        'requests_today': usage.requests_today if usage else 0,
        'requests_limit_today': DAILY_LIMIT,
    }


@app.post('/api/chat/lecture')
def chat_lecture(payload: LectureRequest, request: Request, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    allowed, err = check_and_increment_usage(db, user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)
    minute_ok, minute_err = check_minute_limit(db, user_id)
    if not minute_ok:
        raise HTTPException(status_code=429, detail=minute_err)

    ok, err = ensure_mode_access(db, user_id, 'lecture', payload.lesson_id)
    if not ok:
        raise HTTPException(status_code=403, detail=err)

    lesson = db.get(Lesson, payload.lesson_id)
    if not lesson or not lesson.is_published:
        raise HTTPException(status_code=404, detail='lesson_not_found')

    session = create_ai_session(db, user_id=user_id, mode='lecture', lesson_id=payload.lesson_id)
    retrieval = app.state.retriever.retrieve(
        RetrievalQuery(
            user_id=user_id,
            mode='lecture',
            lesson_id=payload.lesson_id,
            lesson_source_path=lesson.md_file_path,
            message=payload.message,
            top_k=app.state.rag_top_k,
        )
    )
    grounded_message = _compose_grounded_message(payload.message, retrieval)

    reply, is_fallback, reason = call_with_fallback(
        fn=lambda: app.state.llm_adapter.lecture_reply(
            lesson_id=payload.lesson_id,
            message=grounded_message,
            message_id=payload.message_id,
        ),
        timeout_seconds=app.state.llm_policy.timeout_seconds,
        fallback_text=app.state.llm_policy.fallback_lecture,
    )

    db.add(AiMessage(session_id=session.id, role='user', content=payload.message, tokens=0))
    db.add(AiMessage(session_id=session.id, role='assistant', content=reply.text, tokens=reply.tokens_used))
    db.commit()

    if 'text/event-stream' in (request.headers.get('accept') or ''):
        last_event_id = request.headers.get('last-event-id')
        return StreamingResponse(
            build_text_stream(payload.message_id, reply.text, tokens_used=reply.tokens_used, last_event_id=last_event_id),
            media_type='text/event-stream',
        )

    return {
        'session_id': session.id,
        'reply': reply.text,
        'provider': reply.provider,
        'fallback_used': is_fallback,
        'fallback_reason': reason,
        'retrieval': {
            'top_k': app.state.rag_top_k,
            'chunks_found': len(retrieval.chunks),
            'citations': [c.__dict__ for c in retrieval.citations],
        },
    }


@app.post('/api/chat/exam/start')
def chat_exam_start(payload: ExamStartRequest, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    allowed, err = check_and_increment_usage(db, user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)
    minute_ok, minute_err = check_minute_limit(db, user_id)
    if not minute_ok:
        raise HTTPException(status_code=429, detail=minute_err)

    ok, err = ensure_mode_access(db, user_id, 'exam', payload.lesson_id)
    if not ok:
        raise HTTPException(status_code=403, detail=err)

    try:
        exam_data = app.state.llm_adapter.build_exam(lesson_id=payload.lesson_id)
        provider = exam_data.get('provider', 'default')
        fallback_reason = 'ok'
    except Exception:
        exam_data = DefaultLlmProviderAdapter().build_exam(lesson_id=payload.lesson_id)
        provider = 'fallback'
        fallback_reason = 'error'
    rubric_data = {'questions': exam_data.get('questions', [])}

    session = create_ai_session(db, user_id=user_id, mode='exam', lesson_id=payload.lesson_id, exam_rubric=json.dumps(rubric_data))
    return {
        'session_id': session.id,
        'questions': [
            {
                'id': q['id'],
                'type': q['type'],
                'text': q['text'],
                **({'options': q['options']} if q.get('options') else {}),
            }
            for q in rubric_data['questions']
        ],
        'provider': provider,
        'fallback_reason': fallback_reason,
    }


@app.post('/api/chat/exam/finish')
def chat_exam_finish(payload: dict, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    session_id = payload.get('session_id')
    answers = payload.get('answers', [])
    s = db.get(AiSession, session_id)
    if not s or s.user_id != user_id or s.mode != 'exam':
        raise HTTPException(status_code=404, detail='session_not_found')

    rubric = json.loads(s.exam_rubric or '{}')
    questions = rubric.get('questions', [])
    correct = 0
    details = []
    for q in questions:
        given = next((a for a in answers if a.get('question_id') == q['id']), None)
        is_correct = bool(given and given.get('answer'))
        if q['type'] == 'multiple_choice':
            is_correct = bool(given and given.get('answer') == q['answer'])
        if is_correct:
            correct += 1
        details.append({'question_id': q['id'], 'is_correct': is_correct, 'comment': 'ok' if is_correct else 'wrong'})

    score = int((correct / len(questions)) * 100) if questions else 0
    passed = score >= 70

    lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == s.lesson_id)).scalar_one_or_none()
    if lp:
        lp.exam_attempts += 1
        lp.exam_score = score
        if passed and lp.status != 'completed':
            complete_lesson_and_unlock_next(db, user_id, s.lesson_id)
        else:
            db.commit()

    return {'session_id': s.id, 'score': score, 'passed': passed, 'lesson_completed': bool(lp and lp.status == 'completed'), 'answers': details}


@app.get('/api/chat/sessions')
def chat_sessions(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    rows = db.execute(select(AiSession).where(AiSession.user_id == user_id).order_by(AiSession.created_at.desc())).scalars().all()
    return {'sessions': [{'id': s.id, 'mode': s.mode, 'lesson_id': s.lesson_id, 'created_at': s.created_at.isoformat()} for s in rows]}


@app.get('/api/chat/sessions/{session_id}')
def chat_session(session_id: str, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    s = db.get(AiSession, session_id)
    if not s or s.user_id != user_id:
        raise HTTPException(status_code=404, detail='session_not_found')
    msgs = db.execute(select(AiMessage).where(AiMessage.session_id == s.id).order_by(AiMessage.created_at.asc())).scalars().all()
    return {'id': s.id, 'mode': s.mode, 'lesson_id': s.lesson_id, 'messages': [{'role': m.role, 'content': m.content} for m in msgs]}


@app.post('/api/chat/consultant')
def chat_consultant(payload: ConsultantRequest, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        token_payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = token_payload.get('user_id')

    allowed, err = check_and_increment_usage(db, user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=err)
    minute_ok, minute_err = check_minute_limit(db, user_id)
    if not minute_ok:
        raise HTTPException(status_code=429, detail=minute_err)

    ok, err = ensure_mode_access(db, user_id, 'consultant', None)
    if not ok:
        raise HTTPException(status_code=403, detail=err)

    opened_lessons = db.execute(
        select(Lesson.md_file_path)
        .join(UserLessonProgress, UserLessonProgress.lesson_id == Lesson.id)
        .where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status != 'locked',
            Lesson.is_published == True,
        )
    ).scalars().all()

    session = create_ai_session(db, user_id=user_id, mode='consultant', lesson_id=None)
    retrieval = app.state.retriever.retrieve(
        RetrievalQuery(
            user_id=user_id,
            mode='consultant',
            lesson_id=None,
            allowed_source_paths=list(opened_lessons),
            message=payload.message,
            top_k=app.state.rag_top_k,
        )
    )
    grounded_message = _compose_grounded_message(payload.message, retrieval)

    reply, is_fallback, reason = call_with_fallback(
        fn=lambda: app.state.llm_adapter.consultant_reply(
            message=grounded_message,
            message_id=payload.message_id,
        ),
        timeout_seconds=app.state.llm_policy.timeout_seconds,
        fallback_text=app.state.llm_policy.fallback_consultant,
    )

    db.add(AiMessage(session_id=session.id, role='user', content=payload.message, tokens=0))
    db.add(AiMessage(session_id=session.id, role='assistant', content=reply.text, tokens=reply.tokens_used))
    db.commit()
    return {
        'session_id': session.id,
        'reply': reply.text,
        'source': 'opened_lessons_only',
        'provider': reply.provider,
        'fallback_used': is_fallback,
        'fallback_reason': reason,
        'retrieval': {
            'top_k': app.state.rag_top_k,
            'chunks_found': len(retrieval.chunks),
            'citations': [c.__dict__ for c in retrieval.citations],
        },
    }


@app.post('/api/progress/lessons/{lesson_id}/complete')
def complete_lesson(lesson_id: str, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db), _: None = Depends(require_csrf)):
    if not access_token:
        raise HTTPException(status_code=401, detail='missing_access')
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid_access')
    user_id = payload.get('user_id')

    lp = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id, UserLessonProgress.lesson_id == lesson_id)).scalar_one_or_none()
    if not lp or lp.status == 'locked':
        raise HTTPException(status_code=403, detail='lesson_locked')

    complete_lesson_and_unlock_next(db, user_id, lesson_id)
    return {'ok': True}
