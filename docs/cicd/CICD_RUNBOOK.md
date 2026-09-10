# 🛠️ SocialConnectIQ CI/CD Operations Runbook

**For:** DevOps Engineers | **Updated:** 2026-10-09

---

## 📋 Quick Reference

| Task | Where | Who |
|------|-------|-----|
| View CI results | GitHub → [Repo] → Actions | Anyone |
| Approve release (Gate 1) | GitHub → deployment → Actions → pending run | DevOps + Tech lead |
| Approve deployment (Gate 2/3) | GitHub → deployment → Actions → pending run | DevOps lead |
| Emergency rollback | GitHub → deployment → Actions → `rollback.yml` | DevOps lead |
| View production logs | GCP Console → Cloud Run → [Service] → Logs | DevOps |

---

## 🔄 Standard Release Process

### Step 1: Verify green CI on main (all 3 repos)
Check: SocialConnectIQ, SocialConnectIQ-frontend, MCPSocialTools → Actions → last run = ✅
Never release from a red main. Fix failing tests first.

### Step 2: Trigger release build
```
GitHub → SocialConnectIQ-deployment → Actions → "Release — Build & Regression"
→ Run workflow → Enter version (e.g., 1.3.0) → Run
```

### Step 3: Human Gate 1 — Approve release promotion
Workflow pauses at `promote-to-rel`. You receive an email notification.
```
GitHub → deployment → Actions → [running workflow] → yellow "Waiting" badge
→ Review CI summary → Click "Approve and deploy"
```
After approval: main merges → rel, Docker images built, regression tests run.

### Step 4: Review regression results
```
GitHub → Actions → [completed run] → Summary tab
Check: "## 🧪 Regression" section. Download reg.html for full report.
If any failures → DO NOT deploy. Fix and re-release.
```

### Step 5: Trigger production deployment
```
GitHub → deployment → Actions → "Deploy — Production"
→ Run workflow → Enter exact version tag (e.g., 1.3.0-abc1234)
→ Initial traffic %: 10 → Run
```

### Step 6-8: Human Gates 2 and 3
**Gate 2** (`pre-deploy-checks`): Verify images exist → Approve
**Gate 3a** (`approve-shift-backend`): All backend services dark-launched → Approve
**Gate 3b FINAL** (`approve-gateway-traffic`): Gateway healthy → Approve
→ 5-minute timer → Traffic shifts → Frontend deploys → Smoke tests run

---

## 🚨 Emergency Rollback (< 2 minutes)

### GitHub Actions (recommended)
```
GitHub → deployment → Actions → "Emergency Rollback" → Run workflow
→ service: all
→ reason: "[describe the incident]"
→ Run
```

### Direct gcloud (if you have local access)
```bash
gcloud run services update-traffic api-gateway \
  --to-revisions=<PREVIOUS_REVISION>=100 \
  --region=us-central1 --project=socialconnectiq-488008
```

### Get previous revision name
```bash
gcloud run revisions list --service=api-gateway \
  --region=us-central1 --sort-by='~metadata.creationTimestamp' --limit=3
```

---

## 📊 Monitoring Dashboard Links

| Dashboard | URL |
|-----------|-----|
| GCP Cloud Run | https://console.cloud.google.com/run?project=socialconnectiq-488008 |
| Cloud Logging | https://console.cloud.google.com/logs?project=socialconnectiq-488008 |
| Cloud Monitoring | https://console.cloud.google.com/monitoring?project=socialconnectiq-488008 |
| Artifact Registry | https://console.cloud.google.com/artifacts?project=socialconnectiq-488008 |
| Firebase Console | https://console.firebase.google.com/project/socialconnectiq-488008 |
| GitHub Actions | https://github.com/AIResearxhLabs/SocialConnectIQ-deployment/actions |
| Production API | https://api-gateway-lk7iu4bo5q-uc.a.run.app/health |

---

## 🔑 First-Time Setup (One-Time Tasks)

### 1. Run GCP WIF setup
```bash
chmod +x scripts/cicd/setup-workload-identity.sh && ./scripts/cicd/setup-workload-identity.sh
# Copy printed values to GitHub Secrets
```

### 2. Configure GitHub Environments
GitHub → SocialConnectIQ-deployment → Settings → Environments:
- `main-to-rel`: reviewers = DevOps+TechLead, branch = main
- `rel-to-deploy`: reviewers = DevOps, branch = rel
- `production`: reviewers = DevOps (2 required), branch = rel, wait = 5min

### 3. Add GitHub Secrets (see IMPLEMENTATION_PLAN.md for values)

### 4. Sync rel branches
```bash
chmod +x scripts/cicd/sync-rel-branches.sh && ./scripts/cicd/sync-rel-branches.sh
```

### 5. Add GitHub Variable (not secret)
GitHub → deployment → Settings → Variables → Actions:
`PRODUCTION_API_GATEWAY_URL` = `https://api-gateway-lk7iu4bo5q-uc.a.run.app`

---

## 🐛 Common Troubleshooting

### Docker build fails
Look at the failed docker-build-check job output. Common: Dockerfile syntax error or bad requirements.txt.

### Coverage below 80%
Add tests for uncovered code paths. Push to main. Re-release.

### Regression tests fail
Download regression-report.html from workflow artifacts. Check which WF-0X failed.
Re-run once (flakiness check). If systematic: bugfix branch → PR → main → re-release.

### Deploy health check fails
```bash
gcloud run services logs read <service> --region=us-central1 --limit=50
```
Common: missing env var, expired Firebase credentials, port mismatch (needs 8080).

### WIF auth error
Re-run setup-workload-identity.sh. Verify GCP_WORKLOAD_IDENTITY_PROVIDER secret is exact match.
Check repo name is exactly: `AIResearxhLabs/SocialConnectIQ-deployment`.

### Stale CI test data in Firestore
Firebase Console → Firestore → delete all documents with `ci_test_` prefix → re-run CI job.

*Last updated: 2026-10-09 | Maintained by DevOps team*
