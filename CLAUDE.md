# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

prompt-shell is a voice-activated terminal context enhancer. It runs as a daemon, listens for a hotkey, captures your terminal state (screen buffer, CWD, recent commands, git branch, detected errors), optionally records voice input, then uses an LLM to rewrite your vague command into a precise, actionable AI prompt — delivering it to your clipboard.

## Common Commands

```bash
# Install dependencies (requires uv)
uv sync --extra dev

# Run linter
uv run ruff check src/ tests/ --output-format=github

# Format code
uv run ruff format src/ tests/

# Run all tests
uv run pytest tests/ -v --tb=short

# Run a single test file
uv run pytest tests/test_error_patterns.py -v

# Build wheel
uv build

# Run as CLI
uv run prompt-shell start
uv run prompt-shell enhance "fix the error"
uv run prompt-shell context
```

**Ruff config:** 100-char line length, rules E/F/I/N/W/UP. Long lines are suppressed in `monitor.py`, `error_patterns.py`, and `test_error_patterns.py` (embedded shell scripts and regex patterns).

**Tests:** `asyncio_mode = auto` — all async tests work without explicit markers.

## Architecture

The pipeline is: **hotkey → terminal snapshot → voice/clipboard → context build → HTTP POST to Cloud Run → Gemini 2.0 Flash → clipboard delivery**.

The system is split into two parts: a **local client** (daemon) and a **Cloud Run enhancement service** (Google Cloud).

```
Local client (src/prompt_shell/)
├── main.py                  # Typer CLI + hotkey daemon + pipeline orchestrator
├── config.py                # Pydantic models for config.yaml
├── terminal/
│   ├── monitor.py           # ABC TerminalBackend with 4 concrete backends (tmux, iTerm2, shell_hook, generic)
│   ├── context.py           # Aggregates TerminalState → ContextPayload; detects project type
│   └── error_patterns.py    # Regex engine for 12+ error families (TypeScript, Rust, Python, Go, etc.)
├── voice/
│   ├── capture.py           # sounddevice mic recording + energy-based VAD
│   └── transcribe.py        # Pluggable engines: faster-whisper (local), OpenAI API, Apple Speech
├── enhancer/
│   ├── enhancement_client.py  # httpx async client → POST /enhance to Cloud Run
│   ├── prompt_builder.py      # Fallback template (when Cloud Run unreachable)
│   └── llm_client.py          # litellm wrapper: Ollama/OpenAI/Anthropic (offline fallback)
└── delivery/
    ├── clipboard.py         # pbcopy / wl-copy / xclip / pyperclip
    ├── iterm_paste.py       # Optional: paste directly into iTerm2 session
    └── notification.py      # osascript (macOS) / notify-send (Linux)

Cloud Run service (cloud_run_service/)
├── main.py                  # FastAPI app: POST /enhance, GET /health
├── prompt_builder.py        # Meta-prompt template renderer
├── gemini_client.py         # google-genai SDK wrapper (Gemini 2.0 Flash)
├── Dockerfile               # Cloud Run container image
└── requirements.txt         # fastapi, uvicorn, google-genai, pydantic
```

### Key Design Decisions

- **Split architecture:** Local daemon handles everything on-device (hotkeys, terminal, voice, delivery). Enhancement runs on Cloud Run — satisfies Gemini Live Agent Challenge requirements (Gemini model, Google GenAI SDK, GCP hosting).
- **Backend auto-detection order:** tmux → iTerm2 → shell_hook → generic. Generic is always available (reads shell history + `/proc/<pid>/cwd`).
- **All state objects are frozen dataclasses** (`TerminalState`, `ContextPayload`) for thread-safety in the async hotkey daemon.
- **Cloud Run failure degrades gracefully** to a local template-based prompt rather than surfacing an error to the user.
- **Shell hook** (`install-hook` command) writes `~/.prompt-shell/shell_state.json` after each command — this feeds the `ShellHookBackend` with CWD, last command, and exit code.

### Config

Runtime config is loaded from `~/.prompt-shell/config.yaml` (or `XDG_CONFIG_HOME`). See `config.example.yaml` for all options. Environment variable substitution is supported (e.g., `api_key: ${GEMINI_API_KEY}`).

Default stack: Gemini 2.0 Flash on Cloud Run, faster-whisper base.en (local), clipboard delivery.
Offline fallback: Ollama + llama3.2:8b (local).

### Deployment

Cloud Run is deployed as part of the versioned release pipeline — **not** on every push to main.

**Normal path:** push a version tag → `release.yml` runs tests → publishes to PyPI → deploys Cloud Run → creates GitHub Release.

```bash
git tag v0.2.0 && git push origin v0.2.0
```

