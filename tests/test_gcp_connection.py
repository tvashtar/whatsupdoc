"""Test script to verify GCP Vertex AI Search connection and configuration.
Run this to make sure your GCP setup is working before building the full bot.
"""

import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def required_gcp_vars() -> list[str]:
    """Required GCP environment variables."""
    return ["PROJECT_ID", "LOCATION", "RAG_CORPUS_ID"]


@pytest.fixture
def gcp_config(required_gcp_vars: list[str]) -> dict[str, str]:
    """GCP configuration from environment variables."""
    config = {}
    missing_vars = []

    for var in required_gcp_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var.lower()] = value

    if missing_vars:
        pytest.skip(f"Missing required GCP environment variables: {', '.join(missing_vars)}")

    return config


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_required_gcp_env_variables(required_gcp_vars: list[str]) -> None:
    """Test that all required GCP environment variables are set."""
    missing_vars = []

    for var in required_gcp_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)

    assert (
        not missing_vars
    ), f"Missing required GCP environment variables: {', '.join(missing_vars)}"

    # Verify each variable has reasonable content
    for var in required_gcp_vars:
        value = os.getenv(var)
        assert value and len(value.strip()) > 0, f"{var} should not be empty"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_gcp_authentication(gcp_config: dict[str, str]) -> None:
    """Test Google Cloud authentication."""
    from google.auth import default

    # Should be able to get default credentials
    credentials, project = default()

    assert credentials is not None, "Should have valid credentials"
    assert project is not None, "Should have a project ID"
    assert isinstance(project, str), "Project ID should be a string"
    assert len(project) > 0, "Project ID should not be empty"

    # Check if authenticated project matches environment variable
    env_project = gcp_config.get("project_id")
    if env_project and project != env_project:
        # This is just a warning, not a failure
        pytest.warns(
            UserWarning, f"Authenticated project ({project}) != PROJECT_ID env var ({env_project})"
        )


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_vertex_rag_client_connection(gcp_config: dict[str, str]) -> None:
    """Test connection to Vertex AI RAG Engine."""
    from whatsupdoc.vertex_rag_client import VertexRAGClient

    # Initialize the client
    client = VertexRAGClient(
        project_id=gcp_config["project_id"],
        location=gcp_config["location"],
        rag_corpus_id=gcp_config["rag_corpus_id"],
    )

    assert client is not None, "RAG client should be created successfully"

    # Test connection
    connection_result = client.test_connection()
    assert connection_result, "RAG Engine connection should succeed"


@pytest.mark.integration
@pytest.mark.requires_gcp
def test_vertex_rag_client_initialization(gcp_config: dict[str, str]) -> None:
    """Test RAG client can be initialized with valid config."""
    from whatsupdoc.vertex_rag_client import VertexRAGClient

    client = VertexRAGClient(
        project_id=gcp_config["project_id"],
        location=gcp_config["location"],
        rag_corpus_id=gcp_config["rag_corpus_id"],
    )

    # Verify client attributes
    assert hasattr(client, "project_id"), "Client should have project_id attribute"
    assert hasattr(client, "location"), "Client should have location attribute"
    assert hasattr(client, "rag_corpus_id"), "Client should have rag_corpus_id attribute"

    assert client.project_id == gcp_config["project_id"], "Project ID should match config"
    assert client.location == gcp_config["location"], "Location should match config"
    assert client.rag_corpus_id == gcp_config["rag_corpus_id"], "RAG corpus ID should match config"
