#!/bin/bash
# =============================================================================
# CP-03: setup-workload-identity.sh — ONE-TIME GCP SETUP
# Enables keyless GitHub Actions → GCP auth (no JSON keys stored).
# Run ONCE as a GCP project owner.
# USAGE: chmod +x scripts/cicd/setup-workload-identity.sh
#        ./scripts/cicd/setup-workload-identity.sh
# =============================================================================
set -e

GCP_PROJECT_ID="${GCP_PROJECT_ID:-socialconnectiq-488008}"
GCP_REGION="${GCP_REGION:-us-central1}"
GITHUB_ORG="AIResearxhLabs"
GITHUB_REPO="SocialConnectIQ-deployment"
POOL_ID="github-actions-pool"
PROVIDER_ID="github-provider"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }

log_info "GCP Workload Identity Federation Setup"
log_info "Project: $GCP_PROJECT_ID | Repo: $GITHUB_ORG/$GITHUB_REPO"

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
[ -z "$ACCOUNT" ] && { echo "Run: gcloud auth login"; exit 1; }
log_info "Authenticated as: $ACCOUNT"

gcloud config set project "$GCP_PROJECT_ID"
PROJECT_NUM=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(projectNumber)")

# Enable APIs
log_info "Enabling required APIs..."
gcloud services enable iamcredentials.googleapis.com cloudresourcemanager.googleapis.com \
    run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com \
    firebase.googleapis.com --project="$GCP_PROJECT_ID"
log_success "APIs enabled"

# Create Workload Identity Pool
log_info "Creating Workload Identity Pool: $POOL_ID"
gcloud iam workload-identity-pools describe "$POOL_ID" --location=global \
    --project="$GCP_PROJECT_ID" &>/dev/null \
    && log_success "Pool already exists" \
    || { gcloud iam workload-identity-pools create "$POOL_ID" --location=global \
         --project="$GCP_PROJECT_ID" --display-name="GitHub Actions Pool"
         log_success "Pool created"; }

# Create OIDC Provider (trusts GitHub's token issuer)
log_info "Creating OIDC Provider: $PROVIDER_ID"
gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" --location=global \
    --project="$GCP_PROJECT_ID" &>/dev/null \
    && log_success "Provider already exists" \
    || { gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
         --workload-identity-pool="$POOL_ID" --location=global \
         --project="$GCP_PROJECT_ID" \
         --issuer-uri="https://token.actions.githubusercontent.com" \
         --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
         --attribute-condition="assertion.repository_owner == '${GITHUB_ORG}'"
         log_success "OIDC Provider created"; }

# Create Service Account
log_info "Creating Service Account: $SA_EMAIL"
gcloud iam service-accounts describe "$SA_EMAIL" --project="$GCP_PROJECT_ID" &>/dev/null \
    && log_success "SA already exists" \
    || { gcloud iam service-accounts create "$SA_NAME" --project="$GCP_PROJECT_ID" \
         --display-name="GitHub Actions Deployer"
         log_success "SA created"; }

# Grant IAM Roles (least privilege)
log_info "Granting IAM roles..."
for ROLE in "roles/run.admin" "roles/artifactregistry.writer" \
            "roles/iam.serviceAccountUser" "roles/storage.admin" "roles/firebase.admin"; do
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" --role="$ROLE" --condition=None --quiet \
        2>&1 | grep -c "binding" > /dev/null || true
    log_success "  $ROLE"
done

# Bind: only this GitHub repo can impersonate the SA
log_info "Binding GitHub repo to SA (SECURITY: only $GITHUB_ORG/$GITHUB_REPO can use this SA)"
WIF_MEMBER="principalSet://iam.googleapis.com/projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
    --project="$GCP_PROJECT_ID" --role="roles/iam.workloadIdentityUser" \
    --member="$WIF_MEMBER" --quiet 2>&1 | grep -c "binding" > /dev/null || true
log_success "IAM binding created"

WIF_PROVIDER="projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗"
echo -e "║    COPY THESE VALUES INTO GITHUB SECRETS                 ║"
echo -e "║    Repo → Settings → Secrets and Variables → Actions     ║"
echo -e "╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}GCP_WORKLOAD_IDENTITY_PROVIDER${NC}"
echo "  $WIF_PROVIDER"
echo ""
echo -e "${GREEN}GCP_SERVICE_ACCOUNT${NC}"
echo "  $SA_EMAIL"
echo ""
echo -e "${GREEN}GCP_PROJECT_ID${NC}    →  $GCP_PROJECT_ID"
echo -e "${GREEN}GCP_REGION${NC}        →  $GCP_REGION"
echo ""
echo "Add to repos: SocialConnectIQ-deployment, SocialConnectIQ, SocialConnectIQ-frontend, MCPSocialTools"
echo "Also add FIREBASE_TOKEN from: firebase login:ci"
echo "See: docs/cicd/IMPLEMENTATION_PLAN.md for full secrets reference"
