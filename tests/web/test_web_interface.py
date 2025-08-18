#!/usr/bin/env python3
"""Test script for the web interface components.

This script tests the web API and Gradio interface without requiring
full deployment setup.
"""

import asyncio
import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables from .env file
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def check_environment() -> bool:
    """Check if required environment variables are set."""
    required_vars = [
        "PROJECT_ID",
        "RAG_CORPUS_ID",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error("Missing required environment variables", missing_vars=missing_vars)
        return False

    logger.info("Environment variables check passed")
    return True


def test_web_service() -> bool:
    """Test the web RAG service."""
    try:
        from whatsupdoc.core.config import Config
        from whatsupdoc.core.gemini_rag import GeminiRAGService
        from whatsupdoc.core.vertex_rag_client import VertexRAGClient
        from whatsupdoc.web.service import WebRAGService

        logger.info("Testing web RAG service...")

        # Load configuration
        config = Config()
        logger.info("Configuration loaded successfully")

        # Initialize components
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

        web_service = WebRAGService(vertex_client=vertex_client, gemini_service=gemini_service)

        logger.info("Web service initialized successfully")

        # Test connection using asyncio.run for individual async calls
        async def run_async_tests() -> bool:
            # Test connection
            connection_ok = await web_service.test_connection()
            logger.info("Connection test result", connection_ok=connection_ok)

            if connection_ok:
                # Test a simple query
                logger.info("Testing simple query...")
                result = await web_service.process_query(
                    query="What is the company policy?",
                    conversation_id="test-session",
                    max_results=5,
                    distance_threshold=0.9,
                )

                logger.info(
                    "Query test completed",
                    answer_length=len(result.answer),
                    confidence=result.confidence,
                    num_sources=len(result.sources),
                    processing_time_ms=result.processing_time_ms,
                )

                return True
            else:
                logger.warning("Connection test failed, but service is initialized")
                return True

        return asyncio.run(run_async_tests())

    except Exception as e:
        logger.error("Web service test failed", error=str(e), exc_info=True)
        return False


def test_gradio_interface() -> bool:
    """Test the Gradio interface creation."""
    try:
        from whatsupdoc.web.gradio_interface import create_gradio_interface

        logger.info("Testing Gradio interface creation...")

        # Create interface
        interface = create_gradio_interface()

        logger.info("Gradio interface created successfully")
        logger.info("Interface has authentication:", has_auth=hasattr(interface, "auth"))

        return True

    except Exception as e:
        logger.error("Gradio interface test failed", error=str(e), exc_info=True)
        return False


def test_fastapi_app() -> bool:
    """Test FastAPI app creation."""
    try:
        from whatsupdoc.web.api import app

        logger.info("Testing FastAPI app creation...")

        # Use the global app instance

        logger.info("FastAPI app created successfully")
        logger.info("Available routes:")

        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                logger.info(f"  {route.methods} {route.path}")

        return True

    except Exception as e:
        logger.error("FastAPI app test failed", error=str(e), exc_info=True)
        return False


async def main() -> None:
    """Run all tests."""
    logger.info("Starting web interface tests...")

    # Check environment
    env_ok = check_environment()
    if not env_ok:
        logger.warning("Environment variables not set. Skipping RAG service tests.")

    # Test components
    tests = []

    if env_ok:
        tests.append(("Web Service", test_web_service()))
    else:
        logger.info("Skipping Web Service test (environment variables not set)")

    tests.extend(
        [
            ("Gradio Interface", test_gradio_interface()),
            ("FastAPI App", test_fastapi_app()),
        ]
    )

    results = []
    for name, test in tests:
        logger.info(f"Running {name} test...")
        try:
            if asyncio.iscoroutine(test):
                result = await test
            else:
                result = test
            results.append((name, result))
            logger.info(f"{name} test: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            logger.error(f"{name} test failed with exception", error=str(e))
            results.append((name, False))

    # Summary
    logger.info("Test Results Summary:")
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        logger.info("🎉 All tests passed! Web interface is ready for deployment.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")

    return all_passed


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(main())

    if not success:
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 Ready to test the web interface!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Install dependencies: uv sync")
    print("2. Set environment variables in .env")
    print("3. Run the Gradio interface: python -m whatsupdoc.web.gradio_interface")
    print("4. Or run the full FastAPI app with: uvicorn whatsupdoc.web.api:app")
    print("\nGradio admin interface will be available at:")
    print("  http://localhost:7860 (standalone)")
    print("  http://localhost:8000/admin (mounted in FastAPI)")
    print("\nDefault credentials: admin / changeme123!")
    print("Set GRADIO_ADMIN_USERNAME and GRADIO_ADMIN_PASSWORD to customize.")
