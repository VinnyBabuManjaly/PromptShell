# PromptShell — Development Guide

For architecture diagrams and the full technical spec, see [`docs/architecture.md`](architecture.md) and [`docs/spec.md`](spec.md).

## Prerequisites

- **macOS or Linux**
- **Python 3.11+**
- **uv** (recommended) or pip for package management

### For Cloud Run deployment
- **Google Cloud SDK** (`gcloud`) — [install](https://cloud.google.com/sdk/docs/install)
- **Google Cloud project** with Cloud Run API enabled
- **Gemini API key** — get a free key at [Google AI Studio](https://aistudio.google.com/)

### Optional (for specific backends)
- **tmux** — recommended for best terminal context (screen buffer capture)
- **iTerm2 3.3+** (macOS) — with Python API enabled for `iterm2` backend
- **xclip/xsel/wl-clipboard** (Linux) — for clipboard support

## Quick Start

```bash
cd prompt-shell

# Install dependencies (faster-whisper and all core deps are included)
uv sync

# Initialize config directory (~/.prompt-shell/config.yaml)
uv run prompt-shell init

# Install the shell hook for terminal state capture
# Automatically appends a source line to ~/.zshrc, ~/.bashrc, or fish conf.d/
uv run prompt-shell install-hook
# Reload the current session without opening a new shell:
# zsh:  source ~/.prompt-shell/hook.zsh
# bash: source ~/.prompt-shell/hook.bash
# fish: source ~/.config/fish/conf.d/prompt_shell.fish

# Run a single enhancement (text mode, no voice/terminal needed)
uv run prompt-shell enhance "fix the build error"

# Run with voice input
uv run prompt-shell enhance --voice

# Start the daemon with global hotkeys
uv run prompt-shell start
```

## Terminal Backends

The service auto-detects the best backend for your environment:

| Backend | Screen Buffer | CWD | Commands | Exit Code | Setup |
|---------|:---:|:---:|:---:|:---:|-------|
| **tmux** | Yes | Yes | Yes | Via hook | Be inside tmux |
| **iterm2** | Yes | Yes | Yes | Yes | `uv sync --extra iterm2` + enable API |
| **shell_hook** | No | Yes | Yes | Yes | `prompt-shell install-hook` |
| **generic** | No | Yes | Partial (history) | No | None |

Auto-detection priority: `tmux` > `iterm2` > `shell_hook` > `generic`

Override in config: `terminal.backend: tmux`

### Shell Hook Installation

The shell hook is a lightweight precmd/preexec addition to your shell that writes CWD, last command, and exit code to a state file. Supports **zsh**, **bash**, and **fish**.

```bash
# Auto-detect and install
prompt-shell install-hook

# Or specify shell explicitly
prompt-shell install-hook --shell bash
prompt-shell install-hook --shell fish
```

## Build & Test

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/
```

## Project Structure

```
src/prompt_shell/
├── main.py              # CLI entry point (typer) + hotkey daemon + pipeline
├── config.py            # Pydantic config models + YAML loader
├── terminal/
│   ├── monitor.py       # Multi-backend terminal capture
│   │                    #   TerminalBackend (ABC)
│   │                    #   ├── TmuxBackend
│   │                    #   ├── ITerm2Backend
│   │                    #   ├── ShellHookBackend
│   │                    #   └── GenericBackend
│   ├── context.py       # Context aggregation + project detection
│   └── error_patterns.py # Regex error detection engine
├── voice/
│   ├── capture.py       # Microphone recording + energy-based VAD
│   └── transcribe.py    # Whisper / Apple Speech / API backends
├── enhancer/
│   ├── enhancement_client.py # httpx async client → POST /enhance to Cloud Run
│   ├── prompt_builder.py     # Fallback template-based prompt (when Cloud Run unreachable)
│   └── llm_client.py         # litellm wrapper: Ollama/OpenAI/Anthropic (offline fallback)
└── delivery/
    ├── clipboard.py     # Cross-platform: pbcopy / xclip / xsel / wl-copy
    ├── iterm_paste.py   # iTerm2 session paste (optional)
    └── notification.py  # Cross-platform: osascript / notify-send
```

## Configuration

Config file: `~/.prompt-shell/config.yaml`

See `config.example.yaml` for all available options.

### Terminal Backends

```yaml
terminal:
  backend: auto  # auto | tmux | iterm2 | shell_hook | generic
```

### LLM Providers

| Provider | Setup | Config |
|----------|-------|--------|
| **Gemini** (default) | Set `GEMINI_API_KEY` + deploy Cloud Run service (see below) | `provider: gemini`, `model: gemini-2.5-flash-lite` |
| **Ollama** (offline fallback) | `brew install ollama && ollama pull llama3.2:8b` | `provider: ollama` |
| **OpenAI** | Set `OPENAI_API_KEY` env var | `provider: openai`, `model: gpt-4o-mini` |
| **Anthropic** | Set `ANTHROPIC_API_KEY` env var | `provider: anthropic`, `model: claude-3.5-haiku` |

### Voice Engines

| Engine | Setup | Config |
|--------|-------|--------|
| **faster-whisper** (default) | Included in base install — no extra setup | `engine: whisper_local` |
| **OpenAI Whisper API** | Set `OPENAI_API_KEY` env var | `engine: whisper_api` |
| **Apple Speech** (macOS only) | `pip install pyobjc-framework-Speech` (manual, not managed by uv) | `engine: apple_speech` |

## Platform-Specific Notes

### macOS
- Clipboard: `pbcopy` / `pbpaste` (built-in)
- Notifications: `osascript` (built-in)
- CWD detection: `lsof` (built-in)
- Hotkeys: Requires Accessibility permission for the terminal app
- Microphone: macOS will prompt for Microphone permission

### Linux
- Clipboard: Install `xclip`, `xsel`, or `wl-clipboard` (Wayland)
- Notifications: Install `libnotify` (`notify-send`)
- CWD detection: `/proc/<pid>/cwd` (built-in)
- Hotkeys: Requires X11 or Wayland support via `pynput`
- Microphone: May need PulseAudio/PipeWire permissions

## Key Hotkeys (daemon mode)

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+P` | Voice capture -> enhance -> clipboard |
| `Ctrl+Shift+L` | Enhance clipboard text with terminal context |
| `Ctrl+Shift+R` | Re-enhance last prompt |
| `Esc` | Cancel voice capture |

## CLI Commands

| Command | Description |
|---------|-------------|
| `prompt-shell start` | Start daemon with hotkeys |
| `prompt-shell enhance "text"` | Enhance text directly |
| `prompt-shell enhance --voice` | Voice input mode |
| `prompt-shell enhance --clipboard` | Enhance clipboard contents |
| `prompt-shell context` | Show current terminal context |
| `prompt-shell context -b tmux` | Use a specific backend (`-b` / `--backend`) |
| `prompt-shell context -n 100` | Set screen buffer lines to capture (`-n` / `--lines`) |
| `prompt-shell install-hook` | Install shell hook (auto-detects shell) |
| `prompt-shell install-hook --shell bash` | Install for a specific shell |
| `prompt-shell init` | Create config directory and default config |

## Google Cloud Run Deployment

The Cloud Run service is deployed automatically as part of the versioned release
pipeline — **not** on every push to main. This keeps the deployed service version
in sync with the published PyPI package.

**Full setup and step-by-step instructions: [`docs/deployment.md`](docs/deployment.md)**

### Release-based deploy (normal path)

```bash
# 1. Update version in pyproject.toml, commit it
git commit -m "chore: bump version to 0.2.0"

# 2. Push a version tag — this triggers the full pipeline
git tag v0.2.0
git push origin v0.2.0
```

Pipeline order: `validate → test → build → publish-pypi → deploy-cloud-run`

Cloud Run deploys only after PyPI publish succeeds. The container image is
tagged with the release version for traceability and rollback.

### First-time / local deploy

Use `deploy.sh` for initial setup before your first tagged release:

```bash
export PROJECT_ID=your-gcp-project-id
export GEMINI_API_KEY=your-gemini-api-key
bash deploy.sh
```

### Manual re-deploy (no new release)

For secret rotation or incident recovery without bumping the version:

**GitHub Actions → Deploy to Cloud Run (Manual) → Run workflow**

### Required GitHub secrets

Set these in **Settings → Secrets and variables → Actions** before the first
release:

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | GCP project ID |
| `GCP_SA_KEY` | Service account JSON key, base64-encoded |
| `GEMINI_API_KEY` | Google AI Studio API key |

### Verify a deployment

```bash
curl $CLOUD_RUN_URL/health
# {"status":"ok"}

curl -X POST $CLOUD_RUN_URL/enhance \
  -H "Content-Type: application/json" \
  -d '{"voice_transcript": "fix the error", "cwd": "/app"}'
```

### Local config after deploy

```yaml
llm:
  provider: gemini
  model: gemini-2.5-flash-lite
  api_key: ${GEMINI_API_KEY}
  cloud_run_url: ${CLOUD_RUN_URL}
```

---

## Troubleshooting

- **"No terminal context"**: Install the shell hook (`prompt-shell install-hook`) or use tmux
- **"Cannot connect to iTerm2"**: Enable Python API in iTerm2 Settings > General > Magic
- **"No speech detected"**: Check microphone permissions in System Settings
- **"Enhancement service unreachable"**: Check `CLOUD_RUN_URL` in config; run `curl $CLOUD_RUN_URL/health` to verify
- **"LLM unavailable"**: For Gemini, check `GEMINI_API_KEY`. For Ollama fallback, ensure it's running (`ollama serve`). For other cloud providers, check their API keys
- **"Clipboard not working" (Linux)**: Install `xclip` or `xsel`: `sudo apt install xclip`
- **"Notifications not showing" (Linux)**: Install `libnotify`: `sudo apt install libnotify-bin`
- **Hotkeys not working**: macOS needs Accessibility permission; Linux needs X11/Wayland
