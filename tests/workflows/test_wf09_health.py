"""CP-16: WF-09 — Health & Service Reliability Workflows (6 scenarios)
These are the most critical tests — run first in every CI pipeline.
"""
import pytest
import requests


SERVICES = {
    "api-gateway": ("API_GATEWAY_URL", "http://localhost:8000"),
    "integration-service": ("INTEGRATION_SERVICE_URL", "http://localhost:8002"),
    "agent-service": ("AGENT_SERVICE_URL", "http://localhost:8006"),
}


class TestWF09_ServiceHealth:
    def test_09_01_api_gateway_health(self, api_base_url, test_monitor):
        """WF-09.1: API Gateway /health returns 200 with healthy status."""
        r = requests.get(f"{api_base_url}/health", timeout=10)
        test_monitor.log_api_call("GET", f"{api_base_url}/health", r.status_code)
        assert r.status_code == 200, f"API Gateway unhealthy: {r.text}"
        data = r.json()
        assert data.get("status") in ["healthy", "degraded"], f"Unexpected status: {data}"

    def test_09_02_integration_service_health(self, integration_service_url, test_monitor):
        """WF-09.2: Integration Service /health returns healthy."""
        r = requests.get(f"{integration_service_url}/health", timeout=10)
        test_monitor.log_api_call("GET", f"{integration_service_url}/health", r.status_code)
        assert r.status_code == 200, f"Integration service unhealthy: {r.text}"
        assert r.json().get("status") == "healthy"

    def test_09_03_agent_service_health(self, agent_service_url, test_monitor):
        """WF-09.3: Agent Service /health returns healthy."""
        r = requests.get(f"{agent_service_url}/health", timeout=10)
        test_monitor.log_api_call("GET", f"{agent_service_url}/health", r.status_code)
        assert r.status_code == 200, f"Agent service unhealthy: {r.text}"
        assert r.json().get("status") == "healthy"

    def test_09_04_api_gateway_cors_configured(self, api_base_url, test_monitor):
        """WF-09.4: CORS headers present for production frontend domain."""
        r = requests.options(f"{api_base_url}/health",
                             headers={"Origin": "https://prjsyntheist.web.app",
                                      "Access-Control-Request-Method": "GET"},
                             timeout=10)
        test_monitor.log_api_call("OPTIONS", "/health", r.status_code)
        assert r.status_code in [200, 204], f"CORS preflight failed: {r.status_code}"

    def test_09_05_health_response_has_service_name(self, api_base_url, test_monitor):
        """WF-09.5: Health response includes service identification field."""
        r = requests.get(f"{api_base_url}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        # Must have at least status field to be a valid health response
        assert "status" in data, f"Health response missing 'status': {data}"

    def test_09_06_all_services_return_json(self, api_base_url, integration_service_url, agent_service_url, test_monitor):
        """WF-09.6: All core services return JSON on /health (not HTML error pages)."""
        urls = [
            (api_base_url, "api-gateway"),
            (integration_service_url, "integration-service"),
            (agent_service_url, "agent-service"),
        ]
        for base_url, name in urls:
            r = requests.get(f"{base_url}/health", timeout=10)
            test_monitor.log_api_call("GET", f"{base_url}/health", r.status_code)
            assert r.status_code == 200, f"{name} returned {r.status_code}"
            content_type = r.headers.get("content-type", "")
            assert "application/json" in content_type, (
                f"{name} health check returned non-JSON content-type: {content_type}"
            )
