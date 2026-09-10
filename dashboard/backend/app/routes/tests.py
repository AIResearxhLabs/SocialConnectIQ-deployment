"""
Test Run Routes — trigger, list, detail.

POST /api/tests/trigger   — trigger CI / regression / smoke tests via GitHub Actions
GET  /api/tests           — list recent test runs
GET  /api/tests/{id}      — single test run detail
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import github_client as gh
from app.database import get_db
from app.models import TestRunRecord, TestRunResponse, TestTriggerRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tests", tags=["tests"])

# Maps run_type → workflow file and GitHub ref
_WORKFLOW_MAP = {
    "ci":         (gh.WORKFLOW_RELEASE, "main"),
    "regression": (gh.WORKFLOW_RELEASE, "main"),
    "smoke":      (gh.WORKFLOW_DEPLOY,  "rel"),
}


def _row_to_response(row: TestRunRecord) -> TestRunResponse:
    return TestRunResponse.model_validate(row)


@router.get("", response_model=List[TestRunResponse])
def list_test_runs(
    limit: int = 50,
    run_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List recent test runs, newest first."""
    query = db.query(TestRunRecord).order_by(TestRunRecord.triggered_at.desc())
    if run_type:
        query = query.filter(TestRunRecord.run_type == run_type)
    return [_row_to_response(r) for r in query.limit(limit).all()]


@router.get("/{run_id}", response_model=TestRunResponse)
def get_test_run(run_id: str, db: Session = Depends(get_db)):
    row = db.query(TestRunRecord).filter(TestRunRecord.id == run_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Test run not found")
    return _row_to_response(row)


@router.post("/trigger", response_model=TestRunResponse, status_code=201)
def trigger_test_run(
    body: TestTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger test execution via GitHub Actions.

    - run_type=ci         → runs full CI pipeline (lint + unit + docker)
    - run_type=regression → runs regression suite against release binaries
    - run_type=smoke      → runs WF-09 health tests against production
    """
    run_id = str(uuid.uuid4())[:8]
    workflow, ref = _WORKFLOW_MAP.get(body.run_type, (gh.WORKFLOW_RELEASE, "main"))

    row = TestRunRecord(
        id=run_id,
        run_type=body.run_type,
        environment=body.environment,
        status="pending",
        triggered_by=body.triggered_by,
        triggered_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    inputs: dict = {}
    if body.version:
        inputs["version"] = body.version

    background_tasks.add_task(_trigger_test_workflow, run_id, workflow, ref, inputs)
    return _row_to_response(row)


# ─── Background helper ─────────────────────────────────────────────────────────

def _trigger_test_workflow(run_id: str, workflow: str, ref: str, inputs: dict) -> None:
    """Background task: fire workflow and poll for run ID."""
    import time
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        try:
            gh.trigger_workflow(workflow, ref=ref, inputs=inputs)
        except Exception as exc:
            logger.error("Test workflow trigger failed %s: %s", workflow, exc)
            row = db.query(TestRunRecord).filter(TestRunRecord.id == run_id).first()
            if row:
                row.status = "failed"
                db.commit()
            return

        row = db.query(TestRunRecord).filter(TestRunRecord.id == run_id).first()
        if row:
            row.status = "running"
            db.commit()

        # Attempt to capture GitHub run ID
        for _ in range(10):
            time.sleep(3)
            try:
                run = gh.get_latest_run(workflow)
                if run:
                    row = db.query(TestRunRecord).filter(TestRunRecord.id == run_id).first()
                    if row:
                        row.github_run_id = str(run["id"])
                        row.github_run_url = run.get("html_url", "")
                        db.commit()
                    break
            except Exception:
                pass
    finally:
        db.close()
