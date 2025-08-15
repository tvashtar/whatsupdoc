#!/usr/bin/env python3
"""Enhanced e2e tests that verify actual chunk retrieval and RAG functionality."""

import asyncio
import os
import sys
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from slack_webhook_tester import SlackWebhookTester

from whatsupdoc.core.config import Config
from whatsupdoc.core.gemini_rag import GeminiRAGService
from whatsupdoc.core.vertex_rag_client import VertexRAGClient

load_dotenv()


class RAGFunctionalityTester:
    """Test actual RAG functionality including chunk retrieval and answer generation."""

    def __init__(self) -> None:
        """Initialize with real config and clients."""
        self.config = Config()
        self.rag_client = VertexRAGClient(
            project_id=self.config.project_id,
            location=self.config.location,
            rag_corpus_id=self.config.rag_corpus_id,
        )
        self.gemini_service = GeminiRAGService(
            project_id=self.config.project_id,
            location=self.config.location,
            model=self.config.gemini_model,
            use_vertex_ai=self.config.use_vertex_ai,
            temperature=self.config.answer_temperature,
        )

        # Webhook tester for end-to-end tests
        webhook_url = "https://whatsupdoc-slack-bot-530988540591.us-central1.run.app/slack/events"
        signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        if signing_secret:
            self.webhook_tester = SlackWebhookTester(webhook_url, signing_secret)
        else:
            self.webhook_tester = None

    async def test_chunk_retrieval(
        self, query: str, min_expected_chunks: int = 1
    ) -> dict[str, Any]:
        """Test that chunks are actually retrieved for a query."""
        print(f"🔍 Testing chunk retrieval for: '{query}'")

        try:
            # Test with multiple thresholds to find what works
            # Higher values = more permissive (allow greater distances/lower similarity)
            thresholds = [0.0, 0.3, 0.6, 1.0]
            best_result = {"threshold": None, "chunks": [], "count": 0}

            for threshold in thresholds:
                print(f"  📊 Testing threshold: {threshold}")
                chunks = await self.rag_client.search_async(
                    query=query, max_results=self.config.max_results, distance_threshold=threshold
                )

                chunk_count = len(chunks)
                print(f"    📄 Found {chunk_count} chunks")

                if chunk_count > best_result["count"]:
                    best_result = {"threshold": threshold, "chunks": chunks, "count": chunk_count}

                if chunk_count >= min_expected_chunks:
                    break

            # Analyze results
            success = best_result["count"] >= min_expected_chunks
            result = {
                "query": query,
                "success": success,
                "chunks_found": best_result["count"],
                "min_expected": min_expected_chunks,
                "best_threshold": best_result["threshold"],
                "chunks": best_result["chunks"][:3],  # First 3 for analysis
                "error": None,
            }

            if success:
                count = best_result["count"]
                threshold = best_result["threshold"]
                print(f"  ✅ SUCCESS: Found {count} chunks (threshold: {threshold})")
                # Show first chunk details
                if best_result["chunks"]:
                    first_chunk = best_result["chunks"][0]
                    print(f"    📋 First chunk: {first_chunk.title}")
                    print(f"    🎯 Confidence: {first_chunk.confidence_score:.3f}")
                    print(f"    📝 Content preview: {first_chunk.content[:100]}...")
            else:
                count = best_result["count"]
                print(f"  ❌ FAILED: Found {count} chunks, expected {min_expected_chunks}")

            return result

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            return {
                "query": query,
                "success": False,
                "chunks_found": 0,
                "min_expected": min_expected_chunks,
                "best_threshold": None,
                "chunks": [],
                "error": str(e),
            }

    async def test_full_rag_pipeline(self, query: str) -> dict[str, Any]:
        """Test the complete RAG pipeline from query to answer."""
        print(f"🤖 Testing full RAG pipeline for: '{query}'")

        try:
            # Step 1: Get chunks
            chunks = await self.rag_client.search_async(
                query=query,
                max_results=self.config.max_results,
                distance_threshold=0.8,  # Use new default threshold
            )

            if not chunks:
                print("  ❌ No chunks found - cannot test RAG generation")
                return {
                    "query": query,
                    "success": False,
                    "stage": "chunk_retrieval",
                    "chunks_found": 0,
                    "answer": None,
                    "error": "No chunks retrieved",
                }

            print(f"  📄 Retrieved {len(chunks)} chunks")

            # Step 2: Generate answer
            rag_response = await self.gemini_service.generate_answer_async(
                query=query,
                search_results=chunks,
                max_context_length=self.config.max_context_length,
            )

            # Analyze answer quality
            answer_has_content = len(rag_response.answer.strip()) > 20
            answer_not_generic = "don't have enough information" not in rag_response.answer.lower()

            success = answer_has_content and answer_not_generic

            result = {
                "query": query,
                "success": success,
                "stage": "complete",
                "chunks_found": len(chunks),
                "answer": rag_response.answer,
                "confidence": rag_response.confidence_score,
                "answer_length": len(rag_response.answer),
                "sources": len(rag_response.sources),
                "error": None,
            }

            if success:
                print(f"  ✅ SUCCESS: Generated {len(rag_response.answer)} char answer")
                print(f"    🎯 Confidence: {rag_response.confidence_score:.3f}")
                print(f"    📝 Answer preview: {rag_response.answer[:150]}...")
            else:
                print("  ❌ FAILED: Poor answer quality")
                print(f"    📝 Answer: {rag_response.answer[:100]}...")

            return result

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            return {
                "query": query,
                "success": False,
                "stage": "error",
                "chunks_found": 0,
                "answer": None,
                "error": str(e),
            }

    async def test_webhook_with_rag_validation(self, query: str) -> dict[str, Any]:
        """Test webhook AND validate that it actually returns meaningful results."""
        print(f"🌐 Testing webhook + RAG validation for: '{query}'")

        if not self.webhook_tester:
            return {
                "query": query,
                "success": False,
                "error": "No webhook tester available (missing SLACK_SIGNING_SECRET)",
            }

        try:
            # Step 1: Test webhook response
            response = self.webhook_tester.test_slash_command(query)
            webhook_success = response.status_code == 200

            # Step 2: Test actual RAG functionality
            rag_result = await self.test_full_rag_pipeline(query)

            # Combined result
            overall_success = webhook_success and rag_result["success"]

            result = {
                "query": query,
                "success": overall_success,
                "webhook_status": response.status_code,
                "webhook_success": webhook_success,
                "rag_success": rag_result["success"],
                "chunks_found": rag_result.get("chunks_found", 0),
                "answer_quality": "good" if rag_result["success"] else "poor",
                "error": rag_result.get("error"),
            }

            if overall_success:
                print("  ✅ SUCCESS: Webhook + RAG both working")
            else:
                print(f"  ❌ FAILED: Webhook={webhook_success}, RAG={rag_result['success']}")

            return result

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            return {"query": query, "success": False, "error": str(e)}

    async def run_comprehensive_tests(self) -> dict[str, Any]:
        """Run comprehensive tests that actually validate functionality."""
        print("🚀 Starting Comprehensive RAG Functionality Tests")
        print("=" * 60)

        # Test queries that should work if corpus is properly indexed
        test_queries = [
            "what policy areas were studied in the politics paper",
            "policy",
            "what llms were used in the political paper",
            "vacation",  # Previously needed 0.6
            "PTO",  # Test borderline cases
            "benefits",  # New test case
        ]

        results = {
            "chunk_retrieval_tests": [],
            "full_rag_tests": [],
            "webhook_rag_tests": [],
            "summary": {},
        }

        # Test 1: Chunk Retrieval
        print("\n📄 Testing Chunk Retrieval")
        print("-" * 40)
        for query in test_queries:  # Test subset for chunk retrieval
            result = await self.test_chunk_retrieval(query, min_expected_chunks=1)
            results["chunk_retrieval_tests"].append(result)

        # Test 2: Full RAG Pipeline
        print("\n🤖 Testing Full RAG Pipeline")
        print("-" * 40)
        for query in test_queries:  # Test subset for full pipeline
            result = await self.test_full_rag_pipeline(query)
            results["full_rag_tests"].append(result)

        # Test 3: Webhook + RAG Validation
        print("\n🌐 Testing Webhook + RAG Validation")
        print("-" * 40)
        for query in test_queries:  # Test subset for webhook
            result = await self.test_webhook_with_rag_validation(query)
            results["webhook_rag_tests"].append(result)

        # Generate Summary
        chunk_success = sum(1 for r in results["chunk_retrieval_tests"] if r["success"])
        rag_success = sum(1 for r in results["full_rag_tests"] if r["success"])
        webhook_success = sum(1 for r in results["webhook_rag_tests"] if r["success"])

        total_chunk = len(results["chunk_retrieval_tests"])
        total_rag = len(results["full_rag_tests"])
        total_webhook = len(results["webhook_rag_tests"])

        results["summary"] = {
            "chunk_retrieval": {"passed": chunk_success, "total": total_chunk},
            "full_rag": {"passed": rag_success, "total": total_rag},
            "webhook_rag": {"passed": webhook_success, "total": total_webhook},
            "overall_success": chunk_success > 0 or rag_success > 0,
        }

        # Print Summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)

        print(f"📄 Chunk Retrieval: {chunk_success}/{total_chunk} passed")
        print(f"🤖 Full RAG Pipeline: {rag_success}/{total_rag} passed")
        print(f"🌐 Webhook + RAG: {webhook_success}/{total_webhook} passed")

        if results["summary"]["overall_success"]:
            print("\n✅ OVERALL: Some RAG functionality is working")
        else:
            print("\n❌ OVERALL: RAG functionality is completely broken")
            print("💡 This indicates the corpus may be empty or API quotas exceeded")

        # Detailed Analysis
        print("\n📋 DETAILED FINDINGS:")

        if chunk_success == 0:
            print("❌ No chunks retrieved for any query - corpus may be empty or misconfigured")
        elif chunk_success < total_chunk:
            msg = f"⚠️  Only {chunk_success}/{total_chunk} queries returned chunks - missing content"
            print(msg)
        else:
            print("✅ Chunk retrieval working for all test queries")

        if rag_success == 0 and chunk_success > 0:
            print("❌ Chunks found but answer generation failing - check Gemini service")
        elif rag_success > 0:
            print("✅ Answer generation working when chunks are available")

        return results


async def main() -> int:
    """Main test runner."""
    tester = RAGFunctionalityTester()
    results = await tester.run_comprehensive_tests()

    # Return exit code based on results
    if results["summary"]["overall_success"]:
        print("\n🎉 Tests completed - some functionality working")
        return 0
    else:
        print("\n💥 Tests completed - major issues detected")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
