#!/usr/bin/env python3

import os
import asyncio
import logging
from typing import List, Dict
from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import structlog

from .config import Config
from .vertex_rag_client import VertexRAGClient, SearchResult
from .gemini_rag import GeminiRAGService, RAGResponse

# Environment variables loaded in app.py

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiting storage (simple in-memory for now)
user_query_count = {}
user_last_reset = {}

class ResearchPaperBot:
    def __init__(self):
        self.config = Config()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.error("Configuration errors", errors=errors)
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        # Debug token format
        print(f"Bot token starts with: {self.config.slack_bot_token[:10]}...")
        print(f"App token starts with: {self.config.slack_app_token[:10]}...")
        
        # Initialize Slack app with explicit token and disable OAuth for Socket Mode
        self.app = App(
            token=self.config.slack_bot_token,
            signing_secret=self.config.slack_signing_secret,
            process_before_response=True  # Enable Socket Mode compatibility
        )
        
        # Initialize Vertex AI RAG Engine client
        self.search_client = VertexRAGClient(
            project_id=self.config.project_id,
            location=self.config.location,
            rag_corpus_id=self.config.rag_corpus_id
        )
        
        # Initialize Gemini RAG service if enabled
        self.rag_service = None
        if self.config.enable_rag_generation:
            self.rag_service = GeminiRAGService(
                project_id=self.config.project_id,
                location=self.config.location,
                model=self.config.gemini_model,
                api_key=self.config.gemini_api_key if not self.config.use_vertex_ai else None,
                use_vertex_ai=self.config.use_vertex_ai,
                temperature=self.config.answer_temperature
            )
        
        # Set up event handlers
        self._setup_handlers()
        
        logger.info("ResearchPaperBot initialized", 
                   project_id=self.config.project_id,
                   bot_name=self.config.bot_name)
    
    def _setup_handlers(self):
        # Handle @mentions
        @self.app.event("app_mention")
        def handle_mention(event, say, client):
            print(f"📢 Received mention: {event.get('text', '')}")
            asyncio.run(self._handle_query(event, say, client, event["text"]))
        
        # Handle slash commands
        @self.app.command("/ask")
        def handle_ask_command(ack, respond, command, client):
            print(f"⚡ Received slash command: {command.get('text', '')}")
            try:
                ack()
                asyncio.run(self._handle_query(command, respond, client, command["text"]))
            except Exception as e:
                print(f"❌ Error in slash command handler: {e}")
                respond({"text": f"❌ Sorry, I encountered an error: {str(e)}"})
        
        # Handle DMs
        @self.app.message("")
        def handle_dm(message, say, client):
            print(f"💬 Received message: {message.get('text', '')} in {message.get('channel_type', 'unknown')}")
            # Only respond to DMs (direct messages)
            if message.get("channel_type") == "im":
                asyncio.run(self._handle_query(message, say, client, message["text"]))
    
    async def _handle_query(self, event_data, respond_func, client, query_text: str):
        user_id = event_data.get("user") or event_data.get("user_id")
        channel_id = event_data.get("channel")
        
        logger.info("Received query", user_id=user_id, query=query_text)
        
        # Check rate limiting
        if not self._check_rate_limit(user_id):
            respond_func({
                "text": f"⚠️ Rate limit exceeded. You can ask up to {self.config.rate_limit_per_user} questions per minute. Please wait a moment and try again."
            })
            return
        
        # Clean the query (remove bot mention)
        clean_query = self._clean_query(query_text)
        
        if not clean_query or len(clean_query.strip()) < 3:
            respond_func({
                "text": "Please provide a research question. For example: 'What are the main findings about machine learning in text analysis?'"
            })
            return
        
        # Send loading message
        loading_response = respond_func({
            "text": f"🔍 Searching and analyzing documents for: `{clean_query}`..."
        })
        
        try:
            # Search for relevant papers
            print(f"🔍 Searching for: '{clean_query}'")
            results = await self.search_client.search(
                query=clean_query,
                max_results=self.config.max_results,
                use_grounded_generation=self.config.use_grounded_generation
            )
            
            # Debug: Show chunk information
            total_chunk_length = sum(len(result.snippet) for result in results)
            print(f"📊 Search returned {len(results)} results")
            print(f"📏 Total length of retrieved chunks: {total_chunk_length:,} characters")
            for i, result in enumerate(results, 1):
                print(f"  Chunk {i}: {len(result.snippet):,} chars (confidence: {result.confidence_score:.1%})")
            
            # Generate comprehensive answer using RAG if enabled and results found
            if results and self.rag_service:
                print("🤖 Generating comprehensive answer with Gemini...")
                rag_response = await self.rag_service.generate_answer(
                    query=clean_query,
                    search_results=results,
                    max_context_length=self.config.max_context_length
                )
                
                # Format and send RAG response
                response_blocks = self._format_rag_response(clean_query, rag_response)
                
                # Update the loading message with RAG answer
                if hasattr(loading_response, 'get') and loading_response.get('ts'):
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_response['ts'],
                        blocks=response_blocks,
                        text=f"Generated comprehensive answer about: {clean_query}"
                    )
                else:
                    respond_func({
                        "blocks": response_blocks,
                        "text": f"Generated comprehensive answer about: {clean_query}"
                    })
            elif results:
                # Fallback to basic search results format if no RAG service
                response_blocks = self._format_search_results(clean_query, results)
                
                # Update the loading message with results
                if hasattr(loading_response, 'get') and loading_response.get('ts'):
                    client.chat_update(
                        channel=channel_id,
                        ts=loading_response['ts'],
                        blocks=response_blocks,
                        text=f"Found {len(results)} research papers about: {clean_query}"
                    )
                else:
                    respond_func({
                        "blocks": response_blocks,
                        "text": f"Found {len(results)} research papers about: {clean_query}"
                    })
            else:
                # No results found
                client.chat_update(
                    channel=channel_id,
                    ts=loading_response.get('ts') if hasattr(loading_response, 'get') else None,
                    text=f"🤔 No relevant documents found for: `{clean_query}`. Try rephrasing your question or using different keywords.",
                ) if hasattr(loading_response, 'get') else respond_func({
                    "text": f"🤔 No relevant documents found for: `{clean_query}`. Try rephrasing your question or using different keywords."
                })
                
        except Exception as e:
            logger.error("Search failed", error=str(e), query=clean_query)
            
            error_message = f"❌ Sorry, I encountered an error while searching: {str(e)}"
            
            if hasattr(loading_response, 'get') and loading_response.get('ts'):
                client.chat_update(
                    channel=channel_id,
                    ts=loading_response['ts'],
                    text=error_message
                )
            else:
                respond_func({"text": error_message})
    
    def _clean_query(self, text: str) -> str:
        # Remove bot mention
        text = text.strip()
        
        # Remove bot mentions like <@U123456>
        import re
        text = re.sub(r'<@U[A-Z0-9]+>', '', text).strip()
        
        # Remove /ask command if present
        if text.startswith('/ask'):
            text = text[4:].strip()
        
        return text
    
    def _check_rate_limit(self, user_id: str) -> bool:
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
    
    def _format_search_results(self, query: str, results: List[SearchResult]) -> List[Dict]:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📚 Research Papers: {query}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Found {len(results)} relevant papers"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        for i, result in enumerate(results, 1):
            # Paper title and confidence
            confidence_emoji = "🟢" if result.confidence_score >= 0.7 else "🟡" if result.confidence_score >= 0.4 else "🔴"
            
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{i}. {result.title}*\n{confidence_emoji} Relevance: {result.confidence_score:.0%}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{result.snippet}```"
                    }
                }
            ])
            
            # Add source link if available
            if result.source_uri:
                source_text = result.source_uri
                if result.source_uri.startswith('gs://'):
                    filename = result.source_uri.split('/')[-1]
                    source_text = f"📄 {filename}"
                
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Source: {source_text}"
                        }
                    ]
                })
            
            # Add separator between results (except last one)
            if i < len(results):
                blocks.append({"type": "divider"})
        
        # Add footer
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💡 *Tip:* Try more specific questions like 'What methodology was used for...' or 'What are the limitations of...'"
                    }
                ]
            }
        ])
        
        return blocks
    
    def _format_rag_response(self, query: str, rag_response: RAGResponse) -> List[Dict]:
        """Format a comprehensive RAG response with generated answer and sources"""
        confidence_emoji = "🟢" if rag_response.confidence_score >= 0.7 else "🟡" if rag_response.confidence_score >= 0.4 else "🔴"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 Answer: {query}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{confidence_emoji} Confidence: {rag_response.confidence_score:.0%} • Sources: {len(rag_response.sources)} documents"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": rag_response.answer
                }
            }
        ]
        
        # Add sources section if available
        if rag_response.sources:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📚 Sources"
                    }
                }
            ])
            
            for i, result in enumerate(rag_response.sources, 1):
                source_confidence_emoji = "🟢" if result.confidence_score >= 0.7 else "🟡" if result.confidence_score >= 0.4 else "🔴"
                
                blocks.extend([
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{i}. {result.title}*\n{source_confidence_emoji} Relevance: {result.confidence_score:.0%}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{result.snippet[:300]}{'...' if len(result.snippet) > 300 else ''}```"
                        }
                    }
                ])
                
                # Add source link if available
                if result.source_uri:
                    source_text = result.source_uri
                    if result.source_uri.startswith('gs://'):
                        filename = result.source_uri.split('/')[-1]
                        source_text = f"📄 {filename}"
                    
                    blocks.append({
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Source: {source_text}"
                            }
                        ]
                    })
                
                # Add separator between sources (except last one)
                if i < len(rag_response.sources):
                    blocks.append({"type": "divider"})
        
        # Add footer with tips
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 *Tip:* This answer was generated from your company documents. For follow-up questions, try asking for more details or clarification on specific points."
                    }
                ]
            }
        ])
        
        return blocks
    
    def start(self):
        # Test connection to Vertex AI
        print("🔍 Testing Vertex AI Search connection...")
        try:
            if not self.search_client.test_connection():
                print("❌ Failed to connect to Vertex AI Search")
                logger.error("Failed to connect to Vertex AI Search")
                raise ConnectionError("Cannot connect to Vertex AI Search")
            print("✅ Vertex AI Search connection successful")
        except Exception as e:
            print(f"❌ Vertex AI Search connection failed: {e}")
            raise
        
        # Test Gemini connection if enabled
        if self.rag_service:
            print("🤖 Testing Gemini connection...")
            try:
                if not self.rag_service.test_connection():
                    print("⚠️ Warning: Gemini connection failed - falling back to search-only mode")
                    logger.warning("Gemini connection failed, using search-only mode")
                    self.rag_service = None
                else:
                    print("✅ Gemini connection successful - RAG generation enabled")
            except Exception as e:
                print(f"⚠️ Warning: Gemini connection failed: {e} - falling back to search-only mode")
                logger.warning("Gemini connection failed", error=str(e))
                self.rag_service = None
        
        print(f"🤖 Starting ResearchPaperBot: {self.config.bot_name}")
        logger.info("Starting ResearchPaperBot", bot_name=self.config.bot_name)
        
        # Start the bot
        print("🔗 Connecting to Slack...")
        try:
            handler = SocketModeHandler(self.app, self.config.slack_app_token)
            print("✅ Socket Mode handler created successfully")
            print("🚀 Bot is starting...")
            print("✅ whatsupdoc research paper bot is running!")
            print("💬 Ready to answer questions about research papers!")
            print("   Try: @whatsupdoc what are the main findings about text analysis?")
            print("   Or:  /ask machine learning methodology")
            print("   Or:  DM me directly")
            print()
            handler.start()
        except Exception as e:
            print(f"❌ Slack connection failed: {e}")
            logger.error("Slack connection failed", error=str(e))
            raise


# Entry point moved to app.py