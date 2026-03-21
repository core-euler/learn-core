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

    # LLM adapter policy
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "8"))
    llm_fallback_lecture: str = os.getenv(
        "LLM_FALLBACK_LECTURE",
        "Сервис AI временно недоступен. Попробуй ещё раз через минуту.",
    )
    llm_fallback_consultant: str = os.getenv(
        "LLM_FALLBACK_CONSULTANT",
        "Консультант временно недоступен. Попробуй повторить запрос позже.",
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "default")  # default|cometapi
    cometapi_base_url: str = os.getenv("COMETAPI_BASE_URL", "https://api.cometapi.com")
    cometapi_api_key: str = os.getenv("COMETAPI_API_KEY", "")
    cometapi_chat_model: str = os.getenv("COMETAPI_CHAT_MODEL", "gpt-5.2")
    cometapi_exam_model: str = os.getenv("COMETAPI_EXAM_MODEL", "gpt-5.2")
    cometapi_embed_model: str = os.getenv("COMETAPI_EMBED_MODEL", "text-embedding-3-small")

    # Minimal RAG contract policy
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "3"))
    rag_chunk_size_chars: int = int(os.getenv("RAG_CHUNK_SIZE_CHARS", "900"))
    rag_chunk_overlap_chars: int = int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", "120"))
    rag_embedding_batch_size: int = int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "32"))


settings = Settings()
