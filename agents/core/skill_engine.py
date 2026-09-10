"""
Universal Skill Interpretation and Execution Engine

This module provides a project-agnostic engine that interprets skill knowledge
artifacts (YAML) and executes them using available tools. It enables agents to
apply skills through reasoning rather than rigid code execution.

Architecture:
- Load: Parse YAML skill definitions
- Reason: Analyze context to determine applicable patterns
- Execute: Apply skill using tool sequences
- Learn: Update skill based on outcomes
"""

import yaml
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

from agents.state import DeploymentState, add_log, update_progress

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Skill identification and versioning"""
    id: str
    name: str
    version: str
    category: str
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DecisionPattern:
    """A conditional action pattern within a skill"""
    condition: str
    action: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    tools_required: List[str]
    success_criteria: str
    failure_handling: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Evaluate if this pattern applies to current context"""
        try:
            # Simple condition evaluation - can be enhanced with AST parsing
            if self.condition == "always":
                return True
            
            # Evaluate environment-based conditions
            if "environment ==" in self.condition:
                env = self.condition.split("==")[1].strip().strip("'\"")
                return context.get("environment") == env
            
            if "environment IN" in self.condition or "environment in" in self.condition:
                # Extract list from condition
                envs_str = self.condition.split("[")[1].split("]")[0]
                envs = [e.strip().strip("'\"") for e in envs_str.split(",")]
                return context.get("environment") in envs
            
            # Add more condition evaluators as needed
            return False
        except Exception as e:
            logger.warning(f"Error evaluating condition '{self.condition}': {e}")
            return False


@dataclass
class ToolStep:
    """A single step in a tool sequence"""
    tool: str
    action: str
    inputs: Dict[str, Any]
    outputs: List[str]
    validation: str
    on_failure: Optional[str] = None


@dataclass
class ToolSequence:
    """Sequence of tool invocations"""
    sequence_name: str
    description: str = ""
    steps: List[ToolStep] = field(default_factory=list)


@dataclass
class Skill:
    """Complete skill knowledge artifact"""
    metadata: SkillMetadata
    understanding: Dict[str, Any]
    knowledge_domains: List[Dict[str, Any]]
    decision_patterns: List[DecisionPattern]
    tool_sequences: List[ToolSequence]
    learning_examples: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    evolution: Dict[str, Any]
    
    @property
    def importance(self) -> str:
        return self.understanding.get("importance", "MEDIUM")


@dataclass
class ExecutionPlan:
    """Plan for executing a skill in context"""
    skill_id: str
    applicable_patterns: List[DecisionPattern]
    selected_sequences: List[ToolSequence]
    context: Dict[str, Any]
    estimated_duration_seconds: float = 0.0
    
    def get_critical_patterns(self) -> List[DecisionPattern]:
        """Get patterns that must succeed"""
        return [p for p in self.applicable_patterns if p.priority == "CRITICAL"]
    
    def get_blocking_patterns(self) -> List[DecisionPattern]:
        """Get patterns that block on failure"""
        return [p for p in self.applicable_patterns if p.priority in ["CRITICAL", "HIGH"]]


@dataclass
class ExecutionResult:
    """Result of skill execution"""
    skill_id: str
    success: bool
    can_proceed: bool
    patterns_executed: List[str]
    patterns_passed: List[str]
    patterns_failed: List[str]
    warnings: List[str]
    execution_time_seconds: float
    detailed_results: Dict[str, Any] = field(default_factory=dict)


