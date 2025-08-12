#!/usr/bin/env python3
"""
Test script to verify GCP Vertex AI Search connection and configuration.
Run this to make sure your GCP setup is working before building the full bot.
"""

import os
from dotenv import load_dotenv

def test_env_variables():
    """Test that all required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'PROJECT_ID',
        'LOCATION', 
        'RAG_CORPUS_ID'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            print(f"  ✅ {var}: {value}")
    
    if missing:
        print(f"  ❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("  ✅ All GCP environment variables found!")
    return True

def test_gcp_auth():
    """Test Google Cloud authentication."""
    print("\n🔐 Testing Google Cloud authentication...")
    
    try:
        from google.auth import default
        credentials, project = default()
        print(f"  ✅ Successfully authenticated with project: {project}")
        
        # Verify the project matches our env var
        env_project = os.getenv('PROJECT_ID')
        if project != env_project:
            print(f"  ⚠️  Warning: Authenticated project ({project}) != PROJECT_ID env var ({env_project})")
        
        return True
    except Exception as e:
        print(f"  ❌ Authentication failed: {e}")
        print("  💡 Try running: gcloud auth application-default login")
        return False

def test_vertex_rag_client():
    """Test connection to Vertex AI RAG Engine."""
    print("\n🔍 Testing Vertex AI RAG Engine connection...")
    
    try:
        from whatsupdoc.vertex_rag_client import VertexRAGClient
        
        # Get configuration
        project_id = os.getenv('PROJECT_ID')
        location = os.getenv('LOCATION')  
        rag_corpus_id = os.getenv('RAG_CORPUS_ID')
        
        print(f"  📍 Using RAG corpus: {rag_corpus_id}")
        
        # Initialize the client
        client = VertexRAGClient(
            project_id=project_id,
            location=location,
            rag_corpus_id=rag_corpus_id
        )
        
        # Test connection
        if client.test_connection():
            print("  ✅ RAG Engine connection successful!")
            return True
        else:
            print("  ❌ RAG Engine connection failed")
            return False
        
    except ImportError:
        print("  ❌ Missing required packages for RAG Engine")
        print("  💡 Install with: uv sync")
        return False
    except Exception as e:
        print(f"  ❌ RAG Engine connection failed: {e}")
        print("  💡 Check your PROJECT_ID, LOCATION, and RAG_CORPUS_ID in .env")
        return False

def main():
    """Run all tests."""
    print("🧪 GCP Vertex AI RAG Engine Setup Verification\n")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        test_env_variables,
        test_gcp_auth,
        test_vertex_rag_client
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Summary
    print("="*50)
    if passed == len(tests):
        print("🎉 All tests passed! Your GCP setup is ready.")
    else:
        print(f"❌ {len(tests) - passed} test(s) failed. Please fix the issues above.")
    
    print("="*50)

if __name__ == "__main__":
    main()