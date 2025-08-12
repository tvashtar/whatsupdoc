#!/usr/bin/env python3

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from whatsupdoc.config import Config
from whatsupdoc.vertex_search import VertexSearchClient
from whatsupdoc.gemini_rag import GeminiRAGService

def test_integration():
    print("🧪 Testing Gemini RAG Integration")
    print()
    
    # Load config
    config = Config()
    
    # Test configuration
    print("🔍 Testing configuration...")
    errors = config.validate()
    if errors:
        print(f"❌ Configuration errors: {errors}")
        return False
    print("  ✅ Configuration valid")
    print(f"  📝 Gemini model: {config.gemini_model}")
    print(f"  🔧 Use Vertex AI: {config.use_vertex_ai}")
    print(f"  🎛️ Temperature: {config.answer_temperature}")
    print(f"  📏 Max context: {config.max_context_length}")
    print()
    
    # Initialize search client
    print("🔍 Testing search client...")
    search_client = VertexSearchClient(
        project_id=config.project_id,
        location=config.location,
        data_store_id=config.data_store_id,
        app_id=config.app_id
    )
    
    if not search_client.test_connection():
        print("❌ Search client connection failed")
        return False
    print("  ✅ Search client connected")
    print()
    
    # Initialize Gemini RAG service
    print("🤖 Testing Gemini RAG service...")
    try:
        rag_service = GeminiRAGService(
            project_id=config.project_id,
            location=config.location,
            model=config.gemini_model,
            api_key=config.gemini_api_key if not config.use_vertex_ai else None,
            use_vertex_ai=config.use_vertex_ai,
            temperature=config.answer_temperature
        )
        
        if not rag_service.test_connection():
            print("❌ Gemini connection failed")
            return False
        print("  ✅ Gemini service connected")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini service: {e}")
        return False
    print()
    
    # Test full RAG pipeline
    print("🔄 Testing full RAG pipeline...")
    test_query = "What are the main research methods mentioned in the documents?"
    
    async def test_rag_pipeline():
        # Search for documents
        print(f"  🔍 Searching for: '{test_query}'")
        results = await search_client.search(
            query=test_query,
            max_results=3,
            use_grounded_generation=True
        )
        print(f"  📊 Found {len(results)} search results")
        
        if not results:
            print("  ⚠️ No search results found - skipping RAG generation")
            return True
        
        # Generate RAG answer
        print("  🤖 Generating RAG answer...")
        rag_response = await rag_service.generate_answer(
            query=test_query,
            search_results=results,
            max_context_length=config.max_context_length
        )
        
        print(f"  📝 Generated answer ({len(rag_response.answer)} chars)")
        print(f"  📊 Confidence: {rag_response.confidence_score:.1%}")
        print(f"  🔗 Uses {len(rag_response.sources)} sources")
        print(f"  📖 Has citations: {rag_response.has_citations}")
        
        # Show a preview of the answer
        answer_preview = rag_response.answer[:200] + "..." if len(rag_response.answer) > 200 else rag_response.answer
        print(f"  💬 Answer preview: {answer_preview}")
        
        return True
    
    try:
        result = asyncio.run(test_rag_pipeline())
        if not result:
            return False
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {e}")
        return False
    
    print()
    print("=" * 50)
    print("🎉 All integration tests passed!")
    print("🚀 Your Slack RAG bot with Gemini is ready!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)