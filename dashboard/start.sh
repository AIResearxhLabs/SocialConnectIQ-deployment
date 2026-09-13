#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# SocialConnectIQ DevOps Dashboard — Start Script
#
# Usage:
#   ./start.sh                          # Uses GITHUB_TOKEN from env or .env file
#   GITHUB_TOKEN=ghp_xxx ./start.sh     # Pass token directly
# ─────────────────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# ── Load .env if it exists ────────────────────────────────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -v '^$' | xargs) 2>/dev/null || true
fi

# Also check repo-root .env for GITHUB_TOKEN if not already set
if [ -z "$GITHUB_TOKEN" ] && [ -f "$REPO_ROOT/.env" ]; then
    GT=$(grep '^GITHUB_TOKEN=' "$REPO_ROOT/.env" | cut -d'=' -f2)
    if [ -n "$GT" ]; then
        export GITHUB_TOKEN="$GT"
    fi
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║    SocialConnectIQ DevOps Dashboard                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Check GITHUB_TOKEN ────────────────────────────────────────────────────────
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠  WARNING: GITHUB_TOKEN is not set."
    echo "   CI status, deploy triggers, and test triggers will show"
    echo "   'unknown' or fail gracefully. The UI still works fully."
    echo ""
    echo "   To enable GitHub features, set your token:"
    echo "   export GITHUB_TOKEN=ghp_your_token_here"
    echo "   Or add it to: $SCRIPT_DIR/.env"
    echo ""
else
    TOKEN_PREVIEW="${GITHUB_TOKEN:0:7}..."
    echo "✅ GITHUB_TOKEN detected: $TOKEN_PREVIEW"
    echo "   → CI status, deploy triggers, and test runs are enabled"
    echo ""
fi

# ── Kill any existing processes on these ports ────────────────────────────────
echo "→ Clearing ports 8080 and 5173..."
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

# ── Start Backend ─────────────────────────────────────────────────────────────
echo "→ Starting backend (FastAPI) on :8080 ..."
cd "$BACKEND_DIR"

# Activate venv if present in repo root
if [ -f "$REPO_ROOT/venv/bin/activate" ]; then
    source "$REPO_ROOT/venv/bin/activate"
fi

# Install deps if needed
pip install -q fastapi uvicorn sqlalchemy pydantic python-dotenv requests httpx 2>/dev/null

export GITHUB_TOKEN="$GITHUB_TOKEN"
export GITHUB_ORG="${GITHUB_ORG:-AIResearxhLabs}"
export DEPLOYMENT_REPO="${DEPLOYMENT_REPO:-SocialConnectIQ-deployment}"
export HEALTH_POLL_INTERVAL="${HEALTH_POLL_INTERVAL:-30}"
export CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload \
    > /tmp/dashboard-backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "   Waiting for backend..."
for i in $(seq 1 15); do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo "   ✅ Backend ready"
        break
    fi
    sleep 1
done

# ── Start Frontend ────────────────────────────────────────────────────────────
echo ""
echo "→ Starting frontend (Vite) on :5173 ..."
cd "$FRONTEND_DIR"

# Install npm deps if needed
if [ ! -d node_modules ]; then
    echo "   Installing npm dependencies..."
    npm install --silent
fi

npm run dev > /tmp/dashboard-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

sleep 3

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Dashboard is running!                               ║"
echo "║                                                      ║"
echo "║  → UI:      http://localhost:5173                    ║"
echo "║  → API:     http://localhost:8080                    ║"
echo "║  → API Docs: http://localhost:8080/docs              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "💡 To enable CI/deploy actions, add your GitHub token:"
    echo "   export GITHUB_TOKEN=ghp_xxx && ./start.sh"
    echo ""
fi

echo "Opening browser..."
open http://localhost:5173 2>/dev/null || xdg-open http://localhost:5173 2>/dev/null || true

echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/dashboard-backend.log"
echo "  Frontend: tail -f /tmp/dashboard-frontend.log"
echo ""
echo "Press Ctrl+C to stop both services."
echo ""

# Wait and trap signals to clean up
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
