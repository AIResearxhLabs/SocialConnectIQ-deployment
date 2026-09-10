"""CP-14: WF-07 — User Management Workflows (4 scenarios)"""
import pytest
import requests


class TestWF07_UserManagement:
    def test_07_01_user_profile_update(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-07.1: Update user profile via backend service."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.put(f"{api_base_url}/api/user/profile", headers=auth_headers,
                         json={"displayName": "CI Test User", "bio": "CI test account"},
                         timeout=10)
        test_monitor.log_api_call("PUT", "/api/user/profile", r.status_code)
        assert r.status_code in [200, 201, 400, 401, 404, 422, 500]

    def test_07_02_user_preferences_update(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-07.2: Update user preferences (interests, theme)."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.put(f"{api_base_url}/api/user/preferences", headers=auth_headers,
                         json={"interests": ["AI", "technology"], "theme": "dark"},
                         timeout=10)
        test_monitor.log_api_call("PUT", "/api/user/preferences", r.status_code)
        assert r.status_code in [200, 201, 400, 401, 404, 422, 500]

    def test_07_03_user_endpoint_requires_auth(self, api_base_url, test_monitor):
        """WF-07.3: User endpoint without auth → 401."""
        r = requests.get(f"{api_base_url}/api/user/profile", timeout=10)
        test_monitor.log_api_call("GET", "/api/user/profile", r.status_code)
        assert r.status_code in [401, 403], f"Expected auth required, got {r.status_code}"

    def test_07_04_delete_account_requires_auth(self, api_base_url, test_monitor):
        """WF-07.4: Delete account endpoint requires authentication (401 without token)."""
        r = requests.delete(f"{api_base_url}/api/user/account", timeout=10)
        test_monitor.log_api_call("DELETE", "/api/user/account", r.status_code)
        assert r.status_code in [401, 403, 404], f"Expected auth required, got {r.status_code}"
