"""CORS and Origin Validation Tests

Tests the FastAPI middleware to ensure it properly blocks unauthorized origins
while allowing requests from the authorized bucket URL.
"""

from typing import Any

import pytest
import requests

# Configuration
API_BASE_URL = "https://whatsupdoc-web-api-rtgwumc6ua-uc.a.run.app"
AUTHORIZED_BUCKET = "https://storage.googleapis.com/whatsupdoc-widget-static"


class TestCORSValidation:
    """Test CORS and origin validation middleware"""

    @pytest.fixture
    def test_payload(self) -> dict[str, Any]:
        """Standard test payload for chat API"""
        import time

        return {
            "query": "test cors validation",
            "conversation_id": f"test-cors-{int(time.time() * 1000)}",
            "max_results": 1,
            "confidence_threshold": 0.5,
        }

    def make_chat_request(
        self, headers: dict[str, str], payload: dict[str, Any]
    ) -> requests.Response:
        """Make a request to the chat API with specific headers"""
        default_headers = {"Content-Type": "application/json", "X-Widget-Version": "1.0.0"}
        default_headers.update(headers)

        return requests.post(
            f"{API_BASE_URL}/api/chat", headers=default_headers, json=payload, timeout=10
        )

    def test_authorized_bucket_origin_allowed(self, test_payload: dict[str, Any]) -> None:
        """Test that requests from authorized bucket are allowed"""
        headers = {
            "Origin": "https://storage.googleapis.com",
            "Referer": f"{AUTHORIZED_BUCKET}/demo.html",
            "X-Widget-Origin": AUTHORIZED_BUCKET,
            "X-Widget-URL": f"{AUTHORIZED_BUCKET}/demo.html",
        }

        response = self.make_chat_request(headers, test_payload)

        # Should be successful (200) or rate limited (429), but not blocked by CORS
        assert response.status_code in [
            200,
            429,
        ], f"Expected success or rate limit, got {response.status_code}: {response.text}"

        # If rate limited, that's actually a good sign - it means CORS passed
        if response.status_code == 429:
            print("✅ Request reached rate limiter (CORS validation passed)")

    def test_unauthorized_bucket_blocked(self, test_payload: dict[str, Any]) -> None:
        """Test that requests from unauthorized buckets are blocked"""
        headers = {
            "Origin": "https://storage.googleapis.com",
            "Referer": "https://storage.googleapis.com/unauthorized-bucket/test.html",
            "X-Widget-Origin": "https://storage.googleapis.com/unauthorized-bucket",
            "X-Widget-URL": "https://storage.googleapis.com/unauthorized-bucket/test.html",
        }

        response = self.make_chat_request(headers, test_payload)

        # Should be blocked (403 or similar)
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        print(f"✅ Unauthorized bucket blocked with status {response.status_code}")

    def test_malicious_domain_blocked(self, test_payload: dict[str, Any]) -> None:
        """Test that requests from malicious domains are blocked"""
        headers = {
            "Origin": "https://malicious-site.com",
            "Referer": "https://malicious-site.com/steal-data.html",
            "X-Widget-Origin": "https://malicious-site.com",
            "X-Widget-URL": "https://malicious-site.com/steal-data.html",
        }

        response = self.make_chat_request(headers, test_payload)

        # Should be blocked
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        print(f"✅ Malicious domain blocked with status {response.status_code}")

    def test_no_referer_blocked(self, test_payload: dict[str, Any]) -> None:
        """Test that requests without referer header are blocked"""
        headers = {
            "Origin": "https://storage.googleapis.com",
            "X-Widget-Origin": AUTHORIZED_BUCKET,
            # Deliberately omitting Referer header
        }

        response = self.make_chat_request(headers, test_payload)

        # Should be blocked due to missing referer
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        print(f"✅ Request without referer blocked with status {response.status_code}")

    def test_health_endpoint_accessible(self) -> None:
        """Test that health endpoint is accessible from any origin"""
        headers = {
            "Origin": "https://malicious-site.com"  # Even malicious origins should access health
        }

        response = requests.get(f"{API_BASE_URL}/api/health", headers=headers, timeout=10)

        assert (
            response.status_code == 200
        ), f"Health endpoint should be accessible, got {response.status_code}"

        health_data = response.json()
        assert (
            health_data.get("status") == "healthy"
        ), "Health endpoint should return healthy status"
        print("✅ Health endpoint accessible from any origin")

    def test_cors_preflight_requests(self) -> None:
        """Test CORS preflight (OPTIONS) requests"""
        # Test preflight from authorized origin
        response = requests.options(
            f"{API_BASE_URL}/api/chat",
            headers={
                "Origin": "https://storage.googleapis.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
            timeout=10,
        )

        # Preflight should succeed
        assert response.status_code in [
            200,
            204,
        ], f"Preflight should succeed, got {response.status_code}"

        # Check CORS headers
        cors_origin = response.headers.get("Access-Control-Allow-Origin")
        assert cors_origin is not None, "Missing Access-Control-Allow-Origin header"
        print(f"✅ CORS preflight successful, allowed origin: {cors_origin}")

    def test_direct_api_access_blocked(self, test_payload: dict[str, Any]) -> None:
        """Test that direct API access (not from widget) is blocked"""
        headers = {
            "Origin": API_BASE_URL,
            "Referer": f"{API_BASE_URL}/api/docs",
            "X-Widget-Origin": API_BASE_URL,
            "X-Widget-URL": f"{API_BASE_URL}/api/docs",
        }

        response = self.make_chat_request(headers, test_payload)

        # Should be blocked - API shouldn't allow requests to itself
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        print(f"✅ Direct API access blocked with status {response.status_code}")


class TestOriginValidationEdgeCases:
    """Test edge cases for origin validation"""

    def test_case_sensitivity(self, test_payload: dict[str, Any]) -> None:
        """Test that origin validation is case-sensitive"""
        headers = {
            "Origin": "https://storage.googleapis.com",
            # Different case - should be blocked
            "Referer": "https://STORAGE.GOOGLEAPIS.COM/whatsupdoc-widget-static/demo.html",
            "X-Widget-Origin": "https://STORAGE.GOOGLEAPIS.COM/whatsupdoc-widget-static",
            "X-Widget-URL": "https://STORAGE.GOOGLEAPIS.COM/whatsupdoc-widget-static/demo.html",
        }

        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            headers=headers,
            json={
                "query": "test case sensitivity",
                "conversation_id": "test-case-sensitivity",
                "max_results": 1,
                "confidence_threshold": 0.5,
            },
            timeout=10,
        )

        # Should be blocked due to case mismatch
        assert (
            response.status_code >= 400
        ), f"Expected error for case mismatch, got {response.status_code}"
        print(f"✅ Case-sensitive validation working, blocked with status {response.status_code}")

    def test_subdomain_variations(self, test_payload: dict[str, Any]) -> None:
        """Test that subdomain variations are blocked"""
        headers = {
            "Origin": "https://evil.storage.googleapis.com",
            "Referer": "https://evil.storage.googleapis.com/whatsupdoc-widget-static/demo.html",
            "X-Widget-Origin": "https://evil.storage.googleapis.com/whatsupdoc-widget-static",
            "X-Widget-URL": "https://evil.storage.googleapis.com/whatsupdoc-widget-static/demo.html",
        }

        response = requests.post(
            f"{API_BASE_URL}/api/chat", headers=headers, json=test_payload, timeout=10
        )

        # Should be blocked
        assert (
            response.status_code >= 400
        ), f"Expected error for subdomain variation, got {response.status_code}"
        print(f"✅ Subdomain variation blocked with status {response.status_code}")


@pytest.fixture
def test_payload() -> dict[str, Any]:
    """Pytest fixture for test payload"""
    import time

    return {
        "query": "test cors validation",
        "conversation_id": f"test-cors-{int(time.time() * 1000)}",
        "max_results": 1,
        "confidence_threshold": 0.5,
    }


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])
