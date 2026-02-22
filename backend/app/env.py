import os


def is_test_mode() -> bool:
    return os.getenv("APP_ENV", "dev") == "test"


def cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def cookie_samesite() -> str:
    return os.getenv("COOKIE_SAMESITE", "lax")
