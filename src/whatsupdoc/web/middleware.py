"""Middleware for web API security and validation."""

from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request origins against allowed domains."""

    def __init__(self, app: Starlette, allowed_origins: list[str]) -> None:
        """Initialize the middleware with allowed origins."""
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Validate origin header for API endpoints."""
        # Skip validation for health checks and docs
        if request.url.path in ["/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)

        # Skip validation for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        # Only validate for API endpoints (but allow OPTIONS preflight requests)
        if request.url.path.startswith("/api/") and request.method != "OPTIONS":
            origin = request.headers.get("origin")
            referer = request.headers.get("referer", "")
            widget_url = request.headers.get("x-widget-url", "")

            # Check if origin is in allowed list (exact match)
            if origin and origin in self.allowed_origins:
                logger.info("Origin validation passed", origin=origin, path=request.url.path)
                return await call_next(request)

            # Check widget URL header (preferred for bucket validation)
            if widget_url:
                for allowed_origin in self.allowed_origins:
                    if widget_url.startswith(allowed_origin):
                        logger.info(
                            "Widget URL validation passed",
                            widget_url=widget_url,
                            allowed_origin=allowed_origin,
                            path=request.url.path,
                        )
                        return await call_next(request)

            # Check if referer starts with any allowed origin (fallback)
            if referer:
                for allowed_origin in self.allowed_origins:
                    if referer.startswith(allowed_origin):
                        logger.info(
                            "Referer validation passed",
                            referer=referer,
                            allowed_origin=allowed_origin,
                            path=request.url.path,
                        )
                        return await call_next(request)

            # Log rejected request
            logger.warning(
                "Origin validation failed",
                origin=origin,
                referer=referer,
                widget_url=widget_url,
                path=request.url.path,
                allowed_origins=self.allowed_origins,
            )

            # Return 403 response directly instead of raising exception
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied: Invalid origin", "error_code": "FORBIDDEN"},
            )

        # Non-API requests pass through
        return await call_next(request)

    def _extract_origin_from_referer(self, referer: str) -> str:
        """Extract origin from referer header."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(referer)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return ""