**Manual re-deploy** (secret rotation, hotfix without a new version):
GitHub Actions → "Deploy to Cloud Run (Manual)" → Run workflow.

**Local deploy** (first-time setup or debugging):
```bash
export PROJECT_ID=... GEMINI_API_KEY=... && bash deploy.sh
```

**Required GitHub repository secrets** (Settings → Secrets → Actions):
- `GCP_PROJECT_ID` — GCP project ID
- `GCP_SA_KEY` — service account JSON key, base64-encoded
- `GEMINI_API_KEY` — Google AI Studio API key

Full setup instructions: [`docs/deployment.md`](docs/deployment.md).

**Relevant files:**
- `deploy.sh` — one-command local deploy script
- `cloudbuild.yaml` — Cloud Build trigger config (reads API key from Secret Manager)
- `.github/workflows/release.yml` — full release pipeline including `deploy-cloud-run` job
- `.github/workflows/deploy-cloud-run.yml` — manual re-deploy workflow
- `cloud_run_service/` — FastAPI service code, Dockerfile, requirements

---

## Coding Standards & Best Practices

### Code Style

- **Clarity over cleverness.** If a line needs a comment to explain what it does, rewrite the line first.
- One responsibility per function. If you need "and" to describe what a function does, split it.
- Name things by what they are, not how they work. `get_relevant_chunks()` not `run_knn_pipeline()`.
- No magic numbers or strings — every constant has a named variable.
- Max function length: ~30 lines. If it's longer, it's doing too much.

### Types & Validation

- All function signatures have type annotations — parameters and return types, no exceptions.
- Use strict types at system boundaries (API inputs, config, external responses). Never trust raw external data.
- Validate early, fail loudly. Catch bad input at the entry point, not deep in business logic.

### Error Handling

- Every error must be actionable — what failed, why, and what to check.
- Never swallow exceptions silently. Log with full context or re-raise.
- Distinguish expected failures (e.g., no LLM available → fallback to template) from unexpected ones (e.g., config parse error). Handle them differently.
- Graceful degradation is intentional and explicit — not a side effect of suppressed errors.

### Async & Concurrency

- All I/O is async. No blocking calls inside async functions.
- Run independent async operations concurrently (`gather`), not sequentially.
- Never use sleep in async code except for intentional backoff with a comment explaining why.

### Configuration & Secrets

- Every tunable value (thresholds, timeouts, model names, limits) lives in config — not hardcoded.
- Secrets come from environment variables only. No defaults for secrets. Fail on startup if required secrets are missing.
- Config is loaded once at startup, not re-read on every request.

### Logging

- Log at the right level: `DEBUG` for internals, `INFO` for meaningful events, `WARNING` for recoverable issues, `ERROR` for failures requiring attention.
- Every log entry includes enough context to be useful in isolation (e.g., backend name, operation, outcome).
- Never log sensitive data: API keys, raw audio content, personal information.
- Use structured logging (key-value or JSON format) — not freeform strings.

### Testing

- Unit tests cover logic in isolation — no network, no filesystem, no subprocess calls.
- Integration tests cover real interactions with external systems (LLM APIs, shell backends).
- Test names describe behavior: `test_returns_fallback_template_when_llm_unavailable`.
- Assert on specific outcomes, not just "no exception was raised."

### Test-Driven Development (TDD)

Every feature, fix, or change starts with a test — not code.

**The cycle (Red → Green → Refactor):**

1. **Red** — Write a failing test that defines the exact behavior you want. Confirm it fails for the right reason.
2. **Green** — Write the minimum code to make that test pass. No more, no less.
3. **Refactor** — Clean up without changing behavior. Tests must still pass.

**Rules:**
- Never write production code without a failing test that justifies it.
- If you find a bug, write a test that reproduces it first — then fix it.
- If a feature is hard to test, that's a design signal. Redesign so it becomes testable.
- **Only write tests directly required by the current task.** Do not write extra tests speculatively or to improve coverage beyond what the task demands. Stick to the plan.

**Test structure (Arrange → Act → Assert):** Set up inputs, call the single thing being tested, verify the outcome. One logical assertion per test. Each test must be independent — no shared mutable state, no relying on execution order.

### Git & Commits

- Commit one logical change at a time. A commit should be explainable in a single sentence.
- Commit message format: `type: short description` — e.g., `feat: add cosine threshold config`, `fix: handle empty chunk list`.
- Never commit broken code. The branch should be runnable at every commit.

### Dependencies

- Add a dependency only when it earns its place. Prefer the standard library when sufficient.
- Every new dependency should be understood, not just installed. Know what it does and why it's needed.
