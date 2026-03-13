# PromptShell — Technical Specification

> **Project**: prompt-shell
> **Version**: 0.1.0 (MVP)
> **Date**: 2026-03-12
> **Challenge**: Gemini Live Agent Challenge — Live Agents category

---

## 1. Problem Statement

When users interact with AI coding assistants (Devin, Copilot, ChatGPT, etc.) from their terminal, voice-dictated or hastily typed prompts are often vague, lack context, and produce suboptimal results. The user says *"fix the error"* but the AI has no idea which error, in which file, or what the terminal currently shows.

**This service bridges that gap** by monitoring the terminal in real-time, capturing voice prompts, and enriching them with full terminal context before sending them to the AI.

---

## 2. Goals

| # | Goal | Success Criteria |
|---|------|-----------------|
| G1 | Capture terminal context from the active terminal in real-time | Screen buffer, CWD, last N commands, exit codes accessible via API (multi-backend: tmux, iTerm2, shell_hook, generic) |
| G2 | Accept voice input and transcribe to text | < 2s latency from speech-end to transcription |
| G3 | Build context-aware enhanced prompts | Enhanced prompt includes: terminal output, CWD, recent commands, error context |
| G4 | Enhance prompts via Gemini 2.0 Flash on Google Cloud Run | Uses Google GenAI SDK; backend hosted on GCP; satisfies Gemini Live Agent Challenge requirements |
| G5 | Deliver enhanced prompt to target AI tool | Copy to clipboard / pipe to stdin / API call |
| G6 | Minimal friction UX | Single hotkey to activate; no manual context copying |

---

## 3. Non-Goals (MVP)

- Multi-monitor / multi-window aggregation
- Prompt history / analytics dashboard
- Fine-tuning or training custom models
- Windows support

---

## 4. User Flow

```
┌─────────────────────────────────────────────────────────┐
│                USER IN TERMINAL (macOS / Linux)          │
│                                                         │
│  1. User runs commands, sees output / errors            │
│  2. User presses HOTKEY (e.g. Ctrl+Shift+P)            │
│  3. Microphone activates → user speaks prompt           │
│     "fix the compilation error in the auth module"      │
│  4. Voice is transcribed to text                        │
│  5. Service reads terminal context (auto-detected       │
│     backend: tmux / iterm2 / shell_hook / generic):     │
│     - Last 100 lines of screen buffer                   │
│     - Current working directory                         │
│     - Last 5 commands + exit codes                      │
│     - Detected error patterns                           │
│  6. LLM generates enhanced prompt:                      │
│     "Fix the TypeScript compilation error TS2345 in     │
│      src/auth/middleware.ts:42 — Argument of type       │
│      'string' is not assignable to parameter of type    │
│      'AuthToken'. The last command `npm run build`      │
│      failed with exit code 1. CWD: ~/project/backend"  │
│  7. Enhanced prompt is delivered to target AI tool       │
└─────────────────────────────────────────────────────────┘
```

---

## 5. System Components

### 5.1 Terminal Monitor (`terminal-monitor`)

**Purpose**: Extract real-time terminal state from any supported terminal on macOS or Linux.

**Architecture**: A pluggable backend system with auto-detection. Each backend implements a common `TerminalBackend` interface exposing `snapshot()`, `get_cwd()`, and `get_screen_buffer()`.

**Backend Selection** (`auto` by default — tries each in order, uses first available):

| # | Backend | Platform | How It Works | Capabilities |
|---|---------|----------|-------------|--------------|
| 1 | **tmux** | macOS, Linux | `tmux capture-pane` for screen buffer; `tmux display-message` for CWD, PID, process info | Screen buffer, CWD, running process, command history |
| 2 | **iterm2** | macOS only | iTerm2 Python API (`iterm2` pip package). Optional dependency: `pip install prompt-shell[iterm2]` | Screen buffer, CWD, last command, exit code, job name |
| 3 | **shell_hook** | macOS, Linux | Lightweight precmd/preexec hook installed in the user's shell (zsh/bash/fish). Writes CWD, last command, and exit code to a state file (`~/.prompt-shell/shell_state.json`) | CWD, last command, exit code (no screen buffer) |
| 4 | **generic** | macOS, Linux | Reads shell history files (`~/.zsh_history`, `~/.bash_history`, `~/.local/share/fish/fish_history`). Detects CWD via `/proc/PID/cwd` (Linux) or `lsof -p PID` (macOS) | CWD, command history (no screen buffer) |

