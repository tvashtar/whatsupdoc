#!/usr/bin/env python3
"""Modern Slack bot implementation using latest async patterns."""

import asyncio
import os
from collections.abc import Callable
from typing import Any

import structlog
from flask import Flask, Response, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from .config import Config
from .error_handler import ModernErrorHandler
from .gemini_rag import GeminiRAGService, RAGResponse
from .vertex_rag_client import VertexRAGClient

logger = structlog.get_logger()

# Rate limiting storage (simple in-memory for now)
user_query_count: dict[str, int] = {}
user_last_reset: dict[str, float] = {}


class SlackBot:
    """Modern Slack bot with proper async patterns and enhanced error handling."""

    def __init__(self) -> None:
        """Initialize the Slack bot with configuration and clients."""
        self.config = Config()

        # Validate configuration
        errors = self.config.validate_config()
        if errors:
            logger.error("Configuration errors", errors=errors)
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        # Use regular App with proper async/sync patterns
        self.app = App(
            token=self.config.slack_bot_token,
            signing_secret=self.config.slack_signing_secret,
            process_before_response=True,
        )

        # Initialize clients with modern implementations
        self.search_client = VertexRAGClient(
            project_id=self.config.project_id,
            location=self.config.location,
            rag_corpus_id=self.config.rag_corpus_id,
        )

        # Initialize Gemini RAG service if enabled
        self.rag_service: GeminiRAGService | None = None
        if self.config.enable_rag_generation:
            self.rag_service = GeminiRAGService(
                project_id=self.config.project_id,
                location=self.config.location,
                model=self.config.gemini_model,
                use_vertex_ai=self.config.use_vertex_ai,
                temperature=self.config.answer_temperature,
            )

        self._setup_handlers()

        logger.info(
            "Modern Slack bot initialized",
            project_id=self.config.project_id,
            bot_name=self.config.bot_name,
        )

    def _setup_handlers(self) -> None:
        """Set up sync event handlers with async logic wrapped properly."""

        @self.app.event("app_mention")
        def handle_mention(
            event: dict[str, Any], say: Callable[..., Any], client: WebClient
        ) -> None:
            asyncio.run(self._handle_query_async(event, say, client, event["text"]))

        @self.app.command("/ask")
        def handle_ask_command(
            ack: Callable[[], None],
            respond: Callable[..., Any],
            command: dict[str, Any],
            client: WebClient,
        ) -> None:
            ack()  # Acknowledge immediately
            asyncio.run(self._handle_query_async(command, respond, client, command["text"]))

        @self.app.message("")
        def handle_dm(message: dict[str, Any], say: Callable[..., Any], client: WebClient) -> None:
            if message.get("channel_type") == "im":
                asyncio.run(self._handle_query_async(message, say, client, message["text"]))

    async def _handle_query_async(
        self,
        event_data: dict[str, Any],
        respond_func: Callable[..., Any],
        client: WebClient,
        query_text: str,
    ) -> None:
        """Modern async query handler with proper error handling."""
        user_id = event_data.get("user") or event_data.get("user_id")
        channel_id = event_data.get("channel")

        logger.info("Processing query", user_id=user_id, query=query_text)

        # Rate limiting check
        if user_id and not await self._check_rate_limit_async(user_id):
            respond_func({"text": "⚠️ Rate limit exceeded. Please wait before trying again."})
            return

        # Clean and validate query
        clean_query = self._clean_query(query_text)
        if not clean_query or len(clean_query.strip()) < 3:
            respond_func({"text": "Please provide a valid research question."})
            return

        # Send loading message
        loading_response = respond_func({"text": f"🔍 Searching for: `{clean_query}`..."})

        # Extract timestamp for potential updates (may be None for webhooks)
        loading_ts = self._extract_timestamp(loading_response)

        try:
            # Search with modern error handling
            results = await ModernErrorHandler.robust_api_call(
                self.search_client.search_async,
                query=clean_query,
                max_results=self.config.max_results,
            )

            if results and self.rag_service:
                # Generate answer using RAG
                rag_response: RAGResponse = await ModernErrorHandler.robust_api_call(
                    self.rag_service.generate_answer_async,
                    query=clean_query,
                    search_results=results,
                    max_context_length=self.config.max_context_length,
                )

                response_blocks = self._format_rag_response(clean_query, rag_response)

                # Update loading message if timestamp is available
                if loading_ts and channel_id:
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_ts,
                        blocks=response_blocks,
                        text=f"Generated answer for: {clean_query}",
                    )
                else:
                    # For webhook responses, send a new message instead of updating
                    respond_func(
                        {
                            "blocks": response_blocks,
                            "text": f"Generated answer for: {clean_query}",
                        }
                    )
            else:
                # Handle no results case
                if loading_ts and channel_id:
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_ts,
                        text=f"🤔 No relevant documents found for: `{clean_query}`",
                    )
                else:
                    # For webhook responses, send a new message instead of updating
                    respond_func(
                        {
                            "text": f"🤔 No relevant documents found for: `{clean_query}`",
                        }
                    )

        except Exception as e:
            error_context = {"query": clean_query, "user_id": user_id}
            error_message = ModernErrorHandler.handle_rag_error(e, error_context)

            if loading_ts and channel_id:
                client.chat_update(
                    channel=channel_id,
                    ts=loading_ts,
                    text=error_message,
                )
            else:
                # For webhook responses, send a new message instead of updating
                respond_func(
                    {
                        "text": error_message,
                    }
                )

    def _extract_timestamp(self, response: dict[str, Any] | object) -> str | None:
        """Extract timestamp from different Slack response types.

        Args:
            response: Could be WebhookResponse (from respond function in slash commands)
                     or dict (from say function in mentions/DMs)

        Returns:
            Timestamp string if available, None otherwise

        """
        if hasattr(response, "body"):
            # WebhookResponse object - no ts available since it's for initial response
            # For webhooks, we can't update the message since there's no ts
            return None
        elif isinstance(response, dict):
            # Dictionary response (from say function) - has ts field
            return response.get("ts")
        else:
            # Unknown response type
            return None

    def _clean_query(self, text: str) -> str:
        """Clean and normalize query text."""
        import re

        text = text.strip()

        # Remove bot mentions like <@U123456>
        text = re.sub(r"<@U[A-Z0-9]+>", "", text).strip()

        # Remove /ask command if present
        if text.startswith("/ask"):
            text = text[4:].strip()

        return text

    async def _check_rate_limit_async(self, user_id: str) -> bool:
        """Async rate limiting check."""
        import time

        current_time = time.time()

        # Reset counter if window expired
        if user_id in user_last_reset:
            if current_time - user_last_reset[user_id] >= self.config.rate_limit_window:
                user_query_count[user_id] = 0
                user_last_reset[user_id] = current_time
        else:
            user_last_reset[user_id] = current_time
            user_query_count[user_id] = 0

        # Check current count
        current_count = user_query_count.get(user_id, 0)
        if current_count >= self.config.rate_limit_per_user:
            return False

        # Increment count
        user_query_count[user_id] = current_count + 1
        return True

    def _format_rag_response(self, query: str, rag_response: RAGResponse) -> list[dict[str, Any]]:
        """Format a comprehensive RAG response with generated answer and sources."""
        confidence_emoji = (
            "🟢"
            if rag_response.confidence_score >= 0.7
            else "🟡"
            if rag_response.confidence_score >= 0.4
            else "🔴"
        )

        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🤖 Answer: {query}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{confidence_emoji} Confidence: {rag_response.confidence_score:.0%} | "
                        f"Sources: {len(rag_response.sources)}"
                    ),
                },
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": rag_response.answer}},
        ]

        # Add condensed sources section if available
        if rag_response.sources:
            # Group sources by document
            doc_counts: dict[str, int] = {}
            for result in rag_response.sources:
                if result.source_uri and result.source_uri.startswith("gs://"):
                    filename = result.source_uri.split("/")[-1]
                    doc_counts[filename] = doc_counts.get(filename, 0) + 1
                else:
                    doc_counts[result.title] = doc_counts.get(result.title, 0) + 1

            # Create source summary
            source_summary = []
            for doc, count in sorted(doc_counts.items(), key=lambda x: x[1], reverse=True):
                source_summary.append(f"📄 {doc} ({count})")

            # Get top result for snippet
            top_result = rag_response.sources[0]
            top_confidence_emoji = (
                "🟢"
                if top_result.confidence_score >= 0.7
                else "🟡"
                if top_result.confidence_score >= 0.4
                else "🔴"
            )

            blocks.extend(
                [
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📚 *Sources ({len(rag_response.sources)} chunks):*\n"
                            + " • ".join(source_summary[:3])
                            + ("..." if len(source_summary) > 3 else ""),
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"*Top Match:* {top_confidence_emoji} "
                                f"{top_result.confidence_score:.0%} relevance\n"
                                f"```{top_result.content[:200]}"
                                f"{'...' if len(top_result.content) > 200 else ''}```"
                            ),
                        },
                    },
                ]
            )

        # Add footer with tips
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                "💡 *Tip:* This answer was generated from your company documents. "
                                "For follow-up questions, try asking for more details or "
                                "clarification on specific points."
                            ),
                        }
                    ],
                },
            ]
        )

        return blocks

    def get_flask_app(self) -> Flask:
        """Create and return Flask app for WSGI deployment."""
        flask_app = Flask(__name__)
        handler = SlackRequestHandler(self.app)

        @flask_app.route("/slack/events", methods=["POST"])
        def slack_events() -> Response:
            return handler.handle(request)

        @flask_app.route("/health", methods=["GET"])
        def health_check() -> tuple[dict[str, str], int]:
            return {"status": "healthy", "service": "whatsupdoc"}, 200

        @flask_app.route("/", methods=["GET"])
        def root() -> tuple[dict[str, str], int]:
            return {
                "status": "running",
                "service": "whatsupdoc-slack-bot",
                "version": "modernized",
            }, 200

        return flask_app

    async def start_async(self) -> None:
        """Async startup with proper resource management."""
        # Test connections
        await self._test_connections()

        port = os.environ.get("PORT")

        if port:
            # HTTP mode for Cloud Run
            logger.info(f"Starting in HTTP mode on port {port}")
            flask_app = Flask(__name__)
            handler = SlackRequestHandler(self.app)

            @flask_app.route("/slack/events", methods=["POST"])
            def slack_events() -> Response:
                return handler.handle(request)

            @flask_app.route("/health", methods=["GET"])
            def health_check() -> tuple[dict[str, str], int]:
                return {"status": "healthy", "service": "whatsupdoc"}, 200

            # Run Flask app
            flask_app.run(host="0.0.0.0", port=int(port))
        else:
            # Socket mode for development
            logger.info("Starting in Socket Mode")
            if not self.config.slack_app_token:
                raise ValueError("SLACK_APP_TOKEN is required for Socket Mode")
            socket_handler = SocketModeHandler(self.app, self.config.slack_app_token)
            socket_handler.start()

    async def _test_connections(self) -> None:
        """Test all external connections with graceful degradation."""
        services_available = []

        # Test Vertex AI connection
        try:
            if await self.search_client.test_connection_async():
                services_available.append("Vertex AI RAG")
                logger.info("Vertex AI RAG Engine: ✅ Connected")
            else:
                logger.warning(
                    "Vertex AI RAG Engine: ⚠️ Not available, will return empty search results"
                )
        except Exception as e:
            logger.warning("Vertex AI RAG Engine: ❌ Connection failed", error=str(e))

        # Test Gemini connection
        if self.rag_service:
            try:
                if await self.rag_service.test_connection_async():
                    services_available.append("Gemini AI")
                    logger.info("Gemini AI: ✅ Connected")
                else:
                    logger.warning("Gemini AI: ⚠️ Not available, disabling answer generation")
                    self.rag_service = None
            except Exception as e:
                logger.warning(
                    "Gemini AI: ❌ Connection failed, disabling answer generation", error=str(e)
                )
                self.rag_service = None

        # Bot can operate with degraded functionality
        if not services_available:
            logger.warning(
                "All AI services unavailable - bot will operate with basic functionality"
            )
        else:
            logger.info(f"Bot ready with: {', '.join(services_available)}")

    def start(self) -> None:
        """Sync wrapper for starting the bot."""
        asyncio.run(self.start_async())
