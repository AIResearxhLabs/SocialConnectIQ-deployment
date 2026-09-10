#!/bin/bash
# CP-21: traffic-shift.sh
# PURPOSE: Gradually shift Cloud Run traffic to a new revision (Blue/Green deployment).
# WHY: Allows safe canary deployments — test with 10% before moving to 100%.
# USAGE: ./traffic-shift.sh <service> <new-revision-name> <percentage>
# EXAMPLE: ./traffic-shift.sh api-gateway api-gateway-00042-abc 50
# NOTE: Get revision names with: gcloud run revisions list --service=<service> --region=us-central1
set -e

SERVICE=$1
REVISION=$2
PERCENTAGE=$3
REGION=${GCP_REGION:-us-central1}
PROJECT=${GCP_PROJECT_ID:-socialconnectiq-488008}

[ -z "$SERVICE" ] || [ -z "$REVISION" ] || [ -z "$PERCENTAGE" ] && {
    echo "Usage: $0 <service> <revision-name> <percentage>"
    echo "Example: $0 api-gateway api-gateway-00042-abc 50"
    echo ""
    echo "Get revision names: gcloud run revisions list --service=<service> --region=$REGION"
    exit 1
}

OLD_PERCENT=$((100 - PERCENTAGE))

echo "🔀 Traffic shift: $SERVICE"
echo "   New revision: $REVISION → ${PERCENTAGE}%"
echo "   Old revision: keeps ${OLD_PERCENT}%"
echo ""

gcloud run services update-traffic "$SERVICE" \
    --region="$REGION" --project="$PROJECT" \
    --to-revisions="${REVISION}=${PERCENTAGE}" --quiet

echo "✅ Traffic shift complete."
echo ""
echo "Monitor error rates for 5 minutes before shifting further."
echo "GCP Monitoring: https://console.cloud.google.com/monitoring"
echo ""
echo "To shift to 100%:  $0 $SERVICE $REVISION 100"
echo "To rollback:       $0 $SERVICE <prev-revision> 100"
