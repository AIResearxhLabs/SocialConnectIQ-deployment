# Knowledge-Based Skills: Quick Start Guide

Get started with knowledge-based skills in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Your First Skill

Create `agents/knowledge/skills/hello_world.yaml`:

```yaml
metadata:
  id: "skill-hello-world-v1"
  name: "Hello World Skill"
  version: "1.0.0"
  category: "example"
  tags: ["tutorial", "example"]
  created_at: "2024-01-15T10:00:00Z"
  updated_at: "2024-01-15T10:00:00Z"

understanding:
  purpose: "Demonstrate basic skill structure"
  when_to_use: "Learning the system"
  prerequisites:
    - "None - this is a beginner example"
  importance: "LOW"
  expected_outcomes:
    - "Successfully execute simple checks"
    - "Learn skill structure"

knowledge_domains:
  - domain: "basic_validation"
    concepts:
      - "Environment awareness"
      - "User role checking"
    relationships:
      - "environment → appropriate_checks"
    constraints:
      - "Production requires extra validation"

decision_patterns:
  - condition: "always"
    action: "greet_user"
    priority: "LOW"
    tools_required: []
    success_criteria: "Greeting generated"
    failure_handling: "WARN: Could not generate greeting"
  
  - condition: "environment == 'production'"
    action: "production_warning"
    priority: "HIGH"
    tools_required: []
    success_criteria: "Warning displayed"
    failure_handling: "INFO: Production warning shown"

tool_sequences:
  - sequence_name: "basic_check"
    description: "Perform basic validation"
    steps:
      - tool: "execute_command"
        action: "check_environment"
        inputs:
          command: "echo $ENVIRONMENT"
        outputs: ["env_value"]
        validation: "Command executes successfully"

learning_examples:
  - scenario: "First execution"
    context:
      environment: "local"
      user_role: "developer"
    actions_taken:
      - "Greeted user"
      - "Checked environment"
    outcome: "SUCCESS"
    metrics:
      execution_time_seconds: 0.5
    insights: "Simple skills execute quickly"

performance_metrics:
  success_rate: 1.0
  avg_execution_time_seconds: 0.5
  failure_modes: []
  optimization_opportunities:
    - "This is already optimal for a tutorial"

evolution:
  learning_enabled: true
  feedback_loops:
    - "Track execution count"
  adaptation_rules:
    - condition: "execution_count > 100"
      action: "Congratulate user for practicing"
      requires_approval: false
  versioning_strategy: "semantic_based_on_changes"
```

## 3. Use the Skill

Create `test_hello_skill.py`:

```python
from agents.core import SkillEngine, SkillLearner
from agents.state import create_initial_state

# Initialize
engine = SkillEngine(skills_dir="./agents/knowledge/skills")
learner = SkillLearner()

# Load skill
print("Loading skill...")
skill = engine.load_skill("hello_world")
print(f"✅ Loaded: {skill.metadata.name} v{skill.metadata.version}")

# Create context
context = {
    "environment": "local",
    "user_role": "developer"
}

# Reason about application
print("\nReasoning about skill application...")
plan = engine.reason_about_application(skill, context)
print(f"✅ Found {len(plan.applicable_patterns)} applicable patterns:")
for pattern in plan.applicable_patterns:
    print(f"   - {pattern.action} (priority: {pattern.priority})")

# Create state
state = create_initial_state(
    environment="local",
    user_email="developer@example.com",
    user_role="developer"
)

# Execute skill
print("\nExecuting skill...")
result, updated_state = engine.execute_skill(skill, plan, state)

print(f"✅ Execution complete:")
print(f"   Success: {result.success}")
print(f"   Can proceed: {result.can_proceed}")
print(f"   Patterns executed: {len(result.patterns_executed)}")
print(f"   Patterns passed: {len(result.patterns_passed)}")
print(f"   Execution time: {result.execution_time_seconds:.3f}s")

# Record for learning
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

print("\n✅ Execution recorded for learning!")
print("\n🎉 Congratulations! You've used your first knowledge-based skill!")
```

