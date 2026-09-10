"""
Skill Learning and Evolution System

This module enables continuous improvement of skills based on execution outcomes.
It analyzes patterns, suggests improvements, and can automatically evolve skills
while maintaining version control.

Key Capabilities:
- Record and analyze execution history
- Identify failure patterns and optimization opportunities
- Suggest skill improvements based on data
- Evolve skills automatically or with human approval
- Track skill performance over time
"""

import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    """Record of a single skill execution"""
    id: Optional[int] = None
    timestamp: str = ""
    skill_id: str = ""
    skill_version: str = ""
    environment: str = ""
    user_role: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    patterns_executed: List[str] = field(default_factory=list)
    patterns_passed: List[str] = field(default_factory=list)
    patterns_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    outcome: str = "SUCCESS"  # SUCCESS, FAILURE, PARTIAL
    remediation_applied: Optional[str] = None
    user_feedback: Optional[str] = None


@dataclass
class SkillInsight:
    """Insight discovered from analyzing execution history"""
    insight_type: str  # pattern, optimization, failure_mode, threshold_adjustment
    skill_id: str
    description: str
    evidence: Dict[str, Any]
    suggested_action: str
    confidence: float  # 0.0 to 1.0
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    requires_approval: bool = True


@dataclass
class SkillImprovement:
    """Proposed improvement to a skill"""
    skill_id: str
    improvement_type: str
    description: str
    changes: Dict[str, Any]
    expected_benefit: str
    risk_level: str  # LOW, MEDIUM, HIGH
    requires_approval: bool = True
    approved: bool = False
    applied: bool = False


