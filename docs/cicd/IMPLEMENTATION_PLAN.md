# 🚀 SocialConnectIQ — CI/CD Implementation Plan
## Master Document: Execution, Learning & DevOps Onboarding

**Version:** 1.0.0 | **Created:** 2026-10-09 | **Repo:** `SocialConnectIQ-deployment`

> **How to Resume After Restart:** Find the first `🔲` checkpoint below and continue from there.
> All files are self-contained — no work is lost when a session restarts.

---

## 📊 Checkpoint Status Tracker

| # | Checkpoint | Repo | Status | Date |
|---|-----------|------|--------|------|
| **CP-01** | Create master CICD plan document | deployment | ✅ | 2026-10-09 |
| **CP-02** | Create `sync-rel-branches.sh` + sync all repos | all | ✅ | 2026-10-09 |
| **CP-03** | Create `setup-workload-identity.sh` (GCP WIF) | deployment | ✅ | 2026-10-09 |
| **CP-04** | Create backend `ci.yml` (SocialConnectIQ) | backend | ✅ | 2026-10-09 |
| **CP-05** | Create frontend `ci.yml` (SocialConnectIQ-frontend) | frontend | ✅ | 2026-10-09 |
| **CP-06** | Create MCP server `ci.yml` (MCPSocialTools) | mcp | ✅ | 2026-10-09 |
| **CP-07** | Create workflow test suite `conftest.py` | deployment | ✅ | 2026-10-09 |
| **CP-08** | Create WF-01 auth tests | deployment | ✅ | 2026-10-09 |
| **CP-09** | Create WF-02 OAuth tests | deployment | ✅ | 2026-10-09 |
| **CP-10** | Create WF-03 posting tests | deployment | ✅ | 2026-10-09 |
| **CP-11** | Create WF-04 scheduling tests | deployment | ✅ | 2026-10-09 |
| **CP-12** | Create WF-05 analytics tests | deployment | ✅ | 2026-10-09 |
| **CP-13** | Create WF-06 trending tests | deployment | ✅ | 2026-10-09 |
| **CP-14** | Create WF-07 user management tests | deployment | ✅ | 2026-10-09 |
| **CP-15** | Create WF-08 billing tests | deployment | ✅ | 2026-10-09 |
| **CP-16** | Create WF-09 health tests | deployment | ✅ | 2026-10-09 |
| **CP-17** | Create `release-and-build.yml` (Stage 2) | deployment | ✅ | 2026-10-09 |
| **CP-18** | Create `deploy-production.yml` (Stage 3) | deployment | ✅ | 2026-10-09 |
| **CP-19** | Create `rollback.yml` | deployment | ✅ | 2026-10-09 |
| **CP-20** | Create `promote-main-to-rel.sh` | deployment | ✅ | 2026-10-09 |
| **CP-21** | Create `traffic-shift.sh` | deployment | ✅ | 2026-10-09 |
| **CP-22** | Create `CICD_RUNBOOK.md` | deployment | ✅ | 2026-10-09 |
| **CP-23** | Update `requirements.txt` | deployment | ✅ | 2026-10-09 |
| **CP-24** | Update `environments.yaml` | deployment | ✅ | 2026-10-09 |
| **CP-25** | Commit and push all files | all | 🔲 | — |
| **CP-26** | Configure GitHub Environments (human gates) | GitHub UI | 🔲 | — |
| **CP-27** | Run `setup-workload-identity.sh` in GCP | GCP CLI | 🔲 | — |
| **CP-28** | Add GitHub Secrets to all repos | GitHub UI | 🔲 | — |
| **CP-29** | First real release: trigger `release-and-build.yml` | GitHub Actions | 🔲 | — |
| **CP-30** | First production deployment | GitHub Actions | 🔲 | — |

---

## 🏗️ System Architecture

```
THREE APPLICATION REPOS → SocialConnectIQ-deployment (Central DevOps Hub)

SocialConnectIQ (backend — 9 Python/FastAPI services on GCP Cloud Run)
  api-gateway(8000) → backend-service(8001) → integration-service(8002)
  agent-service(8006) → auth/analytics/posting/scheduling services

SocialConnectIQ-frontend → React/Vite → Firebase Hosting (prjsyntheist.web.app)

MCPSocialTools → TypeScript/Node.js MCP Server on GCP Cloud Run (port 3001)

Request flow: Browser → Firebase Hosting → API Gateway → Backend Services
                                                       → Agent Service → MCPSocialTools → Platform APIs
```

---

## 🔄 Branch Strategy

