#!/usr/bin/env python3
"""Tests for modern error handling."""

import pytest


@pytest.mark.unit
def test_error_handler_slack_errors():
    """Test error handler for Slack-specific errors."""
    from whatsupdoc.error_handler import ModernErrorHandler

    # Test rate limit error
    rate_limit_error = Exception("rate_limited")
    message = ModernErrorHandler.handle_slack_error(rate_limit_error, {})
    assert "Service temporarily busy" in message

    # Test timeout error
    timeout_error = Exception("timeout occurred")
    message = ModernErrorHandler.handle_slack_error(timeout_error, {})
    assert "Request timed out" in message

    # Test generic error
    generic_error = Exception("something went wrong")
    message = ModernErrorHandler.handle_slack_error(generic_error, {})
    assert "technical issue" in message


@pytest.mark.unit
def test_error_handler_rag_errors():
    """Test error handler for RAG-specific errors."""
    from whatsupdoc.error_handler import ModernErrorHandler

    # Test quota error
    quota_error = Exception("quota exceeded")
    message = ModernErrorHandler.handle_rag_error(quota_error, {})
    assert "Service capacity reached" in message

    # Test authentication error
    auth_error = Exception("authentication failed")
    message = ModernErrorHandler.handle_rag_error(auth_error, {})
    assert "Authentication issue" in message
