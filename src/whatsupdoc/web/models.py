"""Web API models and schemas for the whatsupdoc web interface.

This module defines Pydantic models for request/response schemas used by the
FastAPI web endpoints and Gradio interface.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    query: str = Field(
        ..., description="The user's question or query", min_length=1, max_length=5000
    )
    conversation_id: str | None = Field(None, description="Optional conversation ID for context")
    max_results: int | None = Field(
        10, description="Maximum number of results to return", ge=1, le=50
    )
    confidence_threshold: float | None = Field(
        0.5, description="Minimum confidence threshold", ge=0.0, le=1.0
    )


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    answer: str = Field(..., description="The generated answer")
    confidence: float = Field(..., description="Confidence score for the answer", ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list, description="List of source documents")
    conversation_id: str = Field(..., description="Conversation ID for follow-up queries")
    response_time_ms: int = Field(..., description="Response time in milliseconds")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    request_id: str | None = Field(None, description="Request ID for debugging")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Current timestamp")
    dependencies: dict[str, str] = Field(default_factory=dict, description="Status of dependencies")