```
feature/* / bugfix/* / hotfix/* → PR → main (CI auto-runs)
                                           ↓ Human Gate 1 (DevOps+TechLead)
                                          rel (release build + regression)
                                           ↓ Human Gate 2 (DevOps lead)
                                    GCP Cloud Run + Firebase Hosting

RULE: Never commit directly to rel. Always promote from main using promote-main-to-rel.sh.
RULE: Only rel branch can trigger production deploys (enforced by WIF conditions).
```

---

## 🎓 Technology Explanations (New DevOps Engineers)

### GitHub Actions
CI/CD built into GitHub. `.github/workflows/*.yml` files define automated pipelines.
No separate CI server needed. Jobs run on GitHub-hosted VMs (runners).
`environment:` on a job creates a human approval gate that pauses execution.
Secrets stored in GitHub Settings → Secrets, accessed as `${​{ secrets.NAME }}`.

### GCP Workload Identity Federation (WIF)
**Problem:** GitHub needs GCP access to push images + deploy. Old approach: JSON key
file (permanent, leakable). WIF solution: GitHub proves identity via a 10-min OIDC
token → GCP issues a 1-hour temporary token. Zero long-lived secrets stored anywhere.

```
GitHub Actions → sends OIDC token → GCP WIF Pool → verifies repo+branch
              ← receives 1hr temp token ←────────────────────────────
```

Run `scripts/cicd/setup-workload-identity.sh` ONCE as GCP owner to configure.
Then add 2 secrets to GitHub: GCP_WORKLOAD_IDENTITY_PROVIDER + GCP_SERVICE_ACCOUNT.

### Blue/Green Deployment on Cloud Run
1. Deploy new revision with --no-traffic (zero users affected)
2. Smoke test the new revision via its direct URL
3. Shift traffic gradually: 0% → 10% → 50% → 100%
4. Old revision stays alive for instant rollback (shift 100% back in seconds)

### Firestore Test Collections (ci_test_* prefix)
Same Firestore project, isolated collection paths. CI tests write to ci_test_users/,
ci_test_oauth_states/ etc. Auto-cleanup after each test. Zero risk to production data.

### The rel Branch
Isolates releases from active development. Developers push to main during a release.
rel is always fast-forward from main (never diverged). Only rel triggers production deploys.

---

## 🔑 GitHub Secrets Reference

### SocialConnectIQ-deployment repo
```
GCP_WORKLOAD_IDENTITY_PROVIDER  → output of setup-workload-identity.sh
GCP_SERVICE_ACCOUNT             → output of setup-workload-identity.sh
GCP_PROJECT_ID                  → socialconnectiq-488008
GCP_REGION                      → us-central1
FIREBASE_TOKEN                  → firebase login:ci (copy output)
SLACK_WEBHOOK_URL               → Slack → Incoming Webhooks
REPO_PAT                        → GitHub → Developer Settings → PAT (repo scope)
```

### SocialConnectIQ (backend) repo
```
FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL  → Firebase Console
FIREBASE_CI_TEST_TOKEN  → Firebase Admin SDK custom token for CI test user
TEST_COLLECTION_PREFIX  → ci_test_  (literal string)
GCP_WORKLOAD_IDENTITY_PROVIDER, GCP_SERVICE_ACCOUNT  → same as deployment repo
```

### SocialConnectIQ-frontend + MCPSocialTools repos
```
GCP_WORKLOAD_IDENTITY_PROVIDER, GCP_SERVICE_ACCOUNT, FIREBASE_TOKEN  → same values
```

---

## 🚦 GitHub Environments (Human Gates)

Create in: GitHub → SocialConnectIQ-deployment → Settings → Environments

| Environment | Reviewers | Branch Filter | Wait Timer | Purpose |
|-------------|-----------|---------------|------------|---------|
| `main-to-rel` | DevOps lead + Tech lead | main only | 0 min | Approve release promotion |
| `rel-to-deploy` | DevOps lead | rel only | 0 min | Approve deployment start |
| `production` | DevOps lead (2 required) | rel only | 5 min | Approve traffic shift |

---

## 📋 Workflow Tests (58 Total Scenarios)

WF-01 Auth(7) · WF-02 OAuth(12) · WF-03 Posting(11) · WF-04 Scheduling(5)
WF-05 Analytics(4) · WF-06 Trending(5) · WF-07 UserMgmt(4) · WF-08 Billing(4) · WF-09 Health(6)

---

## 🆘 Emergency Procedures

### Service down RIGHT NOW
```
GitHub UI: SocialConnectIQ-deployment → Actions → rollback.yml → Run workflow
  Enter: service=all, reason="[describe incident]"
```

### Stale test data causing CI failures
```
Firebase Console → Firestore → delete all documents with ci_test_ prefix
Then re-run the failing CI job.
```

*Last updated: 2026-10-09 | Maintained by DevOps team*
