"""
WebSocket Route — real-time deployment and health updates.

ws://host/ws/live   → streams combined health + active deployment status every 5s
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import github_client as gh
from app.health_poller import get_cached_health

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

# Active WebSocket connections
_connections: List[WebSocket] = []


async def broadcast(message: dict) -> None:
    """Send a JSON message to all connected clients."""
    dead: List[WebSocket] = []
    for ws in _connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _connections:
            _connections.remove(ws)


@router.websocket("/ws/live")
async def live_feed(websocket: WebSocket) -> None:
    """
    Live feed WebSocket.

    Client connects once and receives periodic status updates:
      - Service health snapshots
      - Active / recent GitHub Actions run statuses
      - CI status for all three repos
    """
    await websocket.accept()
    _connections.append(websocket)
    logger.info("WebSocket client connected (total=%d)", len(_connections))

    try:
        while True:
            payload = await _build_live_payload()
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.warning("WebSocket error: %s", exc)
    finally:
        if websocket in _connections:
            _connections.remove(websocket)


async def _build_live_payload() -> dict:
    """Build the data payload sent to all WebSocket clients."""
    health = get_cached_health()

    # Pending (waiting) GitHub runs — human gates
    pending_runs = []
    try:
        runs = await asyncio.to_thread(gh.get_pending_deployments)
        pending_runs = [
            {
                "id": str(r["id"]),
                "name": r.get("name", ""),
                "html_url": r.get("html_url", ""),
                "status": r.get("status", ""),
                "created_at": r.get("created_at", ""),
            }
            for r in runs[:5]
        ]
    except Exception:
        pass

    # CI status for all three repos
    ci_statuses = {}
    for repo in ["SocialConnectIQ", "SocialConnectIQ-frontend", "MCPSocialTools"]:
        try:
            ci_statuses[repo] = await asyncio.to_thread(gh.get_ci_status, repo)
        except Exception:
            ci_statuses[repo] = "unknown"

    return {
        "type": "live_update",
        "timestamp": datetime.utcnow().isoformat(),
        "service_health": health,
        "pending_runs": pending_runs,
        "ci_statuses": ci_statuses,
    }
