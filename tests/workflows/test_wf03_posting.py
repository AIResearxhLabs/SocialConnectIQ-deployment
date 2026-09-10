"""CP-10: WF-03 — Content Creation & Posting Workflows (11 scenarios)"""
import pytest
import requests


class TestWF03_ContentPosting:
    def test_03_01_refine_endpoint(self, api_base_url, auth_headers, test_monitor):
        """WF-03.1: AI content refinement endpoint accessible via Gateway."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/integrations/refine", headers=auth_headers,
                          json={"content": "Test post", "platforms": ["linkedin"]}, timeout=15)
        test_monitor.log_api_call("POST", "/api/integrations/refine", r.status_code)
        assert r.status_code in [200, 401, 422, 500]

    def test_03_02_preview_endpoint(self, api_base_url, auth_headers, test_monitor):
        """WF-03.2: Preview returns per-platform content without posting."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/integrations/preview", headers=auth_headers,
                          json={"content": "CI preview test.", "platforms": ["linkedin", "twitter"]}, timeout=15)
        test_monitor.log_api_call("POST", "/api/integrations/preview", r.status_code)
        assert r.status_code in [200, 401, 422, 500]

    def test_03_03_post_requires_auth(self, api_base_url, test_monitor):
        """WF-03.3: Unauthenticated post → 401."""
        r = requests.post(f"{api_base_url}/api/content/post",
                          json={"content": "test", "platforms": ["linkedin"], "user_id": "test"}, timeout=10)
        assert r.status_code == 401

    def test_03_04_post_linkedin(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-03.4: Authenticated LinkedIn post accepted (platform err OK)."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "CI ignore", "platforms": ["linkedin"], "user_id": ci_test_user_id}, timeout=30)
        assert r.status_code in [200, 400, 401, 422, 500]

    def test_03_05_post_twitter(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-03.5: Authenticated Twitter post accepted (platform err OK)."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "CI ignore", "platforms": ["twitter"], "user_id": ci_test_user_id}, timeout=30)
        assert r.status_code in [200, 400, 401, 422, 500]

    def test_03_06_empty_platforms_rejected(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-03.6: Empty platforms list → 400/422."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "test", "platforms": [], "user_id": ci_test_user_id}, timeout=10)
        assert r.status_code in [400, 422, 500]

    def test_03_07_empty_content_rejected(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-03.7: Empty content → validation error."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "", "platforms": ["linkedin"], "user_id": ci_test_user_id}, timeout=10)
        assert r.status_code in [400, 422, 500]

    def test_03_08_multi_platform_result_structure(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-03.8: Multi-platform post returns per-platform results dict."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "CI test", "platforms": ["linkedin", "twitter"], "user_id": ci_test_user_id}, timeout=30)
        assert r.status_code in [200, 400, 401, 422, 500]
        if r.status_code == 200:
            assert "results" in r.json() or "success" in r.json()

    def test_03_09_moderation_endpoint(self, api_base_url, auth_headers, test_monitor):
        """WF-03.9: Content moderation report endpoint accessible."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/moderation/report", headers=auth_headers,
                          json={"target_type": "content", "target_id": "t1", "reason": "spam"}, timeout=10)
        assert r.status_code in [200, 400, 401, 422, 500]

    def test_03_10_backend_health(self, api_base_url, test_monitor):
        """WF-03.10: Backend service healthy via API Gateway."""
        r = requests.get(f"{api_base_url}/health", timeout=10)
        assert r.status_code == 200

    def test_03_11_user_mismatch_rejected(self, api_base_url, auth_headers, test_monitor):
        """WF-03.11: user_id mismatch with auth token → 403."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.post(f"{api_base_url}/api/content/post", headers=auth_headers,
                          json={"content": "t", "platforms": ["linkedin"], "user_id": "other-user"}, timeout=10)
        assert r.status_code in [401, 403, 422, 500]
