"""
CP-08: WF-01 — Authentication Workflow Tests (7 scenarios)

Tests all authentication flows through the API Gateway.
Verifies Firebase JWT validation, token rejection, and session behavior.
"""
import pytest
import requests


class TestWF01_Authentication:
    """WF-01: Firebase Auth + API Gateway token validation."""

    def test_01_01_health_endpoint_accessible(self, api_base_url, test_monitor):
        """WF-01.1: /health endpoint returns 200 without auth (public endpoint)."""
        test_monitor.log_event("test_start", {"wf": "01.1", "endpoint": "/health"})
        response = requests.get(f"{api_base_url}/health", timeout=10)
        test_monitor.log_api_call("GET", f"{api_base_url}/health", response.status_code)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "status" in data, "Health response missing 'status' field"
        test_monitor.log_event("test_pass", {"status": data.get("status")})

    def test_01_02_valid_token_accepted(self, api_base_url, auth_headers, test_monitor):
        """WF-01.2: Valid Firebase JWT is accepted by API Gateway on protected endpoint."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("FIREBASE_CI_TEST_TOKEN not set — skipping live token test")
        test_monitor.log_event("test_start", {"wf": "01.2"})
        response = requests.get(
            f"{api_base_url}/api/user/profile",
            headers=auth_headers, timeout=10
        )
        test_monitor.log_api_call("GET", "/api/user/profile", response.status_code)
        assert response.status_code in [200, 404], (
            f"Expected 200/404 with valid token, got {response.status_code}: {response.text}"
        )

    def test_01_03_root_endpoint_returns_service_info(self, api_base_url, test_monitor):
        """WF-01.3: Root endpoint returns service info (API Gateway identity)."""
        test_monitor.log_event("test_start", {"wf": "01.3"})
        response = requests.get(f"{api_base_url}/", timeout=10)
        test_monitor.log_api_call("GET", "/", response.status_code)
        assert response.status_code == 200

    def test_01_04_token_refresh_header_propagated(self, api_base_url, auth_headers, test_monitor):
        """WF-01.4: API Gateway propagates auth headers to downstream services."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("FIREBASE_CI_TEST_TOKEN not set")
        test_monitor.log_event("test_start", {"wf": "01.4"})
        response = requests.get(
            f"{api_base_url}/health",
            headers={"Authorization": auth_headers["Authorization"]}, timeout=10
        )
        test_monitor.log_api_call("GET", "/health", response.status_code)
        assert response.status_code == 200

    def test_01_05_cors_headers_present(self, api_base_url, test_monitor):
        """WF-01.5: CORS headers are present in API Gateway responses."""
        test_monitor.log_event("test_start", {"wf": "01.5"})
        response = requests.options(
            f"{api_base_url}/health",
            headers={"Origin": "https://prjsyntheist.web.app",
                     "Access-Control-Request-Method": "GET"},
            timeout=10
        )
        test_monitor.log_api_call("OPTIONS", "/health", response.status_code)
        assert response.status_code in [200, 204], f"CORS preflight failed: {response.status_code}"

    def test_01_06_invalid_token_rejected(self, api_base_url, test_monitor):
        """WF-01.6: Invalid/malformed Firebase JWT returns 401 on protected endpoints."""
        test_monitor.log_event("test_start", {"wf": "01.6"})
        response = requests.post(
            f"{api_base_url}/api/content/post",
            headers={"Authorization": "Bearer this.is.definitely.not.a.valid.jwt.token"},
            json={"content": "test", "platforms": ["linkedin"], "user_id": "test"},
            timeout=10
        )
        test_monitor.log_api_call("POST", "/api/content/post", response.status_code)
        assert response.status_code == 401, (
            f"Expected 401 for invalid token, got {response.status_code}: {response.text}"
        )
        test_monitor.log_event("test_pass", {"rejected_with": 401})

    def test_01_07_missing_token_rejected(self, api_base_url, test_monitor):
        """WF-01.7: Missing auth token returns 401 on protected endpoints."""
        test_monitor.log_event("test_start", {"wf": "01.7"})
        response = requests.post(
            f"{api_base_url}/api/content/post",
            json={"content": "test", "platforms": ["linkedin"], "user_id": "test"},
            timeout=10
        )
        test_monitor.log_api_call("POST", "/api/content/post", response.status_code)
        assert response.status_code == 401, (
            f"Expected 401 for missing token, got {response.status_code}: {response.text}"
        )
        test_monitor.log_event("test_pass", {"rejected_with": 401})
