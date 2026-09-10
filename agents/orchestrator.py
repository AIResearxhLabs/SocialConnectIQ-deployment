"""
LangGraph Deployment Orchestrator

This module defines the main orchestration workflow using LangGraph.
It coordinates the deployment process through a state machine that
routes between different deployment strategies based on the environment.

Learning Note: LangGraph uses a graph-based approach where each node
is a function that processes state and returns updated state. Edges
define the flow between nodes.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
import yaml
import os
from datetime import datetime

from agents.state import (
    DeploymentState, 
    create_initial_state,
    add_log,
    update_progress,
    mark_complete,
    Environment,
    UserRole
)
from agents.strategies.local_docker import LocalDockerStrategy
from agents.strategies.base import DeploymentStrategy
from agents.skills.preflight_validator import PreFlightValidator


class DeploymentOrchestrator:
    """
    Main orchestrator that manages the deployment workflow using LangGraph.
    
    This class:
    1. Loads configuration
    2. Authenticates users
    3. Selects appropriate deployment strategy
    4. Orchestrates the deployment workflow
    5. Handles approvals and validation
    """
    
    def __init__(self, config_dir: str = "./config"):
        """
        Initialize the orchestrator.
        
        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = config_dir
        self.environments_config = self._load_environments()
        self.roles_config = self._load_roles()
        self.workflow = self._build_workflow()
    
    def _load_environments(self) -> dict:
        """Load environment configurations from YAML"""
        env_file = os.path.join(self.config_dir, "environments.yaml")
        with open(env_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_roles(self) -> dict:
        """Load role configurations from YAML"""
        roles_file = os.path.join(self.config_dir, "roles.yaml")
        with open(roles_file, 'r') as f:
            return yaml.safe_load(f)
    
    def authenticate_user(self, user_email: str) -> tuple[UserRole, str]:
        """
        Authenticate user and get their role.
        
        Args:
            user_email: User's email address
            
        Returns:
            Tuple of (role, user_name)
        """
        users = self.roles_config.get("users", {})
        
        if user_email in users:
            user_data = users[user_email]
            return user_data["role"], user_data.get("name", user_email)
        
        # Fallback to default role
        default_role = self.roles_config.get("default_role", "developer")
        return default_role, user_email
    
    def check_authorization(self, user_role: UserRole, environment: Environment) -> tuple[bool, str]:
        """
        Check if user is authorized for the target environment.
        
        Args:
            user_role: User's role
            environment: Target environment
            
        Returns:
            Tuple of (is_authorized, reason)
        """
        roles_data = self.roles_config.get("roles", {})
        
        if user_role not in roles_data:
            return False, f"Unknown role: {user_role}"
        
        role_config = roles_data[user_role]
        allowed_envs = role_config.get("environments", [])
        
        if environment not in allowed_envs:
            return False, f"Role '{user_role}' not authorized for {environment} deployment"
        
        return True, "Authorized"
    
    def get_deployment_strategy(self, environment: Environment) -> DeploymentStrategy:
        """
        Select and instantiate the appropriate deployment strategy.
        
        Args:
            environment: Target environment
            
        Returns:
            Deployment strategy instance
        """
        env_config = self.environments_config["environments"][environment]
        
        # For now, only local_docker is implemented
        if environment == "local":
            return LocalDockerStrategy(env_config)
        else:
            # Placeholder for future implementations
            raise NotImplementedError(f"Deployment strategy for {environment} not yet implemented")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        The workflow follows this structure:
        START → initialize → authorize → check_approval → build → deploy → validate → END
        
        Returns:
            Compiled StateGraph workflow
        """
        workflow = StateGraph(DeploymentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("authorize", self._authorize_node)
        workflow.add_node("preflight_validation", self._preflight_validation_node)
        workflow.add_node("check_approval", self._check_approval_node)
        workflow.add_node("build", self._build_node)
        workflow.add_node("deploy", self._deploy_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("complete", self._complete_node)
        workflow.add_node("handle_failure", self._handle_failure_node)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges
        workflow.add_edge("initialize", "authorize")
        workflow.add_conditional_edges(
            "authorize",
            self._should_continue_after_auth,
            {
                "continue": "preflight_validation",
                "fail": "handle_failure"
            }
        )
        workflow.add_conditional_edges(
            "preflight_validation",
            self._should_continue_after_preflight,
            {
                "continue": "check_approval",
                "fail": "handle_failure"
            }
        )
        workflow.add_conditional_edges(
            "check_approval",
            self._should_continue_after_approval,
            {
                "continue": "build",
                "wait": END  # For future human-in-the-loop
            }
        )
        workflow.add_conditional_edges(
            "build",
            self._should_continue_after_build,
            {
                "continue": "deploy",
                "fail": "handle_failure"
            }
        )
        workflow.add_conditional_edges(
            "deploy",
            self._should_continue_after_deploy,
            {
                "continue": "validate",
                "fail": "handle_failure"
            }
        )
        workflow.add_edge("validate", "complete")
        workflow.add_edge("complete", END)
        workflow.add_edge("handle_failure", END)
        
        return workflow.compile()
    
    # Node implementations
    
    def _initialize_node(self, state: DeploymentState) -> DeploymentState:
        """Initialize deployment"""
        state = update_progress(state, "initialize", 5, "initializing")
        state = add_log(state, "INFO", f"Initializing deployment to {state['environment']}", "initialize")
        
        # Select deployment strategy
        try:
            strategy = self.get_deployment_strategy(state["environment"])
            state["deployment_strategy"] = strategy.__class__.__name__
            state = add_log(state, "INFO", f"Selected strategy: {state['deployment_strategy']}", "initialize")
        except Exception as e:
            state = add_log(state, "ERROR", f"Failed to select strategy: {e}", "initialize")
            state["errors"].append(str(e))
            state["status"] = "failed"
        
        return state
    
    def _authorize_node(self, state: DeploymentState) -> DeploymentState:
        """Authorize user for deployment"""
        state = update_progress(state, "authorize", 10, "initializing")
        state = add_log(state, "INFO", f"Authorizing user: {state['user_email']}", "authorize")
        
        # Check authorization
        is_authorized, reason = self.check_authorization(state["user_role"], state["environment"])
        
        if is_authorized:
            state = add_log(state, "INFO", f"✓ User authorized: {reason}", "authorize")
        else:
            state = add_log(state, "ERROR", f"✗ Authorization failed: {reason}", "authorize")
            state["errors"].append(reason)
            state["status"] = "failed"
        
        return state
    
    def _preflight_validation_node(self, state: DeploymentState) -> DeploymentState:
        """Run comprehensive pre-flight validation checks"""
        env_config = self.environments_config["environments"][state["environment"]]
        
        # Initialize validator
        validator = PreFlightValidator(
            environment=state["environment"],
            config=self.environments_config,
            env_config=env_config
        )
        
        # Run all checks
        result, state = validator.validate_all(state)
        
        # If validation failed, mark deployment as failed
        if not result.can_proceed:
            state["status"] = "failed"
            state["errors"].append("Pre-flight validation failed")
        
        return state
    
    def _check_approval_node(self, state: DeploymentState) -> DeploymentState:
        """Check if approval is required"""
        env_config = self.environments_config["environments"][state["environment"]]
        approval_required = env_config.get("approval_required", False)
        
        state["requires_approval"] = approval_required
        
        if approval_required:
            state = add_log(state, "INFO", "Approval required for this environment", "approval")
            state["approval_reason"] = env_config.get("approval_reason", "Environment policy requires approval")
            # For now, we'll auto-approve in local development
            # In production, this would trigger human-in-the-loop
            state = add_log(state, "INFO", "Auto-approving for development", "approval")
            state["approved"] = True
            state["approver"] = state["user_email"]
        else:
            state = add_log(state, "INFO", "No approval required", "approval")
            state["approved"] = True
        
        return state
    
    def _build_node(self, state: DeploymentState) -> DeploymentState:
        """Build deployment artifacts"""
        strategy = self.get_deployment_strategy(state["environment"])
        return strategy.build(state)
    
    def _deploy_node(self, state: DeploymentState) -> DeploymentState:
        """Deploy to target environment"""
        strategy = self.get_deployment_strategy(state["environment"])
        return strategy.deploy(state)
    
    def _validate_node(self, state: DeploymentState) -> DeploymentState:
        """Validate deployment"""
        strategy = self.get_deployment_strategy(state["environment"])
        return strategy.validate(state)
    
    def _complete_node(self, state: DeploymentState) -> DeploymentState:
        """Mark deployment as complete"""
        return mark_complete(state, success=True)
    
    def _handle_failure_node(self, state: DeploymentState) -> DeploymentState:
        """Handle deployment failure"""
        state = add_log(state, "ERROR", "Deployment failed", "failure")
        return mark_complete(state, success=False)
    
    # Conditional edge functions
    
    def _should_continue_after_auth(self, state: DeploymentState) -> Literal["continue", "fail"]:
        """Determine if workflow should continue after authorization"""
        if state["status"] == "failed":
            return "fail"
        return "continue"
    
    def _should_continue_after_preflight(self, state: DeploymentState) -> Literal["continue", "fail"]:
        """Determine if workflow should continue after pre-flight validation"""
        if state["status"] == "failed":
            return "fail"
        return "continue"
    
    def _should_continue_after_approval(self, state: DeploymentState) -> Literal["continue", "wait"]:
        """Determine if workflow should continue after approval check"""
        if state["approved"]:
            return "continue"
        return "wait"  # Would wait for human approval
    
    def _should_continue_after_build(self, state: DeploymentState) -> Literal["continue", "fail"]:
        """Determine if workflow should continue after build"""
        if state["status"] == "failed":
            return "fail"
        return "continue"
    
    def _should_continue_after_deploy(self, state: DeploymentState) -> Literal["continue", "fail"]:
        """Determine if workflow should continue after deployment"""
        if state["status"] == "failed":
            return "fail"
        return "continue"
    
    def deploy(
        self,
        environment: Environment,
        user_email: str,
        services: list = None,
        deploy_frontend: bool = True,
        dry_run: bool = False
    ) -> DeploymentState:
        """
        Execute deployment workflow.
        
        Args:
            environment: Target environment
            user_email: User's email address
            services: List of services to deploy (None = all)
            deploy_frontend: Whether to deploy frontend
            dry_run: If True, simulate deployment
            
        Returns:
            Final deployment state
        """
        # Authenticate user
        user_role, user_name = self.authenticate_user(user_email)
        
        # Create initial state
        initial_state = create_initial_state(
            environment=environment,
            user_email=user_email,
            user_role=user_role,
            services=services,
            deploy_frontend=deploy_frontend,
            triggered_by="manual",
            dry_run=dry_run
        )
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state)
        
        return final_state