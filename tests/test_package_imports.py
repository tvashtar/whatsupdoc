#!/usr/bin/env python3
"""
Test that the whatsupdoc package can be imported correctly and all modules work.
"""

def test_package_imports():
    print("🧪 Testing Package Imports")
    print()
    
    try:
        # Test main package import
        print("📦 Testing main package import...")
        import whatsupdoc
        print(f"  ✅ whatsupdoc package version: {whatsupdoc.__version__}")
        
        # Test configuration module
        print("⚙️  Testing configuration module...")
        from whatsupdoc.config import Config
        config = Config()
        print("  ✅ Config class imported and instantiated")
        
        # Test vertex search module
        print("🔍 Testing vertex search module...")
        from whatsupdoc.vertex_rag_client import VertexRAGClient, SearchResult
        print("  ✅ VertexRAGClient and SearchResult imported")
        
        # Test gemini rag module
        print("🤖 Testing Gemini RAG module...")
        from whatsupdoc.gemini_rag import GeminiRAGService, RAGResponse
        print("  ✅ GeminiRAGService and RAGResponse imported")
        
        # Test slack bot module
        print("💬 Testing Slack bot module...")
        from whatsupdoc.slack_bot import ResearchPaperBot
        print("  ✅ ResearchPaperBot imported")
        
        # Test app entry point
        print("🚀 Testing app entry point...")
        from whatsupdoc.app import main
        print("  ✅ Main entry point imported")
        
        print()
        print("=" * 50)
        print("🎉 All package imports successful!")
        print("📦 Package structure is working correctly")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_package_imports()
    exit(0 if success else 1)