# prompt-shell

[![CI](https://github.com/disencd/prompt-shell/actions/workflows/ci.yml/badge.svg)](https://github.com/disencd/prompt-shell/actions/workflows/ci.yml)
[![Security](https://github.com/disencd/prompt-shell/actions/workflows/security.yml/badge.svg)](https://github.com/disencd/prompt-shell/actions/workflows/security.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A voice-activated, terminal-aware prompt enhancer for AI coding assistants.
It runs as a lightweight daemon on macOS and Linux, monitoring your terminal
in real-time. When you speak a vague command like *"fix the error"*, it
captures your full terminal context — screen buffer, working directory,
recent commands, detected error patterns, git branch — and rewrites it into
a precise, actionable prompt that any AI assistant can act on immediately.

Enhancement is powered by **Gemini 2.0 Flash** running on **Google Cloud Run**,
using the **Google GenAI SDK**.

## Why

AI coding assistants work best when prompts are specific. But when you are
deep in a debugging session, you don't want to manually copy error messages,
file paths, and line numbers into a prompt. This service does that
automatically: you speak (or type) a rough instruction, and it produces a
context-rich prompt ready for Devin, Copilot, ChatGPT, or any other tool.

## How It Works

```
You say: "fix the error"

The service captures:
  - Screen buffer showing: error TS2345 in src/auth/middleware.ts:42
  - CWD: ~/project/backend
  - Last command: npm run build (exit code 1)
  - Git branch: feature/auth-refactor

  Local client sends ContextPayload → Cloud Run → Gemini 2.0 Flash

Enhanced prompt:
  "Fix the TypeScript compilation error TS2345 in src/auth/middleware.ts:42 —
   Argument of type 'string' is not assignable to parameter of type 'AuthToken'.
   The last command `npm run build` failed with exit code 1.
   CWD: ~/project/backend, branch: feature/auth-refactor"
```

## Architecture

```
Local Client (macOS / Linux)          Google Cloud Run
────────────────────────────          ────────────────────────────────
Hotkey listener                       POST /enhance
Terminal snapshot (4 backends)   →    FastAPI service
Voice capture + transcription         Google GenAI SDK
Context builder                   ←   Gemini 2.0 Flash
Clipboard delivery
```

## Features

### Terminal Context Capture

Four pluggable backends auto-detected at startup (tmux > iTerm2 > shell hook > generic):

| Backend | Screen Buffer | CWD | Commands | Exit Code | Setup |
|---------|:---:|:---:|:---:|:---:|-------|
| **tmux** | Yes | Yes | Yes | Via hook | Be inside tmux |
| **iterm2** | Yes | Yes | Yes | Yes | `pip install .[iterm2]` |
| **shell_hook** | No | Yes | Yes | Yes | `prompt-shell install-hook` |
| **generic** | No | Yes | History | No | None (always available) |

- Polls every 2 s in idle mode; captures immediately on hotkey trigger
- Detects project type from manifest files (package.json, Cargo.toml, go.mod, pyproject.toml)
- Reads git branch from the working directory

### Error Detection

A regex engine scans the terminal output and extracts structured error
info (type, code, file, line, message) for 12+ pattern families:

- **Build errors** — TypeScript (`TS*`), ESLint, Rust (`cargo`), Go, Python
- **Runtime errors** — Node.js stack traces, Python tracebacks, segfaults
- **Test failures** — Jest, pytest, `cargo test`
- **Git conflicts** — merge conflict markers
- **Permission errors** — EACCES, sudo prompts

### Voice Capture and Transcription

- Records from the microphone with energy-based voice activity detection (VAD)
- Auto-calibrates a noise floor from the first 0.5 s, then ends on 1 s of silence
- Three transcription backends (auto-fallback):
  - **faster-whisper** (local, offline, private) — default
  - **OpenAI Whisper API** (cloud, most accurate for jargon)
  - **Apple Speech Framework** (macOS native, lowest latency)

### Prompt Enhancement (Gemini on Cloud Run)

- Serializes terminal context + voice transcript into a `ContextPayload`
- Sends it via HTTP POST to the **Cloud Run** enhancement service
- The service builds a meta-prompt and calls **Gemini 2.0 Flash** via the **Google GenAI SDK**
- Falls back to a template-based prompt if the Cloud Run service is unavailable

### Delivery

- **Clipboard** — `pbcopy` (macOS), `xclip` / `xsel` / `wl-copy` (Linux)
- **Terminal paste** — iTerm2 `send_text()`, tmux `send-keys`
- **File pipe** — writes to `~/.prompt-shell/last-prompt.txt`
- **Notification** — `osascript` (macOS), `notify-send` (Linux)

### Global Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+P` | Voice capture, enhance, deliver |
| `Ctrl+Shift+L` | Enhance last clipboard text with terminal context (no voice) |
| `Ctrl+Shift+R` | Re-enhance last prompt with updated terminal context |
| `Esc` | Cancel ongoing voice capture |

### CLI

```
prompt-shell start          # Start the daemon with global hotkeys
prompt-shell enhance "..."  # One-shot: enhance a text prompt
prompt-shell context        # Show current terminal context
prompt-shell install-hook   # Install shell hook (zsh/bash/fish)
prompt-shell init           # Generate default config
```

### Security

- Screen buffer is held in memory only, never persisted to disk
- All transcription is local by default (Whisper); cloud APIs are opt-in
- Gemini API key is read from the `GEMINI_API_KEY` environment variable; never stored in config files
- API keys are referenced via environment variables (`${VAR}` syntax in config)
- Configurable redaction patterns for secrets in terminal output

## Quick Start

```bash
pip install prompt-shell

# Generate default config at ~/.prompt-shell/config.yaml
prompt-shell init

# Install shell hook for terminal state capture (zsh/bash/fish)
prompt-shell install-hook

# One-shot: enhance a prompt with current terminal context
prompt-shell enhance "fix the build error"

# Or start the daemon with global hotkeys
prompt-shell start
```

### Configuration

All settings live in `~/.prompt-shell/config.yaml`:

```yaml
terminal:
  backend: auto          # auto | tmux | iterm2 | shell_hook | generic

voice:
  engine: whisper_local  # whisper_local | whisper_api | apple_speech
  whisper_model: base.en

llm:
  provider: gemini                          # gemini | ollama | openai | anthropic
  model: gemini-2.0-flash
  api_key: ${GEMINI_API_KEY}
  cloud_run_url: ${CLOUD_RUN_URL}           # URL of the deployed Cloud Run service

delivery:
  method: clipboard      # clipboard | iterm_paste | api | file
  show_notification: true
```

## Google Cloud Deployment

The enhancement service runs on Cloud Run using **Gemini 2.0 Flash** via the **Google GenAI SDK**. Deploy it once; the local client calls it on every hotkey trigger.

### One-command deploy

```bash
export PROJECT_ID=your-gcp-project-id
export GEMINI_API_KEY=your-gemini-api-key
bash deploy.sh
```

`deploy.sh` enables the required GCP APIs, builds the container image via Cloud Build, deploys to Cloud Run, and prints the service URL with the config snippet to paste.

### Manual steps (if you prefer)

```bash
# Authenticate and set project
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

# Build image via Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/prompt-shell-enhancer ./cloud_run_service/

# Deploy to Cloud Run
gcloud run deploy prompt-shell-enhancer \
  --image gcr.io/$PROJECT_ID/prompt-shell-enhancer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 30s

# Get service URL
export CLOUD_RUN_URL=$(gcloud run services describe prompt-shell-enhancer \
  --region us-central1 --format 'value(status.url)')
```

### Verify the deployment

```bash
curl $CLOUD_RUN_URL/health
# {"status":"ok"}

curl -X POST $CLOUD_RUN_URL/enhance \
  -H "Content-Type: application/json" \
  -d '{"voice_transcript": "fix the error", "cwd": "/app"}'
```

### Local config

Add the service URL to `~/.prompt-shell/config.yaml`:

```yaml
llm:
  provider: gemini
  model: gemini-2.0-flash
  api_key: ${GEMINI_API_KEY}
  cloud_run_url: ${CLOUD_RUN_URL}
```

### CI/CD (automated deploys)

The repository includes two options for automated deployment:

- **`.github/workflows/deploy-cloud-run.yml`** — GitHub Actions workflow that deploys on every push to `main` that touches `cloud_run_service/`. Requires three repository secrets: `GCP_PROJECT_ID`, `GCP_SA_KEY` (service account JSON, base64-encoded), and `GEMINI_API_KEY`.
- **`cloudbuild.yaml`** — Cloud Build config for use with a Cloud Build trigger. The `GEMINI_API_KEY` is pulled from Secret Manager (secret name: `gemini-api-key`).

### Cost

**~$0/month** at demo/personal scale — Cloud Run scales to zero and the free tier covers millions of requests/month. Gemini 2.0 Flash free tier covers 1,500 requests/day.

## Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](AGENTS.md) | Development guide — prerequisites, build/test/lint commands, cross-platform notes, and contribution workflow |
| [docs/spec.md](docs/spec.md) | Full technical specification — problem statement, requirements, API design, data models, and implementation plan |
| [docs/architecture.md](docs/architecture.md) | System architecture — ASCII diagrams, module layout, data flow, Cloud Run deployment, and extension points |
| [docs/article.md](docs/article.md) | Published article — "I Built a Voice-Activated Prompt Enhancer That Reads Your Terminal" |
| [config.example.yaml](config.example.yaml) | Annotated configuration template with all available options |

## Development

```bash
git clone https://github.com/VinnyBabuManjaly/PromptShell.git
cd PromptShell
uv sync --extra dev
uv run ruff check src/ tests/
uv run pytest tests/ -v
```

## Releasing

```bash
# 1. Update version in pyproject.toml
# 2. Commit and tag
git tag v0.1.0
git push origin v0.1.0
# CI/CD handles: test -> build -> PyPI publish -> GitHub Release -> Docker image
```

## Branch Protection (Recommended)

Configure in GitHub Settings > Branches > `main`:
- Require status check **"CI Pass"** before merging
- Require PR reviews (1+)
- Require branches to be up to date
- Do not allow force pushes

## License

MIT
