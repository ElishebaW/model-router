import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""

    # Models (Per user instructions)
    GOOGLE_MODEL: str = "google/gemini-2.5-flash"
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"

    # Routing Thresholds (Static Routing)
    WORD_COUNT_THRESHOLD: int = 10
    CHAR_COUNT_THRESHOLD: int = 10

    # Backoff & Retry Settings
    MAX_RETRIES: int = 3
    RETRY_MIN_WAIT_SECONDS: float = 0.5
    RETRY_MAX_WAIT_SECONDS: float = 4.0
    REQUEST_TIMEOUT_SECONDS: float = 15.0

    # Application Configuration
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
