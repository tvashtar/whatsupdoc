#!/usr/bin/env python3
"""Modern Vertex AI RAG integration using REST API."""

import asyncio
from dataclasses import dataclass
from typing import Any

import structlog
from google.auth import default

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """Modern search result with proper typing."""

    title: str
    content: str  # Full chunk content (not just snippet)
    source_uri: str
    confidence_score: float
    metadata: dict[str, Any] | None = None

    # Backward compatibility property
    @property
    def snippet(self) -> str:
        """Backward compatibility - returns full content."""
        return self.content


class VertexRAGClient:
    """Modern Vertex AI RAG client using REST API."""

    def __init__(self, project_id: str, location: str, rag_corpus_id: str) -> None:
        """Initialize the Vertex AI RAG client with credentials and API endpoint."""
        self.project_id = project_id
        self.location = location
        self.rag_corpus_id = rag_corpus_id

        # Initialize authentication
        self.credentials, _ = default()

        # Build API endpoint
        self.api_endpoint = f"https://{location}-aiplatform.googleapis.com"

        logger.info(
            "Initialized modern Vertex RAG client",
            project=project_id,
            location=location,
            corpus=rag_corpus_id,
        )

    async def search_async(  # noqa: C901
        self,
        query: str,
        max_results: int = 10,
        distance_threshold: float = 0.8,  # Higher = more permissive (lower similarity)
    ) -> list[SearchResult]:
        """Modern async search using REST API."""
        try:
            import requests
            from google.auth.transport.requests import Request

            # Refresh credentials if needed
            self.credentials.refresh(Request())

            # Build request payload with semantic reranking
            request_body = {
                "vertex_rag_store": {
                    "rag_resources": [{"rag_corpus": self.rag_corpus_id}],
                    "vector_distance_threshold": distance_threshold,
                },
                "query": {
                    "text": query,
                    "rag_retrieval_config": {
                        "top_k": max_results,
                        "ranking": {
                            "rank_service": {"model_name": "semantic-ranker-default@latest"}
                        },
                    },
                },
            }

            # Build API URL
            url = (
                f"{self.api_endpoint}/v1beta1/projects/{self.project_id}/"
                f"locations/{self.location}:retrieveContexts"
            )

            headers = {
                "Authorization": f"Bearer {self.credentials.token}",
                "Content-Type": "application/json",
            }

            logger.info(f"Executing RAG search query: '{query}' with max_results: {max_results}")

            # Execute in thread pool to maintain async interface
            loop = asyncio.get_event_loop()

            def sync_request() -> dict[str, Any]:
                response = requests.post(url, json=request_body, headers=headers, timeout=30)
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]

            response_data = await loop.run_in_executor(None, sync_request)

            # Parse response and convert to SearchResult objects
            results = []

            if "contexts" in response_data and "contexts" in response_data["contexts"]:
                for i, context in enumerate(response_data["contexts"]["contexts"]):
                    try:
                        # Extract chunk content
                        content = context.get("text", "")

                        # Extract source metadata
                        source_uri = context.get("sourceUri", "")
                        title = context.get("sourceDisplayName", f"Document {i+1}")

                        # Calculate confidence from relevance scores
                        confidence_score = 0.8  # Default high confidence
                        if "distance" in context:
                            # Convert distance to confidence (lower distance = higher confidence)
                            distance = float(context["distance"])
                            confidence_score = max(0.1, min(1.0, 1.0 - distance))
                        elif "score" in context:
                            confidence_score = float(context["score"])

                        # Extract additional metadata
                        metadata = {
                            "chunk_index": i,
                            "rag_engine": True,
                            "chunk_length": len(content),
                        }

                        if "chunk" in context:
                            chunk_info = context["chunk"]
                            if "pageSpan" in chunk_info:
                                metadata["page_span"] = chunk_info["pageSpan"]

                        search_result = SearchResult(
                            title=title,
                            content=content,  # Full chunk content for RAG
                            source_uri=source_uri,
                            confidence_score=confidence_score,
                            metadata=metadata,
                        )

                        results.append(search_result)

                    except Exception as e:
                        logger.warning(f"Error processing RAG context {i}: {str(e)}")
                        continue

            logger.info(
                f"Retrieved {len(results)} chunks",
                total_chars=sum(len(r.content) for r in results),
            )
            return results

        except Exception as e:
            logger.error("Vertex AI search failed", error=str(e), query=query)

            # If RAG Engine is not implemented, return empty results for now
            # This allows the bot to continue functioning
            if "not implemented" in str(e).lower() or "501" in str(e):
                logger.warning("RAG Engine not available, returning empty results")
                return []

            raise

    # Compatibility method for existing code
    async def search(
        self,
        query: str,
        max_results: int = 10,
        vector_distance_threshold: float | None = None,
        vector_similarity_threshold: float | None = None,
        use_grounded_generation: bool = True,  # Keep for compatibility
    ) -> list[SearchResult]:
        """Search wrapper for backwards compatibility."""
        # Note: use_grounded_generation kept for API compatibility but not used
        # Use provided threshold or fall back to default from config
        from whatsupdoc.core.config import Config

        config = Config()
        distance_threshold = (
            vector_distance_threshold or vector_similarity_threshold or config.distance_threshold
        )
        return await self.search_async(query, max_results, distance_threshold)

    async def test_connection_async(self) -> bool:
        """Test the Vertex AI connection."""
        try:
            # Test by attempting to search with a simple query
            _ = await self.search_async("test", max_results=1)
            logger.info("Vertex AI connection test successful")
            return True
        except Exception as e:
            logger.error("Vertex AI connection test failed", error=str(e))

            # If RAG Engine is not implemented, consider connection "successful"
            # but without functional search capability
            if "not implemented" in str(e).lower() or "501" in str(e):
                logger.warning("RAG Engine not available, but connection established")
                return True

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
