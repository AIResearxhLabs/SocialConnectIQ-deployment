"""
Dashboard Data Models (SQLAlchemy + Pydantic)

Defines the SQLite schema for deployment history, test runs, and log entries.
All tables are created automatically on first startup.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


# ─── SQLAlchemy ORM Models ────────────────────────────────────────────────────


class DeploymentRecord(Base):
    """Persisted deployment record."""

    __tablename__ = "deployments"

    id = Column(String, primary_key=True)
    environment = Column(String, nullable=False)
    version = Column(String)
    services = Column(JSON)
    status = Column(String, default="pending")  # pending | running | success | failed | rolled_back

    github_run_id = Column(String)
    github_run_url = Column(String)
    workflow_name = Column(String)

    triggered_by = Column(String)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Human gate tracking
    requires_approval = Column(Boolean, default=False)
    approval_gate = Column(String)            # which gate is waiting
    approved_by = Column(String)
    approved_at = Column(DateTime)

    # Phase results stored as JSON blobs
    build_status = Column(JSON)
    deploy_status = Column(JSON)
    validation_status = Column(JSON)

    # Raw log tail
    log_tail = Column(Text)
    error_message = Column(Text)


class TestRunRecord(Base):
    """Persisted test run record."""

    __tablename__ = "test_runs"

    id = Column(String, primary_key=True)
    run_type = Column(String)       # ci | regression | smoke
    environment = Column(String)
    status = Column(String, default="pending")  # pending | running | passed | failed

    github_run_id = Column(String)
    github_run_url = Column(String)

    triggered_by = Column(String)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    total_tests = Column(Integer)
    passed_tests = Column(Integer)
    failed_tests = Column(Integer)
    skipped_tests = Column(Integer)

    report_url = Column(String)    # Link to HTML artifact
    suite_results = Column(JSON)   # Per-suite breakdown


class LogEntry(Base):
    """Individual log line for a deployment or test run."""

    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)   # deployment or test run id
    run_type = Column(String)    # deployment | test
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String, default="INFO")
    step = Column(String)
    service = Column(String)
    message = Column(Text)


# ─── Pydantic Schemas (Request / Response) ────────────────────────────────────


class DeploymentTriggerRequest(BaseModel):
    """Body for POST /api/deployments/trigger"""

    environment: str = Field(..., pattern="^(staging|production)$")
    version: str
    initial_traffic_pct: str = Field("10", pattern="^(10|50|100)$")
    include_frontend: bool = True
    triggered_by: str = "dashboard"


class ApprovalRequest(BaseModel):
    """Body for POST /api/deployments/{id}/approve"""

    action: str = Field(..., pattern="^(approve|reject|rollback)$")
    approver: str
    reason: Optional[str] = None


class TestTriggerRequest(BaseModel):
    """Body for POST /api/tests/trigger"""

    run_type: str = Field(..., pattern="^(ci|regression|smoke)$")
    environment: str = Field("staging", pattern="^(local|staging|production)$")
    version: Optional[str] = None
    triggered_by: str = "dashboard"


class DeploymentResponse(BaseModel):
    """Serialized deployment record."""

    id: str
    environment: str
    version: Optional[str]
    status: str
    workflow_name: Optional[str]
    github_run_id: Optional[str]
    github_run_url: Optional[str]
    triggered_by: Optional[str]
    triggered_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    requires_approval: bool
    approval_gate: Optional[str]
    approved_by: Optional[str]
    build_status: Optional[Dict[str, Any]]
    deploy_status: Optional[Dict[str, Any]]
    validation_status: Optional[Dict[str, Any]]
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class TestRunResponse(BaseModel):
    """Serialized test run record."""

    id: str
    run_type: str
    environment: str
    status: str
    github_run_id: Optional[str]
    github_run_url: Optional[str]
    triggered_by: Optional[str]
    triggered_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_tests: Optional[int]
    passed_tests: Optional[int]
    failed_tests: Optional[int]
    skipped_tests: Optional[int]
    report_url: Optional[str]
    suite_results: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}


class ServiceHealthResponse(BaseModel):
    """Real-time health status of a single service."""

    name: str
    url: str
    status: str   # healthy | unhealthy | unknown
    status_code: Optional[int]
    response_time_ms: Optional[float]
    checked_at: datetime


class DashboardSummaryResponse(BaseModel):
    """Summary card data for the Overview page."""

    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    last_deployment: Optional[DeploymentResponse]
    total_test_runs: int
    last_test_run: Optional[TestRunResponse]
    service_health: List[ServiceHealthResponse]
