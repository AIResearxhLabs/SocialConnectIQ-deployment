# Migration Guide: Code-Based Skills → Knowledge-Based Skills

This guide explains how to migrate from imperative code-based skills to declarative knowledge-based skills.

## Table of Contents

1. [Why Migrate?](#why-migrate)
2. [Architecture Comparison](#architecture-comparison)
3. [Migration Steps](#migration-steps)
4. [Example Migration](#example-migration)
5. [Integration Guide](#integration-guide)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Why Migrate?

### Traditional Code-Based Skills (Imperative)

```python
# agents/skills/preflight_validator.py
class PreFlightValidator:
    def validate_all(self, state):
        # Hard-coded logic
        if not self._check_docker():
            raise ValidationError("Docker not running")
        # ... more checks
```

**Limitations:**
- ❌ Rigid execution path
- ❌ Difficult to adapt to new contexts
- ❌ No learning from outcomes
- ❌ Language-specific (Python)
- ❌ Complex to share across projects

### Knowledge-Based Skills (Declarative)

```yaml
# agents/knowledge/skills/preflight_validation.yaml
decision_patterns:
  - condition: "always"
    action: "validate_docker_daemon"
    priority: "CRITICAL"
    success_criteria: "Docker responds with version"
    failure_handling: "BLOCK: Start Docker Desktop"
```

**Benefits:**
- ✅ Flexible reasoning-based application
- ✅ Adapts to context automatically
- ✅ Learns and improves from outcomes
- ✅ Language-agnostic (YAML)
- ✅ Easy to share and version

---

## Architecture Comparison

### Before: Code Execution
```
User Request → Orchestrator → PreFlightValidator.validate_all()
                                ↓ (executes)
                              Fixed checks in order
                                ↓
                              Results
```

### After: Knowledge Reasoning
```
User Request → Orchestrator → SkillEngine.load_skill()
                                ↓
                              SkillEngine.reason_about_application()
                                ↓ (adapts to context)
                              SkillEngine.execute_skill()
                                ↓
                              Results → SkillLearner.record()
                                          ↓
                                        Learning & Evolution
```

---

## Migration Steps

### Step 1: Analyze Existing Skill

Identify the components of your code-based skill:

```python
# Example: agents/skills/preflight_validator.py

# EXTRACT THESE:
# 1. Purpose: What does this skill do?
# 2. Conditions: When does each check apply?
# 3. Decision Logic: How are decisions made?
# 4. Success Criteria: What defines success?
# 5. Failure Handling: What happens on failure?
# 6. Learning Opportunities: What could improve?
```

### Step 2: Map to Knowledge Schema

Create a YAML file following the schema:

```yaml
# agents/knowledge/skills/[skill_name].yaml

metadata:
  id: "skill-[name]-v1"
  name: "[Human-Readable Name]"
  version: "1.0.0"
  category: "[Category]"
  tags: ["tag1", "tag2"]

understanding:
  purpose: "[What this accomplishes]"
  when_to_use: "[Context for application]"
  importance: "[CRITICAL|HIGH|MEDIUM|LOW]"

decision_patterns:
  # One pattern per logical check
  - condition: "[When to execute]"
    action: "[What to do]"
    priority: "[CRITICAL|HIGH|MEDIUM|LOW]"
    tools_required: ["[tool_name]"]
    success_criteria: "[How to verify success]"
    failure_handling: "[What to do on failure]"

# See skill_schema.yaml for complete structure
```

### Step 3: Convert Logic to Patterns

Map each method/check to a decision pattern:

#### Code (Before):
```python
def _check_docker_daemon(self):
    try:
        client = docker.from_env()
        version = client.version()
        return CheckResult(status="PASS", message="Docker running")
    except Exception as e:
        return CheckResult(
            status="FAIL",
            message="Docker not running",
            remediation="Start Docker Desktop"
        )
```

#### Knowledge (After):
```yaml
decision_patterns:
  - condition: "always"
    action: "validate_docker_daemon_status"
    priority: "CRITICAL"
    tools_required: ["execute_command"]
    success_criteria: "Docker daemon responds with version info"
    failure_handling: "BLOCK: Start Docker Desktop"
    metadata:
      command: "docker info --format '{{.ServerVersion}}'"
      error_patterns:
        - "Cannot connect to the Docker daemon"
```

### Step 4: Add Learning Examples

Capture historical knowledge:

```yaml
learning_examples:
  - scenario: "Docker daemon not running on macOS"
    context:
      environment: "local"
      os: "macOS"
    actions_taken:
      - "Detected connection error"
      - "Provided remediation: Start Docker Desktop"
    outcome: "SUCCESS"
    metrics:
      resolution_time_seconds: 95
    insights: "Clear remediation resolves 98% of cases"
```

### Step 5: Update Orchestrator

Replace direct class usage with SkillEngine:

#### Before:
```python
from agents.skills.preflight_validator import PreFlightValidator

def _preflight_validation_node(self, state):
    validator = PreFlightValidator(env, config, env_config)
    result, state = validator.validate_all(state)
    return state
```

#### After:
```python
from agents.core import SkillEngine, SkillLearner

def __init__(self):
    # ... existing init ...
    self.skill_engine = SkillEngine()
    self.skill_learner = SkillLearner()

def _preflight_validation_node(self, state):
    # Load knowledge artifact
    skill = self.skill_engine.load_skill("preflight_validation")
    
    # Reason about application
    context = {
        "environment": state["environment"],
        "user_role": state["user_role"]
    }
    plan = self.skill_engine.reason_about_application(skill, context)
    
    # Execute with reasoning
    result, state = self.skill_engine.execute_skill(skill, plan, state)
    
    # Learn from outcome
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
    
    return state
```

### Step 6: Enable Learning

Set up continuous improvement:

```python
# In your application startup or periodic job
from agents.core import SkillLearner

learner = SkillLearner()

# Analyze patterns monthly
insights = learner.analyze_patterns("skill-preflight-validation-v1", days=30)

for insight in insights:
    if insight.priority == "HIGH":
        # Alert team or create issue
        print(f"Important insight: {insight.description}")

# Auto-apply low-risk improvements
improvements = learner.suggest_improvements("skill-preflight-validation-v1")

for improvement in improvements:
    if improvement.risk_level == "LOW" and not improvement.requires_approval:
        learner.evolve_skill(
            skill_id=improvement.skill_id,
            improvement=improvement,
            skill_path=Path("./agents/knowledge/skills/preflight_validation.yaml"),
            auto_apply=True
        )
```

---

## Example Migration

### Complete Before/After

#### Before (Code):
```python
# agents/skills/my_skill.py
class MySkill:
    def execute(self, state):
        if state['environment'] == 'production':
            return self._production_check(state)
        else:
            return self._dev_check(state)
    
    def _production_check(self, state):
        # ... complex logic ...
        pass
```

#### After (Knowledge):
```yaml
# agents/knowledge/skills/my_skill.yaml
metadata:
  id: "skill-my-skill-v1"
  name: "My Skill"
  version: "1.0.0"
  category: "validation"

understanding:
  purpose: "Validate environment-specific requirements"
  when_to_use: "Before deployment"
  importance: "HIGH"

decision_patterns:
  - condition: "environment == 'production'"
    action: "production_validation"
    priority: "CRITICAL"
    tools_required: ["execute_command"]
    success_criteria: "All production checks pass"
    failure_handling: "BLOCK: Production requirements not met"
  
  - condition: "environment IN ['local', 'staging']"
    action: "development_validation"
    priority: "HIGH"
    tools_required: ["execute_command"]
    success_criteria: "Development checks pass"
    failure_handling: "WARN: Continue with caution"
```

---

## Integration Guide

### Gradual Migration Strategy

1. **Phase 1: Parallel Running** (Week 1-2)
   - Keep existing code-based skills
   - Add knowledge-based versions alongside
   - Compare results

2. **Phase 2: Primary with Fallback** (Week 3-4)
   - Use knowledge-based skills as primary
   - Fall back to code on errors
   - Fix discrepancies

3. **Phase 3: Knowledge-Only** (Week 5+)
   - Remove code-based skills
   - Monitor learning system
   - Apply improvements

### Testing Strategy

```python
# tests/test_migration.py

def test_skill_equivalence():
    """Verify knowledge-based skill matches code-based behavior"""
    
    # Code-based
    old_validator = PreFlightValidator(env, config)
    old_result = old_validator.validate_all(state)
    
    # Knowledge-based
    engine = SkillEngine()
    skill = engine.load_skill("preflight_validation")
    plan = engine.reason_about_application(skill, context)
    new_result, _ = engine.execute_skill(skill, plan, state)
    
    # Compare
    assert old_result.can_proceed == new_result.can_proceed
    assert set(old_result.failed_checks) == set(new_result.patterns_failed)
```

---

## Best Practices

### 1. Start with Read-Only Skills
Migrate skills that only read/validate before those that modify state.

### 2. Maintain Backward Compatibility
Keep old code during transition:
```python
use_knowledge_skills = os.getenv("USE_KNOWLEDGE_SKILLS", "false") == "true"

if use_knowledge_skills:
    result = skill_engine.execute_skill(skill, plan, state)
else:
    result = old_validator.validate_all(state)
```

### 3. Version Everything
Use semantic versioning:
- Patch (x.x.1): Bug fixes, threshold adjustments
- Minor (x.1.0): New patterns added
- Major (2.0.0): Breaking changes to skill structure

### 4. Document Decision Rationale
Add metadata explaining WHY each pattern exists:
```yaml
decision_patterns:
  - condition: "disk_space < 10GB"
    action: "block_deployment"
    priority: "HIGH"
    metadata:
      rationale: "Prevents disk-full errors during image builds"
      added: "2024-01-15"
      added_by: "devops-team"
```

### 5. Enable Incremental Learning
Start with `learning_enabled: true` but `requires_approval: true` for changes.

---

## Troubleshooting

### Issue: Skill Not Loading

**Error:** `FileNotFoundError: Skill not found`

**Solution:**
```bash
# Verify file exists
ls agents/knowledge/skills/your_skill.yaml

# Check file permissions
chmod 644 agents/knowledge/skills/your_skill.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('agents/knowledge/skills/your_skill.yaml'))"
```

### Issue: Pattern Not Executing

**Problem:** Expected pattern doesn't run

**Debug:**
```python
skill = engine.load_skill("your_skill")
plan = engine.reason_about_application(skill, context)

print("Applicable patterns:")
for pattern in plan.applicable_patterns:
    print(f"  - {pattern.action} (condition: {pattern.condition})")

# Check if condition evaluates correctly
print(f"Context: {context}")
```

### Issue: Performance Degradation

**Problem:** Skill execution slower than code version

**Solutions:**
1. Enable caching:
```python
engine = SkillEngine()
# Skills are automatically cached after first load
```

2. Optimize pattern evaluation:
```yaml
# Instead of complex conditions
condition: "environment == 'local' AND user_role IN ['developer', 'admin']"

# Use simpler checks
condition: "environment == 'local'"
# Then filter in tool execution
```

### Issue: Learning Database Growing Large

**Problem:** SQLite database file too large

**Solution:**
```python
# In maintenance script
learner = SkillLearner()

# Archive old records
conn = sqlite3.connect(learner.db_path)
cursor = conn.cursor()

# Keep only last 90 days
cutoff = (datetime.now() - timedelta(days=90)).isoformat()
cursor.execute("DELETE FROM executions WHERE timestamp < ?", (cutoff,))

conn.commit()
conn.close()
```

---

## Next Steps

1. ✅ Choose first skill to migrate (start with simplest)
2. ✅ Create knowledge artifact following schema
3. ✅ Add to `agents/knowledge/skills/`
4. ✅ Update orchestrator to use SkillEngine
5. ✅ Run tests to verify equivalence
6. ✅ Deploy with monitoring
7. ✅ Review learning insights weekly
8. ✅ Migrate next skill

## Resources

- [Skill Schema Reference](../agents/knowledge/schemas/skill_schema.yaml)
- [Usage Examples](../agents/knowledge/USAGE_EXAMPLE.md)
- [SkillEngine API](../agents/core/skill_engine.py)
- [SkillLearner API](../agents/core/skill_learner.py)

---

**Questions?** Open an issue or consult the team!