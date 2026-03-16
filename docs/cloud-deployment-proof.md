# PromptShell - Proof of Google Cloud Deployment

PromptShell runs a **FastAPI enhancement service on Google Cloud Run** that accepts terminal context (text + screenshot), processes it through **Gemini 2.5 Flash Lite** via the **Google GenAI SDK**, and returns an enhanced developer prompt. This document provides evidence of every Google Cloud integration point.

---

## Google Cloud Services Used

| Service | Purpose | Evidence |
|---------|---------|----------|
| **Google Cloud Run** | Hosts the enhancement service (FastAPI) | [cloud_run_service/main.py](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/main.py) |
| **Google Cloud Build** | Builds Docker container images | [cloudbuild.yaml](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml) |
| **Google Container Registry** | Stores versioned container images | [release.yml#L222](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml#L222) |
| **Google Secret Manager** | Stores GEMINI_API_KEY securely | [cloudbuild.yaml#L58-L61](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml#L58) |
| **Gemini 2.5 Flash Lite** | Multimodal LLM for prompt enhancement | [cloud_run_service/gemini_client.py](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/gemini_client.py) |
| **Google GenAI SDK** | Python SDK for Gemini API calls | [cloud_run_service/requirements.txt](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/requirements.txt) |

---

## 1. Gemini API Integration via Google GenAI SDK

**File:** [`cloud_run_service/gemini_client.py`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/gemini_client.py)

This is the core Google AI integration. It uses the official `google-genai` Python SDK to call Gemini 2.5 Flash Lite with **multimodal input** (text + PNG screenshot).

```python
import google.genai as genai

def create_client(api_key: str) -> genai.Client:
    """Create an authenticated Google GenAI client."""
    return genai.Client(api_key=api_key)

def generate_enhanced_prompt(
    client: genai.Client,
    meta_prompt: str,
    model: str = "gemini-2.5-flash-lite",
    screenshot_b64: str | None = None,
) -> str:
    """Call Gemini to produce an enhanced developer prompt."""
    if screenshot_b64:
        # Multimodal call: text + terminal screenshot
        contents = [
            genai.types.Part.from_text(text=meta_prompt),
            genai.types.Part.from_bytes(
                data=base64.b64decode(screenshot_b64),
                mime_type="image/png",
            ),
        ]
    else:
        contents = meta_prompt

    response = client.models.generate_content(model=model, contents=contents)
    return response.text.strip()
```

**Key points:**
- Uses `google.genai` (Google GenAI SDK) — not a third-party wrapper
- Supports both text-only and multimodal (text + image) requests
- Model: `gemini-2.5-flash-lite` (configurable via `GEMINI_MODEL` env var)
- Screenshot sent as inline PNG via `genai.types.Part.from_bytes()`

---

## 2. FastAPI Service on Cloud Run

**File:** [`cloud_run_service/main.py`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/main.py)

The FastAPI application that runs on Cloud Run, exposing two endpoints:

```python
app = FastAPI(
    title="PromptShell Enhancement Service",
    description="Enhances developer prompts using Gemini 2.5 Flash Lite",
)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

@app.post("/enhance", response_model=EnhanceResponse)
async def enhance(request: EnhanceRequest) -> EnhanceResponse:
    """Enhance a developer prompt using terminal context and Gemini."""
    client = _get_gemini_client()
    meta_prompt = build_meta_prompt(request.model_dump())
    enhanced = generate_enhanced_prompt(
        client, meta_prompt, model=GEMINI_MODEL, screenshot_b64=request.screenshot_b64
    )
    return EnhanceResponse(enhanced_prompt=enhanced)

@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok"}
```

**Request payload** (what the local daemon sends to Cloud Run):

| Field | Type | Description |
|-------|------|-------------|
| `voice_transcript` | string | Transcribed voice command (e.g., "fix the error") |
| `cwd` | string | Current working directory |
| `git_branch` | string | Active git branch |
| `last_commands` | string | Recent terminal commands |
| `detected_errors` | string | Regex-extracted error patterns |
| `screen_buffer_last_50` | string | Last 50 lines of terminal output |
| `project_type` | string | Detected project type (python, node, rust, etc.) |
| `screenshot_b64` | string | Base64-encoded terminal screenshot PNG |

---

## 3. Local Client to Cloud Run Communication

**File:** [`src/prompt_shell/enhancer/enhancement_client.py`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/src/prompt_shell/enhancer/enhancement_client.py)

The local daemon sends the full context payload to Cloud Run via HTTP POST:

```python
async def enhance_via_cloud_run(
    summary: dict,
    cloud_run_url: str,
    timeout: float = 30.0,
) -> str:
    """POST summary to Cloud Run /enhance endpoint."""
    url = cloud_run_url.rstrip("/") + "/enhance"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data["enhanced_prompt"]
```

If Cloud Run is unreachable, the system **degrades gracefully** to a local LLM (litellm/Ollama) or a template-based fallback:

```python
async def enhance_with_fallback(summary, config, fallback_text=None):
    """Try Cloud Run first, fall back to litellm or template."""
    if resolved_url:
        try:
            text = await enhance_via_cloud_run(summary, resolved_url)
            return EnhanceResult(text=text)
        except Exception as e:
            logger.warning("Cloud Run failed: %s — falling back to litellm", e)
    # ... local fallback
```

---

## 4. Meta-Prompt Engineering

**File:** [`cloud_run_service/prompt_builder.py`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/prompt_builder.py)

The prompt builder constructs a structured meta-prompt from the terminal context, which Gemini processes to produce the enhanced output. It includes:

- Intent classification (fix_error, explain, debug, refactor, add_feature, write_test)
- Terminal context assembly (commands, errors, output, CWD, git branch)
- Screenshot analysis instructions (when multimodal input is present)
- Adaptive behavior for screenshot-only mode (when no text buffer is available)

---

## 5. Container Image

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

**File:** [`cloud_run_service/requirements.txt`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/requirements.txt)

```
fastapi>=0.110
uvicorn[standard]>=0.29
google-genai>=1.0
pydantic>=2.5
```

The `google-genai>=1.0` dependency is the **official Google GenAI SDK** for Gemini API access.

---

## 6. Cloud Run Deployment Configuration

Every deployment (automated and manual) uses these Cloud Run settings:

```bash
gcloud run deploy prompt-shell-enhancer \
  --image "gcr.io/$PROJECT/prompt-shell-enhancer:$VERSION" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 30s
```

**Source files:**
- [`.github/workflows/release.yml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml) — automated deploy (lines 226-239)
- [`.github/workflows/deploy-cloud-run.yml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/deploy-cloud-run.yml) — manual deploy
- [`deploy.sh`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/deploy.sh) — local deploy script
- [`cloudbuild.yaml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml) — Cloud Build trigger config

---

## 7. Secret Management via Google Secret Manager

**File:** [`cloudbuild.yaml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml) (lines 58-61)

```yaml
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/gemini-api-key/versions/latest
      env: GEMINI_API_KEY
```

The Gemini API key is stored in **Google Secret Manager** and injected into the Cloud Build step at deploy time. It never appears in source code, build logs, or container images.

**Setup instructions** in [`docs/deployment.md`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/docs/deployment.md):

```bash
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --project "$PROJECT_ID"
```

---

## 8. Health Check & Post-Deploy Verification

Every deployment method includes an automated health check against the live Cloud Run service:

**From [`release.yml`](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml) (lines 251-258):**

```yaml
- name: Verify deployment health
  run: |
    URL="${{ steps.service-url.outputs.url }}"
    STATUS=$(curl -sf "$URL/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    if [ "$STATUS" != "ok" ]; then
      echo "Health check failed — service returned: $STATUS"
      exit 1
    fi
    echo "Health check passed: $URL/health -> $STATUS"
```

The pipeline **fails** if the deployed service doesn't respond with `{"status": "ok"}`.

---

## End-to-End Data Flow on Google Cloud

```
Local daemon                    Google Cloud Run                  Gemini API
─────────────                   ────────────────                  ──────────
Terminal snapshot ──┐
Voice transcript ───┤
Screenshot PNG ─────┤
                    │
                    ├──► POST /enhance ──► prompt_builder.py ──► gemini_client.py
                    │    (FastAPI)          (meta-prompt)         (google-genai SDK)
                    │                                                    │
                    │                                                    ▼
                    │                                            Gemini 2.5 Flash Lite
                    │                                            (multimodal: text+image)
                    │                                                    │
                    │◄── EnhanceResponse ◄── enhanced prompt ◄───────────┘
                    │
Clipboard ◄─────────┘
```

---

## All Evidence Files

| File | What it Proves | Link |
|------|---------------|------|
| `cloud_run_service/gemini_client.py` | Google GenAI SDK usage, Gemini API calls, multimodal input | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/gemini_client.py) |
| `cloud_run_service/main.py` | FastAPI service deployed on Cloud Run, /enhance and /health endpoints | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/main.py) |
| `cloud_run_service/prompt_builder.py` | Meta-prompt engineering for Gemini | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/prompt_builder.py) |
| `cloud_run_service/Dockerfile` | Container image for Cloud Run | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/Dockerfile) |
| `cloud_run_service/requirements.txt` | `google-genai>=1.0` dependency | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloud_run_service/requirements.txt) |
| `cloudbuild.yaml` | Cloud Build + Secret Manager + Container Registry + Cloud Run deploy | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/cloudbuild.yaml) |
| `.github/workflows/release.yml` | Automated CI/CD pipeline deploying to Cloud Run | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/release.yml) |
| `.github/workflows/deploy-cloud-run.yml` | Manual Cloud Run re-deploy workflow | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/.github/workflows/deploy-cloud-run.yml) |
| `deploy.sh` | Local deploy script using gcloud CLI | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/deploy.sh) |
| `src/prompt_shell/enhancer/enhancement_client.py` | Local client HTTP calls to Cloud Run | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/src/prompt_shell/enhancer/enhancement_client.py) |
| `docs/deployment.md` | Full deployment guide (GCP setup, secrets, troubleshooting) | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/docs/deployment.md) |
| `docs/architecture.md` | System architecture showing Cloud Run in the pipeline | [View](https://github.com/VinnyBabuManjaly/PromptShell/blob/main/docs/architecture.md) |
