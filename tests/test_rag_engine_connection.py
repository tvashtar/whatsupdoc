"""Test script to verify Vertex AI RAG Engine connection and functionality.
Run this to make sure your RAG Engine setup is working.
"""

import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def required_env_vars():
    """Required environment variables for RAG Engine tests."""
    return ['PROJECT_ID', 'LOCATION', 'RAG_CORPUS_ID']


@pytest.fixture
def rag_config(required_env_vars):
    """RAG Engine configuration from environment variables."""
    config = {}
    missing_vars = []

    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var.lower()] = value

    if missing_vars:
        pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")

    return config


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_required_env_variables(required_env_vars):
    """Test that all required RAG Engine environment variables are set."""
    missing_vars = []

    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)

    assert not missing_vars, f"Missing required environment variables: {', '.join(missing_vars)}"

    # Verify each variable has a reasonable value
    for var in required_env_vars:
        value = os.getenv(var)
        assert value, f"{var} should not be empty"
        assert len(value) > 0, f"{var} should have content"

@pytest.fixture
def rag_client(rag_config):
    """Create a RAG client for testing."""
    from whatsupdoc.vertex_rag_client import VertexRAGClient

    return VertexRAGClient(
        project_id=rag_config['project_id'],
        location=rag_config['location'],
        rag_corpus_id=rag_config['rag_corpus_id']
    )


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_rag_engine_connection(rag_client):
    """Test connection to Vertex AI RAG Engine."""
    # Test that we can establish a connection
    connection_result = rag_client.test_connection()
    assert connection_result, "RAG Engine connection should succeed"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_get_corpus_info(rag_client):
    """Test getting corpus information."""
    # Should be able to get corpus info without error
    info = rag_client.get_corpus_info()

    assert info is not None, "Corpus info should not be None"
    assert isinstance(info, dict), "Corpus info should be a dictionary"

    # Check for expected fields
    if 'name' in info:
        assert isinstance(info['name'], str), "Corpus name should be a string"
        assert len(info['name']) > 0, "Corpus name should not be empty"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_list_rag_files(rag_client):
    """Test listing files in the RAG corpus."""
    files = rag_client.list_rag_files()

    assert files is not None, "File list should not be None"
    assert isinstance(files, list), "Files should be returned as a list"

    # If files exist, check their structure
    if files:
        for file_info in files[:3]:  # Check first 3 files
            assert isinstance(file_info, dict), "Each file should be a dictionary"

@pytest.mark.integration
@pytest.mark.requires_gcp
@pytest.mark.asyncio
async def test_rag_search(rag_client):
    """Test RAG search functionality."""
    test_query = "What are the main topics in the documents?"

    # Run search
    results = await rag_client.search(test_query, max_results=3)

    # Verify results structure
    assert results is not None, "Search should return results"
    assert isinstance(results, list), "Results should be a list"

    # If we have results, verify their structure
    if results:
        assert len(results) <= 3, "Should not return more than max_results"

        for result in results:
            # Check required attributes exist
            assert hasattr(result, 'title'), "Result should have a title"
            assert hasattr(result, 'confidence_score'), "Result should have a confidence score"
            assert hasattr(result, 'snippet'), "Result should have a snippet"

            # Check data types
            assert isinstance(result.title, str), "Title should be a string"
            assert isinstance(result.confidence_score, (int, float)), "Confidence should be numeric"
            assert isinstance(result.snippet, str), "Snippet should be a string"

            # Check reasonable values
            assert 0 <= result.confidence_score <= 1, "Confidence should be between 0 and 1"
            assert len(result.snippet) > 0, "Snippet should not be empty"


@pytest.mark.integration
@pytest.mark.requires_gcp
@pytest.mark.parametrize("query,expected_min_results", [
    ("test query", 0),  # May return 0 results for generic queries
    ("main topics", 0),  # May return 0 results
])
@pytest.mark.asyncio
async def test_rag_search_parametrized(rag_client, query, expected_min_results):
    """Test RAG search with different queries."""
    results = await rag_client.search(query, max_results=5)

    assert isinstance(results, list), f"Results for query '{query}' should be a list"
    assert len(results) >= expected_min_results, f"Should have at least {expected_min_results} results for '{query}'"
