"""Web service integration layer for RAG pipeline.

This module provides a unified service that combines the Vertex RAG client
and Gemini RAG service for the web API.
"""

import time
from dataclasses import dataclass

import structlog

from whatsupdoc.core.gemini_rag import GeminiRAGService
from whatsupdoc.core.vertex_rag_client import SearchResult, VertexRAGClient

logger = structlog.get_logger()


@dataclass
class WebRAGResult:
    """Result from the web RAG pipeline."""

    answer: str
    confidence: float
    sources: list[str]
    processing_time_ms: int


class WebRAGService:
    """Unified RAG service for web interface."""

    def __init__(self, vertex_client: VertexRAGClient, gemini_service: GeminiRAGService) -> None:
        """Initialize the web RAG service."""
        self.vertex_client = vertex_client
        self.gemini_service = gemini_service

        logger.info("Initialized web RAG service")

    async def process_query(
        self,
        query: str,
        conversation_id: str,
        max_results: int = 10,
        distance_threshold: float = 0.8,
    ) -> WebRAGResult:
        """Process a user query through the complete RAG pipeline.

        Args:
            query: The user's question
            conversation_id: Conversation identifier (for future use)
            max_results: Maximum number of search results to use
            distance_threshold: Vector distance threshold for filtering results

        Returns:
            WebRAGResult with answer, confidence, sources, and timing

        """
        start_time = time.time()

        logger.info(
            "Processing web RAG query",
            conversation_id=conversation_id,
            query_length=len(query),
            max_results=max_results,
        )

        try:
            # Step 1: Search for relevant documents using Vertex RAG
            # Use configurable distance threshold (higher = more permissive)
            search_results = await self.vertex_client.search_async(
                query=query,
                max_results=max_results,
                distance_threshold=distance_threshold,
            )

            # Use all results from Vertex AI (no additional filtering needed)
            filtered_results = search_results

            logger.info(
                "Retrieved search results",
                total_results=len(search_results),
                distance_threshold=distance_threshold,
                conversation_id=conversation_id,
            )

            if not filtered_results:
                # No relevant results found
                processing_time_ms = int((time.time() - start_time) * 1000)
                return WebRAGResult(
                    answer=(
                        "I couldn't find relevant information to answer your question. "
                        "Please try rephrasing your query or ask about a different topic."
                    ),
                    confidence=0.0,
                    sources=[],
                    processing_time_ms=processing_time_ms,
                )

            # Step 2: Generate answer using Gemini with search results
            rag_response = await self.gemini_service.generate_answer_async(
                query=query, search_results=filtered_results
            )

            # Step 3: Extract source information
            sources = self._extract_sources(filtered_results)

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Completed web RAG processing",
                conversation_id=conversation_id,
                processing_time_ms=processing_time_ms,
                confidence=rag_response.confidence_score,
                num_sources=len(sources),
            )

            return WebRAGResult(
                answer=rag_response.answer,
                confidence=rag_response.confidence_score,
                sources=sources,
                processing_time_ms=processing_time_ms,
            )

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Error in web RAG processing",
                conversation_id=conversation_id,
                error=str(e),
                processing_time_ms=processing_time_ms,
                exc_info=True,
            )
            raise

    def _extract_sources(self, search_results: list[SearchResult]) -> list[str]:
        """Extract source information from search results."""
        sources = []

        for result in search_results:
            # Create a clean source description
            source_info = result.title

            # Add page information if available
            if result.metadata and "page_span" in result.metadata:
                page_span = result.metadata["page_span"]
                if "pageStart" in page_span and "pageEnd" in page_span:
                    start_page = page_span["pageStart"]
                    end_page = page_span["pageEnd"]
                    if start_page == end_page:
                        source_info += f" (page {start_page})"
                    else:
                        source_info += f" (pages {start_page}-{end_page})"

            sources.append(source_info)

        return sources

    async def test_connection(self) -> bool:
        """Test connections to both Vertex and Gemini services."""
        try:
            vertex_ok = await self.vertex_client.test_connection_async()
            gemini_ok = await self.gemini_service.test_connection_async()

            logger.info("Connection test results", vertex_ok=vertex_ok, gemini_ok=gemini_ok)

            return vertex_ok and gemini_ok

        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False
