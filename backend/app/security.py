from datetime import datetime, timedelta, timezone
from jose import jwt
import base64
import hashlib
import hmac
import secrets

from .config import settings

try:
    from argon2.low_level import Type, hash_secret_raw
except Exception:  # pragma: no cover - guarded by runtime checks in argon2 path
    Type = None
    hash_secret_raw = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _hash_password_legacy_sha256(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${digest}"


def _verify_password_legacy_sha256(password: str, password_hash: str) -> bool:
    try:
        salt, expected = password_hash.split("$", 1)
    except ValueError:
        return False
    actual = hashlib.sha256((salt + password).encode()).hexdigest()
    return hmac.compare_digest(actual, expected)


def _hash_password_scrypt(password: str) -> str:
    salt = secrets.token_bytes(settings.password_scrypt_salt_bytes)
    digest = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=salt,
        n=settings.password_scrypt_n,
        r=settings.password_scrypt_r,
        p=settings.password_scrypt_p,
        dklen=settings.password_scrypt_dklen,
    )
    return (
        f"scrypt${settings.password_scrypt_n}${settings.password_scrypt_r}"
        f"${settings.password_scrypt_p}${settings.password_scrypt_dklen}"
        f"${_b64(salt)}${_b64(digest)}"
    )


def _verify_password_scrypt(password: str, password_hash: str) -> bool:
    try:
        _, n, r, p, dklen, salt_b64, expected_b64 = password_hash.split("$", 6)
        salt = _b64_decode(salt_b64)
        expected = _b64_decode(expected_b64)
        actual = hashlib.scrypt(
            password=password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=int(dklen),
        )
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)


def _hash_password_argon2id(password: str) -> str:
    if hash_secret_raw is None or Type is None:
        raise RuntimeError("argon2id_selected_but_argon2_not_installed")

    salt = secrets.token_bytes(settings.password_argon2_salt_bytes)
    digest = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=settings.password_argon2_time_cost,
        memory_cost=settings.password_argon2_memory_cost_kib,
        parallelism=settings.password_argon2_parallelism,
        hash_len=settings.password_argon2_hash_len,
        type=Type.ID,
    )
    return (
        f"argon2id${settings.password_argon2_time_cost}${settings.password_argon2_memory_cost_kib}"
        f"${settings.password_argon2_parallelism}${settings.password_argon2_hash_len}"
        f"${_b64(salt)}${_b64(digest)}"
    )


def _verify_password_argon2id(password: str, password_hash: str) -> bool:
    if hash_secret_raw is None or Type is None:
        return False

    try:
        _, time_cost, memory_cost, parallelism, hash_len, salt_b64, expected_b64 = password_hash.split("$", 6)
        salt = _b64_decode(salt_b64)
        expected = _b64_decode(expected_b64)
        actual = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=int(time_cost),
            memory_cost=int(memory_cost),
            parallelism=int(parallelism),
            hash_len=int(hash_len),
            type=Type.ID,
        )
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)


def _is_legacy_hash(password_hash: str) -> bool:
    return password_hash.count("$") == 1 and not password_hash.startswith("scrypt$") and not password_hash.startswith("argon2id$")


def _hash_with_current_policy(password: str) -> str:
    alg = settings.password_kdf_algorithm.lower()
    if alg == "scrypt":
        return _hash_password_scrypt(password)
    if alg == "argon2id":
        return _hash_password_argon2id(password)
    raise RuntimeError("unsupported_password_kdf_algorithm")


def hash_password(password: str) -> str:
    return _hash_with_current_policy(password)


def verify_password(password: str, password_hash: str) -> bool:
    ok, _ = verify_and_maybe_rehash_password(password, password_hash)
    return ok


def verify_and_maybe_rehash_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    if password_hash.startswith("scrypt$"):
        ok = _verify_password_scrypt(password, password_hash)
        return ok, None

    if password_hash.startswith("argon2id$"):
        ok = _verify_password_argon2id(password, password_hash)
        return ok, None

    if _is_legacy_hash(password_hash) and settings.password_legacy_accept:
        ok = _verify_password_legacy_sha256(password, password_hash)
        if ok and settings.password_migrate_on_login:
            return True, _hash_with_current_policy(password)
        return ok, None

    return False, None


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def make_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
