# PromptShell — 4-Minute Demo Script

**Total time:** 4:00
**Format:** Screen recording with voiceover

---

## [0:00–0:25] HOOK — The Problem (25s)
> Hi everyone! Today we’re presenting PromptShell.
> AI assistants understand your code.
> But when something breaks, the real context lives in your terminal.
> What if your terminal could write the prompt for you?

> This is **PromptShell** — a voice-activated, terminal-aware prompt enhancer.
>
> Press a hotkey. Say what you want in plain English. PromptShell reads your terminal — the screen buffer, the errors, the file paths, the exit codes, even takes a screenshot — and rewrites your vague command into a precise, context-rich prompt. Ready to paste into any AI tool.
> Our team consists of Disen and myself, and during this hackathon we built the terminal client, AI enhancement service, and voice capture pipeline behind PromptShell.
> Let me show you how it works.

**[On screen]:** Show the architecture diagram from README briefly (2-3 seconds). Then show terminal with PromptShell daemon running.

---

## [1:00–2:15] LIVE DEMO — Three Scenarios (75s)

### Scenario 1: Fix a build error (25s)

> Let me show you. I have a TypeScript project with a build error.

**[On screen]:** Terminal shows `npm run build` failing with `TS2345` error.

> I press **Ctrl+Alt+E** and say: *"fix the error."*

**[On screen]:** PromptShell activates — shows "Listening...", then "Heard: fix the error", then "Enhancing prompt...", then the enhanced prompt panel.

> Look at what landed in my clipboard.

**[On screen]:** Paste the enhanced prompt — it includes the exact error code, file path, line number, the failed command, the git branch. Everything.

> Three words in. A surgical prompt out. Paste it into any AI tool — it answers correctly on the **first try**.

---

### Scenario 2: Multimodal — screenshot context (25s)

> But what if the error isn't in the text buffer? What if it's in a dialog box, or highlighted in your editor?
>
> PromptShell captures a screenshot alongside the text. Gemini receives both — text and image — as multimodal input.

**[On screen]:** Show the Cloud Run logs or a brief view of the request showing `screenshot_b64` being sent.

> So even when the text buffer doesn't tell the full story, the screenshot fills the gap. Gemini Vision reads what you see.

---

### Scenario 3: Offline fallback (25s)

> Now what happens when you're on a plane? No internet. Cloud Run is unreachable.
>
> PromptShell doesn't break. It falls back to a local LLM — Ollama running on your machine. If even that's not available, it generates a structured template prompt. **You always get output.**

**[On screen]:** Show the fallback in action — "Cloud Run unreachable, falling back to local LLM" message, then the enhanced prompt still appears.

> Three layers of resilience. Cloud Run → local LLM → template. Never fails.

---

## [2:15–3:00] HOW IT WORKS — Architecture (45s)

> Here's what happens under the hood.                                                                                                         
   
> The Multimodal Context Agent launches three captures concurrently — the Terminal State Monitor grabs the screen buffer, Vision Capture takes
> a screenshot, and Speech-to-Text powered by Whisper AI transcribes your voice locally. Your voice never leaves your machine.               

> The Context Aggregator assembles everything — errors, project type, git branch, screenshot —everything into a single payload.

> The AI Orchestrator sends a Multimodal API Request to the Google Cloud AI Platform — Cloud Run runs the Prompt Engineering Engine, which
> feeds both text and screenshot to Gemini 2.5 Flash Lite as multimodal input. Back comes the AI-Enhanced Prompt.

> If Cloud Run is unreachable, the Offline AI Fallback kicks in — local model first, then a template. You always get output.

> Result lands in your clipboard. Done.
---

## [3:00–3:30] THE NUMBERS — Why It Matters (30s)

> Let's talk about what this actually saves.

**[On screen]:** Show the token comparison table from README.

> Without PromptShell, a typical debugging session takes 3 to 5 rounds with your AI assistant. That's 3,000 to 5,000 tokens burned before you get a useful answer.
>
> With PromptShell — **one round. About 1,100 tokens. 60 to 75% fewer tokens.**
>
> At scale, that's roughly **$540 per developer per year** in API credits saved. But honestly, the bigger win is the time. No context switching. No manual copy-paste. Speak and get a precise prompt in two seconds.

---

## [3:30–3:55] TECH STACK + WRAP (25s)

> To recap the stack:
>
> - **Gemini 2.5 Flash Lite** for multimodal prompt enhancement
> - **Google Cloud Run** for serverless hosting — scales to zero, costs nothing at rest
> - **Google GenAI SDK** for the Gemini API integration
> - **faster-whisper** for private, local voice transcription
> - Four terminal backends — works in tmux, iTerm2, any shell with the hook, or generically on any terminal
> - Clipboard delivery that works on macOS and Linux
>
> It's open source. Install with `pip install prompt-shell`.

---

## [3:55–4:00] CLOSE (5s)

> **Stop paying for bad prompts. PromptShell gets it right the first time.**

> **Great developers don’t write great prompts — they write great code. PromptShell handles the rest.**

**[On screen]:** GitHub repo URL + project name.

---

## Production Notes

- **Screen recording tool:** OBS or macOS screen recording
- **Terminal font size:** 16pt+ for readability in video
- **Prepare the scenarios in advance:** have the TypeScript error, the build failure, and the offline fallback ready to go before recording
- **Keep the terminal clean:** only show what's relevant, no extra windows
- **Voiceover pace:** ~150 words per minute. The script above is ~650 words — fits comfortably in 4 minutes with pauses
- **Background music:** subtle, low-volume lo-fi or ambient — optional
