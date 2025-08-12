import logging
from typing import List, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from .vertex_rag_client import SearchResult


@dataclass
class RAGResponse:
    answer: str
    sources: List[SearchResult]
    confidence_score: float
    has_citations: bool = True


class GeminiRAGService:
    def __init__(self, project_id: str, location: str = "us-central1", 
                 model: str = "gemini-2.0-flash-001", api_key: Optional[str] = None,
                 use_vertex_ai: bool = True, temperature: float = 0.3):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.temperature = temperature
        self.use_vertex_ai = use_vertex_ai
        
        # Initialize Gemini client
        if use_vertex_ai:
            # Use Vertex AI
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            logging.info(f"Initialized Gemini RAG service with Vertex AI for project: {project_id}")
        else:
            # Use Gemini Developer API
            if not api_key:
                raise ValueError("GEMINI_API_KEY is required when not using Vertex AI")
            self.client = genai.Client(api_key=api_key)
            logging.info("Initialized Gemini RAG service with Developer API")
    
    async def generate_answer(
        self, 
        query: str, 
        search_results: List[SearchResult],
        max_context_length: int = 8000
    ) -> RAGResponse:
        """Generate a comprehensive answer using Gemini based on search results"""
        try:
            if not search_results:
                return RAGResponse(
                    answer="I couldn't find relevant information to answer your question. Please try rephrasing your query or asking about a different topic.",
                    sources=[],
                    confidence_score=0.0,
                    has_citations=False
                )
            
            # Build context from search results
            context_parts = []
            total_length = 0
            used_sources = []
            
            for i, result in enumerate(search_results, 1):
                # Create a formatted context entry
                source_text = f"Source {i} (Confidence: {result.confidence_score:.1%}):\n"
                source_text += f"Title: {result.title}\n"
                source_text += f"Content: {result.snippet}\n"
                if result.source_uri:
                    source_text += f"URL: {result.source_uri}\n"
                source_text += "\n"
                
                # Check if adding this source would exceed context limit
                if total_length + len(source_text) > max_context_length:
                    break
                
                context_parts.append(source_text)
                total_length += len(source_text)
                used_sources.append(result)
            
            if not context_parts:
                return RAGResponse(
                    answer="The available information is too lengthy to process. Please try a more specific question.",
                    sources=[],
                    confidence_score=0.0,
                    has_citations=False
                )
            
            context = "".join(context_parts)
            
            # Debug: Show what's being passed to Gemini
            print(f"🤖 Passing {len(used_sources)} sources to Gemini (total context: {len(context):,} chars)")
            for i, source in enumerate(used_sources, 1):
                print(f"  Source {i}: {len(source.snippet):,} chars from {source.title[:50]}...")
            
            # Calculate overall confidence from sources
            overall_confidence = sum(result.confidence_score for result in used_sources) / len(used_sources)
            
            # Create the prompt for answer generation
            prompt = self._build_rag_prompt(query, context, len(used_sources))
            
            # Generate answer using Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=1500,
                    response_mime_type="text/plain"
                )
            )
            
            if not response.text:
                return RAGResponse(
                    answer="I'm having trouble generating a response right now. Please try again.",
                    sources=used_sources,
                    confidence_score=overall_confidence,
                    has_citations=False
                )
            
            answer_text = response.text.strip()
            
            # Check if the answer includes citations
            has_citations = any(f"Source {i}" in answer_text for i in range(1, len(used_sources) + 1))
            
            return RAGResponse(
                answer=answer_text,
                sources=used_sources,
                confidence_score=overall_confidence,
                has_citations=has_citations
            )
            
        except Exception as e:
            logging.error(f"Error generating RAG response: {str(e)}")
            return RAGResponse(
                answer=f"I encountered an error while processing your request: {str(e)}",
                sources=search_results[:3],  # Return some sources for context
                confidence_score=0.0,
                has_citations=False
            )
    
    def _build_rag_prompt(self, query: str, context: str, num_sources: int) -> str:
        """Build a comprehensive RAG prompt for answer generation"""
        return f"""You are a helpful AI assistant that answers questions based on the provided context from company documents.

QUERY: {query}

CONTEXT (from company documents):
{context}

INSTRUCTIONS:
1. Answer the question comprehensively using ONLY the information provided in the context above
2. If the context doesn't contain enough information to fully answer the question, say so explicitly
3. Include specific references to sources (e.g., "According to Source 1..." or "Source 2 mentions...")
4. If multiple sources provide similar information, synthesize them coherently
5. If sources contradict each other, acknowledge the discrepancy
6. Maintain a professional, helpful tone
7. Structure your response clearly with proper formatting
8. If the question cannot be answered from the provided context, explain what additional information would be needed

ANSWER:"""

    def test_connection(self) -> bool:
        """Test the Gemini connection"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents="Hello, this is a test. Please respond with 'Connection successful.'"
            )
            
            if response.text and "successful" in response.text.lower():
                logging.info("Gemini connection test successful")
                return True
            else:
                logging.warning("Gemini connection test returned unexpected response")
                return False
                
        except Exception as e:
            logging.error(f"Gemini connection test failed: {str(e)}")
            return False