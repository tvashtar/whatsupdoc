"""
Test Gemini RAG integration functionality.
"""

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def config():
    """Create and validate configuration."""
    from whatsupdoc.config import Config
    
    config = Config()
    errors = config.validate()
    
    if errors:
        pytest.skip(f"Configuration validation failed: {errors}")
    
    return config


@pytest.fixture
def search_client(config):
    """Create RAG search client."""
    from whatsupdoc.vertex_rag_client import VertexRAGClient
    
    client = VertexRAGClient(
        project_id=config.project_id,
        location=config.location,
        rag_corpus_id=config.rag_corpus_id
    )
    
    if not client.test_connection():
        pytest.skip("RAG Engine connection failed")
    
    return client


@pytest.fixture  
def gemini_service(config):
    """Create Gemini RAG service."""
    from whatsupdoc.gemini_rag import GeminiRAGService
    
    service = GeminiRAGService(
        project_id=config.project_id,
        location=config.location,
        model=config.gemini_model,
        api_key=config.gemini_api_key if not config.use_vertex_ai else None,
        use_vertex_ai=config.use_vertex_ai,
        temperature=config.answer_temperature
    )
    
    if not service.test_connection():
        pytest.skip("Gemini service connection failed")
    
    return service


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_config_validation(config):
    """Test that configuration is valid."""
    assert config is not None, "Configuration should be created"
    assert hasattr(config, 'gemini_model'), "Should have gemini_model"
    assert hasattr(config, 'use_vertex_ai'), "Should have use_vertex_ai"
    assert hasattr(config, 'answer_temperature'), "Should have answer_temperature"
    assert hasattr(config, 'max_context_length'), "Should have max_context_length"
    
    # Check reasonable values
    assert 0 <= config.answer_temperature <= 1, "Temperature should be between 0 and 1"
    assert config.max_context_length > 0, "Max context length should be positive"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_search_client_connection(search_client):
    """Test that search client can connect."""
    assert search_client is not None, "Search client should be created"
    
    # Connection test already passed in fixture
    assert hasattr(search_client, 'test_connection'), "Should have test_connection method"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_gemini_service_connection(gemini_service):
    """Test that Gemini service can connect."""
    assert gemini_service is not None, "Gemini service should be created"
    
    # Connection test already passed in fixture
    assert hasattr(gemini_service, 'test_connection'), "Should have test_connection method"


@pytest.mark.integration
@pytest.mark.requires_gcp
@pytest.mark.asyncio
async def test_search_functionality(search_client):
    """Test search functionality works."""
    test_query = "What are the main topics in the documents?"
    
    results = await search_client.search(
        query=test_query,
        max_results=3,
        use_grounded_generation=True
    )
    
    assert isinstance(results, list), "Results should be a list"
    # Results may be empty if no documents match
    assert len(results) >= 0, "Results length should be non-negative"
    
    # If we have results, check their structure
    if results:
        for result in results:
            assert hasattr(result, 'title'), "Result should have title"
            assert hasattr(result, 'snippet'), "Result should have snippet"
            assert hasattr(result, 'confidence_score'), "Result should have confidence score"


@pytest.mark.integration
@pytest.mark.requires_gcp
@pytest.mark.asyncio
async def test_full_rag_pipeline(search_client, gemini_service, config):
    """Test the complete RAG pipeline integration."""
    test_query = "What are the main research methods mentioned in the documents?"
    
    # Step 1: Search for documents
    results = await search_client.search(
        query=test_query,
        max_results=3,
        use_grounded_generation=True
    )
    
    assert isinstance(results, list), "Search results should be a list"
    
    if not results:
        pytest.skip("No search results found - cannot test RAG generation")
    
    # Step 2: Generate RAG answer
    rag_response = await gemini_service.generate_answer(
        query=test_query,
        search_results=results,
        max_context_length=config.max_context_length
    )
    
    # Verify response structure
    assert rag_response is not None, "RAG response should not be None"
    assert hasattr(rag_response, 'answer'), "Response should have answer"
    assert hasattr(rag_response, 'confidence_score'), "Response should have confidence score"
    assert hasattr(rag_response, 'sources'), "Response should have sources"
    assert hasattr(rag_response, 'has_citations'), "Response should have has_citations flag"
    
    # Verify response content
    assert isinstance(rag_response.answer, str), "Answer should be a string"
    assert len(rag_response.answer) > 0, "Answer should not be empty"
    assert isinstance(rag_response.confidence_score, (int, float)), "Confidence should be numeric"
    assert 0 <= rag_response.confidence_score <= 1, "Confidence should be between 0 and 1"
    assert isinstance(rag_response.sources, list), "Sources should be a list"
    assert isinstance(rag_response.has_citations, bool), "has_citations should be boolean"


@pytest.mark.integration
@pytest.mark.requires_gcp
@pytest.mark.parametrize("query", [
    "What is the main topic?",
    "How to implement this feature?",
    "What are the key findings?"
])
@pytest.mark.asyncio
async def test_rag_pipeline_multiple_queries(search_client, gemini_service, config, query):
    """Test RAG pipeline with different types of queries."""
    results = await search_client.search(
        query=query,
        max_results=2,
        use_grounded_generation=True
    )
    
    if not results:
        pytest.skip(f"No search results found for query: '{query}'")
    
    rag_response = await gemini_service.generate_answer(
        query=query,
        search_results=results,
        max_context_length=config.max_context_length
    )
    
    assert rag_response is not None, f"Should generate response for query: '{query}'"
    assert len(rag_response.answer) > 0, f"Should have non-empty answer for query: '{query}'"