# Deployment Guide

This document covers everything needed to deploy the PromptShell Cloud Run
enhancement service to Google Cloud — from first-time GCP setup through to
automated releases via GitHub Actions.

---

## Overview

PromptShell uses a split architecture:

```
Local client (your machine)          Google Cloud Run
────────────────────────────         ─────────────────────────────────
Hotkey listener                      POST /enhance
Terminal snapshot              →     FastAPI  (cloud_run_service/)
Voice capture + transcription        Google GenAI SDK
Context builder                ←     Gemini 2.0 Flash
Clipboard delivery
```

The Cloud Run service is stateless and scales to zero — it only runs when a
request arrives. At personal/demo scale the cost is effectively $0/month.

---

## Prerequisites

| Tool | Install |
|------|---------|
| `gcloud` CLI | [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install) |
| Docker (optional) | Only needed for local image builds; Cloud Build handles it in CI |
| GCP account | [console.cloud.google.com](https://console.cloud.google.com) |
| Gemini API key | [aistudio.google.com](https://aistudio.google.com) — free tier available |

---

## First-time GCP Setup

Run these steps once per GCP project. You only need to do this once.

### 1. Create a GCP project

```bash
gcloud projects create YOUR_PROJECT_ID --name="PromptShell"
gcloud config set project YOUR_PROJECT_ID
```

Or use an existing project — just set `PROJECT_ID`:

```bash
export PROJECT_ID=your-existing-project-id
gcloud config set project $PROJECT_ID
```

### 2. Enable billing

Cloud Run requires billing to be enabled on the project even at free-tier
usage. Go to:
[console.cloud.google.com/billing](https://console.cloud.google.com/billing)
and link a billing account to your project.

### 3. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project "$PROJECT_ID"
```

What each API does:
- `run.googleapis.com` — Cloud Run (runs the container)
- `cloudbuild.googleapis.com` — Cloud Build (builds the Docker image)
- `containerregistry.googleapis.com` — GCR (stores the built image)
- `secretmanager.googleapis.com` — Secret Manager (used by `cloudbuild.yaml`)

### 4. Store the Gemini API key in Secret Manager

This keeps the API key out of environment variables and CI logs.

```bash
export GEMINI_API_KEY=your-gemini-api-key-from-aistudio

echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --data-file=- \
  --project "$PROJECT_ID"
```

Grant Cloud Build permission to read it:

```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project "$PROJECT_ID"
```

### 5. Create a service account for GitHub Actions

GitHub Actions needs a service account to authenticate with GCP.

```bash
# Create the service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions deployer" \
  --project "$PROJECT_ID"

SA_EMAIL="github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant it the roles it needs
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Create and download a JSON key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account="$SA_EMAIL" \
  --project "$PROJECT_ID"
```

Base64-encode the key for use as a GitHub secret:

```bash
# macOS
base64 -i sa-key.json | pbcopy

# Linux
base64 -w 0 sa-key.json
```

**Delete the local key file after copying it:**

```bash
rm sa-key.json
```

---

## GitHub Secrets Setup

Go to your GitHub repository → **Settings → Secrets and variables → Actions**
and add these three repository secrets:

| Secret name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID (e.g. `my-project-123`) |
| `GCP_SA_KEY` | The base64-encoded service account JSON key from the step above |
| `GEMINI_API_KEY` | Your Gemini API key from Google AI Studio |

These secrets are injected into GitHub Actions workflows at runtime and are
never exposed in logs.

---

## Deployment Workflows

### Automatic deploy on release (primary path)

The normal way to deploy is by cutting a versioned release. Push a version
tag and the full release pipeline runs automatically:

```bash
# 1. Update version in pyproject.toml
# 2. Commit the version bump
git commit -m "chore: bump version to 0.2.0"

# 3. Push the tag
git tag v0.2.0
git push origin v0.2.0
```

This triggers `.github/workflows/release.yml`, which runs these jobs in order:

```
validate (tag matches pyproject.toml version)
    ↓
test (Python 3.11/3.12/3.13 × Ubuntu/macOS)
    ↓
build (sdist + wheel)
    ↓
publish-pypi (PyPI via OIDC trusted publisher)
    ↓
deploy-cloud-run  ← Cloud Run deploy happens here
    ↓
github-release (GitHub Release with changelog + artifacts)
docker (multi-platform image pushed to GHCR)
```

The Cloud Run deploy job:
1. Authenticates to GCP using the `GCP_SA_KEY` secret
2. Enables required GCP APIs (idempotent — safe to run every time)
3. Builds the container image via Cloud Build, tagged with the release version
   (e.g. `gcr.io/PROJECT/prompt-shell-enhancer:v0.2.0`)
4. Deploys the versioned image to Cloud Run
5. Runs a `/health` check to confirm the service is up
6. The GitHub Actions environment URL is set to the Cloud Run service URL

Each release gets its own image tag, so you can roll back by redeploying a
previous tag.

### Manual re-deploy (without a new release)

Use `.github/workflows/deploy-cloud-run.yml` when you need to redeploy
without bumping the version — for example, to rotate the `GEMINI_API_KEY`
secret, or to recover from an incident.

Go to **Actions → Deploy to Cloud Run (Manual) → Run workflow**, then choose:
- **Region** (default: `us-central1`)
- **Image tag** (default: `latest` — or specify a version like `v0.1.0`)

### Local deploy (no GitHub Actions)

Use `deploy.sh` from your local machine:

```bash
export PROJECT_ID=your-gcp-project-id
export GEMINI_API_KEY=your-gemini-api-key
bash deploy.sh
```

The script validates env vars, enables APIs, builds the image, deploys, and
prints the service URL with the config snippet.

### Cloud Build trigger (alternative CI)

`cloudbuild.yaml` is provided for teams that prefer to use Cloud Build
triggers instead of GitHub Actions. Create a trigger in the GCP Console
pointing at this file. The Gemini API key is read from Secret Manager
(secret name: `gemini-api-key`) so it never appears in trigger config or
build logs.

---

## After Deploying

### Get the service URL

```bash
gcloud run services describe prompt-shell-enhancer \
  --region us-central1 \
  --project "$PROJECT_ID" \
  --format "value(status.url)"
```

### Verify the service is healthy

```bash
curl https://YOUR_SERVICE_URL/health
# {"status":"ok"}
```

### Test an enhancement

```bash
curl -X POST https://YOUR_SERVICE_URL/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "voice_transcript": "fix the build error",
    "cwd": "/home/user/project",
    "git_branch": "main",
    "last_commands": "npm run build",
    "detected_errors": "TS2345: Argument of type string is not assignable"
  }'
```

### Configure the local client

Add the service URL to `~/.prompt-shell/config.yaml`:

```yaml
llm:
  provider: gemini
  model: gemini-2.0-flash
  api_key: ${GEMINI_API_KEY}
  cloud_run_url: ${CLOUD_RUN_URL}
```

Set the env var in your shell profile:

```bash
echo 'export CLOUD_RUN_URL=https://YOUR_SERVICE_URL' >> ~/.zshrc
echo 'export GEMINI_API_KEY=your-key' >> ~/.zshrc
```

---

## Rollback

To roll back to a previous image:

```bash
# List available image versions
gcloud container images list-tags gcr.io/$PROJECT_ID/prompt-shell-enhancer

# Redeploy a specific version
gcloud run deploy prompt-shell-enhancer \
  --image gcr.io/$PROJECT_ID/prompt-shell-enhancer:v0.1.0 \
  --platform managed \
  --region us-central1 \
  --project "$PROJECT_ID"
```

Or trigger the manual workflow with a specific `image_tag`.

---

## Cost

| Component | Free tier | Estimated cost at demo scale |
|-----------|-----------|------------------------------|
| Cloud Run | 2M requests/month, 360K GB-sec | $0 |
| Cloud Build | 120 build-minutes/day | $0 |
| Container Registry | First 0.5 GB free | $0 |
| Gemini 2.0 Flash | 1,500 requests/day free | $0 |

At personal/demo usage (< 200 requests/day), the total monthly cost is **$0**.

---

## Troubleshooting

**Deploy fails: "Permission denied"**
The service account is missing a required IAM role. Re-run the IAM binding
steps in "Create a service account for GitHub Actions" above.

**Health check fails after deploy**
The container may be failing to start due to a missing `GEMINI_API_KEY`.
Check Cloud Run logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=prompt-shell-enhancer" \
  --project "$PROJECT_ID" --limit 50
```

**`gcloud builds submit` times out**
The default Cloud Build timeout is 10 minutes. The image is small so this
should not happen. If it does, check Cloud Build logs in the GCP Console.

**Local client cannot reach Cloud Run**
Run `curl $CLOUD_RUN_URL/health` from your machine. If that fails:
- Check the URL in your config: `prompt-shell context`
- Verify the service is running: `gcloud run services list --project $PROJECT_ID`
