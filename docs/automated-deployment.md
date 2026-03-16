# PromptShell - Automated Cloud Deployment

PromptShell fully automates the deployment of its Google Cloud Run enhancement service through **four layers** of infrastructure-as-code: a CI/CD release pipeline, a manual deploy workflow, a Cloud Build configuration, and a local deploy script. No manual console clicks are required at any stage.

---

## Deployment Architecture

```
Developer pushes version tag (git tag v0.2.0 && git push origin v0.2.0)
                │
                ▼
┌──────────────────────────────────────────────────────────────────┐
│            GitHub Actions — release.yml (automated)              │
│                                                                  │
│  validate ──► test ──► build ──► publish-pypi ──► deploy-cloud-run
│  (tag check)  (6 matrix)  (wheel)   (OIDC)        │              │
│                                                     ▼            │
│                                            ┌──────────────────┐  │
│                                            │ Google Cloud     │  │
│                                            │ ┌──────────────┐ │  │
│                                            │ │ Cloud Build  │ │  │
│                                            │ │ (build image)│ │  │
│                                            │ └──────┬───────┘ │  │
│                                            │        ▼         │  │
│                                            │ ┌──────────────┐ │  │
│                                            │ │ Cloud Run    │ │  │
│                                            │ │ (deploy+run) │ │  │
│                                            │ └──────┬───────┘ │  │
│                                            │        ▼         │  │
│                                            │  Health check    │  │
│                                            └──────────────────┘  │
│                                                                  │
│  Also in parallel: github-release + docker (GHCR multi-arch)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Primary: Automated Release Pipeline

**File:** [`.github/workflows/release.yml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml)

The release pipeline is the primary deployment path. A single `git tag` triggers the entire flow — no manual intervention.

### Trigger

```bash
git tag v0.2.0
git push origin v0.2.0
```

### Pipeline Jobs (sequential)

| Job | What it does |
|-----|-------------|
| **validate** | Verifies the git tag matches the version in `pyproject.toml` — prevents mismatched releases |
| **test** | Runs the full test suite across a 6-cell matrix (Python 3.11/3.12/3.13 x Ubuntu/macOS) |
| **build** | Builds sdist + wheel distribution packages |
| **publish-pypi** | Publishes to PyPI via OIDC trusted publishing (no API token stored) |
| **deploy-cloud-run** | Builds container via Cloud Build, deploys to Cloud Run, runs health check |
| **github-release** | Creates GitHub Release with auto-generated changelog + build artifacts |
| **docker** | Builds and pushes multi-platform Docker image (amd64 + arm64) to GHCR |

### Cloud Run Deploy Steps (within `deploy-cloud-run` job)

```yaml
# 1. Authenticate to GCP using service account key
- uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}

# 2. Enable required GCP APIs (idempotent)
- run: gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

# 3. Build versioned container image via Cloud Build
- run: gcloud builds submit --tag "gcr.io/$PROJECT/prompt-shell-enhancer:v0.2.0" ./cloud_run_service/

# 4. Deploy to Cloud Run with resource limits and scaling config
- run: gcloud run deploy prompt-shell-enhancer --image "gcr.io/$PROJECT/prompt-shell-enhancer:v0.2.0" ...

# 5. Verify deployment health
- run: curl -sf "$URL/health"
```

Each release gets a **version-tagged container image** (e.g. `gcr.io/PROJECT/prompt-shell-enhancer:v0.2.0`), enabling instant rollback to any previous version.

---

## 2. Manual Re-deploy Workflow

**File:** [`.github/workflows/deploy-cloud-run.yml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/deploy-cloud-run.yml)

For deploying outside of a release — secret rotation, config changes, or incident recovery.

### Trigger

GitHub Actions UI: **Actions > Deploy to Cloud Run (Manual) > Run workflow**

### Configurable Inputs

| Input | Default | Purpose |
|-------|---------|---------|
| `region` | `us-central1` | Cloud Run region |
| `image_tag` | `latest` | Specific version tag (e.g. `v0.1.0`) for rollback |

### What it does

1. Authenticates to GCP via `google-github-actions/auth@v2`
2. Builds container image via `gcloud builds submit`
3. Deploys to Cloud Run with the same resource configuration as the release pipeline
4. Runs a `/health` endpoint check to verify the deployment

---

## 3. Cloud Build Configuration

**File:** [`cloudbuild.yaml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml)

For teams using Google Cloud Build triggers instead of GitHub Actions.

### Steps

| Step | Builder | Action |
|------|---------|--------|
| **build** | `gcr.io/cloud-builders/docker` | Build the Docker image from `cloud_run_service/` |
| **push** | `gcr.io/cloud-builders/docker` | Push to Google Container Registry |
| **deploy** | `gcr.io/google.com/cloudsdktool/cloud-sdk` | Deploy to Cloud Run via `gcloud run deploy` |

