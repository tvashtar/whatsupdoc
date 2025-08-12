#!/usr/bin/env python3
"""
Test script to verify Vertex AI RAG Engine connection and functionality.
Run this to make sure your RAG Engine setup is working.
"""

import os
import asyncio
from dotenv import load_dotenv

def test_env_variables():
    """Test that all required RAG Engine environment variables are set."""
    print("🔍 Testing RAG Engine environment variables...")
    
    required_vars = [
        'PROJECT_ID',
        'LOCATION',
        'RAG_CORPUS_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show partial value for security
            if len(value) > 20:
                display_value = f"{value[:15]}...{value[-10:]}"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"  ❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    
    print("  ✅ All required RAG Engine environment variables found!")
    return True

def test_rag_engine_connection():
    """Test connection to Vertex AI RAG Engine."""
    print("\n🔍 Testing RAG Engine connection...")
    
    try:
        from whatsupdoc.vertex_rag_client import VertexRAGClient
        
        project_id = os.getenv('PROJECT_ID')
        location = os.getenv('LOCATION')
        rag_corpus_id = os.getenv('RAG_CORPUS_ID')
        
        if not all([project_id, location, rag_corpus_id]):
            print("  ❌ Missing required environment variables")
            return False
        
        # Initialize RAG client
        client = VertexRAGClient(
            project_id=project_id,
            location=location,
            rag_corpus_id=rag_corpus_id
        )
        
        # Test connection
        if client.test_connection():
            print("  ✅ RAG Engine connection successful!")
            
            # Get corpus info
            try:
                info = client.get_corpus_info()
                print(f"  📚 Corpus: {info.get('display_name', 'Unknown')}")
                print(f"  🆔 ID: {info.get('name', 'Unknown')}")
                if info.get('description'):
                    print(f"  📝 Description: {info['description']}")
            except Exception as e:
                print(f"  ⚠️  Could not get corpus info: {e}")
            
            # List files in corpus
            try:
                files = client.list_rag_files()
                print(f"  📄 Files in corpus: {len(files)}")
                if files:
                    print(f"  📄 Sample files:")
                    for i, file in enumerate(files[:3]):
                        print(f"    • {file.get('display_name', 'Unknown')}")
                        if i >= 2 and len(files) > 3:
                            print(f"    • ... and {len(files) - 3} more")
                            break
            except Exception as e:
                print(f"  ⚠️  Could not list files: {e}")
            
            return True
        else:
            print("  ❌ RAG Engine connection failed")
            return False
            
    except ImportError as e:
        print(f"  ❌ Missing required packages: {e}")
        print("  💡 Run: uv sync")
        return False
    except Exception as e:
        print(f"  ❌ RAG Engine connection failed: {e}")
        return False

def test_rag_search():
    """Test RAG search functionality."""
    print("\n🔍 Testing RAG search...")
    
    try:
        from whatsupdoc.vertex_rag_client import VertexRAGClient
        
        project_id = os.getenv('PROJECT_ID')
        location = os.getenv('LOCATION')
        rag_corpus_id = os.getenv('RAG_CORPUS_ID')
        
        client = VertexRAGClient(
            project_id=project_id,
            location=location,
            rag_corpus_id=rag_corpus_id
        )
        
        # Test with a simple query
        test_query = "What are the main topics in the documents?"
        print(f"  🔎 Testing query: '{test_query}'")
        
        # Run async search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                client.search(test_query, max_results=3)
            )
            
            if results:
                print(f"  ✅ Search successful! Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"  📄 Result {i}:")
                    print(f"    Title: {result.title}")
                    print(f"    Confidence: {result.confidence_score:.1%}")
                    print(f"    Content length: {len(result.snippet)} chars")
                    if result.snippet:
                        preview = result.snippet[:100].replace('\n', ' ')
                        print(f"    Preview: {preview}{'...' if len(result.snippet) > 100 else ''}")
                    print()
                
                return True
            else:
                print("  ❌ No search results returned")
                return False
                
        finally:
            loop.close()
            
    except Exception as e:
        print(f"  ❌ RAG search failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Vertex AI RAG Engine Setup Verification\n")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        test_env_variables,
        test_rag_engine_connection,
        test_rag_search,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Summary
    print("="*60)
    if passed == len(tests):
        print("🎉 All tests passed! Your RAG Engine setup is ready.")
        print("💡 You can now run the Slack bot with proper chunk-based RAG!")
    else:
        print(f"❌ {len(tests) - passed} test(s) failed. Please fix the issues above.")
    
    print("="*60)

if __name__ == "__main__":
    main()