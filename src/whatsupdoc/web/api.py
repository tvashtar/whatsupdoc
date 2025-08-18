"""FastAPI web application for the whatsupdoc web interface.

This module provides REST API endpoints for the web chatbot interface and
integrates with the existing RAG components from the core module.
"""

import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from whatsupdoc.core.gemini_rag import GeminiRAGService
from whatsupdoc.core.vertex_rag_client import VertexRAGClient
from whatsupdoc.web.config import WebConfig
from whatsupdoc.web.middleware import OriginValidationMiddleware
from whatsupdoc.web.models import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from whatsupdoc.web.service import WebRAGService

logger = structlog.get_logger()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    global web_rag_service, app_config

    logger.info("Initializing web API services...")

    try:
        # Load configuration (already loaded globally, but load again for services)
        app_config = WebConfig()

        # Initialize RAG components
        vertex_client = VertexRAGClient(
            project_id=app_config.project_id,
            location=app_config.location,
            rag_corpus_id=app_config.rag_corpus_id,
        )

        gemini_service = GeminiRAGService(
            project_id=app_config.project_id,
            location=app_config.location,
            model=app_config.gemini_model,
            use_vertex_ai=app_config.use_vertex_ai,
            temperature=app_config.answer_temperature,
        )

        # Create unified web service
        web_rag_service = WebRAGService(vertex_client=vertex_client, gemini_service=gemini_service)

        logger.info(
            "Web API services initialized successfully", cors_origins=app_config.cors_origins_list
        )

    except Exception as e:
        logger.error("Failed to initialize web API services", error=str(e))
        raise

    yield

    # Shutdown logic (if needed in the future)
    logger.info("Shutting down web API services...")


# FastAPI app instance with lifespan
app = FastAPI(
    title="WhatsUpDoc Web API",
    description="Web API for RAG-based document question answering",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Configure CORS and middleware at app creation time
# Load config to get CORS origins
config = WebConfig()

# Add origin validation middleware for additional security FIRST (runs last)
app.add_middleware(OriginValidationMiddleware, allowed_origins=config.allowed_bucket_urls)

# Add CORS middleware for cross-origin requests SECOND (runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files for widget serving
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Global instances - will be initialized on startup
web_rag_service: WebRAGService | None = None
app_config: WebConfig | None = None


async def get_rag_service() -> WebRAGService:
    """Dependency to get the RAG service instance."""
    if web_rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return web_rag_service


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
        # Get config defaults
        max_results = chat_request.max_results or (app_config.max_results if app_config else 10)
        distance_threshold = chat_request.distance_threshold or (
            app_config.distance_threshold if app_config else 0.8
        )

        result = await rag_service.process_query(
            query=chat_request.query,
            conversation_id=conversation_id,
            max_results=max_results,
            distance_threshold=distance_threshold,
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
