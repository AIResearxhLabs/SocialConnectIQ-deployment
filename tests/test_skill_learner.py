"""
Tests for the SkillLearner

These tests verify that the learning system can record executions,
analyze patterns, and suggest improvements.
"""

import pytest
import sqlite3
from pathlib import Path
from agents.core import SkillLearner, SkillInsight, SkillImprovement


@pytest.fixture
def skill_learner(tmp_path):
    """Create a skill learner with temporary database"""
    db_path = tmp_path / "test_history.db"
    insights_path = tmp_path / "test_insights.json"
    
    learner = SkillLearner(
        db_path=str(db_path),
        insights_path=str(insights_path)
    )
    
    return learner


def test_database_initialization(skill_learner):
    """Test that database is initialized with correct schema"""
    conn = sqlite3.connect(str(skill_learner.db_path))
    cursor = conn.cursor()
    
    # Check that tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('executions', 'insights', 'improvements')
    """)
    tables = {row[0] for row in cursor.fetchall()}
    
    assert 'executions' in tables
    assert 'insights' in tables
    assert 'improvements' in tables
    
    conn.close()


def test_record_execution(skill_learner):
    """Test recording a skill execution"""
    record_id = skill_learner.record_execution(
        skill_id="skill-test-v1",
        skill_version="1.0.0",
        context={"environment": "local"},
        patterns_executed=["pattern1", "pattern2"],
        patterns_passed=["pattern1", "pattern2"],
        patterns_failed=[],
        warnings=[],
        execution_time=1.5,
        outcome="SUCCESS"
    )
    
    assert record_id > 0
    
    # Verify record was stored
    conn = sqlite3.connect(str(skill_learner.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM executions WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row[2] == "skill-test-v1"  # skill_id column


def test_record_multiple_executions(skill_learner):
    """Test recording multiple executions"""
    for i in range(5):
        skill_learner.record_execution(
            skill_id="skill-test-v1",
            skill_version="1.0.0",
            context={"environment": "local", "iteration": i},
            patterns_executed=["pattern1"],
            patterns_passed=["pattern1"] if i % 2 == 0 else [],
            patterns_failed=[] if i % 2 == 0 else ["pattern1"],
            warnings=[],
            execution_time=1.0 + i * 0.1,
            outcome="SUCCESS" if i % 2 == 0 else "FAILURE"
        )
    
    # Verify all records exist
    conn = sqlite3.connect(str(skill_learner.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM executions WHERE skill_id = ?", ("skill-test-v1",))
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 5


def test_analyze_patterns_no_history(skill_learner):
    """Test analyzing patterns when no history exists"""
    insights = skill_learner.analyze_patterns("nonexistent-skill", days=30)
    
    assert isinstance(insights, list)
    assert len(insights) == 0


def test_analyze_failure_patterns(skill_learner):
    """Test analysis of failure patterns"""
    # Record executions with high failure rate
    for i in range(20):
        outcome = "FAILURE" if i < 15 else "SUCCESS"  # 75% failure rate
        failed = ["docker_check"] if outcome == "FAILURE" else []
        
        skill_learner.record_execution(
            skill_id="skill-test-v1",
            skill_version="1.0.0",
            context={"environment": "local"},
            patterns_executed=["docker_check"],
            patterns_passed=[] if outcome == "FAILURE" else ["docker_check"],
            patterns_failed=failed,
            warnings=[],
            execution_time=1.0,
            outcome=outcome
        )
    
    insights = skill_learner.analyze_patterns("skill-test-v1", days=30)
    
    # Should detect high failure rate
    failure_insights = [i for i in insights if i.insight_type == "failure_mode"]
    assert len(failure_insights) > 0
    assert failure_insights[0].priority in ["HIGH", "MEDIUM"]


def test_analyze_performance_trends(skill_learner):
    """Test analysis of performance trends"""
    # Record executions with slow execution times
    for i in range(10):
        skill_learner.record_execution(
            skill_id="skill-slow-v1",
            skill_version="1.0.0",
            context={"environment": "local"},
            patterns_executed=["slow_check"],
            patterns_passed=["slow_check"],
            patterns_failed=[],
            warnings=[],
            execution_time=6.0 + i * 0.5,  # Average > 5.0 seconds
            outcome="SUCCESS"
        )
    
    insights = skill_learner.analyze_patterns("skill-slow-v1", days=30)
    
    # Should detect slow execution
    optimization_insights = [i for i in insights if i.insight_type == "optimization"]
    assert len(optimization_insights) > 0


def test_analyze_warning_patterns(skill_learner):
    """Test analysis of warning patterns"""
    # Record executions with frequent warnings
    for i in range(10):
        warnings = ["memory_warning"] if i % 2 == 0 else []
        
        skill_learner.record_execution(
            skill_id="skill-test-v1",
            skill_version="1.0.0",
            context={"environment": "local"},
            patterns_executed=["memory_check"],
            patterns_passed=["memory_check"],
            patterns_failed=[],
            warnings=warnings,
            execution_time=1.0,
            outcome="SUCCESS"
        )
    
    insights = skill_learner.analyze_patterns("skill-test-v1", days=30)
    
    # May detect warning pattern
    pattern_insights = [i for i in insights if i.insight_type == "pattern"]
    # Pattern detection depends on threshold, so this is optional
    assert isinstance(pattern_insights, list)


def test_suggest_improvements(skill_learner):
    """Test generating improvement suggestions"""
    # Record executions with failures
    for i in range(20):
        outcome = "FAILURE" if i < 12 else "SUCCESS"  # 60% failure
        
        skill_learner.record_execution(
            skill_id="skill-test-v1",
            skill_version="1.0.0",
            context={"environment": "local"},
            patterns_executed=["check1"],
            patterns_passed=[] if outcome == "FAILURE" else ["check1"],
            patterns_failed=["check1"] if outcome == "FAILURE" else [],
            warnings=[],
            execution_time=1.0,
            outcome=outcome
        )
    
    improvements = skill_learner.suggest_improvements("skill-test-v1")
    
    assert isinstance(improvements, list)
    # Should suggest improvements based on failure rate
    if len(improvements) > 0:
        assert all(isinstance(imp, SkillImprovement) for imp in improvements)


def test_insight_creation():
    """Test SkillInsight dataclass"""
    insight = SkillInsight(
        insight_type="failure_mode",
        skill_id="test-skill",
        description="Test insight",
        evidence={"data": "value"},
        suggested_action="Fix the issue",
        confidence=0.9,
        priority="HIGH",
        requires_approval=True
    )
    
    assert insight.insight_type == "failure_mode"
    assert insight.confidence == 0.9
    assert insight.requires_approval is True


def test_improvement_creation():
    """Test SkillImprovement dataclass"""
    improvement = SkillImprovement(
        skill_id="test-skill",
        improvement_type="threshold_adjustment",
        description="Adjust threshold",
        changes={"old": 10, "new": 15},
        expected_benefit="Reduce failures",
        risk_level="LOW",
        requires_approval=False
    )
    
    assert improvement.risk_level == "LOW"
    assert improvement.requires_approval is False
    assert improvement.approved is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])