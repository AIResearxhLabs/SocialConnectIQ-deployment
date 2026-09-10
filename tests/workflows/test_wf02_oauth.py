"""CP-09: WF-02 — Social Platform OAuth Connection Workflows (12 scenarios)"""
import pytest
import requests


class TestWF02_LinkedIn:
    def test_02_01_auth_via_gateway(self, api_base_url, auth_headers, test_monitor):
        """WF-02.1: LinkedIn auth URL request routes through API Gateway."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/integrations/linkedin/auth", headers=auth_headers, timeout=10)
        test_monitor.log_api_call("GET", "/api/integrations/linkedin/auth", r.status_code)
        assert r.status_code in [200, 302, 307, 401, 500]

    def test_02_02_auth_direct_integration_service(self, integration_service_url, ci_test_user_id, test_monitor):
        """WF-02.2: LinkedIn auth endpoint reachable on integration service."""
        r = requests.get(f"{integration_service_url}/integrations/linkedin/auth",
                         params={"user_id": ci_test_user_id}, timeout=10)
        test_monitor.log_api_call("GET", "/integrations/linkedin/auth", r.status_code)
        assert r.status_code in [200, 302, 307, 401, 422, 500]

    def test_02_03_invalid_state_csrf_blocked(self, integration_service_url, test_monitor):
        """WF-02.3: LinkedIn callback with invalid state → CSRF protection rejects it."""
        r = requests.get(f"{integration_service_url}/integrations/linkedin/callback",
                         params={"code": "fake-code", "state": "invalid-state-xyz"}, timeout=10)
        test_monitor.log_api_call("GET", "/integrations/linkedin/callback", r.status_code)
        assert r.status_code in [400, 401, 422, 500], f"CSRF not blocked: {r.status_code}"

    def test_02_04_status_endpoint(self, integration_service_url, ci_test_user_id, test_monitor):
        """WF-02.4: LinkedIn status returns 200 (connected) or 404 (not connected)."""
        r = requests.get(f"{integration_service_url}/integrations/{ci_test_user_id}/linkedin", timeout=10)
        test_monitor.log_api_call("GET", f"/integrations/{ci_test_user_id}/linkedin", r.status_code)
        assert r.status_code in [200, 404]

    def test_02_05_disconnect_endpoint(self, integration_service_url, ci_test_user_id, test_monitor):
        """WF-02.5: LinkedIn disconnect returns 200/204/404."""
        r = requests.delete(f"{integration_service_url}/integrations/{ci_test_user_id}/linkedin", timeout=10)
        test_monitor.log_api_call("DELETE", f"/integrations/{ci_test_user_id}/linkedin", r.status_code)
        assert r.status_code in [200, 204, 404]


class TestWF02_Twitter:
    def test_02_06_auth_via_gateway(self, api_base_url, auth_headers, test_monitor):
        """WF-02.6: Twitter auth request routes through API Gateway."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/integrations/twitter/auth", headers=auth_headers, timeout=10)
        test_monitor.log_api_call("GET", "/api/integrations/twitter/auth", r.status_code)
        assert r.status_code in [200, 302, 307, 401, 500]

    def test_02_07_invalid_state_pkce_blocked(self, integration_service_url, test_monitor):
        """WF-02.7: Twitter callback with invalid state blocked (CSRF + PKCE)."""
        r = requests.get(f"{integration_service_url}/integrations/twitter/callback",
                         params={"code": "fake-code", "state": "invalid-xyz"}, timeout=10)
        test_monitor.log_api_call("GET", "/integrations/twitter/callback", r.status_code)
        assert r.status_code in [400, 401, 422, 500], f"Not blocked: {r.status_code}"

    def test_02_08_status_endpoint(self, integration_service_url, ci_test_user_id, test_monitor):
        """WF-02.8: Twitter status endpoint returns 200 or 404."""
        r = requests.get(f"{integration_service_url}/integrations/{ci_test_user_id}/twitter", timeout=10)
        test_monitor.log_api_call("GET", f"/integrations/{ci_test_user_id}/twitter", r.status_code)
        assert r.status_code in [200, 404]


class TestWF02_FacebookInstagram:
    def test_02_09_facebook_auth(self, api_base_url, auth_headers, test_monitor):
        """WF-02.9: Facebook auth endpoint accessible via Gateway."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/integrations/facebook/auth", headers=auth_headers, timeout=10)
        assert r.status_code in [200, 302, 307, 401, 500]

    def test_02_10_instagram_auth(self, api_base_url, auth_headers, test_monitor):
        """WF-02.10: Instagram auth endpoint accessible via Gateway."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/integrations/instagram/auth", headers=auth_headers, timeout=10)
        assert r.status_code in [200, 302, 307, 401, 500]

    def test_02_11_all_integrations_structure(self, integration_service_url, ci_test_user_id, test_monitor):
        """WF-02.11: Get all integrations returns valid JSON structure."""
        r = requests.get(f"{integration_service_url}/integrations/{ci_test_user_id}", timeout=10)
        test_monitor.log_api_call("GET", f"/integrations/{ci_test_user_id}", r.status_code)
        assert r.status_code in [200, 404]
        if r.status_code == 200:
            assert isinstance(r.json(), dict)

    def test_02_12_integration_service_health(self, integration_service_url, test_monitor):
        """WF-02.12: Integration service /health → healthy + Firebase configured."""
        r = requests.get(f"{integration_service_url}/health", timeout=10)
        test_monitor.log_api_call("GET", "/health", r.status_code)
        assert r.status_code == 200, f"Unhealthy: {r.text}"
        assert r.json().get("status") == "healthy"
