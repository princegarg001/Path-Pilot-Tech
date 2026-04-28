"""
═══════════════════════════════════════════════════════════════
PathPilot-AI Backend — Configuration
═══════════════════════════════════════════════════════════════
Central config loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file or environment variables."""

    # ── HuggingFace ──
    hf_api_token: str = ""
    hf_base_url: str = "https://api-inference.huggingface.co/models"

    # ── Model IDs ──
    model_skill_ner: str = "jjzha/jobbert_skill_extraction"
    model_summarizer: str = "facebook/bart-large-cnn"
    model_classifier: str = "facebook/bart-large-mnli"
    model_embeddings: str = "sentence-transformers/all-mpnet-base-v2"
    model_text_gen: str = "mistralai/Mistral-7B-Instruct-v0.3"
    model_keyphrase: str = "ml6team/keyphrase-extraction-kbir-inspec"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: str = "*"

    # ── Reliability ──
    max_retries: int = 3
    cache_ttl: int = 3600  # seconds

    # ── Logging ──
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — loaded once on startup."""
    return Settings()
