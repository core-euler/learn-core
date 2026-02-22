from dataclasses import dataclass


@dataclass
class Settings:
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    access_ttl_minutes: int = 60


settings = Settings()
