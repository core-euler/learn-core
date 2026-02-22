import os
from dataclasses import dataclass


@dataclass
class Settings:
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_ttl_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
