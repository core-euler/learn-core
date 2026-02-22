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
    db.query(DbSession).delete()
    db.query(User).delete()
    db.commit()
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
