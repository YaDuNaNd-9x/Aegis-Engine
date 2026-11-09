from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# AEGIS ENGINE ROOT DIRECTORY
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):

    # Application
    APP_NAME: str = "Aegis Engine"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Backend
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Ollama connection
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=180.0, gt=0)
    OLLAMA_CONNECT_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0)
    OLLAMA_HEALTH_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0)

    # Local models
    FAST_MODEL: str = "qwen2.5:3b"
    REASONING_MODEL: str = "qwen2.5:7b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Generation defaults
    LLM_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=2048, gt=0)
    LLM_KEEP_ALIVE: str = "0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/aegis.db"

    # Vector Database
    CHROMA_PERSIST_DIRECTORY: str = "./storage/chroma"

    # File Storage
    DOCUMENT_STORAGE: str = "./data/documents"
    UPLOAD_STORAGE: str = "./data/uploads"
    REPORT_STORAGE: str = "./storage/reports"

    # Security
    ALLOW_EXTERNAL_NETWORK: bool = False
    MAX_UPLOAD_SIZE_MB: int = Field(default=25, gt=0)
    MAX_EXECUTION_TIME: int = Field(default=10, gt=0)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()


def get_project_root() -> Path:
    return PROJECT_ROOT