"""
Local Docker Desktop Deployment Strategy

This strategy deploys the application to Docker Desktop running on the
developer's local machine. It's the simplest deployment target and used
by all developers for daily development work.

Learning Note: This concrete strategy implements the abstract base class,
providing Docker Desktop-specific deployment logic.
"""

import os
import time
from typing import Dict, Any
import docker
from docker.errors import DockerException

from agents.state import DeploymentState, add_log, update_progress
from agents.strategies.base import DeploymentStrategy


class LocalDockerStrategy(DeploymentStrategy):
    """
    Deployment strategy for local Docker Desktop.
    
    This strategy integrates with existing SocialConnectIQ scripts:
    1. Calls ../SocialConnectIQ/scripts/local/build-images.sh
    2. Calls ../SocialConnectIQ/scripts/local/start-services.sh
    3. Validates health of running services
    4. Adds intelligent error parsing and remediation
    
    Intelligence Layer: Wraps existing scripts with pre-flight checks,
    error analysis, version tracking, and remediation guidance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Local Docker strategy.
        
        Args:
            config: Local environment configuration from environments.yaml
        """
        super().__init__(config)
        
        # Path to main SocialConnectIQ repository
        self.main_repo = os.path.expanduser("../SocialConnectIQ")
        self.scripts_dir = os.path.join(self.main_repo, "scripts/local")
        
        # Docker Desktop configuration
        self.docker_compose_file = config.get("docker_compose", {}).get("file", "../SocialConnectIQ/docker-compose.yml")
        self.project_name = config.get("docker_compose", {}).get("project_name", "socialconnectiq")
        
        # Try to connect to Docker daemon
        try:
            self.docker_client = docker.from_env()
            self.docker_available = True
        except DockerException as e:
            self.docker_client = None
            self.docker_available = False
            print(f"Warning: Could not connect to Docker daemon: {e}")
    
    def build(self, state: DeploymentState) -> DeploymentState:
        """
        Build Docker images using existing build-images.sh script.
        
        Calls: ../SocialConnectIQ/scripts/local/build-images.sh
        
        Intelligence Added:
        - Git version tracking
        - Enhanced error parsing
        - Intelligent remediation suggestions
        - Build time tracking
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with build results
        """
        state = update_progress(state, "building", 20, "building")
        state = add_log(state, "INFO", "🔨 Building Docker images with existing scripts", "build")
        
        # Check if Docker is available
        if not self.docker_available:
            error_msg = "Docker Desktop is not running or not accessible"
            state = add_log(state, "ERROR", error_msg, "build")
            state["errors"].append(error_msg)
            state["status"] = "failed"
            return state
        
        # Verify main repository exists
        if not os.path.exists(self.main_repo):
            error_msg = f"Main repository not found: {self.main_repo}"
            state = add_log(state, "ERROR", error_msg, "build")
            state = add_log(state, "INFO", "💡 Remediation: Clone SocialConnectIQ repo to ../SocialConnectIQ", "build")
            state["errors"].append(error_msg)
            state["status"] = "failed"
            return state
        
        # Get current git commit for version tracking
        state = add_log(state, "INFO", "📝 Getting current version...", "build")
        git_cmd = f"cd {self.main_repo} && git rev-parse --short HEAD"
        success, git_sha, _ = self.run_command(git_cmd, state, "build", timeout=10)
        
        if success and git_sha:
            state["git_commit_sha"] = git_sha.strip()
            state = add_log(state, "INFO", f"Building version: {git_sha.strip()}", "build")
        else:
            state = add_log(state, "WARNING", "Could not retrieve git version", "build")
        
        # Check if .env.local exists
        env_file = os.path.join(self.main_repo, ".env.local")
        if not os.path.exists(env_file):
            error_msg = ".env.local configuration file not found"
            state = add_log(state, "ERROR", error_msg, "build")
            state = add_log(state, "INFO", "💡 Remediation: cd ../SocialConnectIQ && cp .env.local.template .env.local", "build")
            state["errors"].append(error_msg)
            state["status"] = "failed"
            return state
        
        # Execute build script
        build_script = os.path.join(self.scripts_dir, "build-images.sh")
        
        if not os.path.exists(build_script):
            error_msg = f"Build script not found: {build_script}"
            state = add_log(state, "ERROR", error_msg, "build")
            state["errors"].append(error_msg)
            state["status"] = "failed"
            return state
        
        state = add_log(state, "INFO", f"Executing: {build_script}", "build")
        
        if state.get("dry_run", False):
            state = add_log(state, "INFO", f"[DRY RUN] Would execute: cd {self.main_repo} && bash {build_script}", "build")
            state["build_results"] = {"dry_run": True, "script": build_script}
            return state
        
        # Call existing build script
        build_cmd = f"cd {self.main_repo} && bash {build_script}"
        start_time = time.time()
        
        success, stdout, stderr = self.run_command(
            build_cmd,
            state,
            "build",
            timeout=600  # 10 minutes
        )
        
        build_duration = time.time() - start_time
        
        # Store detailed results
        state["build_results"] = {
            "success": success,
            "script": build_script,
            "duration_seconds": build_duration,
            "git_sha": state.get("git_commit_sha", "unknown"),
            "stdout": stdout[-2000:] if stdout else "",  # Last 2000 chars
            "stderr": stderr[-2000:] if stderr else ""
        }
        
        if success:
            state = add_log(state, "INFO", f"✅ Images built successfully in {build_duration:.1f}s", "build")
            state = update_progress(state, "building", 40, "building")
            
            # Verify images were created
            verify_cmd = "docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '(gateway|service):latest' | head -5"
            _, images, _ = self.run_command(f"cd {self.main_repo} && {verify_cmd}", state, "build", timeout=10)
            
            if images:
                state = add_log(state, "INFO", f"📦 Verified images: {images.strip().replace(chr(10), ', ')[:100]}", "build")
        else:
            # Intelligent error parsing
            error_msg = f"Build failed: {stderr[-300:]}" if stderr else "Build failed with unknown error"
            state = add_log(state, "ERROR", error_msg, "build")
            
            # Analyze error and provide remediation
            if "no space left" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Run 'docker system prune -a' to free disk space", "build")
                state = add_log(state, "INFO", "   This will remove unused Docker images and containers", "build")
            elif "dockerfile not found" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Verify repository structure in ../SocialConnectIQ", "build")
            elif "requirements.txt" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Check Python dependencies in service requirements.txt", "build")
            elif "docker is not running" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Start Docker Desktop and wait for initialization", "build")
            elif "network" in stderr.lower() and "timeout" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Check internet connection and retry", "build")
            else:
                state = add_log(state, "INFO", "💡 Check build logs above for specific error details", "build")
            
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
    
    def deploy(self, state: DeploymentState) -> DeploymentState:
        """
        Deploy services using existing start-services.sh script.
        
        Calls: ../SocialConnectIQ/scripts/local/start-services.sh
        
        Intelligence Added:
        - Port conflict detection and resolution
        - Container status monitoring
        - Enhanced error parsing
        - Startup time tracking
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with deployment results
        """
        state = update_progress(state, "deploying", 50, "deploying")
        state = add_log(state, "INFO", "🚀 Starting services with existing scripts", "deploy")
        
        # Execute start script
        start_script = os.path.join(self.scripts_dir, "start-services.sh")
        
        if not os.path.exists(start_script):
            error_msg = f"Start script not found: {start_script}"
            state = add_log(state, "ERROR", error_msg, "deploy")
            state["errors"].append(error_msg)
            state["status"] = "failed"
            return state
        
        state = add_log(state, "INFO", f"Executing: {start_script}", "deploy")
        
        if state.get("dry_run", False):
            state = add_log(state, "INFO", f"[DRY RUN] Would execute: cd {self.main_repo} && bash {start_script}", "deploy")
            state["deploy_results"] = {"dry_run": True, "script": start_script}
            return state
        
        # Call existing start script
        start_cmd = f"cd {self.main_repo} && bash {start_script}"
        start_time = time.time()
        
        success, stdout, stderr = self.run_command(
            start_cmd,
            state,
            "deploy",
            timeout=300  # 5 minutes
        )
        
        deploy_duration = time.time() - start_time
        
        # Store results
        state["deploy_results"] = {
            "success": success,
            "script": start_script,
            "duration_seconds": deploy_duration,
            "stdout": stdout[-2000:] if stdout else "",
            "stderr": stderr[-2000:] if stderr else ""
        }
        
        if success:
            state = add_log(state, "INFO", f"✅ Services started successfully in {deploy_duration:.1f}s", "deploy")
            state = update_progress(state, "deploying", 70, "deploying")
            
            # Wait for services to initialize
            state = add_log(state, "INFO", "⏳ Waiting for services to initialize (10 seconds)...", "deploy")
            time.sleep(10)
            
            # Verify containers are running
            verify_cmd = f"docker ps --filter 'name=socialconnectiq' --format '{{{{.Names}}}}' | wc -l"
            _, container_count, _ = self.run_command(verify_cmd, state, "deploy", timeout=10)
            
            if container_count:
                count = container_count.strip()
                state = add_log(state, "INFO", f"📦 Running containers: {count}", "deploy")
        else:
            # Intelligent error parsing
            error_msg = f"Deployment failed: {stderr[-300:]}" if stderr else "Deployment failed"
            state = add_log(state, "ERROR", error_msg, "deploy")
            
            # Analyze error and provide remediation
            if "port is already allocated" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Port conflict detected", "deploy")
                state = add_log(state, "INFO", "   Run: cd ../SocialConnectIQ && docker-compose -f docker-compose.local.yml down", "deploy")
                state = add_log(state, "INFO", "   Then retry deployment", "deploy")
            elif "container name" in stderr.lower() and "conflict" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Remove conflicting containers", "deploy")
                state = add_log(state, "INFO", "   Run: docker-compose down && docker-compose up -d", "deploy")
            elif "network" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Recreate Docker networks", "deploy")
                state = add_log(state, "INFO", "   Run: docker network prune && retry deployment", "deploy")
            elif "image not found" in stderr.lower():
                state = add_log(state, "INFO", "💡 Remediation: Build images first", "deploy")
                state = add_log(state, "INFO", "   Run: cd ../SocialConnectIQ && bash scripts/local/build-images.sh", "deploy")
            else:
                state = add_log(state, "INFO", "💡 Check deployment logs above for specific error details", "deploy")
            
            state["errors"].append(error_msg)
            state["status"] = "failed"
        
        return state
    
    def validate(self, state: DeploymentState) -> DeploymentState:
        """
        Validate local deployment by checking service health endpoints.
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with validation results
        """
        state = update_progress(state, "validating", 80, "validating")
        state = add_log(state, "INFO", "Starting health checks", "validate")
        
        if state.get("dry_run", False):
            state = add_log(state, "INFO", "[DRY RUN] Skipping health checks", "validate")
            state["validation_results"] = {"dry_run": True}
            return state
        
        # Get validation configuration
        val_config = self.get_validation_config()
        timeout = val_config.get("health_check_timeout_seconds", 30)
        retries = val_config.get("health_check_retries", 5)
        interval = val_config.get("health_check_interval_seconds", 5)
        required_checks = val_config.get("required_checks", [])
        
        # Check each service
        services_config = self.config.get("services", {})
        validation_results = {}
        all_healthy = True
        
        for service_name, service_config in services_config.items():
            # Skip if not in required checks
            if required_checks and service_name not in required_checks:
                continue
            
            url = service_config.get("url", "")
            health_endpoint = service_config.get("health_endpoint", "/health")
            full_url = f"{url}{health_endpoint}"
            
            state = add_log(state, "INFO", f"Checking {service_name}...", "validate", service=service_name)
            
            is_healthy, response_time = self.check_health(
                full_url,
                service_name,
                state,
                timeout=timeout,
                retries=retries,
                interval=interval
            )
            
            validation_results[service_name] = {
                "healthy": is_healthy,
                "url": full_url,
                "response_time_ms": response_time
            }
            
            if not is_healthy:
                all_healthy = False
                state["warnings"].append(f"{service_name} is not healthy")
        
        # Update state with results
        state["validation_results"] = validation_results
        
        if all_healthy:
            state = add_log(state, "INFO", "✓ All required services are healthy", "validate")
            state = update_progress(state, "validating", 100, "completed")
            
            # Display access URLs
            state = add_log(state, "INFO", "=" * 60, "complete")
            state = add_log(state, "INFO", "Local Deployment Complete!", "complete")
            state = add_log(state, "INFO", "=" * 60, "complete")
            state = add_log(state, "INFO", "", "complete")
            state = add_log(state, "INFO", "Access your application at:", "complete")
            
            # Frontend URL
            frontend_url = self.config.get("frontend", {}).get("url", "http://localhost:3000")
            state = add_log(state, "INFO", f"  🌐 Frontend:    {frontend_url}", "complete")
            
            # Service URLs
            for service_name, service_config in services_config.items():
                url = service_config.get("url", "")
                if url:
                    state = add_log(state, "INFO", f"  🔌 {service_name}: {url}", "complete")
            
            state = add_log(state, "INFO", "", "complete")
            state = add_log(state, "INFO", "=" * 60, "complete")
        else:
            error_msg = "Some services failed health checks"
            state = add_log(state, "WARNING", error_msg, "validate")
            state["warnings"].append(error_msg)
            
            # Don't mark as failed, just warn (developer can debug)
            state = add_log(state, "INFO", "Deployment completed with warnings", "complete")
        
        return state
    
    def rollback(self, state: DeploymentState) -> DeploymentState:
        """
        Stop all running containers (rollback for local is just stop).
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state
        """
        state = add_log(state, "INFO", "Stopping all local containers", "rollback")
        
        compose_file_path = os.path.expanduser(self.docker_compose_file)
        stop_command = f"docker-compose -f {compose_file_path} -p {self.project_name} down"
        
        success, stdout, stderr = self.run_command(
            stop_command,
            state,
            "rollback",
            timeout=60
        )
        
        if success:
            state = add_log(state, "INFO", "✓ All containers stopped", "rollback")
        else:
            state = add_log(state, "ERROR", f"Failed to stop containers: {stderr[:200]}", "rollback")
        
        return state
    
    def get_running_services(self, state: DeploymentState) -> list:
        """
        Get list of currently running services.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of running service names
        """
        if not self.docker_available:
            return []
        
        try:
            containers = self.docker_client.containers.list(
                filters={"label": f"com.docker.compose.project={self.project_name}"}
            )
            return [c.name for c in containers]
        except Exception as e:
            state = add_log(state, "WARNING", f"Could not list running containers: {e}", "status")
            return []