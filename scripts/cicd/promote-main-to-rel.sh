#!/bin/bash
# CP-20: promote-main-to-rel.sh
# PURPOSE: Promote latest main to rel + tag with version in all 3 app repos.
# Called by: release-and-build.yml workflow OR manually by DevOps lead.
# USAGE: ./scripts/cicd/promote-main-to-rel.sh 1.3.0
set -e

VERSION=$1
[ -z "$VERSION" ] && { echo "Usage: $0 <version> (e.g., 1.3.0)"; exit 1; }

GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SHORT_SHA=$(git -C "$PARENT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")
TAG="v${VERSION}-${SHORT_SHA}"

log_info "Promoting to release: $TAG"
log_info "Repos: $PARENT_DIR"

git config --global user.email "cicd@socialconnectiq.com"
git config --global user.name "SocialConnectIQ CI"

REPOS=("SocialConnectIQ" "SocialConnectIQ-frontend" "MCPSocialTools" "SocialConnectIQ-deployment")

for REPO in "${REPOS[@]}"; do
    REPO_PATH="$PARENT_DIR/$REPO"
    log_info "Processing $REPO..."

    [ ! -d "$REPO_PATH/.git" ] && { echo "Skipping $REPO (not found at $REPO_PATH)"; continue; }

    cd "$REPO_PATH"
    git fetch origin
    git checkout main && git pull origin main --ff-only

    if git show-ref --verify refs/remotes/origin/rel 2>/dev/null; then
        git checkout -b rel origin/rel 2>/dev/null || git checkout rel
        git merge main --ff-only
    else
        git checkout -b rel
    fi

    git tag "$TAG" -m "Release $VERSION" 2>/dev/null || echo "(tag $TAG already exists)"
    git push origin rel --tags

    log_success "$REPO: rel → $TAG"
    cd "$PARENT_DIR"
done

echo ""
log_success "All repos promoted to $TAG"
echo "Next: trigger release-and-build.yml in GitHub Actions"
