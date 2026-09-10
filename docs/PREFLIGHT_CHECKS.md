# 🔍 Pre-Flight Validation System

## Overview

The Pre-Flight Validator is a comprehensive skill that validates all prerequisites before deployment begins. It ensures system readiness, catches configuration errors early, and provides clear remediation guidance.

## Check Categories

### 1. ⚙️ System Checks (CRITICAL/HIGH)

| Check | Priority | Description |
|-------|----------|-------------|
| **Docker Daemon Status** | CRITICAL | Verifies Docker daemon is running and API is accessible |
| **CLI Tools** | HIGH | Ensures required tools are installed (docker, gcloud, firebase, etc.) |
| **Disk Space** | HIGH | Checks sufficient disk space (10GB for local, 5GB for cloud) |
| **Memory** | HIGH | Validates available RAM (4GB recommended) |
| **Network Connectivity** | MEDIUM | Tests internet and service reachability |

### 2. 📝 Configuration Checks (CRITICAL)

| Check | Priority | Description |
|-------|----------|-------------|
| **Config Files** | CRITICAL | Validates YAML syntax in environments.yaml and roles.yaml |
| **Environment Variables** | CRITICAL | Ensures required env vars are set (DEPLOYMENT_USER, etc.) |
| **Repository Paths** | HIGH | Verifies repository directories exist |

### 3. 🔗 Dependency Checks (HIGH/MEDIUM)

| Check | Priority | Description |
|-------|----------|-------------|
| **Port Availability** | HIGH | Checks if required ports (8080, 8081, 3000, etc.) are free |
| **Docker Images** | MEDIUM | Reports cached images status |
| **Volume Paths** | HIGH | Validates mount paths exist and are accessible |

### 4. 🔐 Permission Checks (CRITICAL/HIGH)

| Check | Priority | Description |
|-------|----------|-------------|
| **User Authorization** | CRITICAL | Validates user role for target environment |
| **File Permissions** | HIGH | Checks read/write access to logs, config directories |
| **Docker Socket** | HIGH | Verifies Docker socket access |

### 5. 🌍 Environment Checks (MEDIUM)

| Check | Priority | Description |
|-------|----------|-------------|
| **Existing Deployment** | MEDIUM | Detects running containers from previous deployments |
| **Service Health** | MEDIUM | Checks health of currently running services |

## Priority Levels

| Priority | Failure Behavior | Description |
|----------|------------------|-------------|
| **CRITICAL** | ❌ BLOCK | Deployment cannot proceed |
| **HIGH** | ⚠️  WARN + BLOCK | Deployment blocked but remediation provided |
| **MEDIUM** | ⚠️  WARNING | Deployment continues with warning |
| **LOW** | ℹ️  INFO | Informational only |

## Workflow Integration

```
START
  ↓
Initialize
  ↓
Authorize User
  ↓
Pre-Flight Validation ← YOU ARE HERE
  ├─ Pass → Continue to Build
  └─ Fail → Stop with remediation
```

## Example Output

```
🔍 Running Pre-Flight Validation Checks...

╭─────────────── System Checks ───────────────╮
│ ✓ Docker daemon                     [  OK  ] │
│ ✓ Docker Compose available          [  OK  ] │
│ ✓ Disk space (25.3 GB available)    [  OK  ] │
│ ⚠ Memory (3.8 GB available)         [ WARN ] │
│ ✓ Network connectivity              [  OK  ] │
╰──────────────────────────────────────────────╯

╭────────────── Configuration Checks ──────────────╮
│ ✓ Environment variables              [  OK  ] │
│ ✓ environments.yaml valid            [  OK  ] │
│ ✓ roles.yaml valid                   [  OK  ] │
│ ✓ Repository path exists             [  OK  ] │
╰──────────────────────────────────────────────────╯

✅ Pre-flight validation PASSED: 18 checks, 1 warnings
```

## Remediation Examples

### Failed Check: Docker Not Running

```
❌ CRITICAL: Docker daemon is not running or not accessible
→ Remediation: Start Docker Desktop and ensure it's fully initialized
```

### Failed Check: Missing CLI Tool

```
❌ HIGH: Required tool not found: gcloud
→ Remediation: Install gcloud - see https://cloud.google.com/sdk/docs/install
```

### Warning: Port In Use

```
⚠️  HIGH: Port 8080 already in use (may be existing deployment)
→ Remediation: Stop service using port 8080 or deployment will update it
```

## Validation Report

Each deployment generates a detailed JSON report:

**Location**: `logs/preflight-{deployment-id}.json`

**Contents**:
```json
{
  "deployment_id": "deploy-local-20260806-110000",
  "environment": "local",
  "timestamp": "2026-08-06T11:00:00Z",
  "validation_result": {
    "passed": true,
    "can_proceed": true,
    "total_checks": 18,
    "elapsed_seconds": 2.3,
    "critical_failures": 0,
    "high_failures": 0,
    "warnings": 1
  },
  "checks": [...]
}
```

## Customization

### Adding Custom Checks

Add custom checks by extending the `PreFlightValidator` class:

```python
def _check_custom_requirement(self):
    """Check custom requirement"""
    start = datetime.now()
    
    # Your check logic here
    if requirement_met:
        self.checks.append(CheckResult(
            name="Custom Requirement",
            category="custom",
            priority="HIGH",
            status="PASS",
            message="Requirement satisfied",
            elapsed_time_ms=(datetime.now() - start).total_seconds() * 1000
        ))
```

### Configuring Checks

Customize checks via `config/environments.yaml`:

```yaml
environments:
  local:
    preflight:
      required_disk_gb: 15  # Increase requirement
      check_network: false  # Disable network checks
      custom_ports: [9000, 9001]  # Additional ports
```

## Troubleshooting

### Pre-Flight Always Fails

1. Check Docker Desktop is running
2. Verify .env file exists with required variables
3. Ensure config/*.yaml files are valid YAML
4. Check repository paths are correct

### Too Many Warnings

Warnings don't block deployment but indicate potential issues:
- Review each warning message
- Follow remediation suggestions
- Warnings can be ignored if understood

### Checks Take Too Long

- Network checks may timeout on slow connections
- Docker checks may be slow if daemon is busy
- Consider increasing timeout values in code

## Benefits

✅ **Early Detection**: Catch issues before deployment starts  
✅ **Clear Feedback**: Detailed error messages with remediation  
✅ **Audit Trail**: Complete validation record for each deployment  
✅ **Time Savings**: Prevents failed deployments due to prerequisites  
✅ **Confidence**: Know exactly what was verified  
✅ **Learning**: Helps users understand requirements  

## Future Enhancements

- [ ] Cloud credentials validation (GCP, AWS, Firebase)
- [ ] Database connectivity checks
- [ ] API endpoint health checks
- [ ] SSL certificate validation
- [ ] Performance benchmarking
- [ ] Configurable check timeouts
- [ ] Custom check plugins
- [ ] Check result caching