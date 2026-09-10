"""
GitHub Actions API Client

Wraps the GitHub REST API for:
  - Triggering workflow_dispatch events
  - Polling run status and jobs
  - Fetching run artifacts list
  - Approving pending environment gates

All methods are synchronous (called from background tasks).
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_ORG = os.getenv("GITHUB_ORG", "AIResearxhLabs")
DEPLOYMENT_REPO = os.getenv("DEPLOYMENT_REPO", "SocialConnectIQ-deployment")

WORKFLOW_RELEASE = "release-and-build.yml"
WORKFLOW_DEPLOY = "deploy-production.yml"
WORKFLOW_ROLLBACK = "rollback.yml"


def _headers() -> Dict[str, str]:
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable is not set.")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _repo_url(repo: str = DEPLOYMENT_REPO) -> str:
    return f"{GITHUB_API_BASE}/repos/{GITHUB_ORG}/{repo}"


def trigger_workflow(
    workflow_file: str,
    ref: str = "main",
    inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Trigger a workflow_dispatch event. Returns metadata dict."""
    url = f"{_repo_url()}/actions/workflows/{workflow_file}/dispatches"
    payload: Dict[str, Any] = {"ref": ref, "inputs": inputs or {}}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    logger.info("Triggered workflow %s on ref=%s", workflow_file, ref)
    return {"workflow": workflow_file, "ref": ref, "inputs": inputs or {}}


def get_latest_run(workflow_file: str, branch: str = "main") -> Optional[Dict[str, Any]]:
    """Get the most recent run for a workflow. Returns run object or None."""
    url = f"{_repo_url()}/actions/workflows/{workflow_file}/runs"
    resp = requests.get(url, headers=_headers(), params={"branch": branch, "per_page": 1}, timeout=15)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    return runs[0] if runs else None


def get_run(run_id: str) -> Dict[str, Any]:
    """Fetch a specific workflow run by ID."""
    url = f"{_repo_url()}/actions/runs/{run_id}"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_run_jobs(run_id: str) -> List[Dict[str, Any]]:
    """Fetch all jobs for a workflow run (for per-step progress)."""
    url = f"{_repo_url()}/actions/runs/{run_id}/jobs"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json().get("jobs", [])


def list_run_artifacts(run_id: str) -> List[Dict[str, Any]]:
    """List artifacts produced by a workflow run."""
    url = f"{_repo_url()}/actions/runs/{run_id}/artifacts"
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json().get("artifacts", [])


def cancel_run(run_id: str) -> bool:
    """Cancel a running workflow. Returns True on success."""
    url = f"{_repo_url()}/actions/runs/{run_id}/cancel"
    resp = requests.post(url, headers=_headers(), timeout=15)
    return resp.status_code in (202, 409)


def get_pending_deployments() -> List[Dict[str, Any]]:
    """Get workflow runs waiting for environment approval (status=waiting)."""
    url = f"{_repo_url()}/actions/runs"
    resp = requests.get(url, headers=_headers(), params={"status": "waiting", "per_page": 20}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("workflow_runs", [])


def get_ci_status(repo: str, branch: str = "main") -> Optional[str]:
    """Get the conclusion of the latest CI push run for a repo."""
    url = f"{_repo_url(repo)}/actions/runs"
    try:
        resp = requests.get(
            url, headers=_headers(),
            params={"branch": branch, "per_page": 1, "event": "push"}, timeout=10
        )
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        return runs[0].get("conclusion") if runs else None
    except Exception as exc:
        logger.warning("Failed to get CI status for %s: %s", repo, exc)
        return None
