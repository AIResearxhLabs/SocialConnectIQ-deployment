"""
Dashboard Backend — FastAPI application entry point.

Startup:
  1. Creates SQLite tables (idempotent)
  2. Starts background health poller loop
  3. Registers all route modules

Endpoints:
  GET  /health                     — dashboard backend health
  GET  /api/health/services        — production services health
  GET  /api/health/ci-status       — CI status across all repos
  GET  /api/health/pending-gates   — GitHub Actions runs awaiting approval
  GET  /api/deployments            — list deployment history
  POST /api/deployments/trigger    — trigger a deployment workflow
  POST /api/deployments/{id}/approve  — approve / reject human gate
  DELETE /api/deployments/{id}     — cancel deployment
  GET  /api/tests                  — list test runs
  POST /api/tests/trigger          — trigger a test run
  GET  /api/tests/{id}             — test run detail
  WS   /ws/live                    — real-time health + gate updates
"""

import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_all_tables
from app.health_poller import background_poll_loop
from app.routes.deployments import router as deployments_router
from app.routes.health import router as health_router
from app.routes.tests import router as tests_router
from app.routes.websocket import router as ws_router

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"dashboard-backend","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
).split(",")

app = FastAPI(
    title="SocialConnectIQ DevOps Dashboard",
    description="Deployment orchestration, test execution, and monitoring dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(deployments_router)
app.include_router(tests_router)
app.include_router(ws_router)


@app.on_event("startup")
async def _startup() -> None:
    """Initialise DB tables and start background health poller."""
    create_all_tables()
    logger.info("Database tables created/verified")
    asyncio.create_task(background_poll_loop())
    logger.info("Dashboard backend started")


@app.get("/health")
async def root_health():
    """Root health endpoint (also used by Docker health-check)."""
    return {"status": "healthy", "service": "dashboard-backend"}
