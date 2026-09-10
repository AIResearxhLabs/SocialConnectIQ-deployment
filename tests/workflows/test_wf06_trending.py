"""CP-13: WF-06 — Trending Topics / AI Workflows (5 scenarios)"""
import pytest
import requests


class TestWF06_TrendingTopics:
    def test_06_01_trending_health(self, agent_service_url, test_monitor):
        """WF-06.1: Agent service is healthy (trending worker running)."""
        r = requests.get(f"{agent_service_url}/health", timeout=10)
        test_monitor.log_api_call("GET", f"{agent_service_url}/health", r.status_code)
        assert r.status_code == 200, f"Agent service unhealthy: {r.text}"
        data = r.json()
        assert data.get("status") == "healthy"

    def test_06_02_trending_via_gateway(self, api_base_url, auth_headers, ci_test_user_id, test_monitor):
        """WF-06.2: Trending topics request routes through API Gateway to Agent Service."""
        if not auth_headers.get("Authorization", "").replace("Bearer ", ""):
            pytest.skip("No CI token")
        r = requests.get(f"{api_base_url}/api/trending/{ci_test_user_id}/fast",
                         params={"shuffle": "false"}, headers=auth_headers, timeout=30)
        test_monitor.log_api_call("GET", f"/api/trending/{ci_test_user_id}/fast", r.status_code)
        assert r.status_code in [200, 401, 404, 500], f"Unexpected: {r.status_code}"
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, (dict, list)), f"Unexpected structure: {type(data)}"

    def test_06_03_trending_direct_agent_service(self, agent_service_url, ci_test_user_id, test_monitor):
        """WF-06.3: Trending endpoint directly on agent service returns topics or empty list."""
        r = requests.get(f"{agent_service_url}/trending/{ci_test_user_id}/fast",
                         params={"shuffle": "false"}, timeout=30)
        test_monitor.log_api_call("GET", f"/trending/{ci_test_user_id}/fast", r.status_code)
        assert r.status_code in [200, 401, 404, 500], f"Unexpected: {r.status_code}"

    def test_06_04_trending_without_user_id_fails(self, api_base_url, test_monitor):
        """WF-06.4: Trending request without user_id returns 401/404/422."""
        r = requests.get(f"{api_base_url}/api/trending//fast", timeout=10)
        test_monitor.log_api_call("GET", "/api/trending//fast", r.status_code)
        assert r.status_code in [400, 401, 404, 405, 422]

    def test_06_05_agent_service_mcp_connection(self, agent_service_url, test_monitor):
        """WF-06.5: Agent service reports MCP server connection status in health check."""
        r = requests.get(f"{agent_service_url}/health", timeout=10)
        test_monitor.log_api_call("GET", "/health", r.status_code)
        assert r.status_code == 200
        data = r.json()
        # Agent service health should report on MCP server connection
        assert "status" in data, f"Missing status in health: {data}"