**Shell Hook Details** (backend `shell_hook`):
- **zsh**: `precmd` / `preexec` functions appended to `~/.zshrc`
- **bash**: `PROMPT_COMMAND` / `DEBUG` trap appended to `~/.bashrc`
- **fish**: `fish_postexec` function added to `~/.config/fish/conf.d/`
- Installed via `prompt-shell install-hook`

**Requirements by Backend**:
- **tmux**: User must be inside a tmux session.
- **iterm2**: iTerm2 with Shell Integration installed and Python API enabled. Optional dependency (`pip install prompt-shell[iterm2]`).
- **shell_hook**: Hook installed via `prompt-shell install-hook`.
- **generic**: No special setup. Always available as fallback.

**Polling Strategy**:
- **Idle mode**: Poll every 2s to maintain a rolling snapshot
- **Active mode** (after hotkey): Immediate full capture

---

### 5.2 Voice Capture (`voice-capture`)

**Purpose**: Record audio from the microphone and transcribe to text.

**Technology Options** (ordered by preference for MVP):

| Option | Pros | Cons | Latency |
|--------|------|------|---------|
| **OpenAI Whisper (local, `whisper.cpp`)** | Private, offline, accurate | Requires ~1GB model download | ~1-2s |
| **Apple Speech Framework (via pyobjc)** | Native, no download, low latency | Less accurate for technical terms | ~0.5s |
| **Deepgram / OpenAI Whisper API** | Most accurate, handles jargon | Requires internet + API key | ~1-3s |

**MVP Choice**: **Whisper.cpp** (local) with fallback to **OpenAI Whisper API**.

**Audio Pipeline**:
```
Microphone → PyAudio/sounddevice capture
           → Voice Activity Detection (VAD) via webrtcvad/silero
           → When silence detected (>1s), finalize recording
           → Whisper transcription
           → Return text
```

**Key Parameters**:
- Sample rate: 16kHz mono
- VAD aggressiveness: 2 (medium)
- Silence threshold: 1.0s
- Max recording duration: 30s
- Whisper model: `base.en` (for speed) or `small.en` (for accuracy)

---

### 5.3 Context Builder (`context-builder`)

**Purpose**: Aggregate terminal data into a structured context object.

**Context Schema**:
```json
{
  "timestamp": "2026-03-11T17:00:00Z",
  "terminal": {
    "cwd": "/Users/disen/project/backend",
    "shell": "zsh",
    "last_commands": [
      { "command": "npm run build", "exit_code": 1, "timestamp": "..." },
      { "command": "git status", "exit_code": 0, "timestamp": "..." }
    ],
    "screen_buffer": "... last 100 lines of visible output ...",
    "detected_errors": [
      {
        "type": "typescript_compilation",
        "code": "TS2345",
        "file": "src/auth/middleware.ts",
        "line": 42,
        "message": "Argument of type 'string' is not assignable..."
      }
    ],
    "running_process": null,
    "git_branch": "feature/auth-refactor"
  }
}
```

**Error Detection Engine**:
Pattern-match the screen buffer against known error signatures:
- **Build errors**: TypeScript, ESLint, Rust, Go, Python traceback
- **Runtime errors**: Node.js stack trace, Python exception, segfault
- **Test failures**: Jest, pytest, cargo test
- **Git conflicts**: merge conflict markers
- **Permission errors**: EACCES, sudo prompts

Each pattern extracts: `error_type`, `code`, `file`, `line`, `message`.

---

### 5.4 Enhancement Service (`cloud_run_service/`)

**Purpose**: Take the serialized `ContextPayload` (sent from the local client) and produce an optimized prompt using Gemini 2.0 Flash.

**Deployment**: Google Cloud Run (stateless, scales to zero, free tier covers demo scale).

**Transport**: The local client sends a JSON-encoded `ContextPayload` via `HTTP POST /enhance` and receives `{ "enhanced_prompt": "..." }` in response.

