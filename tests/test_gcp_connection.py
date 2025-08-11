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
        'DATA_STORE_ID',
        'APP_ID'
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

def test_vertex_search():
    """Test connection to Vertex AI Search."""
    print("\n🔍 Testing Vertex AI Search connection...")
    
    try:
        from google.cloud import discoveryengine_v1 as discoveryengine
        
        # Initialize the client
        client = discoveryengine.SearchServiceClient()
        
        # Build the serving config name
        project_id = os.getenv('PROJECT_ID')
        location = os.getenv('LOCATION')  
        data_store_id = os.getenv('DATA_STORE_ID')
        
        serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/servingConfigs/default_config"
        
        print(f"  📍 Using serving config: {serving_config}")
        
        # Test with a simple search
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query="test",
            page_size=1  # Just get 1 result to test connection
        )
        
        response = client.search(request)
        
        # Try to get first result to verify the connection works
        results = list(response.results)
        
        print(f"  ✅ Successfully connected to Vertex AI Search!")
        print(f"  📊 Data store appears to be working (found {len(results)} results for test query)")
        
        if results:
            print(f"  📄 Sample result title: {results[0].document.derived_struct_data.get('title', 'No title')}")
        
        return True
        
    except ImportError:
        print("  ❌ Missing google-cloud-discoveryengine package")
        print("  💡 Install with: pip install google-cloud-discoveryengine")
        return False
    except Exception as e:
        print(f"  ❌ Vertex AI Search connection failed: {e}")
        print("  💡 Check your PROJECT_ID, LOCATION, DATA_STORE_ID, and APP_ID in .env")
        return False

def main():
    """Run all tests."""
    print("🧪 GCP Vertex AI Search Setup Verification\n")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        test_env_variables,
        test_gcp_auth,
        test_vertex_search
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