class SkillEngine:
    """
    Universal skill interpretation and execution engine.
    
    This engine is project-agnostic and can be used by any agent to
    interpret and apply skills defined as knowledge artifacts.
    
    Usage:
        engine = SkillEngine(skills_dir="./agents/knowledge/skills")
        skill = engine.load_skill("preflight_validation")
        plan = engine.reason_about_application(skill, context)
        result = engine.execute_skill(skill, plan, state)
    """
    
    def __init__(self, skills_dir: str = "./agents/knowledge/skills"):
        """
        Initialize the skill engine.
        
        Args:
            skills_dir: Directory containing skill YAML files
        """
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def load_skill(self, skill_name: str) -> Skill:
        """
        Load and parse a skill knowledge artifact.
        
        Args:
            skill_name: Name of skill file (without .yaml extension)
            
        Returns:
            Parsed Skill object
            
        Raises:
            FileNotFoundError: If skill file doesn't exist
            ValueError: If skill YAML is invalid
        """
        skill_path = self.skills_dir / f"{skill_name}.yaml"
        
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")
        
        # Check cache
        if skill_name in self.loaded_skills:
            logger.debug(f"Using cached skill: {skill_name}")
            return self.loaded_skills[skill_name]
        
        try:
            with open(skill_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Parse metadata
            metadata = SkillMetadata(
                id=data['metadata']['id'],
                name=data['metadata']['name'],
                version=data['metadata']['version'],
                category=data['metadata']['category'],
                tags=data['metadata'].get('tags', []),
                created_at=data['metadata'].get('created_at', ''),
                updated_at=data['metadata'].get('updated_at', '')
            )
            
            # Parse decision patterns
            patterns = []
            for p in data.get('decision_patterns', []):
                patterns.append(DecisionPattern(
                    condition=p['condition'],
                    action=p['action'],
                    priority=p['priority'],
                    tools_required=p['tools_required'],
                    success_criteria=p['success_criteria'],
                    failure_handling=p['failure_handling'],
                    metadata=p.get('metadata', {})
                ))
            
            # Parse tool sequences
            sequences = []
            for seq in data.get('tool_sequences', []):
                steps = []
                for step in seq.get('steps', []):
                    steps.append(ToolStep(
                        tool=step['tool'],
                        action=step['action'],
                        inputs=step['inputs'],
                        outputs=step['outputs'],
                        validation=step['validation'],
                        on_failure=step.get('on_failure')
                    ))
                sequences.append(ToolSequence(
                    sequence_name=seq['sequence_name'],
                    description=seq.get('description', ''),
                    steps=steps
                ))
            
            # Create skill object
            skill = Skill(
                metadata=metadata,
                understanding=data.get('understanding', {}),
                knowledge_domains=data.get('knowledge_domains', []),
                decision_patterns=patterns,
                tool_sequences=sequences,
                learning_examples=data.get('learning_examples', []),
                performance_metrics=data.get('performance_metrics', {}),
                evolution=data.get('evolution', {})
            )
            
            # Cache the skill
            self.loaded_skills[skill_name] = skill
            logger.info(f"Loaded skill: {skill.metadata.name} v{skill.metadata.version}")
            
            return skill
            
        except Exception as e:
            raise ValueError(f"Failed to parse skill {skill_name}: {e}")
    
    def reason_about_application(
        self,
        skill: Skill,
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Analyze context and determine how to apply the skill.
        
        This is where the "reasoning" happens - the engine evaluates
        which decision patterns apply given the current context.
        
        Args:
            skill: The skill to apply
            context: Current execution context (environment, state, etc.)
            
        Returns:
            ExecutionPlan with applicable patterns and sequences
        """
        logger.info(f"Reasoning about skill application: {skill.metadata.name}")
        
        # Evaluate which patterns apply to current context
        applicable_patterns = []
        for pattern in skill.decision_patterns:
            if pattern.should_execute(context):
                applicable_patterns.append(pattern)
                logger.debug(f"Pattern applicable: {pattern.action} (priority: {pattern.priority})")
        
        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        applicable_patterns.sort(key=lambda p: priority_order.get(p.priority, 99))
        
        # Select relevant tool sequences
        # For now, include all sequences - in future, can be more selective
        selected_sequences = skill.tool_sequences
        
        # Estimate execution time based on historical metrics
        avg_time = skill.performance_metrics.get('avg_execution_time_seconds', 2.0)
        
        plan = ExecutionPlan(
            skill_id=skill.metadata.id,
            applicable_patterns=applicable_patterns,
            selected_sequences=selected_sequences,
            context=context,
            estimated_duration_seconds=avg_time
        )
        
        logger.info(f"Execution plan: {len(applicable_patterns)} patterns, "
                   f"{len(selected_sequences)} sequences")
        
        return plan
    
    def execute_skill(
        self,
        skill: Skill,
        plan: ExecutionPlan,
        state: DeploymentState,
        tool_executor: Optional[Any] = None
    ) -> Tuple[ExecutionResult, DeploymentState]:
        """
        Execute the skill according to the plan.
        
        Args:
            skill: The skill to execute
            plan: Execution plan from reason_about_application
            state: Current deployment state
            tool_executor: Optional custom tool executor
            
        Returns:
            Tuple of (ExecutionResult, updated_state)
        """
        start_time = datetime.now()
        
        state = add_log(
            state,
            "INFO",
            f"Executing skill: {skill.metadata.name}",
            "skill_execution"
        )
        
        patterns_executed = []
        patterns_passed = []
        patterns_failed = []
        warnings = []
        can_proceed = True
        
        # Execute each applicable pattern
        for pattern in plan.applicable_patterns:
            patterns_executed.append(pattern.action)
            
            state = add_log(
                state,
                "DEBUG",
                f"Evaluating: {pattern.action} (priority: {pattern.priority})",
                "skill_execution"
            )
            
            # Execute pattern (simplified - real implementation would invoke tools)
            # For now, we'll delegate to the original preflight validator
            # In a full implementation, this would use tool_executor
            success = self._execute_pattern(pattern, plan.context, state)
            
            if success:
                patterns_passed.append(pattern.action)
                state = add_log(
                    state,
                    "INFO",
                    f"✓ {pattern.action}",
                    "skill_execution"
                )
            else:
                patterns_failed.append(pattern.action)
                
                if pattern.priority == "CRITICAL":
                    can_proceed = False
                    state = add_log(
                        state,
                        "ERROR",
                        f"✗ {pattern.action} (BLOCKING)",
                        "skill_execution"
                    )
                    state = add_log(
                        state,
                        "INFO",
                        f"  → {pattern.failure_handling}",
                        "skill_execution"
                    )
                elif pattern.priority == "HIGH":
                    warnings.append(pattern.action)
                    state = add_log(
                        state,
                        "WARNING",
                        f"⚠ {pattern.action}",
                        "skill_execution"
                    )
                else:
                    warnings.append(pattern.action)
                    state = add_log(
                        state,
                        "INFO",
                        f"ℹ {pattern.action} (advisory)",
                        "skill_execution"
                    )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        result = ExecutionResult(
            skill_id=skill.metadata.id,
            success=len(patterns_failed) == 0,
            can_proceed=can_proceed,
            patterns_executed=patterns_executed,
            patterns_passed=patterns_passed,
            patterns_failed=patterns_failed,
            warnings=warnings,
            execution_time_seconds=elapsed
        )
        
        # Record execution for learning
        self._record_execution(skill, plan, result)
        
        summary = (f"Skill execution: {len(patterns_passed)}/{len(patterns_executed)} passed, "
                  f"{len(warnings)} warnings")
        state = add_log(state, "INFO", summary, "skill_execution")
        
        return result, state
    
    def _execute_pattern(
        self,
        pattern: DecisionPattern,
        context: Dict[str, Any],
        state: DeploymentState
    ) -> bool:
        """
        Execute a single decision pattern.
        
        In a full implementation, this would:
        1. Invoke required tools based on pattern.tools_required
        2. Evaluate success criteria
        3. Handle failures according to failure_handling
        
        For now, returns True (placeholder for integration with actual tool execution)
        """
        # Placeholder - real implementation would execute tools
        # and evaluate success criteria
        return True
    
    def _record_execution(
        self,
        skill: Skill,
        plan: ExecutionPlan,
        result: ExecutionResult
    ):
        """Record execution for learning purposes"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "skill_id": skill.metadata.id,
            "skill_version": skill.metadata.version,
            "context": plan.context,
            "result": {
                "success": result.success,
                "can_proceed": result.can_proceed,
                "execution_time": result.execution_time_seconds,
                "patterns_executed": len(result.patterns_executed),
                "patterns_passed": len(result.patterns_passed),
                "patterns_failed": len(result.patterns_failed)
            }
        }
        
        self.execution_history.append(execution_record)
        logger.debug(f"Recorded execution: {skill.metadata.name}")
    
    def get_skill_performance(self, skill_id: str) -> Dict[str, Any]:
        """Get performance metrics for a skill from execution history"""
        executions = [e for e in self.execution_history if e['skill_id'] == skill_id]
        
        if not executions:
            return {}
        
        total = len(executions)
        successful = sum(1 for e in executions if e['result']['success'])
        avg_time = sum(e['result']['execution_time'] for e in executions) / total
        
        return {
            "total_executions": total,
            "success_rate": successful / total,
            "avg_execution_time_seconds": avg_time,
            "last_executed": executions[-1]['timestamp']
        }