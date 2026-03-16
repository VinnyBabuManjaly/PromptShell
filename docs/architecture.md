# Architecture — PromptShell

## System Overview

PromptShell uses a **split client/cloud architecture**. The local daemon handles everything that needs to be on-device (terminal capture, voice, hotkeys, delivery). The enhancement step runs on Google Cloud Run, where a FastAPI service calls the Gemini API via the Google GenAI SDK. This satisfies the Gemini Live Agent Challenge requirements: Gemini model, Google GenAI SDK, Google Cloud service, and backend hosted on Google Cloud.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        macOS / Linux Host (Local Client)                 │
│                                                                          │
│  ┌─────────────┐    ┌───────────────────────────────────────────────┐   │
│  │  Terminal    │◄──►│              prompt-shell (daemon)             │   │
│  │  (tmux /    │    │                                                │   │
│  │   iTerm2 /  │    │  ┌─────────────┐    ┌──────────────────────┐  │   │
│  │   any+hook /│    │  │  Terminal    │    │   Voice Capture       │  │   │
│  │   generic)  │    │  │  Monitor     │    │   (Microphone)        │  │   │
│  └─────────────┘    │  │  (4 backends)│    │   + Transcription     │  │   │
│                      │  └──────┬───────┘    └──────────┬───────────┘  │   │
│                      │         │                        │              │   │
│                      │         ▼                        ▼              │   │
│                      │  ┌──────────────────────────────────────────┐  │   │
│                      │  │            Context Aggregator                │  │   │
│                      │  │   (merge terminal + voice → ContextPayload│  │   │
│                      │  └──────────────────┬───────────────────────┘  │   │
│                      │                      │                          │   │
│                      │                      │  HTTP POST /enhance      │   │
│                      │                      ▼                          │   │
│                      │  ┌──────────────────────────────────────────┐  │   │
│                      │  │       AI Orchestrator                  │  │   │
│                      │  │  (sends ContextPayload to Cloud Run)      │  │   │
│                      │  └──────────────────┬───────────────────────┘  │   │
│                      │                      │                          │   │
│  ┌──────────────┐    │                      │  ◄── enhanced prompt     │   │
│  │  Global       │── Ctrl+Shift+P ─────►   │                          │   │
│  │  Hotkey       │                      │  ┌──────────────────────────┐  │   │
│  │  Listener     │                      │  │     Delivery Engine       │  │   │
│  └──────────────┘    │                  │  │  (Clipboard / Paste /     │  │   │
│                      │                  │  │   API / File)             │  │   │
│                      │                  └──┴──────────────────────────┘  │   │
│                      └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                          HTTP POST /enhance
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Google Cloud — Cloud Run Service                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI  POST /enhance                                           │   │
│  │                                                                   │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │  Prompt Engineering Engine  (renders context into LLM prompt)     │  │   │
│  │  └───────────────────────────┬────────────────────────────────┘  │   │
│  │                              │                                    │   │
│  │                              ▼                                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │  Google GenAI SDK  →  Gemini 2.0 Flash                     │  │   │
│  │  │  (google-genai, GEMINI_API_KEY)                             │  │   │
│  │  └───────────────────────────┬────────────────────────────────┘  │   │
│  │                              │                                    │   │
│  │                              ▼                                    │   │
│  │               enhanced_prompt (string)  →  HTTP response          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Detail

### 1. Terminal State Monitor

```
┌──────────────────────────────────────────────────────────┐
│              Terminal State Monitor (Multi-Backend)              │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Backend Detector (auto mode)                      │    │
│  │ Probe order: tmux → iterm2 → shell_hook → generic │    │
│  └──────────┬───────────────────────────────────────┘    │
│             │ selects                                     │
│             ▼                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ TerminalBackend ABC                               │    │
│  │  snapshot() → TerminalState                       │    │
│  │  get_cwd() → str                                  │    │
│  │  get_screen_buffer() → str | None                 │    │
│  └──────────────────────────────────────────────────┘    │
│             │ implemented by                              │
│  ┌──────────┴──────────┬───────────┬──────────────┐      │
│  │                     │           │              │      │
│  ▼                     ▼           ▼              ▼      │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │
│  │  tmux    │ │  iterm2  │ │shell_hook │ │ generic  │  │
│  │          │ │(optional)│ │           │ │          │  │
│  │capture-  │ │Python API│ │precmd/    │ │~/.zsh_   │  │
│  │pane,     │ │async get │ │preexec    │ │history,  │  │
│  │display-  │ │screen,   │ │state file │ │/proc/cwd │  │
│  │message   │ │variables │ │(JSON)     │ │or lsof   │  │
│  └──────────┘ └──────────┘ └───────────┘ └──────────┘  │
│  macOS+Linux  macOS only   macOS+Linux   macOS+Linux    │
│                                                          │
│  ┌────────────────┐                                      │
│  │ State Cache    │                                      │
│  │ - screen_buf   │                                      │
│  │ - cwd          │                                      │
│  │ - last_cmds[]  │                                      │
│  │ - exit_codes[] │                                      │
│  │ - git_branch   │                                      │
│  │ - job_name     │                                      │
│  └────────────────┘                                      │
│                                                          │
│  Polling: 2s idle / immediate on trigger                 │
└──────────────────────────────────────────────────────────┘
```

**Backend detection lifecycle**:
1. On startup, `BackendDetector` probes available backends in order: tmux → iterm2 → shell_hook → generic
2. The first backend that reports `is_available() == True` is selected
3. User can override with `--backend <name>` CLI flag or `terminal.backend` config
4. Selected backend's `snapshot()` is called on each poll cycle
5. Maintain a `TerminalState` dataclass with latest data
6. On `snapshot()` call, return a frozen copy of current state

**Backend-specific notes**:
- **tmux**: Checks `$TMUX` env var. Uses `tmux capture-pane -p` for screen buffer, `tmux display-message -p '#{pane_current_path}'` for CWD.
- **iterm2**: Requires `iterm2` pip package (optional extra). Connects via `iterm2.Connection`. Only works on macOS with iTerm2 running + Python API enabled.
- **shell_hook**: Reads `~/.prompt-shell/shell_state.json` written by shell hooks. No screen buffer, but provides CWD, last command, and exit code.
- **generic**: Always available. Reads shell history files and infers CWD via `/proc/PID/cwd` (Linux) or `lsof -p PID` (macOS).

---

### 2. Voice Capture

```
┌────────────────────────────────────────────┐
│            Voice Capture Pipeline            │
│                                             │
│  Microphone                                 │
│      │                                      │
│      ▼                                      │
│  ┌──────────┐   ┌───────┐   ┌───────────┐ │
│  │ Audio    │──►│  VAD  │──►│ Whisper   │ │
│  │ Stream   │   │(energy│   │ Transcribe│ │
│  │ 16kHz    │   │-based)│   │           │ │
│  │ mono     │   │       │   │ text out  │ │
│  └──────────┘   │detect │   └───────────┘ │
│                  │speech │                  │
│                  │end    │                  │
│                  └───────┘                  │
│                                             │
│  States: IDLE → LISTENING → PROCESSING     │
│                    │                        │
│                    ▼                        │
│          Audio frames accumulated           │
│          until silence > 1s detected        │
└────────────────────────────────────────────┘
```

---

### 3. Context Aggregator

```
┌────────────────────────────────────────────────┐
│              Context Aggregator                     │
│                                                  │
│  Input:                                          │
│  ├── TerminalState (from Monitor)                │
│  └── voice_transcript (from Voice Capture)       │
│                                                  │
│  Processing:                                     │
│  ├── 1. Truncate screen buffer to last N lines   │
│  ├── 2. Run Error Detection Engine               │
│  │       ├── Regex pattern matching              │
│  │       ├── Extract: type, code, file, line     │
│  │       └── Classify severity                   │
│  ├── 3. Detect project type from CWD             │
│  │       ├── package.json → Node/TS              │
│  │       ├── Cargo.toml → Rust                   │
│  │       ├── go.mod → Go                         │
│  │       └── pyproject.toml → Python             │
│  ├── 4. Extract git metadata                     │
│  └── 5. Build ContextPayload dataclass           │
│                                                  │
│  Output: ContextPayload (frozen, serializable)   │
└────────────────────────────────────────────────┘
```

---

### 4. Cloud Run Enhancement Service

The local client serializes `ContextPayload` as JSON and sends it via HTTP POST to the Cloud Run service. The service is stateless and auto-scales to zero when idle (zero cost at rest).

```
┌──────────────────────────────────────────────────────────┐
│          Cloud Run Service  (cloud_run_service/)          │
│                                                          │
│  POST /enhance                                           │
│  ├── Input: ContextPayload (JSON)                        │
│  │                                                       │
│  │  ┌──────────────────────────────────────────────┐    │
│  │  │  Prompt Engineering Engine                          │    │
│  │  │                                               │    │
│  │  │  Renders system prompt with:                  │    │
│  │  │  - voice_transcript                           │    │
│  │  │  - cwd, last_commands                         │    │
│  │  │  - screen_buffer (truncated)                  │    │
│  │  │  - detected_errors                            │    │
│  │  │  - project_type, git_branch                   │    │
│  │  └──────────────┬────────────────────────────────┘    │
│  │                 │                                      │
│  │                 ▼                                      │
│  │  ┌──────────────────────────────────────────────┐    │
│  │  │  Google GenAI SDK                             │    │
│  │  │                                               │    │
│  │  │  client = genai.Client(api_key=GEMINI_API_KEY)│    │
│  │  │  model  = "gemini-2.5-flash-lite"                  │    │
│  │  │  response = client.models.generate_content()  │    │
│  │  └──────────────┬────────────────────────────────┘    │
│  │                 │                                      │
│  │                 ▼                                      │
│  └── Output: { "enhanced_prompt": "..." }                │
│                                                          │
│  GET /health  →  { "status": "ok" }                      │
│                                                          │
│  Environment variables:                                  │
│  - GEMINI_API_KEY   (Google AI Studio key)               │
│  - LOG_LEVEL        (default: INFO)                      │
└──────────────────────────────────────────────────────────┘
```

**Fallback**: If the Cloud Run service is unreachable or returns an error, the AI Orchestrator falls back to a local LLM (Ollama via litellm). If the local LLM is also unavailable, it falls back to a template-based prompt. All paths return through the AI Orchestrator — the user always gets a structured prompt, never a raw error.

---

### 5. Delivery Engine

```
┌────────────────────────────────────────────┐
│           Delivery Engine                    │
│                                             │
│  Input: enhanced_prompt (string)            │
│                                             │
│  Strategy (from config):                    │
│  ┌──────────────┐                          │
│  │clipboard     │──► pbcopy (macOS)         │
│  │              │    xclip/xsel/wl-copy (L) │
│  │              │    pyperclip (fallback)    │
│  ├──────────────┤                          │
│  │terminal_paste│──► iterm2 send_text()     │
│  │              │    tmux send-keys          │
│  ├──────────────┤                          │
│  │api           │──► HTTP POST to target    │
│  ├──────────────┤                          │
│  │file          │──► Write to pipe file     │
│  └──────────────┘                          │
│                                             │
│  Always: notification with preview          │
│  (osascript on macOS, notify-send on Linux) │
└────────────────────────────────────────────┘
```

---

## Data Flow (Sequence)

```
User       Hotkey      VoiceCapture   TerminalBackend  ContextBuilder  EnhancementClient  CloudRun(Gemini)  Delivery
  │           │              │                │               │                │                  │             │
  │─press─────►              │                │               │                │                  │             │
  │           │─activate────►│                │               │                │                  │             │
  │           │              │─listen──►      │               │                │                  │             │
  │─speak──────────────────►│               │               │                │                  │             │
  │           │              │◄─silence──     │               │                │                  │             │
  │           │              │─transcribe     │               │                │                  │             │
  │           │  (parallel)  │                │◄─snapshot()   │                │                  │             │
  │           │              │                │──state────────►               │                  │             │
  │           │              │──transcript────────────────────►               │                  │             │
  │           │              │                │               │─serialize──────►                  │             │
  │           │              │                │               │                │─POST /enhance────►             │
  │           │              │                │               │                │                  │─Gemini──►   │
  │           │              │                │               │                │                  │◄─result─    │
  │           │              │                │               │                │◄─enhanced_prompt──            │
  │           │              │                │               │                │──────────────────────────────►│
  │◄────────────────────────────────────────────────notification + clipboard──────────────────────────────────│
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Google Cloud                        │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │           Cloud Run Service                   │    │
│  │                                               │    │
│  │  - Region: us-central1 (or nearest)           │    │
│  │  - Min instances: 0 (scale to zero, free)     │    │
│  │  - Max instances: 10                          │    │
│  │  - Memory: 512Mi                              │    │
│  │  - CPU: 1                                     │    │
│  │  - Timeout: 30s                               │    │
│  │  - Auth: unauthenticated (public endpoint)    │    │
│  │                                               │    │
│  │  Secrets (via env vars):                      │    │
│  │  - GEMINI_API_KEY → Secret Manager            │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Services used:                                       │
│  ✓ Cloud Run      (compute hosting)                   │
│  ✓ Gemini API     (via Google AI Studio key)          │
│  ✓ Secret Manager (optional, for API key)             │
│  ✓ Artifact Registry (Docker image storage)           │
└─────────────────────────────────────────────────────┘
```

### Deploy commands

```bash
# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/prompt-shell-enhancer ./cloud_run_service/

# Deploy to Cloud Run
gcloud run deploy prompt-shell-enhancer \
  --image gcr.io/$PROJECT_ID/prompt-shell-enhancer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 10
```

---

## Error Handling Strategy

| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Backend Detection | No backend available | Fall through to generic (always available). Log warning. |
| tmux Backend | Not inside tmux session | `is_available()` returns False; detector moves to next backend. |
| iterm2 Backend | iTerm2 not running / API disabled | `is_available()` returns False; detector moves to next backend. |
| shell_hook Backend | Hook not installed / state file missing | `is_available()` returns False; falls to generic. User prompted to run `prompt-shell install-hook`. |
| generic Backend | No shell history found | Return empty history. CWD via `/proc` (Linux) or `lsof` (macOS). |
| Voice Capture | No microphone permission | Show OS permission prompt. Log error. |
| Voice Capture | No speech detected (timeout) | Cancel gracefully. Show "No speech detected" notification. |
| Whisper | Model not downloaded | Auto-download on first use. Show progress notification. |
| Cloud Run | Service unreachable / cold start timeout | AI Orchestrator falls back to local LLM, then template. |
| Cloud Run | Returns 5xx | AI Orchestrator falls back to local LLM, then template. |
| Gemini API | Rate limit / quota exceeded | Cloud Run returns 429; AI Orchestrator falls back to local LLM, then template. |
| Delivery | Clipboard failure | Fall back to file pipe + notification. |

---

## Performance Budget

| Step | Target Latency | Notes |
|------|---------------|-------|
| Hotkey detection | < 50ms | Native event loop |
| Terminal snapshot | < 200ms | tmux/iterm2: fast local calls. shell_hook: file read. generic: history parse + /proc or lsof. |
| Voice capture | User-dependent | Ends on silence detection |
| Transcription | < 2s | Whisper base.en on Apple Silicon |
| Context building | < 100ms | Pure CPU, regex matching |
| HTTP POST to Cloud Run | < 200ms | Network + cold start amortised to ~0 on warm instances |
| Gemini enhancement | < 1.5s | Gemini 2.0 Flash — optimised for low latency |
| Delivery | < 100ms | Clipboard is instant |
| **Total (excl. speech)** | **< 4.5s** | End-to-end after speech ends (0.5–1s faster than local Ollama) |
