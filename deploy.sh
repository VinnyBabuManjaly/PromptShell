#!/usr/bin/env bash
# deploy.sh — Deploy the PromptShell enhancement service to Google Cloud Run.
#
# Usage:
#   export PROJECT_ID=your-gcp-project-id
#   export GEMINI_API_KEY=your-gemini-api-key
#   bash deploy.sh
#
# Optional overrides:
#   REGION       — Cloud Run region (default: us-central1)
#   SERVICE_NAME — Cloud Run service name (default: prompt-shell-enhancer)

set -euo pipefail

# ---------------------------------------------------------------------------
# Validate required inputs
# ---------------------------------------------------------------------------
: "${PROJECT_ID:?Required: export PROJECT_ID=your-gcp-project-id}"
: "${GEMINI_API_KEY:?Required: export GEMINI_API_KEY=your-gemini-api-key}"

REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-prompt-shell-enhancer}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "==> Deploying ${SERVICE_NAME} to ${REGION} (project: ${PROJECT_ID})"

# ---------------------------------------------------------------------------
# Enable required GCP APIs
# ---------------------------------------------------------------------------
echo "==> Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
# Build container image via Cloud Build
# ---------------------------------------------------------------------------
echo "==> Building container image..."
gcloud builds submit \
  --tag "$IMAGE" \
  --project "$PROJECT_ID" \
  ./cloud_run_service/

# ---------------------------------------------------------------------------
# Deploy to Cloud Run
# ---------------------------------------------------------------------------
echo "==> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 30s \
  --project "$PROJECT_ID"

# ---------------------------------------------------------------------------
# Print service URL and config snippet
# ---------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format "value(status.url)")

echo ""
echo "==> Deployment complete."
echo "    Service URL: ${SERVICE_URL}"
echo ""
echo "    Verify health:"
echo "      curl ${SERVICE_URL}/health"
echo ""
echo "    Add to ~/.prompt-shell/config.yaml:"
echo "      llm:"
echo "        provider: gemini"
echo "        model: gemini-2.0-flash"
echo "        api_key: \${GEMINI_API_KEY}"
echo "        cloud_run_url: ${SERVICE_URL}"
echo ""
echo "    Or set the environment variable:"
echo "      export CLOUD_RUN_URL=${SERVICE_URL}"
