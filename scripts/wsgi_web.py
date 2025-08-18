#!/usr/bin/env python3
"""WSGI entry point for FastAPI web application production deployment."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

# Load environment variables
load_dotenv()


def create_app() -> FastAPI:
    """Create and configure the FastAPI app for WSGI deployment."""
    from whatsupdoc.web.api import app

    return app


# Create the WSGI application
application = create_app()

if __name__ == "__main__":
    # For local testing
    import uvicorn

    uvicorn.run(application, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