### Secret Management

The Gemini API key is read from **Google Secret Manager** — it never appears in trigger config, build logs, or environment variables:

```yaml
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/gemini-api-key/versions/latest
      env: GEMINI_API_KEY
```

### Manual Invocation

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _REGION=us-central1,_SERVICE_NAME=prompt-shell-enhancer \
  --project $PROJECT_ID
```

---

## 4. Local Deploy Script

**File:** [`deploy.sh`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/deploy.sh)

One-command deployment from a local machine — for first-time setup or debugging.

### Usage

```bash
export PROJECT_ID=your-gcp-project-id
export GEMINI_API_KEY=your-gemini-api-key
bash deploy.sh
```

### What it does

1. **Validates** required environment variables (`PROJECT_ID`, `GEMINI_API_KEY`) — fails immediately with a clear error if missing
2. **Enables GCP APIs** — `run.googleapis.com`, `cloudbuild.googleapis.com`, `containerregistry.googleapis.com`
3. **Builds** the container image via `gcloud builds submit`
4. **Deploys** to Cloud Run with production-ready configuration (512Mi memory, 1 CPU, 0-10 instances, 30s timeout)
5. **Outputs** the service URL + ready-to-paste config snippet for `~/.prompt-shell/config.yaml`

### Optional Overrides

| Variable | Default | Purpose |
|----------|---------|---------|
| `REGION` | `us-central1` | Cloud Run region |
| `SERVICE_NAME` | `prompt-shell-enhancer` | Cloud Run service name |

---

## Container Image

**File:** [`cloud_run_service/Dockerfile`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/Dockerfile)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Minimal image — Python 3.12 slim base, only production dependencies, runs uvicorn on port 8080.

---

## Cloud Run Service Configuration

All deployment methods use the same Cloud Run configuration:

| Parameter | Value | Reason |
|-----------|-------|--------|
| **Memory** | 512Mi | Sufficient for FastAPI + Gemini SDK |
| **CPU** | 1 | Single-threaded request processing |
| **Min instances** | 0 | Scale to zero when idle (cost = $0) |
| **Max instances** | 10 | Handle burst traffic |
| **Timeout** | 30s | Gemini API calls complete in < 5s typically |
| **Auth** | Unauthenticated | Public endpoint for the local daemon |

---

## Secrets Management

Secrets are handled securely across all deployment methods:

| Secret | GitHub Actions | Cloud Build | Local |
|--------|---------------|-------------|-------|
| `GCP_SA_KEY` | GitHub repository secret | N/A (runs in-project) | `gcloud auth` |
| `GCP_PROJECT_ID` | GitHub repository secret | `$PROJECT_ID` (built-in) | Environment variable |
| `GEMINI_API_KEY` | GitHub repository secret | Google Secret Manager | Environment variable |

No secret ever appears in build logs, container images, or source code.

---

## Health Check & Verification

Every deployment method ends with an automated health check:

```bash
curl -sf "$SERVICE_URL/health"
# Response: {"status": "ok"}
```

The release pipeline (`release.yml`) **fails the deployment job** if the health check doesn't return `"ok"`, preventing broken deployments from going unnoticed.

---

## Rollback

Version-tagged images enable instant rollback without rebuilding:

```bash
# List available versions
gcloud container images list-tags gcr.io/$PROJECT_ID/prompt-shell-enhancer

# Rollback to a specific version
gcloud run deploy prompt-shell-enhancer \
  --image gcr.io/$PROJECT_ID/prompt-shell-enhancer:v0.1.0 \
  --platform managed --region us-central1 --project "$PROJECT_ID"
```

Or use the manual workflow with a specific `image_tag` input.

---

## All Relevant Files

| File | Purpose | Link |
|------|---------|------|
| `.github/workflows/release.yml` | Automated release + deploy pipeline | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml) |
| `.github/workflows/deploy-cloud-run.yml` | Manual re-deploy workflow | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/deploy-cloud-run.yml) |
| `cloudbuild.yaml` | Cloud Build trigger config | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml) |
| `deploy.sh` | One-command local deploy script | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/deploy.sh) |
| `cloud_run_service/Dockerfile` | Container image definition | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/Dockerfile) |
| `cloud_run_service/main.py` | FastAPI service (POST /enhance, GET /health) | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/main.py) |
| `cloud_run_service/requirements.txt` | Cloud Run dependencies | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/requirements.txt) |
| `docs/deployment.md` | Full deployment guide (GCP setup, secrets, troubleshooting) | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/docs/deployment.md) |
