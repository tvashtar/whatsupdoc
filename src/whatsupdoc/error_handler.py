#!/usr/bin/env python3
"""Modern error handling and retry logic using tenacity."""

from collections.abc import Callable
from typing import Any, TypeVar

import structlog
from google.api_core.exceptions import RetryError, ServiceUnavailable
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()

T = TypeVar("T")


class ModernErrorHandler:
    """Enhanced error handling with exponential backoff and proper logging."""

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ServiceUnavailable, RetryError)),
        reraise=True,
    )
    async def robust_api_call(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Robust API call with exponential backoff."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.warning("API call failed, retrying", error=str(e), func=func.__name__)
            raise

    @staticmethod
    def handle_slack_error(error: Exception, context: dict[str, Any]) -> str:
        """Standardized Slack error message formatting."""
        logger.error("Slack operation failed", error=str(error), **context)

        error_str = str(error).lower()
        if "rate_limited" in error_str:
            return "⚠️ Service temporarily busy. Please try again in a moment."
        elif "timeout" in error_str:
            return "⏱️ Request timed out. Please try a simpler question."
        else:
            return "❌ Sorry, I encountered a technical issue. Please try again later."

    @staticmethod
    def handle_rag_error(error: Exception, context: dict[str, Any]) -> str:
        """Standardized RAG error message formatting."""
        logger.error("RAG operation failed", error=str(error), **context)

        error_str = str(error).lower()
        if "quota" in error_str or "limit" in error_str:
            return "⚠️ Service capacity reached. Please try again in a few minutes."
        elif "timeout" in error_str:
            return "⏱️ Search timed out. Please try a more specific question."
        elif "authentication" in error_str or "unauthorized" in error_str:
            return "🔒 Authentication issue. Please contact support."
        else:
            return "❌ Search service unavailable. Please try again later."
