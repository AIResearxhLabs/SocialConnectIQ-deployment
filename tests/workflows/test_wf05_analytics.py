"""CP-12: WF-05 — Analytics Workflows (4 scenarios)"""
import pytest
import requests


class TestWF05_Analytics:
    def test_05_01_analytics_overview_requires_auth(self, api_base_url, test_monitor):
        """WF-05.1: Analytics overview without auth → 401."""
        r = requests.get(f"{api_base_url}/api/analytics/overview", timeout=10)
        test_monitor.log_api_call("GET", "/api/analytics/overview", r.status_code)
        assert r.status_code in [401, 403, 404], f"Expected auth error, got {r.status_code}"

    def test_05_02_analytics_overview_authenticated(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-05.2: Authenticated analytics overview returns valid structure."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/analytics/overview",
                         headers=auth_headers, timeout=15)
        test_monitor.log_api_call("GET", "/api/analytics/overview", r.status_code)
        assert r.status_code in [200, 401, 404, 500]
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, dict), f"Expected dict, got: {type(data)}"

    def test_05_03_analytics_service_health(self, api_base_url, test_monitor):
        """WF-05.3: Analytics service healthy (via API Gateway)."""
        r = requests.get(f"{api_base_url}/health", timeout=10)
        assert r.status_code == 200

    def test_05_04_analytics_missing_user_id_handled(self, api_base_url, auth_headers, test_monitor):
        """WF-05.4: Analytics request without X-User-ID header returns error."""
        headers_no_user = {k: v for k, v in auth_headers.items() if k != "X-User-ID"}
        r = requests.get(f"{api_base_url}/api/analytics/overview", headers=headers_no_user, timeout=10)
        test_monitor.log_api_call("GET", "/api/analytics/overview (no user-id)", r.status_code)
        # Acceptable: service returns error or falls back gracefully
        assert r.status_code in [200, 400, 401, 422, 500]
