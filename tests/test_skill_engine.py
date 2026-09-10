"""
Tests for the SkillEngine

These tests verify that the skill engine can correctly load, reason about,
and execute skills defined as knowledge artifacts.
"""

import pytest
import yaml
from pathlib import Path
from agents.core import SkillEngine, Skill, ExecutionPlan, ExecutionResult
from agents.state import create_initial_state


@pytest.fixture
def skill_engine(tmp_path):
    """Create a skill engine with temporary skills directory"""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    
    # Create a test skill
    test_skill = {
        "metadata": {
            "id": "skill-test-v1",
            "name": "Test Skill",
            "version": "1.0.0",
            "category": "testing",
            "tags": ["test"]
        },
        "understanding": {
            "purpose": "Test skill for unit tests",
            "when_to_use": "During testing",
            "importance": "LOW"
        },
        "knowledge_domains": [],
        "decision_patterns": [
            {
                "condition": "always",
                "action": "test_action",
                "priority": "HIGH",
                "tools_required": ["execute_command"],
                "success_criteria": "Action completes",
                "failure_handling": "WARN"
            },
            {
                "condition": "environment == 'production'",
                "action": "production_action",
                "priority": "CRITICAL",
                "tools_required": [],
                "success_criteria": "Production check passes",
                "failure_handling": "BLOCK"
            }
        ],
        "tool_sequences": [
            {
                "sequence_name": "test_sequence",
                "description": "Test sequence",
                "steps": [
                    {
                        "tool": "execute_command",
                        "action": "test",
                        "inputs": {"command": "echo test"},
                        "outputs": ["result"],
                        "validation": "output contains 'test'"
                    }
                ]
            }
        ],
        "learning_examples": [],
        "performance_metrics": {
            "success_rate": 0.95,
            "avg_execution_time_seconds": 1.0
        },
        "evolution": {
            "learning_enabled": True
        }
    }
    
    skill_path = skills_dir / "test_skill.yaml"
    with open(skill_path, 'w') as f:
        yaml.dump(test_skill, f)
    
    return SkillEngine(skills_dir=str(skills_dir))


def test_load_skill(skill_engine):
    """Test loading a skill from YAML"""
    skill = skill_engine.load_skill("test_skill")
    
    assert skill.metadata.id == "skill-test-v1"
    assert skill.metadata.name == "Test Skill"
    assert skill.metadata.version == "1.0.0"
    assert len(skill.decision_patterns) == 2
    assert len(skill.tool_sequences) == 1


def test_load_skill_caching(skill_engine):
    """Test that skills are cached after first load"""
    skill1 = skill_engine.load_skill("test_skill")
    skill2 = skill_engine.load_skill("test_skill")
    
    assert skill1 is skill2  # Same object due to caching


def test_load_nonexistent_skill(skill_engine):
    """Test loading a skill that doesn't exist"""
    with pytest.raises(FileNotFoundError):
        skill_engine.load_skill("nonexistent_skill")


def test_reason_about_application(skill_engine):
    """Test reasoning about skill application"""
    skill = skill_engine.load_skill("test_skill")
    
    context = {
        "environment": "local",
        "user_role": "developer"
    }
    
    plan = skill_engine.reason_about_application(skill, context)
    
    assert isinstance(plan, ExecutionPlan)
    assert plan.skill_id == "skill-test-v1"
    # Should include the "always" pattern but not the production one
    assert len(plan.applicable_patterns) == 1
    assert plan.applicable_patterns[0].action == "test_action"


def test_reason_about_application_production(skill_engine):
    """Test reasoning for production environment"""
    skill = skill_engine.load_skill("test_skill")
    
    context = {
        "environment": "production",
        "user_role": "prod-ops"
    }
    
    plan = skill_engine.reason_about_application(skill, context)
    
    # Should include both "always" and production patterns
    assert len(plan.applicable_patterns) == 2
    actions = [p.action for p in plan.applicable_patterns]
    assert "test_action" in actions
    assert "production_action" in actions


def test_reason_prioritizes_critical(skill_engine):
    """Test that reasoning prioritizes critical patterns"""
    skill = skill_engine.load_skill("test_skill")
    
    context = {"environment": "production"}
    plan = skill_engine.reason_about_application(skill, context)
    
    # Critical pattern should come first
    assert plan.applicable_patterns[0].priority == "CRITICAL"


def test_execute_skill(skill_engine):
    """Test skill execution"""
    skill = skill_engine.load_skill("test_skill")
    context = {"environment": "local"}
    plan = skill_engine.reason_about_application(skill, context)
    
    state = create_initial_state(
        environment="local",
        user_email="test@example.com",
        user_role="developer"
    )
    
    result, updated_state = skill_engine.execute_skill(skill, plan, state)
    
    assert isinstance(result, ExecutionResult)
    assert result.skill_id == "skill-test-v1"
    assert len(result.patterns_executed) > 0
    assert result.execution_time_seconds >= 0


def test_get_skill_performance(skill_engine):
    """Test retrieving skill performance metrics"""
    skill = skill_engine.load_skill("test_skill")
    context = {"environment": "local"}
    plan = skill_engine.reason_about_application(skill, context)
    
    state = create_initial_state(
        environment="local",
        user_email="test@example.com",
        user_role="developer"
    )
    
    # Execute the skill
    result, _ = skill_engine.execute_skill(skill, plan, state)
    
    # Get performance metrics
    performance = skill_engine.get_skill_performance("skill-test-v1")
    
    assert "total_executions" in performance
    assert "success_rate" in performance
    assert performance["total_executions"] == 1


def test_execution_plan_methods():
    """Test ExecutionPlan helper methods"""
    from agents.core.skill_engine import DecisionPattern
    
    patterns = [
        DecisionPattern(
            condition="always",
            action="critical_action",
            priority="CRITICAL",
            tools_required=[],
            success_criteria="",
            failure_handling=""
        ),
        DecisionPattern(
            condition="always",
            action="high_action",
            priority="HIGH",
            tools_required=[],
            success_criteria="",
            failure_handling=""
        ),
        DecisionPattern(
            condition="always",
            action="low_action",
            priority="LOW",
            tools_required=[],
            success_criteria="",
            failure_handling=""
        )
    ]
    
    plan = ExecutionPlan(
        skill_id="test",
        applicable_patterns=patterns,
        selected_sequences=[],
        context={}
    )
    
    critical = plan.get_critical_patterns()
    assert len(critical) == 1
    assert critical[0].action == "critical_action"
    
    blocking = plan.get_blocking_patterns()
    assert len(blocking) == 2
    actions = [p.action for p in blocking]
    assert "critical_action" in actions
    assert "high_action" in actions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])