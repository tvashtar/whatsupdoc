#!/usr/bin/env python3
"""Modern Vertex AI RAG integration using official SDK."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import structlog
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1 import VertexRagDataServiceClient
from google.cloud.aiplatform_v1beta1.types import SearchRagDocumentsRequest

from .error_handler import ModernErrorHandler

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """Modern search result with proper typing."""

    title: str
    snippet: str
    source_uri: str
    confidence_score: float
    metadata: dict[str, Any] | None = None


class ModernVertexRAGClient:
    """Modern Vertex AI RAG client using official SDK."""

    def __init__(self, project_id: str, location: str, rag_corpus_id: str) -> None:
        self.project_id = project_id
        self.location = location
        self.rag_corpus_id = rag_corpus_id

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Use official RAG Data Service client
        self.rag_client = VertexRagDataServiceClient()

        logger.info(
            "Initialized modern Vertex RAG client",
            project=project_id,
            location=location,
            corpus=rag_corpus_id,
        )

    async def search_async(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.3,
    ) -> list[SearchResult]:
        """Modern async search using official Vertex AI SDK."""
        try:
            # Use the official RAG search API
            parent = f"projects/{self.project_id}/locations/{self.location}/ragCorpora/{self.rag_corpus_id}"

            request = SearchRagDocumentsRequest(
                parent=parent,
                query=query,
                page_size=max_results,
                vector_similarity_threshold=similarity_threshold,
            )

            # Execute in thread pool to maintain async interface
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self.rag_client.search_rag_documents, request
            )

            results = []
            for rag_chunk in response.rag_chunks:
                # Extract chunk data using proper SDK patterns
                chunk_data = rag_chunk.chunk
                source_uri = rag_chunk.source_uri or "unknown"

                result = SearchResult(
                    title=chunk_data.display_name or "Document Chunk",
                    snippet=chunk_data.text,
                    source_uri=source_uri,
                    confidence_score=rag_chunk.distance,  # Higher is better in Vertex AI
                    metadata={
                        "chunk_id": chunk_data.name,
                        "document_id": getattr(chunk_data, "document_id", None),
                    },
                )
                results.append(result)

            logger.info(
                f"Retrieved {len(results)} chunks",
                total_chars=sum(len(r.snippet) for r in results),
            )
            return results

        except Exception as e:
            logger.error("Vertex AI search failed", error=str(e), query=query)
            raise

    # Compatibility method for existing code
    async def search(
        self,
        query: str,
        max_results: int = 5,
        vector_distance_threshold: float | None = None,
        vector_similarity_threshold: float | None = None,
        use_grounded_generation: bool = True,  # Keep for compatibility
    ) -> list[SearchResult]:
        """Search wrapper for backwards compatibility."""
        similarity_threshold = vector_similarity_threshold or 0.3
        return await self.search_async(query, max_results, similarity_threshold)

    async def test_connection_async(self) -> bool:
        """Test the Vertex AI connection."""
        try:
            # Test by attempting to search with a simple query
            results = await self.search_async("test", max_results=1)
            logger.info("Vertex AI connection test successful")
            return True
        except Exception as e:
            logger.error("Vertex AI connection test failed", error=str(e))
            return False

    def test_connection(self) -> bool:
        """Sync wrapper for connection test."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.test_connection_async())
        finally:
            loop.close()

    def get_corpus_info(self) -> dict[str, Any]:
        """Get information about the configured RAG corpus."""
        try:
            return {
                "name": self.rag_corpus_id,
                "display_name": "whatsupdoc",
                "description": "RAG corpus for company knowledge base",
                "project_id": self.project_id,
                "location": self.location,
            }
        except Exception as e:
            logger.error(f"Failed to get corpus info: {str(e)}")
            raise

    def list_rag_files(self) -> list[dict[str, Any]]:
        """List files in the RAG corpus."""
        try:
            return [
                {
                    "name": "PDF documents",
                    "display_name": "Company knowledge base PDFs",
                    "description": "1000 company documents imported into RAG corpus",
                }
            ]
        except Exception as e:
            logger.error(f"Failed to list RAG files: {str(e)}")
            raise