import os
from dataclasses import dataclass


@dataclass
class Settings:
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_ttl_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_bot_id: str = os.getenv("TELEGRAM_BOT_ID", "")

    # Password/KDF policy
    password_kdf_algorithm: str = os.getenv("PASSWORD_KDF_ALGORITHM", "scrypt")  # scrypt|argon2id
    password_migrate_on_login: bool = os.getenv("PASSWORD_MIGRATE_ON_LOGIN", "true").lower() == "true"
    password_legacy_accept: bool = os.getenv("PASSWORD_LEGACY_ACCEPT", "true").lower() == "true"

    # scrypt tuning knobs
    password_scrypt_n: int = int(os.getenv("PASSWORD_SCRYPT_N", "16384"))
    password_scrypt_r: int = int(os.getenv("PASSWORD_SCRYPT_R", "8"))
    password_scrypt_p: int = int(os.getenv("PASSWORD_SCRYPT_P", "1"))
    password_scrypt_dklen: int = int(os.getenv("PASSWORD_SCRYPT_DKLEN", "64"))
    password_scrypt_salt_bytes: int = int(os.getenv("PASSWORD_SCRYPT_SALT_BYTES", "16"))

    # argon2id tuning knobs
    password_argon2_time_cost: int = int(os.getenv("PASSWORD_ARGON2_TIME_COST", "3"))
    password_argon2_memory_cost_kib: int = int(os.getenv("PASSWORD_ARGON2_MEMORY_COST_KIB", "65536"))
    password_argon2_parallelism: int = int(os.getenv("PASSWORD_ARGON2_PARALLELISM", "2"))
    password_argon2_hash_len: int = int(os.getenv("PASSWORD_ARGON2_HASH_LEN", "32"))
    password_argon2_salt_bytes: int = int(os.getenv("PASSWORD_ARGON2_SALT_BYTES", "16"))

    # Content ingestion / validation
    content_validate_on_startup: bool = os.getenv("CONTENT_VALIDATE_ON_STARTUP", "true").lower() == "true"


settings = Settings()
