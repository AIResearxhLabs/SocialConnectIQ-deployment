"""
Health Routes

GET /api/health                — dashboard backend own health
GET /api/health/services       — live poll of all production services
GET /api/health/ci-status      — CI pipeline status across all repos
GET /api/health/pending-gates  — GitHub Actions runs waiting for human approval
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter

from app import github_client as gh
from app.health_poller import get_cached_health, poll_once

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])

_REPOS = ["SocialConnectIQ", "SocialConnectIQ-frontend", "MCPSocialTools"]


@router.get("")
async def dashboard_health():
    """Dashboard backend health check."""
    return {"status": "healthy", "service": "dashboard-backend", "timestamp": datetime.utcnow().isoformat()}


@router.get("/services")
async def services_health():
    """Return current health state of all production services (from cache + fresh poll)."""
    results = await poll_once()
    return {"services": results, "polled_at": datetime.utcnow().isoformat()}


@router.get("/ci-status")
async def ci_status():
    """Return the latest CI pipeline conclusion for all three application repos."""
    statuses = {}
    for repo in _REPOS:
        try:
            statuses[repo] = await asyncio.to_thread(gh.get_ci_status, repo) or "unknown"
        except Exception as exc:
            logger.warning("CI status fetch failed for %s: %s", repo, exc)
            statuses[repo] = "error"
    return {"repos": statuses, "checked_at": datetime.utcnow().isoformat()}


@router.get("/pending-gates")
async def pending_gates():
    """Return GitHub Actions runs currently waiting for environment approval."""
    try:
        runs = await asyncio.to_thread(gh.get_pending_deployments)
        simplified = [
            {
                "id": str(r["id"]),
                "workflow": r.get("name", ""),
                "html_url": r.get("html_url", ""),
                "created_at": r.get("created_at", ""),
            }
            for r in runs
        ]
        return {"pending_runs": simplified, "count": len(simplified)}
    except Exception as exc:
        logger.error("Failed to fetch pending gates: %s", exc)
        return {"pending_runs": [], "count": 0, "error": str(exc)}