**Meta-Prompt Template**:
```
You are a prompt engineer. Given the user's raw voice command and their
terminal context, rewrite the command into a precise, actionable prompt
suitable for an AI coding assistant.

Rules:
1. Include specific file paths, error codes, and line numbers from context
2. Reference the exact error messages visible in the terminal
3. Mention the current working directory and project structure hints
4. Keep the enhanced prompt concise but complete (max ~200 words)
5. Preserve the user's intent — do not add new tasks they didn't request
6. If the terminal shows a specific technology stack, mention it

RAW VOICE COMMAND: {{voice_transcript}}

TERMINAL CONTEXT:
- CWD: {{context.terminal.cwd}}
- Last commands: {{context.terminal.last_commands}}
- Screen buffer (last 50 lines): {{context.terminal.screen_buffer}}
- Detected errors: {{context.terminal.detected_errors}}
- Git branch: {{context.terminal.git_branch}}

OUTPUT: Write the enhanced prompt only. No explanation.
```

**LLM**:
| Provider | Model | SDK | Cost | Hosting |
|----------|-------|-----|------|---------|
| **Gemini** (default) | `gemini-2.0-flash` | `google-genai` | Free tier: 1,500 req/day | **Google Cloud Run** |
| Ollama (local fallback) | `llama3.2:8b` | `litellm` | Free | Local only |
| OpenAI (optional) | `gpt-4o-mini` | `litellm` | ~$0.001/prompt | Cloud |
| Anthropic (optional) | `claude-3.5-haiku` | `litellm` | ~$0.001/prompt | Cloud |

**Default**: Gemini 2.0 Flash via Cloud Run. Local Ollama is the offline fallback.

**Cloud Run service endpoints**:
- `POST /enhance` — accepts `ContextPayload` JSON, returns `{ "enhanced_prompt": "..." }`
- `GET /health` — returns `{ "status": "ok" }` for Cloud Run health checks

---

### 5.5 Delivery Engine (`delivery`)

**Purpose**: Send the enhanced prompt to the target AI tool.

**Delivery Methods**:

| Method | Target | Implementation |
|--------|--------|---------------|
| **Clipboard** | Any tool | `pbcopy` (macOS), `xclip`/`xsel`/`wl-copy` (Linux), `pyperclip` (fallback) |
| **Paste into terminal** | Active terminal session | iTerm2 `session.async_send_text()` (macOS/iTerm2); `tmux send-keys` (tmux) |
| **API call** | Devin, ChatGPT API | HTTP POST |
| File pipe | Any tool reading a file | Write to `~/.prompt-shell/last-prompt.txt` |
| **Notification** | User feedback | `osascript` (macOS), `notify-send` (Linux), console (fallback) |

**Default flow**: Copy to clipboard + show notification with preview.

---

## 6. Hotkey & CLI System

**Global Hotkey**: Registered via accessibility APIs (`pynput` on macOS; `pynput` or `evdev` on Linux).

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+P` | Activate voice capture → enhance → deliver |
| `Ctrl+Shift+L` | Capture terminal context only (no voice) → enhance last clipboard text |
| `Ctrl+Shift+R` | Re-enhance last prompt with updated terminal context |
| `Esc` | Cancel ongoing voice capture |

**CLI Commands**:

| Command | Description |
|---------|-------------|
| `prompt-shell start` | Start the service daemon |
| `prompt-shell install-hook` | Install shell hook for current shell (zsh/bash/fish) |
| `prompt-shell context` | Capture and display terminal context |
| `prompt-shell context --backend tmux` | Capture context using a specific backend |

---

## 7. Configuration

File: `~/.prompt-shell/config.yaml`

```yaml
# Terminal
terminal:
  backend: auto                # auto | tmux | iterm2 | shell_hook | generic
  screen_buffer_lines: 100
  poll_interval_ms: 2000

# Voice
voice:
  engine: whisper_local        # whisper_local | whisper_api | apple_speech
  whisper_model: base.en       # tiny.en | base.en | small.en
  silence_threshold_sec: 1.0
  max_duration_sec: 30
  vad_aggressiveness: 2

# LLM
llm:
  provider: ollama             # ollama | openai | anthropic
  model: llama3.2:8b
  api_key: ${OPENAI_API_KEY}   # env var reference
  temperature: 0.3
  max_tokens: 500

# Delivery
delivery:
  method: clipboard            # clipboard | iterm_paste | api | file
  show_notification: true
  notification_preview_chars: 100

# Hotkeys
hotkeys:
  activate: ctrl+shift+p
  context_only: ctrl+shift+l
  re_enhance: ctrl+shift+r
  cancel: escape

