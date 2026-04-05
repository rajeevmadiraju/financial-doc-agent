from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    openai_api_key: str

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    collection_name: str = "financial_docs"

    # Models
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k_retrieval: int = 6

    # App
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()