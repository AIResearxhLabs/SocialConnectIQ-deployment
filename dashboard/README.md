# 🖥️ SocialConnectIQ DevOps Dashboard

A full-stack, real-time DevOps dashboard for DevOps engineers to:
- ✅ **Trigger deployments** (staging / production) via GitHub Actions
- ✅ **Monitor progress** with live WebSocket updates
- ✅ **Approve / reject human gates** inline (no need to open GitHub)
- ✅ **Run tests** (CI, regression, smoke) on demand
- ✅ **Monitor service health** across all production Cloud Run services
- ✅ **Emergency rollback** with one click
- ✅ **View logs** — deployment history and test run details

---

## 🏗️ Architecture

```
browser → React/Vite (port 5173) → FastAPI backend (port 8080) → GitHub Actions API
                                                               → Cloud Run /health endpoints (WebSocket poll)
                                                               → SQLite (deployment history)
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.11+
- Node.js 20+
- A GitHub Personal Access Token with `repo` + `workflow` scopes

### 1. Backend

```bash
cd dashboard/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export GITHUB_TOKEN=ghp_yourtoken
uvicorn app.main:app --reload --port 8080
```

### 2. Frontend

```bash
cd dashboard/frontend
npm install
npm run dev   # → http://localhost:5173
```

### 3. Docker Compose (both together)

```bash
cd dashboard
export GITHUB_TOKEN=ghp_yourtoken
docker-compose up --build
# Dashboard: http://localhost:5173
# API:       http://localhost:8080
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Dashboard backend health |
| GET | `/api/health/services` | Poll all Cloud Run services |
| GET | `/api/health/ci-status` | CI pipeline status (3 repos) |
| GET | `/api/health/pending-gates` | GitHub Actions awaiting approval |
| GET | `/api/deployments` | List deployments |
| POST | `/api/deployments/trigger` | Trigger workflow |
| POST | `/api/deployments/{id}/approve` | Approve / reject gate |
| DELETE | `/api/deployments/{id}` | Cancel deployment |
| GET | `/api/tests` | List test runs |
| POST | `/api/tests/trigger` | Trigger test run |
| WS | `/ws/live` | Real-time health + gate stream |

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ | GitHub PAT (repo + workflow scopes) |
| `GITHUB_ORG` | — | Default: `AIResearxhLabs` |
| `DEPLOYMENT_REPO` | — | Default: `SocialConnectIQ-deployment` |
| `PROD_API_GATEWAY_URL` | — | Production API Gateway URL |
| `HEALTH_POLL_INTERVAL` | — | Seconds between health polls (default: 30) |
| `CORS_ORIGINS` | — | Comma-separated allowed origins |

---

## 🧪 Running Tests

```bash
cd dashboard/backend
DASHBOARD_DB_URL=sqlite:///./test.db GITHUB_TOKEN=test pytest tests/ -v
```

10 tests · all green ✅
