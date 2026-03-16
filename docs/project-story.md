# PromptShell - Project Story

## The Moment That Started It All

It was 2 AM during a debugging session. A React build had just failed with a wall of TypeScript errors. We selected the terminal output, switched to ChatGPT, pasted it in, typed *"fix this"* - then realized the AI had no idea which project we was in, what branch we was on, or what commands I'd just run. So we went back, copied the file path, the error line, the git branch, the working directory, added context about the framework version... by the time I'd assembled a useful prompt, five minutes had passed - and we hadn't even started fixing the bug.

That friction - the **context gap** between what your terminal knows and what your AI tool sees - happens dozens of times a day. Every developer we talked to had the same workflow: see error, manually copy context, switch windows, paste, add explanation, submit. It's a tax on every single AI interaction.

**What if the terminal could speak for itself?**

That question became PromptShell.

---

## What PromptShell Does

PromptShell is a voice-activated, terminal-aware prompt enhancer. You press a hotkey, say something as vague as *"fix it"* or *"why does it keep crashing"*, and PromptShell:

1. **Captures your full terminal state** - screen buffer, working directory, recent commands with exit codes, git branch, detected error patterns
2. **Takes a screenshot** of what you're actually looking at
3. **Transcribes your voice** command
4. **Sends everything to Gemini 2.5 Flash Lite** on Google Cloud Run - text context + screenshot as multimodal input
5. **Delivers a precise, actionable prompt** to your clipboard - ready to paste into any AI tool

Two words in. A surgical diagnosis out.

```
Input:  "fix it"
Output: Fix the two TypeScript errors blocking the build in my-app.

        1. src/components/AuthModal.tsx:47 - TS2345: `userId` is typed as
           `string | undefined` but passed to a function expecting `string`.
           Add a null guard or update the function signature.

        2. src/hooks/useSession.ts:91 - TS2322: Return type is `number`
           but `SessionStatus` enum is expected. Cast or map the return
           value to the correct enum variant.

        Branch: feature/auth-modal, CWD: ~/projects/my-app
```

---

## How we Built It

### Architecture: Split Client + Cloud

The core design decision was a **split architecture**: a local daemon handles everything that must stay on-device (hotkeys, terminal capture, voice recording, clipboard delivery), while the intelligence runs on **Google Cloud Run** via the **Google GenAI SDK**.

```
Local Daemon (Python)          Cloud Run (FastAPI)
┌─────────────────────┐        ┌──────────────────────┐
│ Terminal Monitor    │        │ POST /enhance        │
│ (4 backends)        │        │                      │
│ Voice Capture       │──HTTP──│ Prompt Engineering   │
│ Context Aggregator  │        │ Engine               │
│ Clipboard Delivery  │        │                      │
│ Hotkey Listener     │◄─HTTP──│ Gemini 2.5 Flash Lite│
└─────────────────────┘        │ (Google GenAI SDK)   │
                               └──────────────────────┘
```

This wasn't arbitrary - it was driven by the realization that terminal context is **inherently local** (you can't read someone's tmux buffer from the cloud), while LLM inference benefits from cloud-scale compute and API access.

### The Terminal Monitor: 4 Backends, 1 Interface

The hardest engineering problem was capturing terminal state across different environments. A developer might be using tmux, iTerm2, a bare Linux terminal, or running inside a container. we built a **pluggable backend system** with auto-detection:

| Backend | How It Works | Richness |
|---------|-------------|----------|
| **tmux** | `tmux capture-pane` | Full screen buffer, CWD, command history |
| **iTerm2** | AppleScript automation | Full screen buffer via iTerm2 API |
| **shell_hook** | Post-command hook writes JSON state | CWD, last command, exit code |
| **generic** | `/proc/<pid>/cwd` + shell history files | CWD, command history |

The system tries each in order and uses the first one that works. This means PromptShell works in *any* terminal - the quality degrades gracefully rather than failing entirely.

### Multimodal Intelligence

The enhancement engine doesn't just process text - it receives the terminal **screenshot** alongside the structured context. This is critical for cases where the real information is visual:

- TUI applications (lazygit, htop) that don't leave text in the buffer
- Errors buried 70+ lines above the current scroll position
- Color-coded output where formatting carries meaning

Gemini 2.5 Flash Lite processes both modalities through a carefully engineered meta-prompt that instructs it to:
1. Classify the user's intent (fix, explain, debug, generate, refactor)
2. Extract specifics from both text and screenshot
3. Produce a diagnostic prompt - not just a copy of the error, but a root cause analysis

### Error Pattern Detection

PromptShell includes a regex engine that recognizes **12+ error families** across languages:

$$\text{Languages} = \{\text{TypeScript, Python, Rust, Go, Java, C/C++, Ruby, Docker, Git, Shell, ...}\}$$

