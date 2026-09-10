# Script Integration Guide: Intelligent Wrapper Around Existing Scripts

## Overview

The SocialConnectIQ deployment agent integrates with your existing deployment scripts, adding an intelligence layer on top without modifying the original scripts.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  SocialConnectIQ-deployment (Intelligence Layer)             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Deploy Agent CLI (deploy_agent.py)                     │  │
│  │  ↓                                                      │  │
│  │ Orchestrator (LangGraph workflow)                      │  │
│  │  ↓                                                      │  │
│  │ Pre-flight Validation ✅ (18+ checks)                   │  │
│  │  ↓                                                      │  │
│  │ LocalDockerStrategy                                    │  │
│  │  • Version tracking (git SHA)                          │  │
│  │  • Error parsing & remediation                         │  │
│  │  • Health validation                                   │  │
│  │  • Learning from failures                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                         ↓ Calls                               │
└────────────────────────┼────────────────────────────────────┘
                         ↓
┌────────────────────────┼────────────────────────────────────┐
│  SocialConnectIQ (Your Existing Scripts)                     │
│  scripts/local/                                              │
│  ├── build-images.sh      ← Agent calls this                │
│  │   • Builds all service images                            │
│  │   • Tags with :latest                                    │
│  │   • Smart caching                                        │
│  │                                                           │
│  └── start-services.sh    ← Agent calls this                │
│      • Starts docker-compose                                │
│      • Health checks                                        │
│      • Status display                                       │
└──────────────────────────────────────────────────────────────┘
```

## What the Agent Adds

### 1. Pre-Flight Validation ✅
Before your scripts run:
- ✅ Docker daemon running?
- ✅ Sufficient disk space (>10GB)?
- ✅ Required ports available?
- ✅ Configuration files exist?
- ✅ User authorized?
- ✅ Repository accessible?

### 2. Version Tracking 📝
```bash
# Agent automatically tracks:
Git SHA: abc123f
Build Time: 2024-01-15 14:30:00
Deployment ID: deploy-local-20240115-143000
```

### 3. Intelligent Error Parsing 🧠

**Before** (raw script error):
```
Error: no space left on device
```

**After** (agent intelligence):
```
❌ Build failed: no space left on device
💡 Remediation: Run 'docker system prune -a' to free disk space
   This will remove unused Docker images and containers
   Expected to free: ~15GB
```

### 4. Learning System 📊

The agent learns from each deployment:
- Tracks which errors occur most frequently
- Measures remediation success rates
- Suggests optimizations based on patterns
- Auto-improves over time

## Integration Flow

### Local Deployment

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User runs: python deploy_agent.py --env local            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Agent: Pre-Flight Validation                             │
│    ✅ Docker: Running                                        │
│    ✅ Disk: 45GB available                                   │
│    ✅ Ports: 8000-8007 available                            │
│    ✅ Config: .env.local exists                             │
│    ✅ Repo: ../SocialConnectIQ found                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Agent: Get Version                                        │
│    📝 Git SHA: abc123f                                       │
│    📝 Building version abc123f                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Agent calls: bash scripts/local/build-images.sh          │
│    🔨 Your script builds images                             │
│    ✅ Agent verifies: Images created successfully           │
│    📊 Agent records: Build took 180s                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Agent calls: bash scripts/local/start-services.sh        │
│    🚀 Your script starts containers                         │
│    ✅ Agent verifies: Containers running                    │
│    ⏳ Agent waits: 10s for initialization                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Agent: Health Validation                                 │
│    ✅ API Gateway (8000): Healthy                           │
│    ✅ Backend (8001): Healthy                               │
│    ✅ Auth (8002): Healthy                                  │
│    ... (all services checked)                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Agent: Report & Learn                                    │
│    ✅ Deployment Complete (192s total)                      │
│    📝 Log saved: logs/deployment-20240115-143000.log       │
│    📊 Learning recorded for future improvements             │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Basic Deployment
```bash
python deploy_agent.py --env local
```

**What happens:**
1. Pre-flight validation (18+ checks)
2. Calls `build-images.sh`
3. Calls `start-services.sh`
4. Health validation
5. Shows access URLs
6. Records for learning

### With Your Scripts Directly
```bash
# You can still use your scripts directly!
cd ../SocialConnectIQ
./scripts/local/build-images.sh
./scripts/local/start-services.sh
```

**No conflicts** - the agent just wraps your scripts with intelligence.

## Error Handling Examples

### Example 1: Disk Space Issue

**Your script output:**
```
ERROR: no space left on device
```

**Agent enhancement:**
```
❌ Build failed: no space left on device
💡 Remediation: Run 'docker system prune -a' to free disk space
   This will remove unused Docker images and containers
   