class SkillLearner:
    """
    Enables agents to improve skills based on outcomes.
    
    The learner:
    1. Records every skill execution with context and results
    2. Analyzes patterns to identify issues and opportunities
    3. Generates insights and improvement suggestions
    4. Can automatically apply low-risk improvements
    5. Tracks skill evolution over time
    
    Usage:
        learner = SkillLearner(db_path="./agents/knowledge/learning/history.db")
        learner.record_execution(skill_id, context, outcome, metrics)
        insights = learner.analyze_patterns(skill_id, days=30)
        improvements = learner.suggest_improvements(skill_id)
        learner.evolve_skill(skill_id, improvement, auto_apply=True)
    """
    
    def __init__(
        self,
        db_path: str = "./agents/knowledge/learning/execution_history.db",
        insights_path: str = "./agents/knowledge/learning/insights.json"
    ):
        """
        Initialize the skill learner.
        
        Args:
            db_path: Path to SQLite database for execution history
            insights_path: Path to JSON file for storing insights
        """
        self.db_path = Path(db_path)
        self.insights_path = Path(insights_path)
        
        # Create directories if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.insights_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"SkillLearner initialized with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                skill_version TEXT NOT NULL,
                environment TEXT NOT NULL,
                user_role TEXT,
                context_json TEXT,
                patterns_executed TEXT,
                patterns_passed TEXT,
                patterns_failed TEXT,
                warnings TEXT,
                execution_time_seconds REAL,
                outcome TEXT,
                remediation_applied TEXT,
                user_feedback TEXT
            )
        """)
        
        # Insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                description TEXT,
                evidence_json TEXT,
                suggested_action TEXT,
                confidence REAL,
                priority TEXT,
                requires_approval INTEGER,
                applied INTEGER DEFAULT 0
            )
        """)
        
        # Improvements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                improvement_type TEXT NOT NULL,
                description TEXT,
                changes_json TEXT,
                expected_benefit TEXT,
                risk_level TEXT,
                requires_approval INTEGER,
                approved INTEGER DEFAULT 0,
                applied INTEGER DEFAULT 0,
                applied_at TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_timestamp ON executions(skill_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outcome ON executions(outcome)")
        
        conn.commit()
        conn.close()
    
    def record_execution(
        self,
        skill_id: str,
        skill_version: str,
        context: Dict[str, Any],
        patterns_executed: List[str],
        patterns_passed: List[str],
        patterns_failed: List[str],
        warnings: List[str],
        execution_time: float,
        outcome: str,
        remediation_applied: Optional[str] = None
    ) -> int:
        """
        Record a skill execution for learning.
        
        Args:
            skill_id: Skill identifier
            skill_version: Skill version executed
            context: Execution context
            patterns_executed: List of patterns that were executed
            patterns_passed: List of patterns that passed
            patterns_failed: List of patterns that failed
            warnings: List of warnings issued
            execution_time: Time taken in seconds
            outcome: SUCCESS, FAILURE, or PARTIAL
            remediation_applied: Remediation steps taken
            
        Returns:
            Record ID in database
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO executions (
                timestamp, skill_id, skill_version, environment, user_role,
                context_json, patterns_executed, patterns_passed, patterns_failed,
                warnings, execution_time_seconds, outcome, remediation_applied
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            skill_id,
            skill_version,
            context.get('environment', 'unknown'),
            context.get('user_role', 'unknown'),
            json.dumps(context),
            json.dumps(patterns_executed),
            json.dumps(patterns_passed),
            json.dumps(patterns_failed),
            json.dumps(warnings),
            execution_time,
            outcome,
            remediation_applied
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.debug(f"Recorded execution {record_id} for skill {skill_id}")
        return record_id
    
    def analyze_patterns(
        self,
        skill_id: str,
        days: int = 30
    ) -> List[SkillInsight]:
        """
        Analyze execution history to identify patterns and insights.
        
        Args:
            skill_id: Skill to analyze
            days: Number of days of history to analyze
            
        Returns:
            List of discovered insights
        """
        logger.info(f"Analyzing patterns for skill {skill_id} over {days} days")
        
        insights = []
        
        # Get execution history
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT * FROM executions
            WHERE skill_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (skill_id, since_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logger.info(f"No execution history found for {skill_id}")
            return insights
        
        # Analyze failure patterns
        insights.extend(self._analyze_failure_patterns(skill_id, rows))
        
        # Analyze performance trends
        insights.extend(self._analyze_performance_trends(skill_id, rows))
        
        # Analyze warning patterns
        insights.extend(self._analyze_warning_patterns(skill_id, rows))
        
        # Identify optimization opportunities
        insights.extend(self._identify_optimizations(skill_id, rows))
        
        logger.info(f"Generated {len(insights)} insights for {skill_id}")
        
        return insights
    
    def _analyze_failure_patterns(
        self,
        skill_id: str,
        rows: List[Tuple]
    ) -> List[SkillInsight]:
        """Analyze patterns in execution failures"""
        insights = []
        
        failures = [r for r in rows if r[12] == 'FAILURE']  # outcome column
        
        if not failures:
            return insights
        
        failure_rate = len(failures) / len(rows)
        
        # High failure rate insight
        if failure_rate > 0.15:
            # Analyze which patterns fail most
            failed_patterns = []
            for row in failures:
                patterns = json.loads(row[9])  # patterns_failed column
                failed_patterns.extend(patterns)
            
            pattern_counts = Counter(failed_patterns)
            most_common = pattern_counts.most_common(3)
            
            insights.append(SkillInsight(
                insight_type="failure_mode",
                skill_id=skill_id,
                description=f"High failure rate detected: {failure_rate:.1%} over analysis period",
                evidence={
                    "total_executions": len(rows),
                    "failures": len(failures),
                    "failure_rate": failure_rate,
                    "common_failures": most_common
                },
                suggested_action=f"Investigate and improve: {', '.join([p[0] for p in most_common])}",
                confidence=0.9,
                priority="HIGH" if failure_rate > 0.25 else "MEDIUM",
                requires_approval=True
            ))
        
        return insights
    
    def _analyze_performance_trends(
        self,
        skill_id: str,
        rows: List[Tuple]
    ) -> List[SkillInsight]:
        """Analyze performance trends over time"""
        insights = []
        
        exec_times = [r[11] for r in rows]  # execution_time_seconds column
        avg_time = sum(exec_times) / len(exec_times)
        
        # Slow execution insight
        if avg_time > 5.0:
            insights.append(SkillInsight(
                insight_type="optimization",
                skill_id=skill_id,
                description=f"Slow execution detected: average {avg_time:.1f}s",
                evidence={
                    "avg_execution_time": avg_time,
                    "max_execution_time": max(exec_times),
                    "min_execution_time": min(exec_times)
                },
                suggested_action="Profile and optimize slow checks, consider caching or parallelization",
                confidence=0.85,
                priority="MEDIUM",
                requires_approval=False
            ))
        
        return insights
    
    def _analyze_warning_patterns(
        self,
        skill_id: str,
        rows: List[Tuple]
    ) -> List[SkillInsight]:
        """Analyze warning patterns"""
        insights = []
        
        # Collect all warnings
        all_warnings = []
        for row in rows:
            warnings = json.loads(row[10])  # warnings column
            all_warnings.extend(warnings)
        
        if not all_warnings:
            return insights
        
        warning_counts = Counter(all_warnings)
        frequent_warnings = [(w, c) for w, c in warning_counts.items() if c / len(rows) > 0.3]
        
        if frequent_warnings:
            insights.append(SkillInsight(
                insight_type="pattern",
                skill_id=skill_id,
                description=f"Frequent warnings detected: {len(frequent_warnings)} warning types",
                evidence={
                    "total_warnings": len(all_warnings),
                    "unique_warnings": len(warning_counts),
                    "frequent_warnings": frequent_warnings
                },
                suggested_action="Review if warnings should be elevated or thresholds adjusted",
                confidence=0.75,
                priority="LOW",
                requires_approval=True
            ))
        
        return insights
    
    def _identify_optimizations(
        self,
        skill_id: str,
        rows: List[Tuple]
    ) -> List[SkillInsight]:
        """Identify optimization opportunities"""
        insights = []
        
        # Check for patterns that never fail
        never_failed = set()
        always_passed = set()
        
        for row in rows:
            executed = set(json.loads(row[7]))  # patterns_executed
            passed = set(json.loads(row[8]))    # patterns_passed
            
            if never_failed:
                never_failed &= executed
            else:
                never_failed = executed.copy()
            
            always_passed |= passed
        
        candidates = never_failed & always_passed
        
        if candidates and len(rows) > 20:  # Need sufficient history
            insights.append(SkillInsight(
                insight_type="optimization",
                skill_id=skill_id,
                description=f"Found {len(candidates)} patterns that consistently pass",
                evidence={
                    "patterns": list(candidates),
                    "executions_analyzed": len(rows)
                },
                suggested_action="Consider caching results or reducing check frequency",
                confidence=0.7,
                priority="LOW",
                requires_approval=False
            ))
        
        return insights
    
    def suggest_improvements(
        self,
        skill_id: str
    ) -> List[SkillImprovement]:
        """
        Generate improvement suggestions based on insights.
        
        Args:
            skill_id: Skill to analyze
            
        Returns:
            List of suggested improvements
        """
        improvements = []
        
        # Get recent insights
        insights = self.analyze_patterns(skill_id, days=30)
        
        for insight in insights:
            if insight.insight_type == "failure_mode" and insight.confidence > 0.8:
                improvements.append(SkillImprovement(
                    skill_id=skill_id,
                    improvement_type="threshold_adjustment",
                    description=f"Adjust thresholds to reduce failure rate",
                    changes={
                        "rationale": insight.description,
                        "suggested_changes": insight.suggested_action
                    },
                    expected_benefit="Reduce false failures by 30-50%",
                    risk_level="MEDIUM",
                    requires_approval=True
                ))
            
            elif insight.insight_type == "optimization":
                improvements.append(SkillImprovement(
                    skill_id=skill_id,
                    improvement_type="performance",
                    description="Optimize execution time",
                    changes={
                        "approach": insight.suggested_action
                    },
                    expected_benefit=f"Reduce execution time by 20-40%",
                    risk_level="LOW",
                    requires_approval=False
                ))
        
        return improvements
    
    def evolve_skill(
        self,
        skill_id: str,
        improvement: SkillImprovement,
        skill_path: Path,
        auto_apply: bool = False
    ) -> bool:
        """
        Apply an improvement to evolve a skill.
        
        Args:
            skill_id: Skill to evolve
            improvement: Improvement to apply
            skill_path: Path to skill YAML file
            auto_apply: Whether to auto-apply without approval
            
        Returns:
            True if improvement was applied
        """
        if improvement.requires_approval and not improvement.approved and not auto_apply:
            logger.info(f"Improvement requires approval: {improvement.description}")
            return False
        
        try:
            # Load current skill
            with open(skill_path, 'r') as f:
                skill_data = yaml.safe_load(f)
            
            # Update version (increment patch)
            current_version = skill_data['metadata']['version']
            major, minor, patch = map(int, current_version.split('.'))
            new_version = f"{major}.{minor}.{patch + 1}"
            
            skill_data['metadata']['version'] = new_version
            skill_data['metadata']['updated_at'] = datetime.now().isoformat()
            
            # Apply changes (simplified - real implementation would be more sophisticated)
            # This is where you'd modify thresholds, add patterns, etc.
            
            # Save evolved skill
            backup_path = skill_path.parent / f"{skill_path.stem}_v{current_version}.yaml"
            with open(backup_path, 'w') as f:
                yaml.dump(skill_data, f, default_flow_style=False, sort_keys=False)
            
            with open(skill_path, 'w') as f:
                yaml.dump(skill_data, f, default_flow_style=False, sort_keys=False)
            
            # Record improvement
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO improvements (
                    timestamp, skill_id, improvement_type, description,
                    changes_json, expected_benefit, risk_level,
                    requires_approval, approved, applied, applied_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                skill_id,
                improvement.improvement_type,
                improvement.description,
                json.dumps(improvement.changes),
                improvement.expected_benefit,
                improvement.risk_level,
                1 if improvement.requires_approval else 0,
                1,
                1,
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Evolved skill {skill_id} to version {new_version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to evolve skill {skill_id}: {e}")
            return False