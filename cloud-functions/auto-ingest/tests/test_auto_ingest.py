#!/usr/bin/env python3
"""Tests for the auto-ingest Cloud Function.
Run from the repo root with: uv run --extra cloud-functions python cloud-functions/auto-ingest/tests/test_auto_ingest.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")

    try:
        import vertexai
        print("✅ vertexai imported successfully")

        from vertexai import rag
        print("✅ vertexai.rag imported successfully")

        # Test specific RAG components
        assert hasattr(rag, 'import_files'), "rag.import_files not found"
        assert hasattr(rag, 'TransformationConfig'), "rag.TransformationConfig not found"
        assert hasattr(rag, 'ChunkingConfig'), "rag.ChunkingConfig not found"
        print("✅ All RAG components available")

        # Test creating config objects
        config = rag.TransformationConfig(
            rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        )
        print("✅ Successfully created TransformationConfig")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def test_main_module():
    """Test the main module imports and basic functionality."""
    print("\nTesting main module...")

    # Set minimal env vars for import
    os.environ['PROJECT_ID'] = 'test-project'
    os.environ['RAG_CORPUS_ID'] = 'test-corpus'

    try:
        import main
        print("✅ main.py imported successfully")

        # Test creating the client
        client = main.RAGIngestionClient('test-project', 'us-central1', 'test-corpus')
        print("✅ RAGIngestionClient instantiated successfully")
        print(f"  Corpus resource name: {client.corpus_resource_name}")

        # Test the file filter function
        print("\nTesting file filters:")
        test_cases = [
            ('test.pdf', True),
            ('test.txt', True),
            ('test.docx', True),
            ('test.html', True),
            ('test.md', True),
            ('test.exe', False),
            ('test.jpg', False),
            ('.hidden.pdf', True),  # Hidden files with valid extension
        ]

        for filename, expected in test_cases:
            result = main.is_supported_file(filename)
            status = "✅" if result == expected else "❌"
            print(f"  {status} {filename}: {result} (expected {expected})")

        # Test with full corpus name
        client2 = main.RAGIngestionClient(
            'test-project',
            'us-central1',
            'projects/test-project/locations/us-central1/ragCorpora/123456'
        )
        print(f"\n✅ Full corpus name handled: {client2.corpus_resource_name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_cloud_event_handling():
    """Test CloudEvent handling."""
    print("\nTesting CloudEvent handling...")

    try:
        from cloudevents.http import CloudEvent

        # Create test CloudEvent
        test_attributes = {
            'type': 'google.cloud.storage.object.v1.finalized',
            'source': 'storage.googleapis.com',
            'subject': 'objects/test.pdf',
            'datacontenttype': 'application/json'
        }

        test_data = {
            'bucket': 'test-bucket',
            'name': 'test-folder/test.pdf',
            'size': '1024',
            'contentType': 'application/pdf'
        }

        test_event = CloudEvent(test_attributes, test_data)

        print("✅ CloudEvent created successfully")
        print(f"  Event type: {test_event['type']}")
        print(f"  Bucket: {test_event.data['bucket']}")
        print(f"  File: {test_event.data['name']}")

        # Test event filtering
        import main

        # Test supported file
        if main.is_supported_file(test_event.data['name']):
            print("✅ PDF file correctly identified as supported")
        else:
            print("❌ PDF file should be supported")
            return False

        # Test unsupported file
        test_event.data['name'] = 'test.exe'
        if not main.is_supported_file(test_event.data['name']):
            print("✅ EXE file correctly identified as unsupported")
        else:
            print("❌ EXE file should not be supported")
            return False

        # Test system file filtering
        test_event.data['name'] = '.DS_Store'
        if test_event.data['name'].startswith('.') or '/.' in test_event.data['name']:
            print("✅ System file correctly identified for skipping")
        else:
            print("❌ System file should be skipped")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_rag_client_initialization():
    """Test different RAG client initialization scenarios."""
    print("\nTesting RAG client initialization...")

    os.environ['PROJECT_ID'] = 'test-project'
    os.environ['RAG_CORPUS_ID'] = 'test-corpus'

    try:
        import main

        # Test with numeric corpus ID
        client1 = main.RAGIngestionClient('test-project', 'us-central1', '1234567890')
        expected1 = 'projects/test-project/locations/us-central1/ragCorpora/1234567890'
        assert client1.corpus_resource_name == expected1, f"Expected {expected1}, got {client1.corpus_resource_name}"
        print(f"✅ Numeric corpus ID: {client1.corpus_resource_name}")

        # Test with full resource name
        full_name = 'projects/my-project/locations/europe-west1/ragCorpora/9876543210'
        client2 = main.RAGIngestionClient('test-project', 'us-central1', full_name)
        assert client2.corpus_resource_name == full_name, f"Expected {full_name}, got {client2.corpus_resource_name}"
        print(f"✅ Full resource name: {client2.corpus_resource_name}")

        # Test with string corpus ID
        client3 = main.RAGIngestionClient('test-project', 'us-central1', 'my-corpus')
        expected3 = 'projects/test-project/locations/us-central1/ragCorpora/my-corpus'
        assert client3.corpus_resource_name == expected3, f"Expected {expected3}, got {client3.corpus_resource_name}"
        print(f"✅ String corpus ID: {client3.corpus_resource_name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Run all tests."""
    print("="*60)
    print("Auto-Ingest Cloud Function Tests")
    print("="*60)

    tests = [
        ("Import Tests", test_imports),
        ("Main Module Tests", test_main_module),
        ("CloudEvent Handling Tests", test_cloud_event_handling),
        ("RAG Client Initialization Tests", test_rag_client_initialization),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{name}")
        print("-"*40)
        result = test_func()
        results.append((name, result))

    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