Each pattern extracts structured data - error codes, file paths, line numbers - which feeds into the meta-prompt as additional signal. When the regex engine finds `TS2345` in the screen buffer, the enhanced prompt doesn't just say "there's a TypeScript error" - it says *which* error, *where*, and *what it means*.

### Voice Pipeline

Voice input uses energy-based Voice Activity Detection (VAD) to know when you've stopped speaking, then transcribes via faster-whisper (local, ~1.5s latency) or OpenAI Whisper API. The transcription becomes the "user intent" - the seed that Gemini transforms into a full prompt using all the captured context.

---

## The Numbers

| Metric | Value |
|--------|-------|
| Total source code | ~3,300 lines of Python |
| Test suite | 125 tests |
| Terminal backends | 4 (tmux, iTerm2, shell_hook, generic) |
| Error pattern families | 12+ languages |
| Voice engines supported | 3 (faster-whisper, OpenAI API, Apple Speech) |
| Cloud Run cold start | < 3s |
| End-to-end latency | ~4s (hotkey → clipboard) |

---

## Challenges

### Challenge 1: The Empty Buffer Problem

The most insidious bug took days to track down. Enhanced prompts were coming back vague and useless - just copy-pasting error messages verbatim. The pipeline *appeared* to work: logs showed context being collected, HTTP requests succeeding, Gemini responding.

The root cause was a **cascading data gap**. On Linux without tmux, the shell_hook and generic backends don't capture the screen buffer - they only get metadata (CWD, commands, exit codes). This meant:

$$\text{screen\_buffer} = \text{""} \implies \text{error\_regex} = \text{no matches} \implies \text{terminal output section} = \text{omitted}$$

Gemini received the voice transcript, some metadata, and a screenshot image - but the meta-prompt's instructions said *"copy error text verbatim"* and *"be as concise as possible."* So it did exactly that: copied whatever it could OCR from the screenshot and produced a shallow result.

**The fix was two-fold:**

1. **OCR fallback**: When the backend returns an empty screen buffer but a screenshot exists, PromptShell runs Tesseract OCR on the screenshot to populate the buffer. This gives the error regex something to work with.

2. **Meta-prompt rewrite**: Changed the instructions from "copy errors verbatim" to "perform diagnostic analysis - identify root cause, explain the error chain, and suggest specific fixes." The model went from being a copy machine to being a diagnostic engine.

### Challenge 2: Frozen State and Race Conditions

All state objects (`TerminalState`, `ContextPayload`) are **frozen dataclasses** for thread-safety in the async hotkey daemon. This is the right design - but it means you can't just `state.screen_buffer = ocr_text`. Every modification requires `dataclasses.replace()`, creating a new immutable instance.

The shell hook also introduced a race condition: the hook writes a JSON state file after each command, and the daemon reads it on hotkey press. If the timing is wrong, you get a half-written JSON file:

```
Invalid control character at: line 1 column 97
```

This is because shell `printf >` is not atomic on most filesystems. A proper fix would involve `rename(2)`-based atomic writes - but for the MVP, the daemon handles the parse error gracefully and falls back to the generic backend.

### Challenge 3: Making Gemini *Think*, Not Copy

The first version of the meta-prompt produced responses like:

> Fix this error. `NameError: name 'flask' is not defined`

That's not enhancement - that's a parrot. The breakthrough was realizing that the meta-prompt's instructions were *too permissive*. Telling the model to "be concise" with error context meant it took the shortest path: just repeat the error.

The rewritten instructions explicitly require:
- Identifying the root cause, not just the symptom
- Explaining *why* the error occurs
- Providing specific file paths, line numbers, and fix strategies
- Connecting related errors (e.g., a missing header causing both a compilation failure *and* a linker error downstream)

After the rewrite, the same Flask error produced a prompt with the full diagnostic: missing import, which file, which line, what the correct import statement should be, and why the error manifests as `NameError` rather than `ImportError`.

### Challenge 4: The Screenshot-Only Edge Case

When running without tmux on a bare Linux terminal, the system has *no text buffer at all* - the only terminal context is the screenshot PNG. This is actually the most impressive demo scenario but also the hardest to get right.

The meta-prompt now detects this case and switches to an aggressive mode:

> *"No terminal text buffer was captured. The screenshot is your ONLY source of terminal content. You MUST read every line of terminal output visible in the screenshot, transcribe all error messages verbatim, and use that as the basis for your analysis."*

This turns Gemini into a combined OCR + diagnostic engine, and the results are remarkably good - it can read compiler errors, stack traces, and even TUI layouts from a terminal screenshot.

---

## What we Learned

### 1. The Pipeline is the Product

PromptShell's value isn't in any single component - it's in the **pipeline**. Voice transcription, terminal capture, error detection, screenshot analysis, prompt engineering, and clipboard delivery each solve a small problem. Together, they create something none of them could alone: the ability to say *"fix it"* and get a surgical prompt.

