"""
Pre-Flight Validation Skill

This module implements comprehensive pre-deployment validation checks.
It ensures all prerequisites are met before triggering deployment workflows,
catching potential issues early and providing clear remediation guidance.

Learning Note: This is a "skill" - a specialized capability that the agent
uses to accomplish a specific task. Skills are reusable and testable.
"""

import os
import socket
import shutil
import psutil
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import yaml
import requests
from pathlib import Path

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from agents.state import DeploymentState, add_log, update_progress


# Check Result Models
@dataclass
class CheckResult:
    """Result of a single validation check"""
    name: str
    category: str  # system, config, dependency, permission, environment
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str    # PASS, FAIL, WARN, SKIP
    message: str
    remediation: Optional[str] = None
    elapsed_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_blocking(self) -> bool:
        """Check if this failure should block deployment"""
        return self.status == "FAIL" and self.priority in ["CRITICAL", "HIGH"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "message": self.message,
            "remediation": self.remediation,
            "elapsed_time_ms": self.elapsed_time_ms,
            "metadata": self.metadata
        }


@dataclass
class ValidationResult:
    """Aggregated result of all validation checks"""
    passed: bool
    can_proceed: bool
    checks: List[CheckResult]
    critical_failures: List[CheckResult]
    high_failures: List[CheckResult]
    warnings: List[CheckResult]
    total_checks: int
    elapsed_time_seconds: float
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "passed": self.passed,
            "can_proceed": self.can_proceed,
            "total_checks": self.total_checks,
            "elapsed_time_seconds": self.elapsed_time_seconds,
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
            "critical_failures": len(self.critical_failures),
            "high_failures": len(self.high_failures),
            "warnings": len(self.warnings)
        }


