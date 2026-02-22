import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl
from urllib.request import urlopen

_cached_bot_id: str | None = None


def validate_telegram_payload(payload: dict, bot_token: str, max_age_seconds: int = 86400) -> bool:
    payload = dict(payload)
    their_hash = payload.pop("hash", None)
    if not their_hash:
        return False

    auth_date = payload.get("auth_date")
    try:
        auth_date_int = int(auth_date)
    except Exception:
        return False

    now = int(time.time())
    if now - auth_date_int > max_age_seconds:
        return False

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    check_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(check_hash, their_hash)


def parse_telegram_callback_query(raw_query: str) -> dict:
    return dict(parse_qsl(raw_query, keep_blank_values=True))


def resolve_bot_id(bot_token: str) -> str | None:
    global _cached_bot_id
    if _cached_bot_id:
        return _cached_bot_id
    try:
        with urlopen(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            if data.get("ok") and data.get("result", {}).get("id"):
                _cached_bot_id = str(data["result"]["id"])
                return _cached_bot_id
    except Exception:
        return None
    return None
