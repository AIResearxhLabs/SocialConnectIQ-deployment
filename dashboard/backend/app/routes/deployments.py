"""
Deployment Routes — POST trigger, GET list/detail, POST approve, DELETE cancel.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import github_client as gh
from app.database import get_db
from app.models import (
    ApprovalRequest,
    DeploymentRecord,
    DeploymentResponse,
    DeploymentTriggerRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/deployments", tags=["deployments"])


def _row_to_response(row: DeploymentRecord) -> DeploymentResponse:
    return DeploymentResponse.model_validate(row)


@router.get("", response_model=List[DeploymentResponse])
def list_deployments(
    limit: int = 50,
    environment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return recent deployments, newest first."""
    query = db.query(DeploymentRecord).order_by(DeploymentRecord.triggered_at.desc())
    if environment:
        query = query.filter(DeploymentRecord.environment == environment)
    return [_row_to_response(r) for r in query.limit(limit).all()]


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    row = db.query(DeploymentRecord).filter(DeploymentRecord.id == deployment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return _row_to_response(row)


@router.post("/trigger", response_model=DeploymentResponse, status_code=201)
def trigger_deployment(
    body: DeploymentTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger a GitHub Actions deployment workflow."""
    deploy_id = str(uuid.uuid4())[:8]
    workflow = gh.WORKFLOW_RELEASE if body.environment == "staging" else gh.WORKFLOW_DEPLOY
    inputs = {
        "version": body.version,
        "include_frontend": str(body.include_frontend).lower(),
        "initial_traffic_pct": body.initial_traffic_pct,
    }
    row = DeploymentRecord(
        id=deploy_id,
        environment=body.environment,
        version=body.version,
        status="pending",
        workflow_name=workflow,
        triggered_by=body.triggered_by,
        triggered_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    background_tasks.add_task(_trigger_and_track, deploy_id, workflow, inputs)
    return _row_to_response(row)


@router.post("/{deployment_id}/approve", response_model=DeploymentResponse)
def approve_deployment(
    deployment_id: str,
    body: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve or reject a human gate for a deployment."""
    row = db.query(DeploymentRecord).filter(DeploymentRecord.id == deployment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if body.action == "approve" and row.github_run_id and row.approval_gate:
        try:
            gh.approve_pending_run(row.approval_gate, row.github_run_id, body.reason or "Approved via dashboard")
        except Exception as exc:
            logger.warning("GitHub approval call failed: %s", exc)

    row.approved_by = body.approver
    row.approved_at = datetime.utcnow()
    row.status = "approved" if body.action == "approve" else "rejected"

    if body.action == "rollback" and row.github_run_id:
        try:
            gh.trigger_workflow(gh.WORKFLOW_ROLLBACK, inputs={"service": "all", "reason": body.reason or "Dashboard rollback"})
            row.status = "rolling_back"
        except Exception as exc:
            logger.warning("Rollback trigger failed: %s", exc)

    db.commit()
    db.refresh(row)
    return _row_to_response(row)


@router.delete("/{deployment_id}", status_code=204)
def cancel_deployment(deployment_id: str, db: Session = Depends(get_db)):
    """Cancel a running deployment."""
    row = db.query(DeploymentRecord).filter(DeploymentRecord.id == deployment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if row.github_run_id:
        gh.cancel_run(row.github_run_id)
    row.status = "cancelled"
    db.commit()


# ─── Background helper ─────────────────────────────────────────────────────────

def _trigger_and_track(deploy_id: str, workflow: str, inputs: dict) -> None:
    """Background task: fire workflow, poll for run ID, update DB."""
    import time
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        try:
            gh.trigger_workflow(workflow, ref="main", inputs=inputs)
        except Exception as exc:
            logger.error("Workflow trigger failed %s: %s", workflow, exc)
            _set_status(db, deploy_id, "failed", str(exc))
            return

        _set_status(db, deploy_id, "running")

        for _ in range(10):
            time.sleep(3)
            try:
                run = gh.get_latest_run(workflow)
                if run:
                    row = db.query(DeploymentRecord).filter(DeploymentRecord.id == deploy_id).first()
                    if row:
                        row.github_run_id = str(run["id"])
                        row.github_run_url = run.get("html_url", "")
                        db.commit()
                    break
            except Exception:
                pass
    finally:
        db.close()


def _set_status(db: Session, deploy_id: str, status: str, error: str = None) -> None:
    row = db.query(DeploymentRecord).filter(DeploymentRecord.id == deploy_id).first()
    if row:
        row.status = status
        if error:
            row.error_message = error
        db.commit()
