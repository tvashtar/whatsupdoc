"""Gradio interface for RAG pipeline testing and administration.

This module provides a simple Gradio-based web interface for testing
the RAG pipeline with basic authentication.
"""

import asyncio
import os

import gradio as gr
import structlog
from dotenv import load_dotenv

from whatsupdoc.core.config import Config
from whatsupdoc.core.gemini_rag import GeminiRAGService
from whatsupdoc.core.vertex_rag_client import VertexRAGClient
from whatsupdoc.web.service import WebRAGService

# Load environment variables
load_dotenv()

logger = structlog.get_logger()

# Global service instance
_web_rag_service: WebRAGService | None = None


def initialize_rag_service() -> WebRAGService:
    """Initialize the RAG service for Gradio interface."""
    global _web_rag_service

    if _web_rag_service is None:
        logger.info("Initializing RAG service for Gradio interface")

        # Load configuration
        config = Config()

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

        _web_rag_service = WebRAGService(vertex_client=vertex_client, gemini_service=gemini_service)

        logger.info("RAG service initialized for Gradio interface")

    return _web_rag_service


async def process_query_async(
    query: str, max_results: int = 10, confidence_threshold: float = 0.5
) -> tuple[str, str, str, str]:
    """Process a query through the RAG pipeline.

    Returns:
        Tuple of (answer, confidence, sources, processing_time)

    """
    if not query or not query.strip():
        return "Please enter a question.", "0.00", "No sources", "0ms"

    try:
        rag_service = initialize_rag_service()

        result = await rag_service.process_query(
            query=query.strip(),
            conversation_id="gradio-session",
            max_results=max_results,
            confidence_threshold=confidence_threshold,
        )

        # Format sources as a readable list
        sources_text = (
            "\n".join([f"• {source}" for source in result.sources])
            if result.sources
            else "No sources found"
        )

        return (
            result.answer,
            f"{result.confidence:.2f}",
            sources_text,
            f"{result.processing_time_ms}ms",
        )

    except Exception as e:
        logger.error("Error in Gradio query processing", error=str(e), exc_info=True)
        return (f"Error processing query: {str(e)}", "0.00", "Error occurred", "N/A")


def process_query_sync(
    query: str, max_results: int = 10, confidence_threshold: float = 0.5
) -> tuple[str, str, str, str]:
    """Synchronous wrapper for the async query processing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            process_query_async(query, max_results, confidence_threshold)
        )
    finally:
        loop.close()


async def test_connection_async() -> str:
    """Test the RAG service connections."""
    try:
        rag_service = initialize_rag_service()
        connection_ok = await rag_service.test_connection()

        if connection_ok:
            return "✅ All services connected successfully"
        else:
            return "❌ Service connection failed"

    except Exception as e:
        logger.error("Connection test failed", error=str(e))
        return f"❌ Connection test error: {str(e)}"


def test_connection_sync() -> str:
    """Synchronous wrapper for connection testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_connection_async())
    finally:
        loop.close()


def create_gradio_interface() -> gr.Blocks:
    """Create the Gradio interface for RAG testing."""
    with gr.Blocks(
        title="WhatsUpDoc RAG Interface",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
            margin: auto !important;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .status-box {
            background-color: #f0f0f0;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        """,
    ) as interface:
        # Header
        gr.Markdown(
            """
            # 🤖 WhatsUpDoc RAG Interface

            Test the RAG (Retrieval-Augmented Generation) pipeline for document question answering.
            """,
            elem_classes=["header"],
        )

        # Main query interface
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Query Testing")

                query_input = gr.Textbox(
                    label="Question",
                    placeholder="Ask a question about the company documents...",
                    lines=3,
                    max_lines=5,
                )

                with gr.Row():
                    max_results = gr.Slider(
                        label="Max Results", minimum=1, maximum=20, value=10, step=1
                    )
                    confidence_threshold = gr.Slider(
                        label="Confidence Threshold", minimum=0.0, maximum=1.0, value=0.5, step=0.1
                    )

                submit_btn = gr.Button("Submit Query", variant="primary")

            with gr.Column(scale=3):
                gr.Markdown("### 📋 Results")

                answer_output = gr.Textbox(label="Answer", lines=8, max_lines=15, interactive=False)

                with gr.Row():
                    confidence_output = gr.Textbox(
                        label="Confidence Score", interactive=False, scale=1
                    )
                    processing_time = gr.Textbox(
                        label="Processing Time", interactive=False, scale=1
                    )

                sources_output = gr.Textbox(
                    label="Sources", lines=6, max_lines=10, interactive=False
                )

        # Connection test section (moved to bottom)
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🔧 Service Status")
                connection_status = gr.Textbox(
                    label="Connection Status",
                    value="Click 'Test Connection' to check services",
                    interactive=False,
                    elem_classes=["status-box"],
                )
                test_btn = gr.Button("Test Connection", variant="secondary")

        # Event handlers
        test_btn.click(fn=test_connection_sync, outputs=connection_status)

        submit_btn.click(
            fn=process_query_sync,
            inputs=[query_input, max_results, confidence_threshold],
            outputs=[answer_output, confidence_output, sources_output, processing_time],
        )

        # Allow Enter key to submit query
        query_input.submit(
            fn=process_query_sync,
            inputs=[query_input, max_results, confidence_threshold],
            outputs=[answer_output, confidence_output, sources_output, processing_time],
        )

    return interface


def get_auth_credentials() -> tuple[str, str]:
    """Get authentication credentials from environment variables."""
    username = os.getenv("GRADIO_ADMIN_USERNAME", "admin")
    password = os.getenv("GRADIO_ADMIN_PASSWORD", "changeme123!")

    if password == "changeme123!":
        logger.warning(
            "Using default Gradio admin password. "
            "Set GRADIO_ADMIN_PASSWORD environment variable for security."
        )

    return username, password


def launch_gradio_interface(
    host: str = "127.0.0.1", port: int = 7860, share: bool = False, debug: bool = False
) -> None:
    """Launch the Gradio interface."""
    logger.info("Launching Gradio interface", host=host, port=port, share=share)

    interface = create_gradio_interface()

    # Get authentication credentials
    username, password = get_auth_credentials()

    interface.launch(
        server_name=host,
        server_port=port,
        share=share,
        debug=debug,
        show_error=True,
        quiet=not debug,
        auth=(username, password),
        auth_message="Enter admin credentials to access the RAG testing interface.",
    )


if __name__ == "__main__":
    # For standalone testing
    launch_gradio_interface(debug=True)
