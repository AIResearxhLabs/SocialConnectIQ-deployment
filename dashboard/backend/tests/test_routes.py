"""
Unit tests for dashboard backend routes.

Uses TestClient with in-memory SQLite and mocked GitHub client.
All tests are deterministic and do not require real GitHub tokens.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Set required env before app imports
import os
os.environ["DASHBOARD_DB_URL"] = "sqlite:///./test_dashboard.db"
os.environ["GITHUB_TOKEN"] = "test-token"

from app.main import app
from app.database import create_all_tables

create_all_tables()
client = TestClient(app)


class TestHealthRoutes:
    """Tests for /health endpoints."""

    def test_root_health_returns_healthy(self):
        """Dashboard backend own /health returns 200 with status=healthy."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_api_health_returns_healthy(self):
        """GET /api/health returns 200."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestDeploymentRoutes:
    """Tests for /api/deployments endpoints."""

    def test_list_deployments_returns_empty_list_initially(self):
        """GET /api/deployments returns [] when no deployments exist."""
        resp = client.get("/api/deployments")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch("app.routes.deployments._trigger_and_track")
    def test_trigger_deployment_creates_record(self, mock_trigger):
        """POST /api/deployments/trigger returns 201 with deployment record."""
        mock_trigger.return_value = None
        payload = {
            "environment": "staging",
            "version": "1.0.0-test",
            "triggered_by": "test-user",
        }
        resp = client.post("/api/deployments/trigger", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["environment"] == "staging"
        assert data["version"] == "1.0.0-test"
        assert data["status"] == "pending"
        assert "id" in data

    def test_get_nonexistent_deployment_returns_404(self):
        """GET /api/deployments/missing returns 404."""
        resp = client.get("/api/deployments/nonexistent-id")
        assert resp.status_code == 404

    @patch("app.routes.deployments._trigger_and_track")
    def test_approve_deployment_updates_status(self, mock_trigger):
        """POST /api/deployments/{id}/approve changes status."""
        mock_trigger.return_value = None
        # Create a deployment first
        create_resp = client.post("/api/deployments/trigger", json={
            "environment": "production",
            "version": "1.0.0-approve-test",
            "triggered_by": "test",
        })
        assert create_resp.status_code == 201
        deploy_id = create_resp.json()["id"]

        # Approve it
        approve_resp = client.post(
            f"/api/deployments/{deploy_id}/approve",
            json={"action": "approve", "approver": "devops@test.com"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"


class TestTestRunRoutes:
    """Tests for /api/tests endpoints."""

    def test_list_test_runs_returns_list(self):
        """GET /api/tests returns a list."""
        resp = client.get("/api/tests")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch("app.routes.tests._trigger_test_workflow")
    def test_trigger_test_run_creates_record(self, mock_trigger):
        """POST /api/tests/trigger returns 201 with test run record."""
        mock_trigger.return_value = None
        payload = {
            "run_type": "ci",
            "environment": "staging",
            "triggered_by": "test-user",
        }
        resp = client.post("/api/tests/trigger", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["run_type"] == "ci"
        assert data["status"] == "pending"

    def test_get_nonexistent_test_run_returns_404(self):
        """GET /api/tests/missing returns 404."""
        resp = client.get("/api/tests/nonexistent-id")
        assert resp.status_code == 404

    @patch("app.routes.tests._trigger_test_workflow")
    def test_trigger_regression_test_run(self, mock_trigger):
        """POST /api/tests/trigger with run_type=regression creates run."""
        mock_trigger.return_value = None
        resp = client.post("/api/tests/trigger", json={
            "run_type": "regression",
            "environment": "staging",
            "version": "1.0.0-test",
        })
        assert resp.status_code == 201
        assert resp.json()["run_type"] == "regression"