# Error patterns (extensible)
error_patterns:
  - name: typescript
    regex: "error TS(\\d+): (.+)"
    extract: [code, message]
  - name: python_traceback
    regex: "File \"(.+)\", line (\\d+)"
    extract: [file, line]
```

---

## 8. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | **Python 3.11+** | Rich ML/audio ecosystem; iTerm2 API is Python-native |
| Terminal (tmux) | `subprocess` (tmux CLI) | `tmux capture-pane`, `tmux display-message` — works on any terminal inside tmux |
| Terminal (iterm2) | `iterm2` (pip, optional) | Official iTerm2 scripting library. Optional: `pip install prompt-shell[iterm2]` |
| Terminal (shell_hook) | Shell rc files + JSON state | Lightweight precmd/preexec hooks for zsh/bash/fish |
| Terminal (generic) | Shell history files + `/proc` / `lsof` | Fallback: reads `~/.zsh_history`, `~/.bash_history`, fish history |
| Audio capture | `sounddevice` + `numpy` | Low-latency, cross-platform audio |
| VAD | Energy-based (custom) | Noise-floor calibration; no C binary dependency |
| Transcription | `faster-whisper` | Fast local inference with int8 quantization |
| **LLM (primary)** | **`google-genai` SDK + Gemini 2.0 Flash** | **Google GenAI SDK; hosted on Cloud Run; satisfies challenge requirements** |
| LLM (fallback) | `litellm` | Unified interface to Ollama/OpenAI/Anthropic for offline/alt use |
| **Cloud hosting** | **Google Cloud Run** | **Stateless FastAPI service; scales to zero; satisfies GCP hosting requirement** |
| Hotkeys | `pynput` | Global hotkey registration on macOS and Linux |
| Clipboard | `pbcopy` / `xclip` / `xsel` / `wl-copy` / `pyperclip` | Platform-native clipboard: `pbcopy` (macOS), `xclip`/`xsel`/`wl-copy` (Linux), `pyperclip` (fallback) |
| Notifications | `osascript` / `notify-send` | `osascript` (macOS), `notify-send` (Linux), console (fallback) |
| Config | `pydantic` + `PyYAML` | Typed config with validation |
| CLI | `typer` | Ergonomic CLI framework |
| Async | `asyncio` | Required by iTerm2 API; used across the service |
| HTTP client | `httpx` | Async HTTP client for local → Cloud Run calls |
| Cloud Run service | `fastapi` + `uvicorn` | Lightweight ASGI service for the enhancement endpoint |
| Packaging | `uv` / `pyproject.toml` | Modern Python packaging with optional extras (`[iterm2]`, `[gcp]`) |

---

## 9. Directory Structure

```
prompt-shell/
├── SPEC.md                          # This file
├── ARCHITECTURE.md                  # System architecture
├── AGENTS.md                        # Build/run instructions
├── pyproject.toml                   # Project metadata & dependencies
├── config.example.yaml              # Example configuration
├── Dockerfile                       # Local client Docker image
├── cloud_run_service/               # Google Cloud Run enhancement service
│   ├── main.py                      # FastAPI app (POST /enhance, GET /health)
│   ├── prompt_builder.py            # Meta-prompt template renderer
│   ├── gemini_client.py             # google-genai SDK wrapper
│   ├── Dockerfile                   # Cloud Run Docker image
│   └── requirements.txt             # fastapi, uvicorn, google-genai, pydantic
├── src/
│   └── prompt_shell/
│       ├── __init__.py
│       ├── main.py                  # Entry point, CLI
│       ├── config.py                # Configuration loader
│       ├── terminal/
│       │   ├── __init__.py
│       │   ├── base.py              # TerminalBackend ABC (common interface)
│       │   ├── tmux.py              # tmux backend (capture-pane, display-message)
│       │   ├── iterm2_backend.py    # iTerm2 backend (optional, macOS only)
│       │   ├── shell_hook.py        # Shell hook backend (reads state file)
│       │   ├── generic.py           # Generic fallback (history files + /proc/lsof)
│       │   ├── detector.py          # Auto-detection: tmux → iterm2 → shell_hook → generic
│       │   ├── hooks/               # Shell hook install scripts
│       │   │   ├── zsh_hook.sh      # precmd/preexec for zsh
│       │   │   ├── bash_hook.sh     # PROMPT_COMMAND/DEBUG trap for bash
│       │   │   └── fish_hook.fish   # fish_postexec for fish
│       │   ├── context.py           # Context builder
│       │   └── error_patterns.py    # Error detection regex engine
│       ├── voice/
│       │   ├── __init__.py
│       │   ├── capture.py           # Audio recording + VAD
│       │   └── transcribe.py        # Whisper / Apple Speech
│       ├── enhancer/
│       │   ├── __init__.py
│       │   ├── enhancement_client.py  # HTTP client → Cloud Run POST /enhance
│       │   ├── prompt_builder.py      # Fallback template (no Cloud Run)
│       │   └── llm_client.py          # LiteLLM wrapper (Ollama/OpenAI/Anthropic fallback)
│       └── delivery/
│           ├── __init__.py
│           ├── clipboard.py         # Cross-platform clipboard delivery
│           ├── terminal_paste.py    # Terminal paste (iTerm2 / tmux send-keys)
│           └── notification.py      # Cross-platform notifications
└── tests/
    ├── test_terminal_monitor.py
    ├── test_terminal_backends.py    # Tests for tmux, iterm2, shell_hook, generic
    ├── test_context_builder.py
    ├── test_voice_capture.py
    ├── test_prompt_shell.py
    ├── test_enhancement_client.py   # Tests for Cloud Run HTTP client
    └── test_error_patterns.py
