from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Response, Cookie, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .schemas import RegisterRequest, LoginRequest, RegisterResponse, UserOut
from .security import (
    hash_password,
    verify_password,
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
import os

app = FastAPI(title="LLM Handbook MVP Backend")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def _set_auth_cookies(resp: Response, access: str, refresh: str) -> None:
    resp.set_cookie("access_token", access, httponly=True)
    resp.set_cookie("refresh_token", refresh, httponly=True)


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


@app.post("/api/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")

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
    return resp


@app.post("/api/auth/refresh")
def refresh(refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
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
def logout(refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if refresh_token:
        refresh_hash = hash_refresh_token(refresh_token)
        session = db.execute(select(DbSession).where(DbSession.refresh_token_hash == refresh_hash)).scalar_one_or_none()
        if session:
            session.is_revoked = True
            db.commit()

    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@app.post("/api/auth/logout-all")
def logout_all(access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
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
    return resp


@app.post('/_test/reset')
def _test_reset(db: Session = Depends(get_db)):
    Base.metadata.create_all(bind=engine)
    db.query(UserLessonProgress).delete()
    db.query(UserModuleProgress).delete()
    db.query(Lesson).delete()
    db.query(Module).delete()
    db.query(DbSession).delete()
    db.query(User).delete()
    db.commit()
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


@app.post('/_test/seed-course')
def _test_seed_course(db: Session = Depends(get_db)):
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
    modules = db.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == user_id)).scalars().all()
    lessons = db.execute(select(UserLessonProgress).where(UserLessonProgress.user_id == user_id)).scalars().all()
    return {
        'modules_count': len(modules),
        'lessons_count': len(lessons),
        'module_statuses': [m.status for m in modules],
        'lesson_statuses': [l.status for l in lessons],
    }


@app.post('/api/progress/lessons/{lesson_id}/complete')
def complete_lesson(lesson_id: str, access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
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
