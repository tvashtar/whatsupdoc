"""Web-specific configuration management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebConfig(BaseSettings):
    """Web interface configuration - only requires RAG-related environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Google Cloud / Vertex AI settings (required for RAG)
    project_id: str = Field(alias="PROJECT_ID")
    location: str = "us-central1"
    rag_corpus_id: str

    # Gemini settings
    gemini_model: str = "gemini-2.5-flash-lite"
    use_vertex_ai: bool = True
    answer_temperature: float = 0.1

    # RAG pipeline settings (from core config)
    max_results: int = 10  # Maximum search results (configurable via MAX_RESULTS env var)
    distance_threshold: float = 0.8  # Vector distance threshold for filtering results
    max_context_length: int = 100000  # Maximum context for Gemini

    # Web interface settings
    # CORS needs broad origin for preflight, custom middleware validates specific bucket via referer
    cors_origins_list: list[str] = [
        "https://storage.googleapis.com"
    ]  # Broad origin for CORS preflight
    allowed_bucket_urls: list[str] = [
        "https://storage.googleapis.com/whatsupdoc-widget-static"
    ]  # Specific buckets for validation

    # Optional Google Cloud credentials (will use default if not specified)
    google_cloud_credentials_path: str | None = None
