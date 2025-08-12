#!/usr/bin/env python3

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from whatsupdoc.config import Config
from whatsupdoc.vertex_search import VertexSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_vertex_search():
    # Load environment variables
    load_dotenv()
    
    # Initialize config
    config = Config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print(f"Testing Vertex AI Search connection...")
    print(f"Project ID: {config.project_id}")
    print(f"Data Store ID: {config.data_store_id}")
    print(f"Location: {config.location}")
    print(f"App ID: {config.app_id}")
    print()
    
    # Initialize search client
    search_client = VertexSearchClient(
        project_id=config.project_id,
        location=config.location,
        data_store_id=config.data_store_id,
        app_id=config.app_id
    )
    
    # Test connection
    print("Testing connection...")
    if not search_client.test_connection():
        print("❌ Connection test failed")
        return False
    
    print("✅ Connection test passed")
    print()
    
    # Test queries for research papers
    test_queries = [
        "What are the main findings about text as data?",
        "methodology",
        "machine learning approaches"
    ]
    
    for query in test_queries:
        print(f"Testing query: '{query}'")
        try:
            results = await search_client.search(
                query=query,
                max_results=3,
                use_grounded_generation=config.use_grounded_generation
            )
            
            print(f"  Retrieved {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result.title}")
                print(f"       Snippet: {result.snippet[:100]}...")
                print(f"       Source: {result.source_uri}")
                print(f"       Confidence: {result.confidence_score:.2f}")
                print()
                
        except Exception as e:
            print(f"  ❌ Query failed: {str(e)}")
            return False
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_vertex_search())
    sys.exit(0 if success else 1)