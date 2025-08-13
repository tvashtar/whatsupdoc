#!/usr/bin/env python3
"""Modern Gemini integration using latest google-genai SDK patterns."""

import asyncio
import logging
from dataclasses import dataclass

import structlog
from google import genai
from google.genai import types

from .error_handler import ModernErrorHandler
from .modern_vertex_rag_client import SearchResult

logger = structlog.get_logger()


@dataclass
class RAGResponse:
    """Enhanced RAG response with proper typing."""

    answer: str
    sources: list[SearchResult]
    confidence_score: float
    has_citations: bool = True


class ModernGeminiRAGService:
    """Modern Gemini integration using latest google-genai SDK patterns."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model: str = "gemini-2.5-flash",
        use_vertex_ai: bool = True,
        temperature: float = 0.1,
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.model = model
        self.temperature = temperature

        # Use modern client initialization
        if use_vertex_ai:
            self.client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
                http_options=types.HttpOptions(api_version="v1"),
            )
        else:
            self.client = genai.Client()  # Uses GOOGLE_API_KEY env var

        logger.info(
            "Initialized modern Gemini client", model=model, vertex_ai=use_vertex_ai
        )

    async def generate_answer_async(
        self,
        query: str,
        search_results: list[SearchResult],
        max_context_length: int = 100000,
    ) -> RAGResponse:
        """Modern async answer generation using latest Gemini patterns."""
        try:
            # Build context from search results
            context_parts = []
            total_length = 0

            for i, result in enumerate(search_results, 1):
                chunk_text = f"[Source {i}: {result.title}]\n{result.snippet}\n"
                if total_length + len(chunk_text) <= max_context_length:
                    context_parts.append(chunk_text)
                    total_length += len(chunk_text)
                else:
                    break

            context = "\n".join(context_parts)

            # Modern prompt template
            prompt = f"""Based on the following company documents, provide a comprehensive answer to the user's question. Be specific, cite relevant information, and indicate if the answer cannot be fully determined from the provided context.

Question: {query}

Context:
{context}

Please provide a detailed, helpful answer based on the above context. If you cannot answer fully based on the provided documents, please indicate what additional information might be needed."""

            # Use modern generate_content with proper config
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=2048,
                        candidate_count=1,
                    ),
                ),
            )

            # Calculate confidence based on context quality
            avg_confidence = (
                sum(r.confidence_score for r in search_results) / len(search_results)
                if search_results
                else 0.0
            )

            return RAGResponse(
                answer=response.text,
                sources=search_results,
                confidence_score=avg_confidence,
                has_citations=True,
            )

        except Exception as e:
            logger.error("Gemini generation failed", error=str(e), query=query)
            raise

    # Compatibility wrapper for existing code
    async def generate_answer(
        self,
        query: str,
        search_results: list[SearchResult],
        max_context_length: int = 100000,
    ) -> RAGResponse:
        """Backwards compatibility wrapper."""
        return await self.generate_answer_async(query, search_results, max_context_length)

    async def test_connection_async(self) -> bool:
        """Test the Gemini connection."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents="Hello, this is a test. Please respond with 'Connection successful.'",
                ),
            )

            if response.text and "successful" in response.text.lower():
                logger.info("Gemini connection test successful")
                return True
            else:
                logger.warning("Gemini connection test returned unexpected response")
                return False

        except Exception as e:
            logger.error("Gemini connection test failed", error=str(e))
            return False

    def test_connection(self) -> bool:
        """Sync wrapper for connection test."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.test_connection_async())
        finally:
            loop.close()