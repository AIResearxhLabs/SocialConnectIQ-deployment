## Knowledge-Based Skills System: Usage Guide

This document demonstrates how to use the knowledge-based skills system where skills are declarative knowledge that agents reason about and apply, rather than imperative code they execute.

### Architecture Overview

```
agents/
├── core/                         # REUSABLE ACROSS ALL PROJECTS
│   ├── skill_engine.py          # Interprets and executes skills
│   ├── skill_learner.py         # Enables continuous improvement
│   └── __init__.py
│
├── knowledge/                    # PROJECT-SPECIFIC
│   ├── schemas/
│   │   └── skill_schema.yaml    # Skill definition standard
│   ├── skills/
│   │   └── preflight_validation.yaml  # Skill as knowledge
│   └── learning/
│       ├── execution_history.db  # Learning database
│       └── insights.json         # Discovered insights
```

### Basic Usage

#### 1. Load and Apply a Skill

```python
from agents.core import SkillEngine, SkillLearner
from agents.state import create_initial_state

# Initialize the engine (reusable across projects)
engine = SkillEngine(skills_dir="./agents/knowledge/skills")

# Initialize the learner for continuous improvement
learner = SkillLearner()

# Load a skill (parses YAML knowledge artifact)
skill = engine.load_skill("preflight_validation")

# Create execution context
context = {
    "environment": "local",
    "user_role": "developer",
    "config_loaded": True
}

# Reason about how to apply the skill
plan = engine.reason_about_application(skill, context)

# Execute the skill
state = create_initial_state(
    environment="local",
    user_email="developer@company.com",
    user_role="developer"
)

result, updated_state = engine.execute_skill(skill, plan, state)

# Record execution for learning
learner.record_execution(
    skill_id=skill.metadata.id,
    skill_version=skill.metadata.version,
    context=context,
    patterns_executed=result.patterns_executed,
    patterns_passed=result.patterns_passed,
    patterns_failed=result.patterns_failed,
    warnings=result.warnings,
    execution_time=result.execution_time_seconds,
    outcome="SUCCESS" if result.success else "FAILURE"
)

# Check if deployment can proceed
if result.can_proceed:
    print("✅ Pre-flight validation passed")
else:
    print("❌ Pre-flight validation failed - cannot proceed")
    print(f"Failed patterns: {result.patterns_failed}")
```

#### 2. Analyze and Learn from History

```python
# Analyze patterns over the last 30 days
insights = learner.analyze_patterns("skill-preflight-validation-v1", days=30)

for insight in insights:
    print(f"{insight.priority}: {insight.description}")
    print(f"  Suggested action: {insight.suggested_action}")
    print(f"  Confidence: {insight.confidence:.0%}")
    print()

# Get improvement suggestions
improvements = learner.suggest_improvements("skill-preflight-validation-v1")

for improvement in improvements:
    print(f"Improvement: {improvement.description}")
    print(f"  Expected benefit: {improvement.expected_benefit}")
    print(f"  Risk level: {improvement.risk_level}")
    if improvement.requires_approval:
        print(f"  ⚠️ Requires approval before applying")
    print()
```

#### 3. Evolve Skills Based on Learning

```python
from pathlib import Path

# Apply a low-risk improvement automatically
for improvement in improvements:
    if improvement.risk_level == "LOW" and not improvement.requires_approval:
        skill_path = Path("./agents/knowledge/skills/preflight_validation.yaml")
        success = learner.evolve_skill(
            skill_id=improvement.skill_id,
            improvement=improvement,
            skill_path=skill_path,
            auto_apply=True
        )
        if success:
            print(f"✅ Auto-applied improvement: {improvement.description}")

# High-risk improvements require manual approval
for improvement in improvements:
    if improvement.requires_approval:
        print(f"⚠️ Manual approval needed: {improvement.description}")
        # In a real system, this would trigger a review workflow
```

### Integration with Orchestrator

