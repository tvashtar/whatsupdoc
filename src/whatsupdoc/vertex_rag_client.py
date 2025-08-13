import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from google.auth import default


@dataclass
class SearchResult:
    """Search result from RAG Engine - compatible with existing code"""

    title: str
    snippet: str  # Now contains full chunk content, not just snippets
    source_uri: str
    confidence_score: float
    metadata: dict[str, Any] | None = None


class VertexRAGClient:
    """Client for Vertex AI RAG Engine - provides proper chunk-based RAG retrieval.
    Uses the Google Cloud AI Platform client to access RAG functionality.
    """

    def __init__(self, project_id: str, location: str, rag_corpus_id: str) -> None:
        self.project_id = project_id
        self.location = location
        self.rag_corpus_id = rag_corpus_id

        # Initialize authentication
        self.credentials, _ = default()  # type: ignore

        # Build API endpoint
        self.api_endpoint = f"https://{location}-aiplatform.googleapis.com"

        logging.info(f"Initialized VertexRAGClient for project: {project_id}, corpus: {rag_corpus_id}")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        vector_distance_threshold: float | None = None,
        vector_similarity_threshold: float | None = None,
        use_grounded_generation: bool = True  # Keep for compatibility
    ) -> list[SearchResult]:
        """Search the RAG corpus for relevant chunks using REST API.
        Returns SearchResult objects with full chunk content.
        """
        try:
            import requests
            from google.auth.transport.requests import Request

            # Refresh credentials if needed
            self.credentials.refresh(Request())

            # Build request payload
            request_body = {
                "vertex_rag_store": {
                    "rag_resources": [
                        {"rag_corpus": self.rag_corpus_id}
                    ]
                },
                "query": {
                    "text": query,
                    "similarity_top_k": max_results
                }
            }

            # Add optional filters
            if vector_distance_threshold:
                request_body["vertex_rag_store"]["vector_distance_threshold"] = vector_distance_threshold
            if vector_similarity_threshold:
                request_body["vertex_rag_store"]["vector_similarity_threshold"] = vector_similarity_threshold

            # Build API URL
            url = f"{self.api_endpoint}/v1beta1/projects/{self.project_id}/locations/{self.location}:retrieveContexts"

            headers = {
                "Authorization": f"Bearer {self.credentials.token}",
                "Content-Type": "application/json"
            }

            logging.info(f"Executing RAG search query: '{query}' with max_results: {max_results}")

            # Make the API request
            response = requests.post(url, json=request_body, headers=headers, timeout=30)
            response.raise_for_status()

            response_data = response.json()

            # Parse response and convert to SearchResult objects
            search_results = []

            if "contexts" in response_data and "contexts" in response_data["contexts"]:
                for i, context in enumerate(response_data["contexts"]["contexts"]):
                    try:
                        # Extract chunk content
                        content = context.get("text", "")

                        # Extract source metadata
                        source_uri = ""
                        title = f"Document {i+1}"

                        if "sourceMetadata" in context:
                            source_metadata = context["sourceMetadata"]
                            source_uri = source_metadata.get("sourceUri", "")
                            if "title" in source_metadata:
                                title = source_metadata["title"]

                        # Calculate confidence from relevance scores
                        confidence_score = 0.8  # Default high confidence
                        if "distance" in context:
                            # Convert distance to confidence (lower distance = higher confidence)
                            distance = float(context["distance"])
                            confidence_score = max(0.1, min(1.0, 1.0 - distance))
                        elif "relevanceScore" in context:
                            confidence_score = float(context["relevanceScore"])

                        # Extract additional metadata
                        metadata = {
                            "chunk_index": i,
                            "rag_engine": True,
                            "chunk_length": len(content),
                        }

                        if "sourceMetadata" in context:
                            metadata["source_metadata"] = context["sourceMetadata"]

                        search_result = SearchResult(
                            title=title,
                            snippet=content,  # Full chunk content for RAG
                            source_uri=source_uri,
                            confidence_score=confidence_score,
                            metadata=metadata
                        )

                        search_results.append(search_result)

                    except Exception as e:
                        logging.warning(f"Error processing RAG context {i}: {str(e)}")
                        continue

            avg_length = sum(len(r.snippet) for r in search_results) / len(search_results) if search_results else 0
            logging.info(f"Retrieved {len(search_results)} RAG chunks (avg length: {avg_length:.0f} chars)")
            return search_results

        except Exception as e:
            logging.error(f"RAG search failed: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """Test the connection to Vertex AI RAG Engine"""
        try:
            # Test by attempting to retrieve contexts with a simple query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(self.search("test", max_results=1))
                logging.info("RAG Engine connection test successful")
                return True
            finally:
                loop.close()

        except Exception as e:
            logging.error(f"RAG Engine connection test failed: {str(e)}")
            return False

    def get_corpus_info(self) -> dict[str, Any]:
        """Get information about the configured RAG corpus"""
        try:
            # For now, return basic info extracted from the corpus ID
            # Full implementation would use RAG Data Service API
            return {
                "name": self.rag_corpus_id,
                "display_name": "whatsupdoc",
                "description": "RAG corpus for company knowledge base",
                "project_id": self.project_id,
                "location": self.location,
            }

        except Exception as e:
            logging.error(f"Failed to get corpus info: {str(e)}")
            raise

    def list_rag_files(self) -> list[dict[str, Any]]:
        """List files in the RAG corpus"""
        try:
            # For now, return placeholder info
            # Full implementation would use RAG Data Service API to list files
            return [
                {
                    "name": "PDF documents",
                    "display_name": "Company knowledge base PDFs",
                    "description": "1000 company documents imported into RAG corpus"
                }
            ]

        except Exception as e:
            logging.error(f"Failed to list RAG files: {str(e)}")
            raise
