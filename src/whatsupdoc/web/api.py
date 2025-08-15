"""FastAPI web application for the whatsupdoc web interface.

This module provides REST API endpoints for the web chatbot interface and
integrates with the existing RAG components from the core module.
"""

import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from whatsupdoc.core.gemini_rag import GeminiRAGService
from whatsupdoc.core.vertex_rag_client import VertexRAGClient
from whatsupdoc.web.config import WebConfig
from whatsupdoc.web.gradio_interface import create_authenticated_interface
from whatsupdoc.web.models import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from whatsupdoc.web.service import WebRAGService

logger = structlog.get_logger()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# FastAPI app instance
app = FastAPI(
    title="WhatsUpDoc Web API",
    description="Web API for RAG-based document question answering",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be configured properly during startup
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global instances - will be initialized on startup
web_rag_service: WebRAGService | None = None
config: WebConfig | None = None


async def get_rag_service() -> WebRAGService:
    """Dependency to get the RAG service instance."""
    if web_rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return web_rag_service


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    global web_rag_service, config

    logger.info("Initializing web API services...")

    try:
        # Load configuration
        config = WebConfig()

        # Initialize RAG components
        vertex_client = VertexRAGClient(
            project_id=config.project_id,
            location=config.location,
            rag_corpus_id=config.rag_corpus_id,
        )

        gemini_service = GeminiRAGService(
            project_id=config.project_id,
            location=config.location,
            model=config.gemini_model,
            use_vertex_ai=config.use_vertex_ai,
            temperature=config.answer_temperature,
        )

        # Create unified web service
        web_rag_service = WebRAGService(vertex_client=vertex_client, gemini_service=gemini_service)

        # Mount Gradio interface at /admin
        try:
            import gradio as gr

            gradio_interface = create_authenticated_interface()

            # Mount the Gradio app
            gr.mount_gradio_app(app, gradio_interface, path="/admin")

            logger.info("Gradio interface mounted at /admin")

        except Exception as e:
            logger.error("Failed to mount Gradio interface", error=str(e))
            # Continue without Gradio interface

        logger.info("Web API services initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize web API services", error=str(e))
        raise


@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    dependencies = {
        "rag_service": "unhealthy",
        "vertex_ai": "disconnected",
        "gemini": "disconnected",
    }

    if web_rag_service:
        try:
            connection_ok = await web_rag_service.test_connection()
            dependencies["rag_service"] = "healthy" if connection_ok else "unhealthy"
            dependencies["vertex_ai"] = "connected" if connection_ok else "disconnected"
            dependencies["gemini"] = "connected" if connection_ok else "disconnected"
        except Exception:
            pass  # Keep default unhealthy status

    return HealthResponse(
        status="healthy" if web_rag_service else "unhealthy",
        version="0.1.0",
        timestamp=datetime.now(UTC).isoformat(),
        dependencies=dependencies,
    )


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    rag_service: WebRAGService = Depends(get_rag_service),
) -> ChatResponse:
    """Main chat endpoint for processing user queries.

    Rate limited to 10 requests per minute per IP address.
    """
    request_id = str(uuid.uuid4())
    conversation_id = chat_request.conversation_id or str(uuid.uuid4())

    logger.info(
        "Processing chat request",
        request_id=request_id,
        conversation_id=conversation_id,
        query_length=len(chat_request.query),
    )

    try:
        # Process the query using the unified RAG service
        result = await rag_service.process_query(
            query=chat_request.query,
            conversation_id=conversation_id,
            max_results=chat_request.max_results or 10,
            confidence_threshold=chat_request.confidence_threshold or 0.5,
        )

        logger.info(
            "Chat request processed successfully",
            request_id=request_id,
            response_time_ms=result.processing_time_ms,
            confidence=result.confidence,
        )

        return ChatResponse(
            answer=result.answer,
            confidence=result.confidence,
            sources=result.sources,
            conversation_id=conversation_id,
            response_time_ms=result.processing_time_ms,
        )

    except Exception as e:
        logger.error(
            "Error processing chat request", request_id=request_id, error=str(e), exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to process query",
                error_code="PROCESSING_ERROR",
                request_id=request_id,
            ).model_dump(),
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    request_id = str(uuid.uuid4())

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", error_code="INTERNAL_ERROR", request_id=request_id
        ).model_dump(),
    )


def configure_cors(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    """Configure CORS middleware for the FastAPI app."""
    if allowed_origins is None:
        # Default to common development origins
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://policyisforlovers.com",
            "https://www.policyisforlovers.com",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    logger.info("CORS configured", allowed_origins=allowed_origins)


def create_web_app(cors_origins: list[str] | None = None, mount_gradio: bool = True) -> FastAPI:
    """Create and configure the FastAPI web application."""
    configure_cors(app, cors_origins)

    if mount_gradio:
        # Mount Gradio interface at /admin
        try:
            import gradio as gr

            gradio_interface = create_authenticated_interface()

            # Mount the Gradio app
            gr.mount_gradio_app(app, gradio_interface, path="/admin")

            logger.info("Gradio interface mounted at /admin")

        except Exception as e:
            logger.error("Failed to mount Gradio interface", error=str(e))
            # Continue without Gradio interface

    return app
