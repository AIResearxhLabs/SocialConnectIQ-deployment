"""
Agent Core Components

This package contains project-agnostic components that enable knowledge-based
skill systems for AI agents:

- SkillEngine: Universal skill interpretation and execution
- SkillLearner: Continuous improvement through learning
"""

from agents.core.skill_engine import (
    SkillEngine,
    Skill,
    SkillMetadata,
    DecisionPattern,
    ToolSequence,
    ExecutionPlan,
    ExecutionResult
)

from agents.core.skill_learner import (
    SkillLearner,
    ExecutionRecord,
    SkillInsight,
    SkillImprovement
)

__all__ = [
    # Engine components
    'SkillEngine',
    'Skill',
    'SkillMetadata',
    'DecisionPattern',
    'ToolSequence',
    'ExecutionPlan',
    'ExecutionResult',
    # Learner components
    'SkillLearner',
    'ExecutionRecord',
    'SkillInsight',
    'SkillImprovement',
]