class PreFlightValidator:
    """
    Comprehensive pre-deployment validation skill.
    
    This skill performs thorough checks across multiple categories:
    - System checks (Docker, CLI tools, resources)
    - Configuration checks (env vars, YAML files, paths)
    - Dependency checks (ports, volumes, images)
    - Permission checks (authorization, file access)
    - Environment checks (existing deployments, health)
    """
    
    def __init__(self, environment: str, config: Dict[str, Any], env_config: Dict[str, Any]):
        """
        Initialize the pre-flight validator.
        
        Args:
            environment: Target environment (local, staging, production)
            config: Global configuration
            env_config: Environment-specific configuration
        """
        self.environment = environment
        self.config = config
        self.env_config = env_config
        self.checks: List[CheckResult] = []
        self.start_time = datetime.now()
        
    def validate_all(self, state: DeploymentState) -> Tuple[ValidationResult, DeploymentState]:
        """
        Run all validation checks in priority order.
        
        Args:
            state: Current deployment state
            
        Returns:
            Tuple of (ValidationResult, updated_state)
        """
        state = update_progress(state, "preflight", 7, "initializing")
        state = add_log(state, "INFO", "🔍 Running pre-flight validation checks...", "preflight")
        
        # Run checks in priority order
        state = self._run_critical_checks(state)
        state = self._run_high_priority_checks(state)
        state = self._run_medium_priority_checks(state)
        state = self._run_low_priority_checks(state)
        
        # Aggregate results
        result = self._aggregate_results()
        
        # Add validation results to state
        state["validation_results"]["preflight"] = result.to_dict()
        
        # Log summary
        if result.can_proceed:
            state = add_log(state, "INFO", f"✅ {result.summary}", "preflight")
        else:
            state = add_log(state, "ERROR", f"❌ {result.summary}", "preflight")
            for failure in result.critical_failures:
                state = add_log(state, "ERROR", f"  • {failure.message}", "preflight")
                if failure.remediation:
                    state = add_log(state, "INFO", f"    → {failure.remediation}", "preflight")
        
        return result, state
    
    def _run_critical_checks(self, state: DeploymentState) -> DeploymentState:
        """Run CRITICAL priority checks (blocking failures)"""
        state = add_log(state, "INFO", "Running critical system checks...", "preflight")
        
        # Docker daemon check
        self._check_docker_daemon()
        
        # Configuration file integrity
        self._check_configuration_files()
        
        # Environment variables
        self._check_required_env_vars()
        
        # User authorization (already done, but validate again)
        self._check_user_authorization(state)
        
        return state
    
    def _run_high_priority_checks(self, state: DeploymentState) -> DeploymentState:
        """Run HIGH priority checks (blocking with remediation)"""
        state = add_log(state, "INFO", "Running high priority checks...", "preflight")
        
        # Required CLI tools
        self._check_required_tools()
        
        # System resources
        self._check_system_resources()
        
        # Repository paths
        self._check_repository_paths()
        
        # Port availability
        self._check_port_availability()
        
        # File permissions
        self._check_file_permissions()
        
        return state
    
    def _run_medium_priority_checks(self, state: DeploymentState) -> DeploymentState:
        """Run MEDIUM priority checks (warnings)"""
        state = add_log(state, "INFO", "Running medium priority checks...", "preflight")
        
        # Network connectivity
        self._check_network_connectivity()
        
        # Docker images
        self._check_docker_images()
        
        # Existing deployment detection
        self._check_existing_deployment(state)
        
        return state
    
    def _run_low_priority_checks(self, state: DeploymentState) -> DeploymentState:
        """Run LOW priority checks (informational)"""
        state = add_log(state, "INFO", "Running low priority checks...", "preflight")
        
        # Optional tools
        self._check_optional_tools()
        
        # Performance metrics
        self._check_performance_metrics()
        
        return state
    
    # === CRITICAL CHECKS ===
    
    def _check_docker_daemon(self):
        """Check if Docker daemon is running and accessible"""
        start = datetime.now()
        
        if not DOCKER_AVAILABLE:
            self.checks.append(CheckResult(
                name="Docker SDK Available",
                category="system",
                priority="CRITICAL",
                status="FAIL",
                message="Docker Python SDK not installed",
                remediation="Install docker package: pip install docker",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
            ))
            return
        
        try:
            client = docker.from_env()
            version = client.version()
            api_version = version.get('ApiVersion', 'unknown')
            
            self.checks.append(CheckResult(
                name="Docker Daemon Status",
                category="system",
                priority="CRITICAL",
                status="PASS",
                message=f"Docker daemon running (API v{api_version})",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                metadata={"api_version": api_version, "version_info": version}
            ))
        except Exception as e:
            self.checks.append(CheckResult(
                name="Docker Daemon Status",
                category="system",
                priority="CRITICAL",
                status="FAIL",
                message="Docker Desktop is not running or not accessible",
                remediation="Start Docker Desktop and ensure it's fully initialized",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                metadata={"error": str(e)}
            ))
    
    def _check_configuration_files(self):
        """Check configuration file integrity"""
        start = datetime.now()
        config_files = {
            "environments.yaml": "./config/environments.yaml",
            "roles.yaml": "./config/roles.yaml"
        }
        
        for name, path in config_files.items():
            if not os.path.exists(path):
                self.checks.append(CheckResult(
                    name=f"Configuration File: {name}",
                    category="config",
                    priority="CRITICAL",
                    status="FAIL",
                    message=f"Configuration file not found: {path}",
                    remediation=f"Ensure {path} exists",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
                continue
            
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f)
                    if not data:
                        raise ValueError("Empty configuration file")
                
                self.checks.append(CheckResult(
                    name=f"Configuration File: {name}",
                    category="config",
                    priority="CRITICAL",
                    status="PASS",
                    message=f"Configuration file valid: {name}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
            except Exception as e:
                self.checks.append(CheckResult(
                    name=f"Configuration File: {name}",
                    category="config",
                    priority="CRITICAL",
                    status="FAIL",
                    message=f"Invalid configuration file: {name}",
                    remediation=f"Fix YAML syntax in {path}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"error": str(e)}
                ))
    
    def _check_required_env_vars(self):
        """Check required environment variables"""
        start = datetime.now()
        
        required_vars = {
            "local": ["DEPLOYMENT_USER", "DOCKER_HOST"],
            "staging": ["DEPLOYMENT_USER", "GCP_PROJECT_ID_STAGING", "FIREBASE_PROJECT_STAGING"],
            "production": ["DEPLOYMENT_USER", "GCP_PROJECT_ID_PROD", "FIREBASE_PROJECT_PROD"]
        }
        
        env_vars = required_vars.get(self.environment, required_vars["local"])
        
        for var in env_vars:
            value = os.getenv(var)
            if not value:
                self.checks.append(CheckResult(
                    name=f"Environment Variable: {var}",
                    category="config",
                    priority="CRITICAL",
                    status="FAIL",
                    message=f"Required environment variable not set: {var}",
                    remediation=f"Set {var} in .env file or export it",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
            else:
                self.checks.append(CheckResult(
                    name=f"Environment Variable: {var}",
                    category="config",
                    priority="CRITICAL",
                    status="PASS",
                    message=f"Environment variable set: {var}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"masked_value": value[:3] + "..." if len(value) > 3 else "***"}
                ))
    
    def _check_user_authorization(self, state: DeploymentState):
        """Validate user authorization"""
        start = datetime.now()
        
        # This was already checked, but we validate the state
        if state.get("status") == "failed" and any("not authorized" in err for err in state.get("errors", [])):
            self.checks.append(CheckResult(
                name="User Authorization",
                category="permission",
                priority="CRITICAL",
                status="FAIL",
                message=f"User not authorized for {self.environment} deployment",
                remediation="Contact admin to update your role in config/roles.yaml",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
            ))
        else:
            self.checks.append(CheckResult(
                name="User Authorization",
                category="permission",
                priority="CRITICAL",
                status="PASS",
                message=f"User authorized for {self.environment} deployment",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
            ))
    
    # === HIGH PRIORITY CHECKS ===
    
    def _check_required_tools(self):
        """Check for required CLI tools"""
        start = datetime.now()
        
        tool_requirements = {
            "local": ["docker", "docker-compose"],
            "staging": ["docker", "gcloud", "firebase"],
            "production": ["docker", "gcloud", "firebase", "kubectl"]
        }
        
        tools = tool_requirements.get(self.environment, tool_requirements["local"])
        
        for tool in tools:
            tool_path = shutil.which(tool)
            if tool_path:
                self.checks.append(CheckResult(
                    name=f"CLI Tool: {tool}",
                    category="system",
                    priority="HIGH",
                    status="PASS",
                    message=f"Tool available: {tool}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"path": tool_path}
                ))
            else:
                self.checks.append(CheckResult(
                    name=f"CLI Tool: {tool}",
                    category="system",
                    priority="HIGH",
                    status="FAIL",
                    message=f"Required tool not found: {tool}",
                    remediation=f"Install {tool} - see documentation",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
    
    def _check_system_resources(self):
        """Check system resources (disk, memory)"""
        start = datetime.now()
        
        # Disk space check
        try:
            disk = psutil.disk_usage('/')
            available_gb = disk.free / (1024 ** 3)
            required_gb = 10 if self.environment == "local" else 5
            
            if available_gb < required_gb:
                self.checks.append(CheckResult(
                    name="Disk Space",
                    category="system",
                    priority="HIGH",
                    status="FAIL",
                    message=f"Insufficient disk space: {available_gb:.1f}GB available, {required_gb}GB required",
                    remediation="Free up disk space before deploying",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"available_gb": available_gb, "required_gb": required_gb}
                ))
            else:
                self.checks.append(CheckResult(
                    name="Disk Space",
                    category="system",
                    priority="HIGH",
                    status="PASS",
                    message=f"Sufficient disk space: {available_gb:.1f}GB available",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"available_gb": available_gb}
                ))
        except Exception as e:
            self.checks.append(CheckResult(
                name="Disk Space",
                category="system",
                priority="HIGH",
                status="WARN",
                message="Could not check disk space",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                metadata={"error": str(e)}
            ))
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            recommended_gb = 4.0
            
            if available_gb < 2.0:
                self.checks.append(CheckResult(
                    name="Available Memory",
                    category="system",
                    priority="HIGH",
                    status="WARN",
                    message=f"Low memory: {available_gb:.1f}GB available (recommended: {recommended_gb}GB)",
                    remediation="Close unnecessary applications to free memory",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"available_gb": available_gb}
                ))
            else:
                self.checks.append(CheckResult(
                    name="Available Memory",
                    category="system",
                    priority="HIGH",
                    status="PASS",
                    message=f"Sufficient memory: {available_gb:.1f}GB available",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"available_gb": available_gb}
                ))
        except Exception as e:
            self.checks.append(CheckResult(
                name="Available Memory",
                category="system",
                priority="HIGH",
                status="WARN",
                message="Could not check memory",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                metadata={"error": str(e)}
            ))
    
    def _check_repository_paths(self):
        """Check repository paths exist"""
        start = datetime.now()
        
        repo_paths = {
            "Main Repository": self.env_config.get("docker_compose", {}).get("file", "../SocialConnectIQ/docker-compose.yml"),
        }
        
        for name, path in repo_paths.items():
            # Get directory from file path
            repo_dir = str(Path(path).parent)
            
            if os.path.exists(repo_dir) and os.path.exists(os.path.join(repo_dir, ".git")):
                self.checks.append(CheckResult(
                    name=f"Repository: {name}",
                    category="config",
                    priority="HIGH",
                    status="PASS",
                    message=f"Repository found: {repo_dir}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"path": repo_dir}
                ))
            else:
                self.checks.append(CheckResult(
                    name=f"Repository: {name}",
                    category="config",
                    priority="HIGH",
                    status="FAIL",
                    message=f"Repository not found: {repo_dir}",
                    remediation=f"Clone repository to {repo_dir} or update path in config",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"path": repo_dir}
                ))
    
    def _check_port_availability(self):
        """Check if required ports are available"""
        start = datetime.now()
        
        # Get ports from service configuration
        services = self.env_config.get("services", {})
        ports_to_check = []
        
        for service_name, service_config in services.items():
            url = service_config.get("url", "")
            if "localhost:" in url:
                try:
                    port = int(url.split(":")[-1].split("/")[0])
                    ports_to_check.append((service_name, port))
                except:
                    pass
        
        # Also check frontend port
        frontend_url = self.env_config.get("frontend", {}).get("url", "")
        if "localhost:" in frontend_url:
            try:
                port = int(frontend_url.split(":")[-1].split("/")[0])
                ports_to_check.append(("frontend", port))
            except:
                pass
        
        for service_name, port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use
                self.checks.append(CheckResult(
                    name=f"Port {port} ({service_name})",
                    category="dependency",
                    priority="HIGH",
                    status="WARN",
                    message=f"Port {port} already in use (may be existing deployment)",
                    remediation=f"Stop service using port {port} or deployment will update it",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"port": port, "service": service_name}
                ))
            else:
                # Port is available
                self.checks.append(CheckResult(
                    name=f"Port {port} ({service_name})",
                    category="dependency",
                    priority="HIGH",
                    status="PASS",
                    message=f"Port {port} available",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                    metadata={"port": port, "service": service_name}
                ))
    
    def _check_file_permissions(self):
        """Check file system permissions"""
        start = datetime.now()
        
        paths_to_check = {
            "Logs Directory": "./logs",
            "Config Directory": "./config",
        }
        
        for name, path in paths_to_check.items():
            if os.path.exists(path):
                if os.access(path, os.R_OK | os.W_OK):
                    self.checks.append(CheckResult(
                        name=f"Permissions: {name}",
                        category="permission",
                        priority="HIGH",
                        status="PASS",
                        message=f"Directory accessible: {path}",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                    ))
                else:
                    self.checks.append(CheckResult(
                        name=f"Permissions: {name}",
                        category="permission",
                        priority="HIGH",
                        status="FAIL",
                        message=f"Insufficient permissions for: {path}",
                        remediation=f"Grant read/write permissions: chmod +rw {path}",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                    ))
            else:
                self.checks.append(CheckResult(
                    name=f"Permissions: {name}",
                    category="permission",
                    priority="HIGH",
                    status="WARN",
                    message=f"Directory does not exist: {path}",
                    remediation=f"Directory will be created automatically",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
    
    # === MEDIUM PRIORITY CHECKS ===
    
    def _check_network_connectivity(self):
        """Check network connectivity"""
        start = datetime.now()
        
        test_urls = {
            "Internet": "https://www.google.com",
            "Docker Hub": "https://hub.docker.com"
        }
        
        if self.environment in ["staging", "production"]:
            test_urls["GCP"] = "https://cloud.google.com"
            test_urls["Firebase"] = "https://firebase.google.com"
        
        for name, url in test_urls.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    self.checks.append(CheckResult(
                        name=f"Network: {name}",
                        category="system",
                        priority="MEDIUM",
                        status="PASS",
                        message=f"Can reach {name}",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                    ))
                else:
                    self.checks.append(CheckResult(
                        name=f"Network: {name}",
                        category="system",
                        priority="MEDIUM",
                        status="WARN",
                        message=f"Unexpected response from {name}",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                    ))
            except:
                self.checks.append(CheckResult(
                    name=f"Network: {name}",
                    category="system",
                    priority="MEDIUM",
                    status="WARN",
                    message=f"Cannot reach {name}",
                    remediation="Check internet connection",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
    
    def _check_docker_images(self):
        """Check Docker images status"""
        start = datetime.now()
        
        if not DOCKER_AVAILABLE:
            return
        
        try:
            client = docker.from_env()
            images = client.images.list()
            
            self.checks.append(CheckResult(
                name="Docker Images",
                category="dependency",
                priority="MEDIUM",
                status="PASS",
                message=f"Docker has {len(images)} cached images",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                metadata={"image_count": len(images)}
            ))
        except:
            self.checks.append(CheckResult(
                name="Docker Images",
                category="dependency",
                priority="MEDIUM",
                status="WARN",
                message="Could not check Docker images",
                elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
            ))
    
    def _check_existing_deployment(self, state: DeploymentState):
        """Check for existing deployment"""
        start = datetime.now()
        
        if self.environment == "local" and DOCKER_AVAILABLE:
            try:
                client = docker.from_env()
                project_name = self.env_config.get("docker_compose", {}).get("project_name", "socialconnectiq")
                containers = client.containers.list(
                    filters={"label": f"com.docker.compose.project={project_name}"}
                )
                
                if containers:
                    self.checks.append(CheckResult(
                        name="Existing Deployment",
                        category="environment",
                        priority="MEDIUM",
                        status="WARN",
                        message=f"Found {len(containers)} running containers from previous deployment",
                        remediation="Deployment will update existing containers",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000,
                        metadata={"container_count": len(containers)}
                    ))
                else:
                    self.checks.append(CheckResult(
                        name="Existing Deployment",
                        category="environment",
                        priority="MEDIUM",
                        status="PASS",
                        message="No existing deployment detected (fresh deployment)",
                        elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                    ))
            except:
                pass
    
    # === LOW PRIORITY CHECKS ===
    
    def _check_optional_tools(self):
        """Check for optional but recommended tools"""
        start = datetime.now()
        
        optional_tools = ["git", "curl", "jq"]
        
        for tool in optional_tools:
            tool_path = shutil.which(tool)
            if tool_path:
                self.checks.append(CheckResult(
                    name=f"Optional Tool: {tool}",
                    category="system",
                    priority="LOW",
                    status="PASS",
                    message=f"Optional tool available: {tool}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
            else:
                self.checks.append(CheckResult(
                    name=f"Optional Tool: {tool}",
                    category="system",
                    priority="LOW",
                    status="SKIP",
                    message=f"Optional tool not found: {tool}",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
    
    def _check_performance_metrics(self):
        """Check system performance metrics"""
        start = datetime.now()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent > 80:
                self.checks.append(CheckResult(
                    name="CPU Usage",
                    category="system",
                    priority="LOW",
                    status="WARN",
                    message=f"High CPU usage: {cpu_percent}%",
                    remediation="Consider waiting for CPU to settle",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
            else:
                self.checks.append(CheckResult(
                    name="CPU Usage",
                    category="system",
                    priority="LOW",
                    status="PASS",
                    message=f"Normal CPU usage: {cpu_percent}%",
                    elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
                ))
        except:
            pass
    
    # === RESULT AGGREGATION ===
    
    def _aggregate_results(self) -> ValidationResult:
        """Aggregate all check results into final validation result"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        critical_failures = [c for c in self.checks if c.priority == "CRITICAL" and c.status == "FAIL"]
        high_failures = [c for c in self.checks if c.priority == "HIGH" and c.status == "FAIL"]
        warnings = [c for c in self.checks if c.status == "WARN"]
        
        passed = len(critical_failures) == 0 and len(high_failures) == 0
        can_proceed = len(critical_failures) == 0  # High failures can be overridden with warnings
        
        # Generate summary
        if passed:
            summary = f"Pre-flight validation PASSED: {len(self.checks)} checks, {len(warnings)} warnings"
        elif can_proceed:
            summary = f"Pre-flight validation PASSED WITH WARNINGS: {len(high_failures)} high priority issues"
        else:
            summary = f"Pre-flight validation FAILED: {len(critical_failures)} critical issues"
        
        return ValidationResult(
            passed=passed,
            can_proceed=can_proceed,
            checks=self.checks,
            critical_failures=critical_failures,
            high_failures=high_failures,
            warnings=warnings,
            total_checks=len(self.checks),
            elapsed_time_seconds=elapsed,
            summary=summary
        )