```

---

## 10. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Terminal output may contain secrets | Screen buffer is held in memory only, never persisted. Configurable redaction patterns for API keys, tokens. |
| Voice data privacy | All transcription local by default (faster-whisper). Cloud APIs opt-in only. |
| Context sent to Cloud Run | ContextPayload is sent over HTTPS to Cloud Run. Redaction patterns strip secrets before serialization. |
| Gemini API key | Stored as a Cloud Run environment variable (or Secret Manager). Never in config files or source code. |
| LLM data leakage | Gemini on Cloud Run is default. Local Ollama is the offline fallback. Warning shown when cloud is selected. |
| API keys in config | Support env var references (`${VAR}`) in config. `.prompt-shell/` added to `.gitignore`. |
| Microphone access | macOS will prompt for permission. Linux uses PulseAudio/PipeWire permissions. Service cannot bypass. |
| Cloud Run endpoint | Endpoint is public (unauthenticated) for demo simplicity. Production deployments should add Cloud Run IAM auth. |

---

## 11. MVP Milestones

| Phase | Deliverable | Effort |
|-------|------------|--------|
| **P0** | Terminal monitor: multi-backend (tmux, iTerm2, shell_hook, generic) + auto-detection | 2-3 days |
| **P1** | Voice capture: record + transcribe with Whisper | 1-2 days |
| **P2** | Context builder: aggregate terminal data + error detection | 1 day |
| **P3** | Cloud Run service: FastAPI + Google GenAI SDK + Gemini 2.0 Flash | 1 day |
| **P4** | Enhancement client: local HTTP client → Cloud Run; fallback to template | 0.5 day |
| **P5** | Delivery: clipboard + notification | 0.5 day |
| **P6** | Hotkey system + CLI + config | 1 day |
| **P7** | GCP deployment: Cloud Run deploy + architecture diagram + demo video | 1 day |
| **P8** | Integration testing + polish | 1-2 days |

---

## 12. Challenge Compliance (Gemini Live Agent Challenge)

| Requirement | How Met |
|-------------|---------|
| Uses a Gemini model | Gemini 2.0 Flash via `google-genai` SDK in Cloud Run service |
| Uses Google GenAI SDK or ADK | `google-genai` Python SDK (`genai.Client`) |
| Uses at least one Google Cloud service | Cloud Run (compute) |
| Backend hosted on Google Cloud | FastAPI service deployed to Cloud Run |
| Category fit | **Live Agents** — real-time voice input + live terminal context + multimodal audio/text pipeline |

---

## 13. Future Enhancements (Post-MVP)

- **Windows support**: Terminal backends for Windows Terminal / PowerShell
- **Prompt history**: SQLite-backed prompt log with search
- **Prompt templates**: User-defined templates for common tasks (debug, refactor, explain)
- **IDE integration**: VS Code extension that reads terminal panel
- **Team sharing**: Share effective prompt patterns across a team
- **Fine-tuned enhancer**: Train a small model specifically for prompt rewriting
- **Streaming delivery**: Stream enhanced prompt directly into AI chat input
- **Multi-language voice**: Support non-English voice input
