from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Encryption — generate once: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    fernet_key: str

    # LLM
    openai_api_key: str

    # Auth — leave empty to disable in local dev
    api_key: str = ""

    # RAG
    security_docs_path: str = "data/security_docs.txt"

    # Storage
    db_path: str = "data/alerts.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
