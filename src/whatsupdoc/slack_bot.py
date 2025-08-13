#!/usr/bin/env python3
"""Modern Slack bot implementation using latest async patterns."""

import asyncio
import os
from typing import Any, Dict, List, Optional

import structlog
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import Config
from .error_handler import ModernErrorHandler
from .gemini_rag import GeminiRAGService, RAGResponse
from .vertex_rag_client import VertexRAGClient, SearchResult

logger = structlog.get_logger()

# Rate limiting storage (simple in-memory for now)
user_query_count: Dict[str, int] = {}
user_last_reset: Dict[str, float] = {}


class SlackBot:
    """Modern Slack bot with proper async patterns and enhanced error handling."""

    def __init__(self) -> None:
        self.config = Config()

        # Validate configuration
        errors = self.config.validate()
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
        self.rag_service: Optional[GeminiRAGService] = None
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
        def handle_mention(event, say, client):
            asyncio.run(self._handle_query_async(event, say, client, event["text"]))

        @self.app.command("/ask")
        def handle_ask_command(ack, respond, command, client):
            ack()  # Acknowledge immediately
            asyncio.run(self._handle_query_async(command, respond, client, command["text"]))

        @self.app.message("")
        def handle_dm(message, say, client):
            if message.get("channel_type") == "im":
                asyncio.run(self._handle_query_async(message, say, client, message["text"]))

    async def _handle_query_async(
        self, event_data: Dict[str, Any], respond_func, client, query_text: str
    ) -> None:
        """Modern async query handler with proper error handling."""
        user_id = event_data.get("user") or event_data.get("user_id")
        channel_id = event_data.get("channel")

        logger.info("Processing query", user_id=user_id, query=query_text)

        # Rate limiting check
        if not await self._check_rate_limit_async(user_id):
            respond_func({
                "text": f"⚠️ Rate limit exceeded. Please wait before trying again."
            })
            return

        # Clean and validate query
        clean_query = self._clean_query(query_text)
        if not clean_query or len(clean_query.strip()) < 3:
            respond_func({
                "text": "Please provide a valid research question."
            })
            return

        # Send loading message
        loading_response = respond_func({
            "text": f"🔍 Searching for: `{clean_query}`..."
        })

        try:
            # Search with modern error handling
            results = await ModernErrorHandler.robust_api_call(
                self.search_client.search_async,
                query=clean_query,
                max_results=self.config.max_results,
            )

            if results and self.rag_service:
                # Generate answer using RAG
                rag_response = await ModernErrorHandler.robust_api_call(
                    self.rag_service.generate_answer_async,
                    query=clean_query,
                    search_results=results,
                    max_context_length=self.config.max_context_length,
                )

                response_blocks = self._format_rag_response(clean_query, rag_response)

                # Update loading message
                client.chat_update(
                    channel=channel_id,
                    ts=loading_response.get("ts"),
                    blocks=response_blocks,
                    text=f"Generated answer for: {clean_query}",
                )
            else:
                # Handle no results case
                client.chat_update(
                    channel=channel_id,
                    ts=loading_response.get("ts"),
                    text=f"🤔 No relevant documents found for: `{clean_query}`",
                )

        except Exception as e:
            error_context = {"query": clean_query, "user_id": user_id}
            error_message = ModernErrorHandler.handle_rag_error(e, error_context)

            client.chat_update(
                channel=channel_id,
                ts=loading_response.get("ts"),
                text=error_message,
            )

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

    def _format_rag_response(self, query: str, rag_response: RAGResponse) -> List[Dict[str, Any]]:
        """Format a comprehensive RAG response with generated answer and sources."""
        confidence_emoji = (
            "🟢"
            if rag_response.confidence_score >= 0.7
            else "🟡"
            if rag_response.confidence_score >= 0.4
            else "🔴"
        )

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🤖 Answer: {query}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{confidence_emoji} Confidence: {rag_response.confidence_score:.0%} | Sources: {len(rag_response.sources)}",
                },
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": rag_response.answer}},
        ]

        # Add sources section if available
        if rag_response.sources:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📚 Sources"},
                },
            ])

            for i, result in enumerate(rag_response.sources, 1):
                source_confidence_emoji = (
                    "🟢"
                    if result.confidence_score >= 0.7
                    else "🟡"
                    if result.confidence_score >= 0.4
                    else "🔴"
                )

                blocks.extend([
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{i}. {result.title}*\n{source_confidence_emoji} Relevance: {result.confidence_score:.0%}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{result.snippet[:300]}{'...' if len(result.snippet) > 300 else ''}```",
                        },
                    },
                ])

                # Add source link if available
                if result.source_uri:
                    source_text = result.source_uri
                    if result.source_uri.startswith("gs://"):
                        filename = result.source_uri.split("/")[-1]
                        source_text = f"📄 {filename}"

                    blocks.append({
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"Source: {source_text}"}
                        ],
                    })

                # Add separator between sources (except last one)
                if i < len(rag_response.sources):
                    blocks.append({"type": "divider"})

        # Add footer with tips
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 *Tip:* This answer was generated from your company documents. For follow-up questions, try asking for more details or clarification on specific points.",
                    }
                ],
            },
        ])

        return blocks

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
            def slack_events():
                return handler.handle(request)

            @flask_app.route("/health", methods=["GET"])
            def health_check():
                return {"status": "healthy", "service": "whatsupdoc"}, 200

            # Run Flask app
            flask_app.run(host="0.0.0.0", port=int(port))
        else:
            # Socket mode for development
            logger.info("Starting in Socket Mode")
            if not self.config.slack_app_token:
                raise ValueError("SLACK_APP_TOKEN is required for Socket Mode")
            handler = SocketModeHandler(self.app, self.config.slack_app_token)
            handler.start()

    async def _test_connections(self) -> None:
        """Test all external connections."""
        # Test Vertex AI connection
        if not await self.search_client.test_connection_async():
            raise ConnectionError("Cannot connect to Vertex AI RAG Engine")

        # Test Gemini connection
        if self.rag_service and not await self.rag_service.test_connection_async():
            logger.warning("Gemini connection failed, using search-only mode")
            self.rag_service = None

    def start(self) -> None:
        """Sync wrapper for starting the bot."""
        asyncio.run(self.start_async())