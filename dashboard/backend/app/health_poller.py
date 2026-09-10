"""
Service Health Poller

Polls /health endpoints for all configured services and caches results
in memory. The WebSocket broadcaster reads from this cache to push
real-time updates to the dashboard.
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

# Service definitions: name → URL (override via env vars)
_DEFAULT_SERVICES: List[Dict] = [
    {"name": "api-gateway",         "url": os.getenv("PROD_API_GATEWAY_URL", "https://api-gateway-lk7iu4bo5q-uc.a.run.app")},
    {"name": "integration-service", "url": os.getenv("PROD_INTEGRATION_URL", "https://integration-service-lk7iu4bo5q-uc.a.run.app")},
    {"name": "agent-service",       "url": os.getenv("PROD_AGENT_URL",       "https://agent-service-lk7iu4bo5q-uc.a.run.app")},
    {"name": "backend-service",     "url": os.getenv("PROD_BACKEND_URL",     "https://backend-service-lk7iu4bo5q-uc.a.run.app")},
]

POLL_INTERVAL_SECONDS = int(os.getenv("HEALTH_POLL_INTERVAL", "30"))

# In-memory cache: name → health dict
_health_cache: Dict[str, Dict] = {}


def get_cached_health() -> List[Dict]:
    """Return the latest cached health results for all services."""
    return list(_health_cache.values())


async def poll_once() -> List[Dict]:
    """
    Poll all service /health endpoints once.
    Updates the in-memory cache and returns results.
    """
    results = []
    async with httpx.AsyncClient(timeout=8.0) as client:
        tasks = [_check_service(client, svc) for svc in _DEFAULT_SERVICES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    healthy_results = []
    for svc, result in zip(_DEFAULT_SERVICES, results):
        if isinstance(result, Exception):
            entry = {
                "name": svc["name"],
                "url": svc["url"],
                "status": "unknown",
                "status_code": None,
                "response_time_ms": None,
                "checked_at": datetime.utcnow().isoformat(),
            }
        else:
            entry = result
        _health_cache[svc["name"]] = entry
        healthy_results.append(entry)

    return healthy_results


async def _check_service(client: httpx.AsyncClient, svc: Dict) -> Dict:
    """Check a single service health endpoint."""
    url = f"{svc['url'].rstrip('/')}/health"
    start = time.monotonic()
    try:
        resp = await client.get(url)
        elapsed_ms = (time.monotonic() - start) * 1000
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass

        status = "healthy" if resp.status_code == 200 and body.get("status") in ("healthy", "ok", None) else "unhealthy"
        return {
            "name": svc["name"],
            "url": svc["url"],
            "status": status,
            "status_code": resp.status_code,
            "response_time_ms": round(elapsed_ms, 1),
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        return {
            "name": svc["name"],
            "url": svc["url"],
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": None,
            "error": str(exc),
            "checked_at": datetime.utcnow().isoformat(),
        }


async def background_poll_loop() -> None:
    """
    Long-running background task that continuously polls service health.
    Start via asyncio.create_task() during FastAPI startup.
    """
    logger.info("Health poller started (interval=%ds)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            await poll_once()
        except Exception as exc:
            logger.error("Health poll error: %s", exc)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
