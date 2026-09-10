#!/bin/bash
# =============================================================================
# CP-02: sync-rel-branches.sh
# PURPOSE: Create or sync the 'rel' branch in all 3 application repositories.
# WHEN TO RUN:
#   - First time: Creates rel from main HEAD in repos that don't have it
#   - Subsequent runs: Fast-forward merges main into rel (syncs latest code)
# USAGE:
#   cd /path/to/SocialConnectIQ-deployment
#   chmod +x scripts/cicd/sync-rel-branches.sh
#   ./scripts/cicd/sync-rel-branches.sh
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error()   { echo -e "${RED}[✗]${NC} $1"; }
log_step()    { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PARENT_DIR="$(cd "$DEPLOYMENT_ROOT/.." && pwd)"

REPOS=(
    "SocialConnectIQ:$PARENT_DIR/SocialConnectIQ"
    "SocialConnectIQ-frontend:$PARENT_DIR/SocialConnectIQ-frontend"
    "MCPSocialTools:$PARENT_DIR/MCPSocialTools"
    "SocialConnectIQ-deployment:$DEPLOYMENT_ROOT"
)

echo ""
log_info "SocialConnectIQ — Sync rel Branches"
log_info "Creates or fast-forwards rel from main in all repos"
echo ""

FAILED_REPOS=()
SYNCED_REPOS=()

for repo_entry in "${REPOS[@]}"; do
    repo_name="${repo_entry%%:*}"
    repo_path="${repo_entry#*:}"
    log_step "$repo_name"

    if [ ! -d "$repo_path/.git" ]; then
        log_error "Repository not found at: $repo_path — skipping"
        FAILED_REPOS+=("$repo_name (not found)")
        continue
    fi

    cd "$repo_path"

    log_info "Fetching latest from origin..."
    git fetch origin --prune 2>&1 | sed 's/^/  /'

    log_info "Pulling main..."
    git checkout main
    git pull origin main --ff-only 2>&1 | sed 's/^/  /' || {
        log_error "Could not pull main in $repo_name — resolve conflicts manually"
        FAILED_REPOS+=("$repo_name (main pull failed)")
        continue
    }

    MAIN_SHA=$(git rev-parse --short HEAD)
    log_info "main is at: $MAIN_SHA"

    LOCAL_REL=$(git branch --list rel)
    REMOTE_REL=$(git ls-remote --heads origin rel)

    if [ -z "$LOCAL_REL" ] && [ -z "$REMOTE_REL" ]; then
        log_info "rel does not exist — creating from main HEAD ($MAIN_SHA)"
        git checkout -b rel
        git push origin rel
        log_success "$repo_name: rel branch CREATED at $MAIN_SHA"
    else
        if [ -z "$LOCAL_REL" ]; then
            git checkout -b rel origin/rel
        else
            git checkout rel
            git pull origin rel --ff-only 2>/dev/null || true
        fi

        REL_SHA=$(git rev-parse --short HEAD)
        log_info "rel is currently at: $REL_SHA"

        if [ "$REL_SHA" = "$MAIN_SHA" ]; then
            log_success "$repo_name: rel is already up to date ($MAIN_SHA)"
            SYNCED_REPOS+=("$repo_name (already current)")
            continue
        fi

        log_info "Fast-forwarding rel to main ($REL_SHA → $MAIN_SHA)..."
        git merge main --ff-only 2>&1 | sed 's/^/  /' || {
            log_error "DIVERGED in $repo_name — manual merge needed"
            log_error "Run: cd $repo_path && git log --oneline rel..main"
            FAILED_REPOS+=("$repo_name (diverged)")
            continue
        }

        git push origin rel
        NEW_SHA=$(git rev-parse --short HEAD)
        log_success "$repo_name: rel UPDATED $REL_SHA → $NEW_SHA"
    fi

    SYNCED_REPOS+=("$repo_name → $MAIN_SHA")
    cd "$DEPLOYMENT_ROOT"
done

echo ""
log_info "══════════════ SYNC SUMMARY ══════════════"

if [ ${​#SYNCED_REPOS[@]} -gt 0 ]; then
    log_success "Synced (${​#SYNCED_REPOS[@]}):"
    for r in "${SYNCED_REPOS[@]}"; do echo "  ✓ $r"; done
fi

if [ ${​#FAILED_REPOS[@]} -gt 0 ]; then
    log_error "Failed (${​#FAILED_REPOS[@]}):"
    for r in "${FAILED_REPOS[@]}"; do echo "  ✗ $r"; done
    exit 1
fi

echo ""
log_success "All rel branches synced with main!"
echo ""
echo "Next: trigger release-and-build.yml in GitHub Actions"
echo "  https://github.com/AIResearxhLabs/SocialConnectIQ-deployment/actions"
