from datetime import datetime, timedelta, timezone
import secrets

from fastapi import FastAPI, HTTPException, Response, Cookie, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
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
from .database import get_db, Base, engine
from .entities import User, Session as DbSession
from .course_entities import Module, Lesson, UserLessonProgress, UserModuleProgress
from .progress_service import bootstrap_progress_for_user, complete_lesson_and_unlock_next
from .course_schemas import ModuleOut, LessonOut, LessonContentOut
from .ai_entities import AiSession, AiMessage
from .ai_schemas import LectureRequest, ExamStartRequest, ConsultantRequest
from .ai_service import ensure_mode_access, create_ai_session
from .usage_entities import UserUsage
from .limits_service import check_and_increment_usage, DAILY_LIMIT
from .rate_limit_entities import UserRateWindow
from .minute_limit_service import check_minute_limit, MINUTE_LIMIT
from .streaming import build_text_stream
from .llm_provider import DefaultLlmProviderAdapter, LlmPolicy, call_with_fallback
from .retrieval import RetrievalQuery, StubChunkIndex, StubRetriever
from .env import is_test_mode, cookie_secure, cookie_samesite
from .telegram_auth import validate_telegram_payload, resolve_bot_id
from .config import settings
from .content_index import validate_default_content_index
import os
import json

app = FastAPI(title="LLM Handbook MVP Backend")
app.state.llm_adapter = DefaultLlmProviderAdapter()
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
    return RegisterResponse(user=UserOut(id=user.id, email=user.email, first_name=user.first_name, auth_method=user.auth_method))


@app.get('/api/auth/telegram/callback')
def auth_telegram_callback(
    id: str,
    first_name: str,
    username: str | None = None,
    photo_url: str | None = None,
    auth_date: str | None = None,
    hash: str | None = None,
    db: Session = Depends(get_db),
):
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail='telegram_auth_not_configured')

    payload = {
        'id': id,
        'first_name': first_name,
        'username': username or '',
        'photo_url': photo_url or '',
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
            first_name=first_name,
            auth_method='telegram',
            telegram_id=id,
            telegram_username=username,
            photo_url=photo_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        bootstrap_progress_for_user(db, user.id)

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

    return UserOut(id=user.id, email=user.email, first_name=user.first_name, auth_method=user.auth_method)


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
    Base.metadata.create_all(bind=engine)
    db.query(UserLessonProgress).delete()
    db.query(UserModuleProgress).delete()
    db.query(Lesson).delete()
    db.query(Module).delete()
    db.query(AiMessage).delete()
    db.query(AiSession).delete()
    db.query(UserUsage).delete()
    db.query(UserRateWindow).delete()
    db.query(DbSession).delete()
    db.query(User).delete()
    db.commit()
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
    m1 = Module(title='M1', description='m1', order_index=1, is_published=True)
    m2 = Module(title='M2', description='m2', order_index=2, is_published=True)
    db.add_all([m1, m2])
    db.commit()
    db.refresh(m1)
    db.refresh(m2)
    db.add_all([
        Lesson(module_id=m1.id, title='L1', description='l1', order_index=1, md_file_path='content/m1/l1.md', is_published=True),
        Lesson(module_id=m1.id, title='L2', description='l2', order_index=2, md_file_path='content/m1/l2.md', is_published=True),
        Lesson(module_id=m2.id, title='L3', description='l3', order_index=1, md_file_path='content/m2/l1.md', is_published=True),
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

        out_modules.append({
            'module_id': m.id,
            'status': mp.status if mp else 'locked',
            'completed_at': mp.completed_at.isoformat() if mp and mp.completed_at else None,
            'lessons': lesson_items,
        })

    overall_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
    return {'overall_percent': overall_percent, 'modules': out_modules}


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

    session = create_ai_session(db, user_id=user_id, mode='lecture', lesson_id=payload.lesson_id)
    retrieval = app.state.retriever.retrieve(
        RetrievalQuery(
            user_id=user_id,
            mode='lecture',
            lesson_id=payload.lesson_id,
            message=payload.message,
            top_k=app.state.rag_top_k,
        )
    )

    reply, is_fallback, reason = call_with_fallback(
        fn=lambda: app.state.llm_adapter.lecture_reply(
            lesson_id=payload.lesson_id,
            message=payload.message,
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

    session = create_ai_session(db, user_id=user_id, mode='consultant', lesson_id=None)
    retrieval = app.state.retriever.retrieve(
        RetrievalQuery(
            user_id=user_id,
            mode='consultant',
            lesson_id=None,
            message=payload.message,
            top_k=app.state.rag_top_k,
        )
    )

    reply, is_fallback, reason = call_with_fallback(
        fn=lambda: app.state.llm_adapter.consultant_reply(
            message=payload.message,
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
