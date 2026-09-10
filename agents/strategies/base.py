"""
Base Deployment Strategy

This module defines the abstract base class for all deployment strategies.
Each environment (local, staging, production) implements its own strategy
by inheriting from this base class.

Learning Note: This is the Strategy Pattern from design patterns. It allows
us to encapsulate deployment logic for each environment and swap them out
dynamically based on the target environment.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import subprocess
import time
import requests
from datetime import datetime

from agents.state import DeploymentState, add_log, update_progress


class DeploymentStrategy(ABC):
    """
    Abstract base class for deployment strategies.
    
    Each environment (local, staging, production) implements this interface
    with environment-specific deployment logic.
    
    Learning Note: The @abstractmethod decorator ensures that subclasses
    MUST implement these methods, enforcing a consistent interface across
    all strategies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the deployment strategy.
        
        Args:
            config: Environment-specific configuration from environments.yaml
        """
        self.config = config
        self.name = config.get("name", "Unknown")
        self.target = config.get("target", "unknown")
    
    @abstractmethod
    def build(self, state: DeploymentState) -> DeploymentState:
        """
        Build Docker images or compile application code.
        
        This method should:
        1. Build all required Docker images
        2. Tag images appropriately
        3. Update state with build results
        4. Handle build failures gracefully
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with build results
        """
        pass
    
    @abstractmethod
    def deploy(self, state: DeploymentState) -> DeploymentState:
        """
        Deploy services to the target environment.
        
        This method should:
        1. Deploy backend services
        2. Deploy frontend (if applicable)
        3. Configure service settings
        4. Update state with deployment results
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with deployment results
        """
        pass
    
    @abstractmethod
    def validate(self, state: DeploymentState) -> DeploymentState:
        """
        Validate the deployment by checking service health.
        
        This method should:
        1. Check health endpoints of all services
        2. Run smoke tests
        3. Verify frontend is accessible
        4. Update state with validation results
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state with validation results
        """
        pass
    
    def rollback(self, state: DeploymentState) -> DeploymentState:
        """
        Rollback to previous deployment (optional, environment-specific).
        
        Base implementation does nothing. Override in subclasses where
        rollback is supported (e.g., production).
        
        Args:
            state: Current deployment state
            
        Returns:
            Updated state after rollback
        """
        state = add_log(state, "WARNING", "Rollback not implemented for this environment", "rollback")
        return state
    
    # Helper methods that subclasses can use
    
    def run_command(
        self, 
        command: str, 
        state: DeploymentState,
        step: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> tuple[bool, str, str]:
        """
        Execute a shell command and capture output.
        
        Learning Note: This is a utility method that handles command execution,
        logging, and error handling consistently across all strategies.
        
        Args:
            command: Shell command to execute
            state: Current deployment state (for logging)
            step: Current step name
            cwd: Working directory for command
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        state = add_log(state, "INFO", f"Executing: {command}", step)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout or 300
            )
            
            success = result.returncode == 0
            
            if success:
                state = add_log(state, "INFO", f"Command succeeded", step)
            else:
                state = add_log(state, "ERROR", f"Command failed with exit code {result.returncode}", step)
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            state = add_log(state, "ERROR", error_msg, step)
            return False, "", error_msg
            
        except Exception as e:
            error_msg = f"Command execution error: {str(e)}"
            state = add_log(state, "ERROR", error_msg, step)
            return False, "", error_msg
    
    def check_health(
        self,
        url: str,
        service_name: str,
        state: DeploymentState,
        timeout: int = 30,
        retries: int = 5,
        interval: int = 5
    ) -> tuple[bool, Optional[float]]:
        """
        Check if a service health endpoint is responding.
        
        Args:
            url: Full URL to health endpoint
            service_name: Name of service being checked
            state: Current deployment state
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            interval: Seconds between retries
            
        Returns:
            Tuple of (is_healthy, response_time_ms)
        """
        state = add_log(
            state, 
            "INFO", 
            f"Checking health of {service_name} at {url}", 
            "validate",
            service=service_name
        )
        
        for attempt in range(1, retries + 1):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=timeout)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    state = add_log(
                        state,
                        "INFO",
                        f"✓ {service_name} is healthy (response time: {response_time:.0f}ms)",
                        "validate",
                        service=service_name
                    )
                    return True, response_time
                else:
                    state = add_log(
                        state,
                        "WARNING",
                        f"Health check returned status {response.status_code} (attempt {attempt}/{retries})",
                        "validate",
                        service=service_name
                    )
                    
            except requests.exceptions.Timeout:
                state = add_log(
                    state,
                    "WARNING",
                    f"Health check timed out (attempt {attempt}/{retries})",
                    "validate",
                    service=service_name
                )
                
            except requests.exceptions.ConnectionError:
                state = add_log(
                    state,
                    "WARNING",
                    f"Could not connect to service (attempt {attempt}/{retries})",
                    "validate",
                    service=service_name
                )
                
            except Exception as e:
                state = add_log(
                    state,
                    "WARNING",
                    f"Health check error: {str(e)} (attempt {attempt}/{retries})",
                    "validate",
                    service=service_name
                )
            
            # Wait before retry (except on last attempt)
            if attempt < retries:
                time.sleep(interval)
        
        # All retries failed
        state = add_log(
            state,
            "ERROR",
            f"✗ {service_name} health check failed after {retries} attempts",
            "validate",
            service=service_name
        )
        return False, None
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration dictionary
        """
        services = self.config.get("services", {})
        return services.get(service_name, {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """
        Get validation configuration for this environment.
        
        Returns:
            Validation configuration dictionary
        """
        return self.config.get("validation", {})
    
    def requires_approval(self) -> bool:
        """
        Check if this environment requires deployment approval.
        
        Returns:
            True if approval is required, False otherwise
        """
        return self.config.get("approval_required", False)
    
    def get_approval_count(self) -> int:
        """
        Get number of approvals required for this environment.
        
        Returns:
            Number of required approvals (default: 1)
        """
        return self.config.get("approval_count", 1)
    
    def __str__(self) -> str:
        """String representation of strategy"""
        return f"{self.__class__.__name__}(environment={self.name}, target={self.target})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return self.__str__()