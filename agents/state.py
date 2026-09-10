"""
Deployment Agent State Definitions

This module defines the state models used by the LangGraph deployment agent.
State represents the data that flows through the agent workflow, tracking
deployment progress, status, and decisions.

Learning Note: In LangGraph, state is immutable - each node returns a new
state rather than modifying the existing one. This makes workflows predictable
and easier to debug.
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Type aliases for clarity
Environment = Literal["local", "staging", "production"]
DeploymentStatus = Literal["initializing", "building", "deploying", "validating", 
                           "completed", "failed", "awaiting_approval"]
ServiceStatus = Literal["pending", "building", "deploying", "healthy", "unhealthy", "failed"]
UserRole = Literal["developer", "staging-ops", "prod-ops", "admin"]


class ServiceState(BaseModel):
    """State for an individual service being deployed"""
    name: str
    status: ServiceStatus = "pending"
    url: Optional[str] = None
    health_check_url: Optional[str] = None
    build_time_seconds: Optional[float] = None
    error: Optional[str] = None


class DeploymentState(TypedDict):
    """
    Main state object that flows through the LangGraph workflow.
    
    This TypedDict defines all data needed to track a deployment from
    start to finish. Each node in the workflow can read and update this state.
    
    Learning Note: TypedDict is used instead of Pydantic for LangGraph state
    because it provides better compatibility with the framework's type system.
    """
    
    # Deployment identification
    deployment_id: str
    timestamp: str
    
    # Environment and user context
    environment: Environment
    user_email: str
    user_role: UserRole
    
    # Deployment configuration
    services_to_deploy: List[str]  # e.g., ["api-gateway", "backend-service"]
    deploy_frontend: bool
    skip_validation: bool
    
    # Current workflow status
    current_step: str
    status: DeploymentStatus
    progress_percentage: int
    
    # Strategy selection (set by orchestrator)
    deployment_strategy: str  # e.g., "local_docker", "gcp_staging"
    
    # Service-level tracking
    services: Dict[str, Dict[str, Any]]  # service_name -> service_state
    
    # Build and deployment results
    build_results: Dict[str, Any]
    deploy_results: Dict[str, Any]
    validation_results: Dict[str, Any]
    
    # Timing information
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]
    
    # Logs and errors
    logs: List[Dict[str, Any]]  # [{timestamp, level, message, step}]
    errors: List[str]
    warnings: List[str]
    
    # Human-in-the-loop approval workflow
    requires_approval: bool
    approval_reason: Optional[str]
    approval_requested_at: Optional[str]
    approved: bool
    approver: Optional[str]
    approved_at: Optional[str]
    approval_action: Optional[Literal["retry", "skip", "abort"]]
    
    # Rollback information (for production)
    previous_deployment_id: Optional[str]
    rollback_available: bool
    
    # Metadata
    git_commit_sha: Optional[str]
    triggered_by: str  # "manual", "ci", "schedule"
    dry_run: bool


class ValidationCheck(BaseModel):
    """Individual validation check result"""
    check_name: str
    service: str
    status: Literal["passed", "failed", "skipped"]
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class LogEntry(BaseModel):
    """Structured log entry for deployment tracking"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    step: str
    message: str
    service: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def create_initial_state(
    environment: Environment,
    user_email: str,
    user_role: UserRole,
    services: Optional[List[str]] = None,
    deploy_frontend: bool = True,
    triggered_by: str = "manual",
    dry_run: bool = False
) -> DeploymentState:
    """
    Factory function to create initial deployment state.
    
    This is the starting point for any deployment. The orchestrator will
    call this to initialize the state before starting the workflow.
    
    Args:
        environment: Target environment (local, staging, production)
        user_email: Email of user triggering deployment
        user_role: User's role (determines permissions)
        services: List of services to deploy (None = all)
        deploy_frontend: Whether to deploy frontend to Firebase
        triggered_by: How deployment was initiated
        dry_run: If True, simulate deployment without actual changes
    
    Returns:
        Initial DeploymentState ready for the workflow
    """
    deployment_id = f"deploy-{environment}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now().isoformat()
    
    return DeploymentState(
        # Identification
        deployment_id=deployment_id,
        timestamp=timestamp,
        
        # Context
        environment=environment,
        user_email=user_email,
        user_role=user_role,
        
        # Configuration
        services_to_deploy=services or ["all"],
        deploy_frontend=deploy_frontend,
        skip_validation=False,
        
        # Status
        current_step="initializing",
        status="initializing",
        progress_percentage=0,
        
        # Strategy (will be set by orchestrator)
        deployment_strategy="",
        
        # Service tracking (will be populated during workflow)
        services={},
        
        # Results (empty initially)
        build_results={},
        deploy_results={},
        validation_results={},
        
        # Timing
        start_time=timestamp,
        end_time=None,
        duration_seconds=None,
        
        # Logs
        logs=[{
            "timestamp": timestamp,
            "level": "INFO",
            "message": f"Deployment initialized for {environment}",
            "step": "initialize"
        }],
        errors=[],
        warnings=[],
        
        # Approval (default: not required)
        requires_approval=False,
        approval_reason=None,
        approval_requested_at=None,
        approved=False,
        approver=None,
        approved_at=None,
        approval_action=None,
        
        # Rollback
        previous_deployment_id=None,
        rollback_available=False,
        
        # Metadata
        git_commit_sha=None,
        triggered_by=triggered_by,
        dry_run=dry_run
    )


def add_log(state: DeploymentState, level: str, message: str, step: str, 
            service: Optional[str] = None) -> DeploymentState:
    """
    Helper to add a log entry to state.
    
    Learning Note: This returns a NEW state object with the log added,
    rather than modifying the existing state. This is the LangGraph pattern.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "step": step,
        "service": service
    }
    
    state["logs"].append(log_entry)
    return state


def update_progress(state: DeploymentState, step: str, 
                   percentage: int, status: DeploymentStatus) -> DeploymentState:
    """
    Helper to update deployment progress.
    
    Args:
        state: Current deployment state
        step: Name of current step
        percentage: Progress percentage (0-100)
        status: Overall deployment status
    
    Returns:
        Updated state
    """
    state["current_step"] = step
    state["progress_percentage"] = percentage
    state["status"] = status
    
    return add_log(state, "INFO", f"Progress: {percentage}% - {step}", step)


def mark_complete(state: DeploymentState, success: bool = True) -> DeploymentState:
    """Mark deployment as complete (success or failure)"""
    end_time = datetime.now()
    start_time = datetime.fromisoformat(state["start_time"])
    duration = (end_time - start_time).total_seconds()
    
    state["end_time"] = end_time.isoformat()
    state["duration_seconds"] = duration
    state["status"] = "completed" if success else "failed"
    state["progress_percentage"] = 100 if success else state["progress_percentage"]
    
    message = f"Deployment {'completed successfully' if success else 'failed'} in {duration:.1f}s"
    return add_log(state, "INFO" if success else "ERROR", message, "complete")