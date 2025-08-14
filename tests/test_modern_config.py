#!/usr/bin/env python3
"""Tests for modern Pydantic configuration."""

import os
from unittest.mock import patch

import pytest


@pytest.mark.unit
def test_modern_config_validation():
    """Test modern config validation with Pydantic."""
    from whatsupdoc.config import Config

    # Test with valid configuration (clear environment first)
    with patch.dict(
        os.environ,
        {
            "PROJECT_ID": "test-project",
            "RAG_CORPUS_ID": "test-corpus",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_SIGNING_SECRET": "test-secret",
            "PORT": "8080",  # Cloud Run mode, no app token needed
        },
        clear=True,
    ):
        config = Config()
        assert config.project_id == "test-project"
        assert config.rag_corpus_id == "test-corpus"
        assert config.slack_bot_token == "xoxb-test"
        assert config.gemini_model == "gemini-2.5-flash-lite"  # default


@pytest.mark.unit
def test_modern_config_socket_mode():
    """Test config validation for Socket Mode."""
    from pydantic import ValidationError

    from whatsupdoc.config import Config

    # Test that Pydantic validator catches missing app token in Socket Mode
    # Set up environment without PORT (Socket Mode) and without SLACK_APP_TOKEN
    with patch.dict(
        os.environ,
        {
            "PROJECT_ID": "test-project",
            "RAG_CORPUS_ID": "test-corpus",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_SIGNING_SECRET": "test-secret",
            # Explicitly exclude PORT and SLACK_APP_TOKEN to trigger Socket Mode validation
        },
        clear=True,
    ):
        # Create a custom config class that skips .env file loading for this test
        class TestConfig(Config):
            model_config = {
                **Config.model_config,
                "env_file": None,  # Disable .env file loading
            }

        # Should raise ValidationError during creation due to missing SLACK_APP_TOKEN
        with pytest.raises(ValidationError) as exc_info:
            TestConfig()

        # Verify the error message contains our validation
        assert "SLACK_APP_TOKEN required for Socket Mode" in str(exc_info.value)


@pytest.mark.unit
def test_modern_config_field_validation():
    """Test field validation and constraints."""
    from pydantic import ValidationError

    from whatsupdoc.config import Config

    with patch.dict(
        os.environ,
        {
            "PROJECT_ID": "test-project",
            "RAG_CORPUS_ID": "test-corpus",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_SIGNING_SECRET": "test-secret",
            "PORT": "8080",
            "MAX_RESULTS": "25",  # Above max limit of 20
            "ANSWER_TEMPERATURE": "3.0",  # Above max limit of 2.0
        },
    ):
        with pytest.raises(ValidationError) as exc_info:
            Config()

        errors = str(exc_info.value)
        assert "Input should be less than or equal to 20" in errors
        assert "Input should be less than or equal to 2" in errors


@pytest.mark.unit
def test_modern_config_defaults():
    """Test default values."""
    from whatsupdoc.config import Config

    with patch.dict(
        os.environ,
        {
            "PROJECT_ID": "test-project",
            "RAG_CORPUS_ID": "test-corpus",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "SLACK_SIGNING_SECRET": "test-secret",
            "PORT": "8080",
        },
        clear=True,
    ):
        config = Config()

        # Test defaults
        assert config.location == "us-central1"
        assert config.use_grounded_generation == True
        assert config.response_timeout == 30
        assert config.bot_name == "whatsupdoc"
        assert config.rate_limit_per_user == 10
        assert config.rate_limit_window == 60
        assert config.gemini_model == "gemini-2.5-flash-lite"
        assert config.use_vertex_ai == True
        assert config.enable_rag_generation == True
        assert config.max_context_length == 100000
        assert config.answer_temperature == 0.1