## 4. Run It

```bash
python test_hello_skill.py
```

Expected output:
```
Loading skill...
✅ Loaded: Hello World Skill v1.0.0

Reasoning about skill application...
✅ Found 1 applicable patterns:
   - greet_user (priority: LOW)

Executing skill...
✅ Execution complete:
   Success: True
   Can proceed: True
   Patterns executed: 1
   Patterns passed: 1
   Execution time: 0.023s

✅ Execution recorded for learning!

🎉 Congratulations! You've used your first knowledge-based skill!
```

## 5. Learn from Executions

After running multiple times, analyze patterns:

```python
# Analyze after 10+ executions
insights = learner.analyze_patterns("skill-hello-world-v1", days=7)

print(f"Found {len(insights)} insights:")
for insight in insights:
    print(f"  {insight.priority}: {insight.description}")
```

## Next Steps

### Try Production Environment

Modify context to trigger production pattern:

```python
context = {
    "environment": "production",  # Changed!
    "user_role": "prod-ops"
}

plan = engine.reason_about_application(skill, context)
# Should now have 2 patterns (greet_user + production_warning)
```

### Create Your Own Skill

1. Copy `hello_world.yaml` to `my_skill.yaml`
2. Customize the patterns
3. Load with `engine.load_skill("my_skill")`

### Explore Real Skills

Check out the production-ready skill:

```python
skill = engine.load_skill("preflight_validation")
print(f"Patterns: {len(skill.decision_patterns)}")
print(f"Learning examples: {len(skill.learning_examples)}")
```

### Enable Learning

Run the skill 20+ times, then:

```python
improvements = learner.suggest_improvements("skill-hello-world-v1")
for improvement in improvements:
    print(f"Suggestion: {improvement.description}")
    print(f"Benefit: {improvement.expected_benefit}")
```

## Key Concepts

### 1. Skills are Knowledge, Not Code

```yaml
# This is knowledge the agent reasons about
decision_patterns:
  - condition: "environment == 'production'"
    action: "extra_checks"
```

NOT:
```python
# This is code the agent blindly executes
if environment == "production":
    extra_checks()
```

### 2. Agents Reason, Don't Just Execute

The agent evaluates conditions and decides which patterns apply:
- "Environment is production → Apply production patterns"
- "Priority is CRITICAL → Must succeed or block"
- "Tool is execute_command → Need shell access"

### 3. Skills Learn and Evolve

Every execution is recorded. The system:
- Identifies failure patterns
- Suggests optimizations
- Auto-applies low-risk improvements
- Tracks performance trends

## Troubleshooting

### Skill not loading?

```python
# Check file exists
import os
assert os.path.exists("agents/knowledge/skills/hello_world.yaml")

# Validate YAML
import yaml
with open("agents/knowledge/skills/hello_world.yaml") as f:
    data = yaml.safe_load(f)
    print("YAML is valid!")
```

### Pattern not executing?

```python
# Debug pattern evaluation
for pattern in skill.decision_patterns:
    result = pattern.should_execute(context)
    print(f"{pattern.action}: {result}")
```

### Learning not working?

```python
# Check database
import sqlite3
conn = sqlite3.connect("agents/knowledge/learning/execution_history.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM executions")
count = cursor.fetchone()[0]
print(f"Recorded executions: {count}")
```

## Resources

- 📖 [Complete Documentation](README.md)
- 📘 [Usage Examples](USAGE_EXAMPLE.md)
- 📗 [Migration Guide](../../docs/KNOWLEDGE_SKILLS_MIGRATION.md)
- 📕 [Skill Schema](schemas/skill_schema.yaml)

## Community

Questions? Found a bug? Want to contribute?

- Open an issue on GitHub
- Join our discussions
- Share your skills!

---

**Happy skill building!** 🚀