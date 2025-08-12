"""
Test that the whatsupdoc package can be imported correctly and all modules work.
"""
import pytest
import whatsupdoc


@pytest.mark.unit
def test_main_package_import():
    """Test that the main package can be imported and has version."""
    assert hasattr(whatsupdoc, '__version__')
    assert isinstance(whatsupdoc.__version__, str)
    assert len(whatsupdoc.__version__) > 0


@pytest.mark.unit
def test_config_module_import():
    """Test that config module imports and instantiates correctly."""
    from whatsupdoc.config import Config
    
    # Should be able to instantiate without errors
    config = Config()
    assert config is not None


@pytest.mark.unit
def test_vertex_rag_client_import():
    """Test that vertex RAG client modules import correctly."""
    from whatsupdoc.vertex_rag_client import VertexRAGClient, SearchResult
    
    # Classes should be importable and callable
    assert callable(VertexRAGClient)
    assert callable(SearchResult)


@pytest.mark.unit  
def test_gemini_rag_import():
    """Test that Gemini RAG modules import correctly."""
    from whatsupdoc.gemini_rag import GeminiRAGService, RAGResponse
    
    # Classes should be importable and callable
    assert callable(GeminiRAGService)
    assert callable(RAGResponse)


@pytest.mark.unit
def test_slack_bot_import():
    """Test that Slack bot module imports correctly."""
    from whatsupdoc.slack_bot import ResearchPaperBot
    
    # Class should be importable and callable
    assert callable(ResearchPaperBot)


@pytest.mark.unit
def test_app_entry_point_import():
    """Test that app entry point imports correctly."""
    from whatsupdoc.app import main
    
    # Function should be importable and callable
    assert callable(main)