This taught me that in AI-powered tools, **integration is the innovation**. The models are commodities. The orchestration - knowing what context to capture, how to structure it, and what instructions to give the model - is what creates value.

### 2. Prompt Engineering is Software Engineering

The meta-prompt went through multiple iterations, and each one changed the output quality dramatically. A single phrase - "be concise" - turned a capable model into a copy machine. Replacing it with "perform diagnostic analysis" unlocked the behavior we wanted.

This isn't vibe-based tweaking. It's engineering: define the desired behavior, write a test case, change the prompt, measure the output. The meta-prompt has the same lifecycle as code - it needs version control, testing, and iteration.

### 3. Graceful Degradation > Feature Flags

Rather than requiring tmux or a specific terminal, PromptShell works everywhere and gets *better* with richer environments. On a bare terminal it uses screenshots. With a shell hook it adds commands and CWD. With tmux it gets the full buffer. Each capability is additive, and the absence of any one doesn't break the system.

This pattern - **always work, progressively enhance** - turned out to be more important than any individual feature.

### 4. Multimodal Changes the Game

The screenshot input isn't a gimmick. There are entire categories of terminal state that *only exist visually*: TUI applications, color-coded diffs, merge conflict displays in lazygit. Text extraction misses all of this. Giving the model the screenshot means it can see exactly what the developer sees - and that context is what makes the difference between a generic prompt and a precise one.

---

## What's Next

PromptShell today solves the terminal-to-AI context gap. The roadmap extends it into a **full developer context platform**.

### Near-Term: Deeper Intelligence

- **Codebase-Aware RAG** - Index the local codebase into a vector store. When a `TS2345` error fires in `auth.ts`, the enhanced prompt automatically includes the function definition, the expected type, and the caller that passed the wrong type. The developer never has to say "look at this file" again.
- **Multi-Turn Conversation Memory** - Track previous prompts, what the developer tried, and what failed. If you enhance *"fix the error"*, try the suggestion, and it doesn't work - the next *"try again"* includes the full history: original error, first fix attempt, what changed, new error.
- **Gemini Live Streaming** - Replace request-response with Gemini's streaming API. The enhanced prompt appears token-by-token in real time. Combined with streaming voice input, the entire loop becomes conversational with sub-second perceived latency.

### Mid-Term: Beyond the Terminal

- **IDE-Native Integration** - VS Code extension and JetBrains plugin that capture open files, cursor position, linter warnings, and debug breakpoints alongside terminal state. Moves PromptShell from a terminal tool to a full developer context engine.
- **Browser DevTools Capture** - Extend multimodal context to console errors, network failures, and React component trees. When a frontend developer says *"fix the error"*, PromptShell captures both the terminal (build output) and the browser (runtime error) - full-stack context in a single prompt.
- **CI/CD Pipeline Agent** - When a GitHub Actions or Jenkins pipeline fails, a PromptShell agent captures the failed step's logs, environment, and diff - then generates an enhanced prompt automatically as a PR comment. Debugging starts before the developer even opens the logs.

### Long-Term: Platform & Scale

- **Custom Error Pattern SDK** - A plugin API that lets teams define regex patterns for proprietary frameworks, internal tooling, or domain-specific errors (Terraform, Kubernetes, database migrations). Ship patterns as installable pip packages.
- **Smart Model Routing** - Classify request complexity and route to the cheapest model that can handle it - simple typos to Flash Lite, complex multi-file debugging to Flash, architectural questions to Pro. Projected 50-70% cost reduction at scale.
- **Team & Org Features** - Shared prompt templates tuned for the org's stack, centralized config distribution, usage analytics dashboards, and role-based enhancement styles (frontend vs. backend vs. SRE).
- **Plugin Architecture** - Every component (backend, transcriber, enhancer, delivery) implements a standard interface and loads dynamically. Third parties ship plugins as packages: `prompt-shell-plugin-kubernetes`, `prompt-shell-plugin-datadog`, `prompt-shell-plugin-slack`.
- **Voice Conversation Mode** - Continuous voice-driven debugging powered by Gemini Live's bidirectional streaming. Speak, enhance, respond, follow up - true voice-driven AI pair programming with no typing required.

---

## Built With

- **Gemini 2.5 Flash Lite** - multimodal prompt enhancement (Google GenAI SDK)
- **Google Cloud Run** - serverless backend hosting
- **Python 3.11+** - local daemon and cloud service
- **FastAPI** - Cloud Run HTTP service
- **faster-whisper** - local voice transcription
- **Tesseract OCR** - screenshot text extraction fallback
- **pynput** - global hotkey capture
- **sounddevice** - microphone recording

---

*"Great developers write great code, not great prompts. Just say 'fix it' - Prompt-Shell sees your terminal and does the rest."*
