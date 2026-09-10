# Knowledge-Based Skills System

A revolutionary approach to AI agent capabilities where skills are represented as declarative knowledge that agents **reason about and apply**, rather than imperative code they blindly execute.

## Philosophy

Traditional approach (code):
```python
# Agent executes predefined logic
validator.validate_all()  # Rigid, no reasoning
```

Knowledge-based approach:
```yaml
# Agent understands and reasons
understanding:
  purpose: "Verify prerequisites"
  when_to_use: "Before deployment"

decision_patterns:
  - condition: "environment == 'production'"
    action: "validate_extra_checks"
    # Agent evaluates and decides
```

## Architecture

```
agents/knowledge/
├── schemas/                    # Skill definition standards
│   └── skill_schema.yaml      # Universal skill format
│
├── skills/                     # Skill knowledge artifacts
│   ├── preflight_validation.yaml
│   ├── docker_deployment.yaml
│   └── health_validation.yaml
│
└── learning/                   # Continuous improvement
    ├── execution_history.db   # SQLite: execution records
    └── insights.json          # Discovered patterns
```

## Key Components

### 1. Skill Artifacts (YAML)

Skills as declarative knowledge:
- **Understanding**: Why and when to use
- **Decision Patterns**: Conditional logic
- **Tool Sequences**: How to execute
- **Learning Examples**: Historical outcomes
- **Evolution Rules**: How to improve

### 2. SkillEngine (Universal)

Project-agnostic engine that:
- **Loads** YAML skill definitions
- **Reasons** about applicability
- **Executes** with context awareness
- **Records** for learning

### 3. SkillLearner (Adaptive)

Continuous improvement system:
- **Analyzes** execution patterns
- **Identifies** optimization opportunities
- **Suggests** improvements
- **Evolves** skills automatically

## Usage

### Basic Usage

```python
from agents.core import SkillEngine, SkillLearner

# Initialize
engine = SkillEngine()
learner = SkillLearner()

# Load skill
skill = engine.load_skill("preflight_validation")

# Reason about application
context = {"environment": "local", "user_role": "developer"}
plan = engine.reason_about_application(skill, context)

# Execute with reasoning
result, state = engine.execute_skill(skill, plan, state)

# Learn from outcome
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
```

### Continuous Learning

```python
# Analyze patterns (monthly)
insights = learner.analyze_patterns("skill-preflight-validation-v1", days=30)

for insight in insights:
    if insight.priority == "HIGH":
        print(f"⚠️  {insight.description}")
        print(f"   → {insight.suggested_action}")

# Get improvement suggestions
improvements = learner.suggest_improvements("skill-preflight-validation-v1")

# Auto-apply low-risk improvements
for improvement in improvements:
    if improvement.risk_level == "LOW":
        learner.evolve_skill(
            skill_id=improvement.skill_id,
            improvement=improvement,
            skill_path=Path("./agents/knowledge/skills/preflight_validation.yaml"),
            auto_apply=True
        )
```

## Creating New Skills

1. **Define the skill** (see `schemas/skill_schema.yaml` for complete structure):

```yaml
metadata:
  id: "skill-my-new-skill-v1"
  name: "My New Skill"
  version: "1.0.0"
  category: "deployment_execution"

understanding:
  purpose: "What this skill does"
  when_to_use: "When to apply it"
  importance: "CRITICAL"

decision_patterns:
  - condition: "environment == 'production'"
    action: "extra_production_checks"
    priority: "CRITICAL"
    tools_required: ["execute_command"]
    success_criteria: "All checks pass"
    failure_handling: "BLOCK: Cannot proceed"

tool_sequences:
  - sequence_name: "production_validation"
    steps:
      - tool: "execute_command"
        action: "verify_credentials"
        inputs:
          command: "gcloud auth list"
        outputs: ["accounts"]
        validation: "Active account present"

learning_examples:
  - scenario: "Missing credentials in production"
    context:
      environment: "production"
    actions_taken:
      - "Detected missing auth"
      - "Prompted user to authenticate"
    outcome: "SUCCESS"
    insights: "Pre-auth checks prevent deployment failures"

performance_metrics:
  success_rate: 0.98
  avg_execution_time_seconds: 1.5

evolution:
  learning_enabled: true
  feedback_loops:
    - "Track credential failures"
    - "Monitor auth patterns"
```

2. **Save** to `agents/knowledge/skills/my_new_skill.yaml`

3. **Use** in your code:

```python
skill = engine.load_skill("my_new_skill")
plan = engine.reason_about_application(skill, context)
result, state = engine.execute_skill(skill, plan, state)
```

## Benefits

| Aspect | Code-Based | Knowledge-Based |
|--------|-----------|-----------------|
| **Adaptability** | Fixed logic | Reasons about context |
| **Learning** | Manual updates | Automatic improvement |
| **Sharing** | Language-specific | Universal YAML |
| **Transparency** | Hidden in code | Explicit reasoning |
| **Evolution** | Requires developer | Self-improving |
| **Portability** | Project-locked | Cross-project reuse |

## Examples

### Example 1: Environment-Aware Validation

```yaml
# Skill adapts checks based on environment
decision_patterns:
  - condition: "environment == 'local'"
    priority: "HIGH"
    action: "check_docker_desktop"
    
  - condition: "environment == 'production'"
    priority: "CRITICAL"
    action: "verify_cloud_credentials"
```

The agent **reasons**: "In local environment, check Docker Desktop. In production, verify cloud credentials instead."

### Example 2: Failure Learning

```yaml
# Skill learns from failures
learning_examples:
  - scenario: "Port conflict detected"
    outcome: "SUCCESS"
    remediation_applied: "Stopped conflicting service"
    insights: "Most conflicts are user's own sessions - offer to stop automatically"
```

After 20+ similar cases, the skill **evolves** to auto-suggest stopping the conflicting process.

### Example 3: Performance Optimization

```yaml
# Skill optimizes itself
performance_metrics:
  avg_execution_time_seconds: 5.2

evolution:
  adaptation_rules:
    - condition: "execution_time > 5.0 consistently"
      action: "Parallelize independent checks"
      requires_approval: false
```

The skill **learns** it's slow and automatically adds parallelization.

## Documentation

- 📖 [Skill Schema Reference](schemas/skill_schema.yaml)
- 📘 [Usage Examples](USAGE_EXAMPLE.md)
- 📗 [Migration Guide](../../docs/KNOWLEDGE_SKILLS_MIGRATION.md)
- 📕 [SkillEngine API](../core/skill_engine.py)
- 📙 [SkillLearner API](../core/skill_learner.py)

## Testing

```bash
# Run skill engine tests
pytest tests/test_skill_engine.py -v

# Run skill learner tests
pytest tests/test_skill_learner.py -v

# Run all knowledge system tests
pytest tests/test_skill*.py -v
```

## Future Enhancements

- [ ] Multi-agent skill sharing
- [ ] Federated learning across deployments
- [ ] Natural language skill queries
- [ ] Visual skill editor
- [ ] Skill marketplace
- [ ] Auto-generated skills from execution traces

## Contributing

To contribute a new skill:

1. Create skill YAML following schema
2. Include learning examples from real scenarios
3. Test with SkillEngine
4. Submit PR with documentation

---

**Transform your AI agents from code executors to knowledge reasoners!** 🚀