📊 Historical data shows this resolves 95% of disk space issues
```

### Example 2: Port Conflict

**Your script output:**
```
Error: port 8000 is already allocated
```

**Agent enhancement:**
```
❌ Deployment failed: port 8000 already allocated
💡 Remediation: Port conflict detected
   Run: cd ../SocialConnectIQ && docker-compose -f docker-compose.local.yml down
   Then retry deployment

🔍 Detected: Previous deployment still running
💡 Automatic cleanup available in next version
```

### Example 3: Missing Configuration

**Your script output:**
```
ERROR: Configuration file '.env.local' not found
```

**Agent enhancement:**
```
❌ Build failed: .env.local not found
💡 Remediation: 
   1. cd ../SocialConnectIQ
   2. cp .env.local.template .env.local
   3. Edit .env.local with your values
   4. Retry deployment

📖 See: docs/CONFIGURATION.md for required variables
```

## Key Benefits

### For Developers
1. **Pre-flight checks catch issues early** - Before wasting 5 minutes on a build
2. **Clear remediation guidance** - No more guessing what went wrong
3. **Version tracking** - Know exactly what's deployed
4. **Learning system** - Gets smarter over time

### For Your Scripts
1. **No modifications needed** - Your scripts work as-is
2. **Backward compatible** - Can still use scripts directly
3. **Intelligence layer** - Added on top, not embedded
4. **Easy updates** - Update scripts independently

### For Operations
1. **Audit trail** - Complete logs of every deployment
2. **Success metrics** - Track deployment success rates
3. **Failure analysis** - Understand what fails and why
4. **Continuous improvement** - System learns and suggests optimizations

## Configuration

### Point to Your Scripts

In `config/environments.yaml`:

```yaml
environments:
  local:
    main_repo_path: "../SocialConnectIQ"
    scripts_dir: "../SocialConnectIQ/scripts/local"
    
    scripts:
      build: "scripts/local/build-images.sh"
      start: "scripts/local/start-services.sh"
      stop: "docker-compose -f docker-compose.local.yml down"
```

## Next Steps

### For GCP Deployment

The same pattern applies for GCP:

```yaml
  staging:
    main_repo_path: "../SocialConnectIQ"
    scripts_dir: "../SocialConnectIQ/scripts/gcp"
    
    scripts:
      build: "scripts/gcp/build-images.sh staging"
      deploy: "scripts/gcp/push-and-deploy.sh staging"
```

Agent will add:
- ✅ GCP authentication checks
- ✅ Artifact Registry verification
- ✅ Cloud Run health monitoring
- ✅ Deployment history tracking
- ✅ Rollback capabilities

## Monitoring & Observability

Every deployment generates:

1. **Structured logs**: `logs/deployment-YYYYMMDD-HHMMSS.log`
2. **Metrics**: Success rate, duration, failures
3. **Learning data**: Patterns and insights
4. **Audit trail**: Who deployed what, when

## Future Enhancements

Based on learning data, the system can:

1. **Auto-cleanup** before builds (if disk space < 15GB)
2. **Auto-retry** on transient failures
3. **Pre-emptive warnings** based on patterns
4. **Optimization suggestions** from performance data
5. **Automated rollback** on failure detection

## Questions?

- 📖 See `QUICKSTART.md` for basic usage
- 📘 See `docs/KNOWLEDGE_SKILLS_SYSTEM.md` for architecture details
- 📗 See `agents/knowledge/skills/socialconnectiq_local_deployment.yaml` for the skill definition

Your scripts remain **your scripts** - the agent just makes them smarter! 🚀