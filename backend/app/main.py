from fastapi import FastAPI, HTTPException, Response, Cookie
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

from .schemas import RegisterRequest, LoginRequest, RegisterResponse, UserOut
from .store import store, InMemoryStore
from .models import new_user, new_session
from .security import hash_password, verify_password, create_access_token, make_refresh_token, hash_refresh_token, decode_access_token

app = FastAPI(title="LLM Handbook MVP Backend")


def _set_auth_cookies(resp: Response, access: str, refresh: str) -> None:
    resp.set_cookie("access_token", access, httponly=True)
    resp.set_cookie("refresh_token", refresh, httponly=True)


@app.post("/api/auth/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest):
    if store.get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="email_exists")
    user = new_user(email=payload.email, password_hash=hash_password(payload.password), first_name=payload.email.split("@")[0], auth_method="email")
    store.add_user(user)
    return RegisterResponse(user=UserOut(id=user.id, email=user.email, first_name=user.first_name, auth_method=user.auth_method))


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = store.get_user_by_email(payload.email)
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    access = create_access_token(user.id)
    refresh = make_refresh_token()
    session = new_session(user.id, hash_refresh_token(refresh))
    store.add_session(session)

    resp = JSONResponse({"ok": True})
    _set_auth_cookies(resp, access, refresh)
    return resp


@app.post("/api/auth/refresh")
def refresh(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing_refresh")

    refresh_hash = hash_refresh_token(refresh_token)
    session = store.get_session_by_refresh_hash(refresh_hash)

    if refresh_hash in store.used_refresh_hashes:
        # Reuse detection, must invalidate all sessions for same user if known
        if session:
            store.revoke_all_for_user(session.user_id)
        raise HTTPException(status_code=401, detail="refresh_reuse_detected")

    if not session or session.is_revoked or session.is_expired:
        raise HTTPException(status_code=401, detail="invalid_refresh")

    store.revoke_session(session)

    new_refresh = make_refresh_token()
    new_s = new_session(session.user_id, hash_refresh_token(new_refresh))
    store.add_session(new_s)
    access = create_access_token(session.user_id)

    resp = JSONResponse({"ok": True})
    _set_auth_cookies(resp, access, new_refresh)
    return resp


@app.get("/api/auth/me", response_model=UserOut)
def me(access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing_access")
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_access")
    user = store.users.get(payload.get("user_id"))
    if not user:
        raise HTTPException(status_code=401, detail="invalid_access")
    return UserOut(id=user.id, email=user.email, first_name=user.first_name, auth_method=user.auth_method)


@app.post("/api/auth/logout")
def logout(refresh_token: str | None = Cookie(default=None)):
    if refresh_token:
        refresh_hash = hash_refresh_token(refresh_token)
        session = store.get_session_by_refresh_hash(refresh_hash)
        if session and not session.is_revoked:
            store.revoke_session(session)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@app.post("/api/auth/logout-all")
def logout_all(access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="missing_access")
    try:
        payload = decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_access")
    user_id = payload.get("user_id")
    store.revoke_all_for_user(user_id)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


@app.post('/_test/reset')
def _test_reset():
    global store
    # replace state for deterministic tests
    from .store import InMemoryStore
    new_store = InMemoryStore()
    import backend.app.store as s
    s.store = new_store
    globals()['store'] = new_store
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}