```python
# In agents/orchestrator.py

from agents.core import SkillEngine, SkillLearner

class DeploymentOrchestrator:
    def __init__(self, config_dir: str = "./config"):
        # ... existing initialization ...
        
        # Initialize knowledge-based skills system
        self.skill_engine = SkillEngine()
        self.skill_learner = SkillLearner()
    
    def _preflight_validation_node(self, state: DeploymentState) -> DeploymentState:
        """Run pre-flight validation using knowledge-based skill"""
        
        # Load the skill
        skill = self.skill_engine.load_skill("preflight_validation")
        
        # Build context from current state
        context = {
            "environment": state["environment"],
            "user_role": state["user_role"],
            "config": self.environments_config,
            "state_status": state["status"]
        }
        
        # Reason about application
        plan = self.skill_engine.reason_about_application(skill, context)
        
        # Execute the skill
        result, state = self.skill_engine.execute_skill(skill, plan, state)
        
        # Record for learning
        self.skill_learner.record_execution(
            skill_id=skill.metadata.id,
            skill_version=skill.metadata.version,
            context=context,
            patterns_executed=result.patterns_executed,
            patterns_passed=result.patterns_passed,
            patterns_failed=result.patterns_failed,
            warnings=result.warnings,
            execution_time=result.execution_time_seconds,
            outcome="SUCCESS" if result.success else "FAILURE"
        )
        
        # Update state based on result
        if not result.can_proceed:
            state["status"] = "failed"
            state["errors"].append("Pre-flight validation failed")
        
        # Store validation results
        state["validation_results"]["preflight"] = {
            "success": result.success,
            "can_proceed": result.can_proceed,
            "patterns_executed": result.patterns_executed,
            "patterns_passed": result.patterns_passed,
            "patterns_failed": result.patterns_failed,
            "warnings": result.warnings,
            "execution_time": result.execution_time_seconds
        }
        
        return state
```

### Creating New Skills

To create a new skill as knowledge (not code):

1. **Define the skill** using the schema:

```yaml
# agents/knowledge/skills/my_new_skill.yaml
metadata:
  id: "skill-my-new-skill-v1"
  name: "My New Skill"
  version: "1.0.0"
  category: "deployment_execution"
  tags: ["deployment", "docker"]

understanding:
  purpose: "What this skill accomplishes"
  when_to_use: "When to apply this skill"
  prerequisites:
    - "What must be true before applying"
  importance: "HIGH"

decision_patterns:
  - condition: "environment == 'local'"
    action: "perform_local_deployment"
    priority: "CRITICAL"
    tools_required: ["execute_command"]
    success_criteria: "Deployment completes without errors"
    failure_handling: "BLOCK: Check logs and remediate"

# ... (see skill_schema.yaml for complete structure)
```

2. **Load and use** the skill:

```python
skill = engine.load_skill("my_new_skill")
plan = engine.reason_about_application(skill, context)
result, state = engine.execute_skill(skill, plan, state)
```

### Benefits of Knowledge-Based Skills

1. **Language Agnostic**: Skills work across different projects and languages
2. **Transparent Reasoning**: Clear why agents make decisions
3. **Continuous Learning**: Skills improve automatically from outcomes
4. **Easy Sharing**: Skills can be shared as YAML files
5. **Version Control**: Skill evolution is tracked and reversible
6. **Explainable**: Each decision has clear success criteria and rationale

### Comparison: Code vs Knowledge

**Old Approach (Code-based)**:
```python
# Rigid, imperative execution
validator = PreFlightValidator(env, config)
result = validator.validate_all(state)  # Executes predefined checks
```

**New Approach (Knowledge-based)**:
```python
# Flexible, reasoning-based application
skill = engine.load_skill("preflight_validation")
plan = engine.reason_about_application(skill, context)  # Adapts to context
result, state = engine.execute_skill(skill, plan, state)  # Applies intelligently
```

### Next Steps

1. Gradually migrate existing skills from code to knowledge artifacts
2. Enable learning on production systems to gather real-world data
3. Review and apply suggested improvements monthly
4. Share successful skills across projects
5. Contribute improved skills back to the knowledge base