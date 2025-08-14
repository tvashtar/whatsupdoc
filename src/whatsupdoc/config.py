#!/usr/bin/env python3
"""Modern configuration using Pydantic for validation."""

import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Type-safe configuration with validation."""

    # GCP Settings
    project_id: str = Field(..., description="Google Cloud Project ID")
    location: str = Field(default="us-central1", description="GCP region")
    rag_corpus_id: str = Field(..., description="Vertex AI RAG Corpus ID")

    # Slack Settings
    slack_bot_token: str = Field(..., description="Slack Bot Token")
    slack_signing_secret: str = Field(..., description="Slack Signing Secret")
    slack_app_token: str | None = Field(default=None, description="Slack App Token for Socket Mode")

    # Feature Configuration
    use_grounded_generation: bool = Field(default=True)
    max_results: int = Field(default=7, ge=1, le=20)
    response_timeout: int = Field(default=30, ge=5, le=120)

    # Bot Configuration
    bot_name: str = Field(default="KnowledgeBot")
    rate_limit_per_user: int = Field(default=10, ge=1, le=100)
    rate_limit_window: int = Field(default=60, ge=30, le=3600)

    # Gemini Settings
    gemini_model: str = Field(default="gemini-2.5-flash-lite")
    use_vertex_ai: bool = Field(default=True)
    enable_rag_generation: bool = Field(default=True)
    max_context_length: int = Field(default=100000, ge=1000, le=1000000)
    answer_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    @field_validator("slack_app_token", mode="before")
    @classmethod
    def validate_slack_app_token(cls, v: str | None) -> str | None:
        """App token required only if not running in Cloud Run."""
        if not os.getenv("PORT") and not v:
            raise ValueError("SLACK_APP_TOKEN required for Socket Mode")
        return v

    @field_validator(
        "project_id", "rag_corpus_id", "slack_bot_token", "slack_signing_secret", mode="before"
    )
    @classmethod
    def validate_required_fields(cls, v: str | None) -> str:
        """Validate that required fields are not empty."""
        if not v or not v.strip():
            raise ValueError("This field is required and cannot be empty")
        return v.strip() if v else ""

    def validate_config(self) -> list[str]:
        """Additional validation for backwards compatibility."""
        errors = []

        if not self.project_id:
            errors.append("PROJECT_ID is required")
        if not self.rag_corpus_id:
            errors.append("RAG_CORPUS_ID is required")
        if not self.slack_bot_token:
            errors.append("SLACK_BOT_TOKEN is required")
        if not self.slack_signing_secret:
            errors.append("SLACK_SIGNING_SECRET is required")

        # Only require app token if not running in Cloud Run (no PORT env var)
        if not os.getenv("PORT") and not self.slack_app_token:
            errors.append("SLACK_APP_TOKEN is required for Socket Mode")

        return errors
