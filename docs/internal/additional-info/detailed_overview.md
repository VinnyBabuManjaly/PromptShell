Your task is to analyze an entire code repository from the provided directory structure and file contents to build a deep understanding 
 of the system.                                                                                                                         
                                                                                                                                        
IMPORTANT:                                                                                                                              
Do NOT summarize files one by one.                                                                                                      
Instead, reverse-engineer the project as if you are onboarding a new senior engineer and need to explain how the system actually works. 
                                                                                                                                        
Your explanation must come from understanding the code, logic flow, dependencies, and architecture — not just filenames.                
                                                                                                                                        
You must read and interpret:                                                                                                            
- Source code files                                                                                                                     
- Config files                                                                                                                          
- Dependency manifests                                                                                                                  
- Environment files                                                                                                                     
- Infrastructure configs                                                                                                                
- Scripts                                                                                                                               
- API definitions                                                                                                                       
- Database models                                                                                                                       
- Documentation                                                                                                                         
- Tests                                                                                                                                 
                                                                                                                                        
Your goal is to reconstruct the **mental model of the system**.                                                                         
                                                                                                                                        
Produce the explanation in the following structured format.                                                                             
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
1. PROJECT PURPOSE                                                                                                                      
Explain in plain human language:                                                                                                        
- What problem this project solves                                                                                                      
- Who the users are                                                                                                                     
- What the system does end-to-end                                                                                                       
- Real-world use case                                                                                                                   
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
2. SYSTEM OVERVIEW (HIGH LEVEL)                                                                                                         
Explain the entire system like an architecture diagram in words.                                                                        
                                                                                                                                        
Describe:                                                                                                                               
- Major components                                                                                                                      
- System boundaries                                                                                                                     
- External integrations                                                                                                                 
- Inputs and outputs                                                                                                                    
                                                                                                                                        
Explain how the whole system flows from start → finish.                                                                                 
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
3. CORE ARCHITECTURE                                                                                                                    
Identify the architectural style used:                                                                                                  
Examples:                                                                                                                               
- Monolith                                                                                                                              
- Layered architecture                                                                                                                  
- Microservices                                                                                                                         
- Event-driven                                                                                                                          
- MVC                                                                                                                                   
- Hexagonal / Clean Architecture                                                                                                        
- Data pipeline                                                                                                                         
- ML pipeline                                                                                                                           
                                                                                                                                        
Explain WHY the project follows this structure.                                                                                         
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
4. MAIN COMPONENTS OF THE SYSTEM                                                                                                        
                                                                                                                                        
Identify the real logical components, not just folders.                                                                                 
                                                                                                                                        
For each component explain:                                                                                                             
- Responsibility                                                                                                                        
- Key classes/functions                                                                                                                 
- How it interacts with other components                                                                                                
- What data it handles                                                                                                                  
                                                                                                                                        
Example components:                                                                                                                     
- API layer                                                                                                                             
- Business logic layer                                                                                                                  
- Data layer                                                                                                                            
- ML models                                                                                                                             
- Caching                                                                                                                               
- Background jobs                                                                                                                       
- Workers                                                                                                                               
- External services                                                                                                                     
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
5. EXECUTION FLOW (VERY IMPORTANT)                                                                                                      
                                                                                                                                        
Explain what happens when the system runs.                                                                                              
                                                                                                                                        
Example flows:                                                                                                                          
                                                                                                                                        
User request → API → service → database → response                                                                                      
                                                                                                                                        
or                                                                                                                                      
                                                                                                                                        
Data ingestion → processing → model inference → output                                                                                  
                                                                                                                                        
Write this like a story of how the system executes.                                                                                     
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
6. DATA FLOW                                                                                                                            
                                                                                                                                        
Explain how data moves through the system.                                                                                              
                                                                                                                                        
Include:                                                                                                                                
- Inputs                                                                                                                                
- Transformations                                                                                                                       
- Storage                                                                                                                               
- Outputs                                                                                                                               
                                                                                                                                        
Mention schemas, models, or structures when relevant.                                                                                   
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
7. KEY TECHNOLOGIES USED                                                                                                                
                                                                                                                                        
List technologies and explain their role:                                                                                               
                                                                                                                                        
Example:                                                                                                                                
- FastAPI → API framework                                                                                                               
- Redis → caching                                                                                                                       
- PostgreSQL → persistence                                                                                                              
- React → frontend                                                                                                                      
                                                                                                                                        
Explain WHY they might have been chosen.                                                                                                
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
8. IMPORTANT DESIGN DECISIONS                                                                                                           
                                                                                                                                        
Identify architectural decisions such as:                                                                                               
                                                                                                                                        
- Why caching is used                                                                                                                   
- Why async processing exists                                                                                                           
- Why certain frameworks are used                                                                                                       
- Why certain abstractions exist                                                                                                        
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
9. DEPENDENCY RELATIONSHIPS                                                                                                             
                                                                                                                                        
Explain the dependency graph conceptually:                                                                                              
Which components depend on which.                                                                                                       
                                                                                                                                        
Example:                                                                                                                                
API → Service Layer → Repository → Database                                                                                             
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
10. CONFIGURATION & ENVIRONMENT                                                                                                         
                                                                                                                                        
Explain:                                                                                                                                
- Config management                                                                                                                     
- Environment variables                                                                                                                 
- Deployment hints                                                                                                                      
- Infrastructure files (Docker, Terraform, etc.)                                                                                        
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
11. HOW TO RUN THE PROJECT                                                                                                              
                                                                                                                                        
Explain clearly:                                                                                                                        
- Setup                                                                                                                                 
- Dependencies                                                                                                                          
- Execution flow                                                                                                                        
- Entry point                                                                                                                           
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
12. POTENTIAL IMPROVEMENTS                                                                                                              
                                                                                                                                        
Based on architecture, suggest:                                                                                                         
- Scalability improvements                                                                                                              
- Code organization improvements                                                                                                        
- Missing abstractions                                                                                                                  
- Testing gaps                                                                                                                          
                                                                                                                                        
--------------------------------------------------                                                                                      
                                                                                                                                        
IMPORTANT GUIDELINES                                                                                                                    
                                                                                                                                        
Your explanation must be:                                                                                                               
- Clear and human-like                                                                                                                  
- Architectural                                                                                                                         
- Concept-driven                                                                                                                        
- Easy for a new engineer to understand                                                                                                 
                                                                                                                                        
Avoid:                                                                                                                                  
❌ listing files                                                                                                                        
❌ repeating directory structure                                                                                                        
❌ shallow summaries                                                                                                                    
                                                                                                                                        
Focus on:                                                                                                                               
✔ system thinking                                                                                                                       
✔ architecture                                                                                                                          
✔ flow of data and control                                                                                                              
✔ design intent                                                                                                                         

● ---                                  
  1. PROJECT PURPOSE
                                                                                                                                        
  The Problem
                                                                                                                                        
  Every developer has experienced this: you're deep in a debugging session, the terminal shows a wall of red, and you switch to an AI
  assistant and type "fix the error". The AI asks for clarification. You go back to the terminal, copy the error message, paste it in,
  add the file path, mention the branch, describe what you were trying to do. By the time you've assembled a useful prompt, you've spent
   more cognitive effort than the fix itself.

  The gap isn't skill — it's context transfer friction. The developer's mental model is rich (they can see the screen, they know the
  stack, they know the last command that failed). The AI gets a one-line approximation of that model.

  What prompt-pulse Does

  prompt-pulse is a background daemon that closes that gap automatically. It monitors the developer's terminal in real-time, captures
  voice input when triggered by a hotkey, and uses an LLM to merge the raw intent with the harvested terminal context — producing a
  precise, context-rich prompt delivered directly to the clipboard.

  Before: Developer says "fix the error" → AI asks: "what error?"
  After: Developer says "fix the error" → AI gets: "Fix TypeScript error TS2345 in src/auth/middleware.ts:42. Argument of type string is
   not assignable to AuthToken. Last command: npm run build (exit code 1). Branch: feature/auth-refactor. CWD: ~/project/backend."

  Users

  Software engineers on macOS or Linux who use AI coding assistants (Copilot, ChatGPT, Devin, Claude) and spend time at the terminal.
  The tool assumes technical fluency — configuration is YAML, installation requires shell hook setup, and voice input is optional.

  ---
  2. SYSTEM OVERVIEW (HIGH LEVEL)

  The system has two runtime boundaries: a local client daemon running on the developer's machine, and a Cloud Run enhancement service
  running on Google Cloud. Currently, only the local client is implemented in code; the Cloud Run service is architecturally planned.

  Developer Machine
  ┌──────────────────────────────────────────────────────────┐
  │                                                           │
  │  pynput keyboard listener (OS thread)                    │
  │       │  Ctrl+Shift+P                                     │
  │       │  run_coroutine_threadsafe()                       │
  │       ▼                                                   │
  │  asyncio event loop                                       │
  │       │                                                   │
  │  ┌────┴────────────────────────────────────────┐         │
  │  │           run_pipeline()                     │         │
  │  │                                             │         │
  │  │  ┌──────────────┐    ┌──────────────────┐  │         │
  │  │  │Terminal       │    │Voice Capture     │  │         │
  │  │  │Monitor        │    │(sounddevice +    │  │         │
  │  │  │               │    │ numpy VAD)       │  │         │
  │  │  │ tmux/iTerm2/  │    │                  │  │         │
  │  │  │ shell_hook/   │    │ → WAV bytes      │  │         │
  │  │  │ generic       │    └────────┬─────────┘  │         │
  │  │  │               │             │Transcribe   │         │
  │  │  │ → TerminalState│            │(faster-     │         │
  │  │  └───────┬───────┘            │ whisper)    │         │
  │  │          │                     │             │         │
  │  │          └──────────┬──────────┘             │         │
  │  │                     ▼                        │         │
  │  │          ContextBuilder                      │         │
  │  │          (error detection +                  │         │
  │  │           project detection)                 │         │
  │  │                     │                        │         │
  │  │                     ▼ ContextPayload         │         │
  │  │          LLM Client                          │         │
  │  │          (litellm → Ollama/OpenAI/Anthropic) │         │
  │  │          [→ Cloud Run/Gemini, planned]        │         │
  │  │                     │                        │         │
  │  │                     ▼ enhanced_prompt: str   │         │
  │  │          Delivery Engine                     │         │
  │  │          (clipboard + notification)           │         │
  │  └─────────────────────────────────────────────┘         │
  └──────────────────────────────────────────────────────────┘
           │                            ▲
           │ HTTP POST /enhance          │ enhanced_prompt
           ▼ (planned)                  │
  ┌─────────────────────────────────────┐
  │  Google Cloud Run                   │
  │  FastAPI + google-genai SDK         │
  │  Gemini 2.0 Flash                   │
  └─────────────────────────────────────┘

  External integrations:
  - LLM provider (Ollama on localhost:11434, OpenAI API, Anthropic API, or Gemini via Cloud Run)
  - Whisper (local model) or OpenAI Whisper API for transcription
  - Apple Speech Framework (macOS only, via pyobjc — optional)
  - iTerm2 Python API (macOS optional extra)
  - OS clipboard (pbcopy/xclip/wl-copy)
  - OS notification system (osascript/notify-send)

  Inputs: Hotkey press + microphone audio (or clipboard text)
  Output: Enhanced prompt string on clipboard + desktop notification

  ---
  3. CORE ARCHITECTURE

  Style: Linear Pipeline with Strategy Pattern at Every Stage

  This is not MVC, hexagonal, or microservices. It is a linear data transformation pipeline where each stage has a pluggable strategy
  selected at runtime from configuration.

  Trigger → [Context Strategy] → [Intent Strategy] → [Fixed Transform] → [LLM Strategy] → [Delivery Strategy]

  Every variable concern in the pipeline is hidden behind an Abstract Base Class or factory function:

  - Terminal capture → TerminalBackend ABC with 4 implementations
  - Transcription → TranscriptionEngine ABC with 3 implementations
  - LLM → LLMClient wrapping litellm with 3 provider backends
  - Delivery → config-driven dispatch to clipboard/paste/file/api

  The fixed part is the pipeline orchestrator (run_pipeline in main.py), the ContextBuilder, and the ErrorDetectionEngine. These never
  change regardless of which strategies are selected.

  Why This Structure

  The author solved a platform diversity problem: tmux users, iTerm2 users, generic terminal users, macOS, Linux — all need to work.
  Rather than conditional branches scattered through the code, each environment concern is isolated into its own backend class. The
  pipeline code stays clean; the environment complexity lives in the strategy implementations.

  The frozen dataclass chain (TerminalState → ContextPayload) enforces that data is never mutated as it flows through the pipeline,
  which matters because the pipeline runs across a thread boundary (pynput OS thread → asyncio event loop).

  ---
  4. MAIN COMPONENTS OF THE SYSTEM

  Component 1: Hotkey Daemon (main.py:144–224)

  Responsibility: Bridge between OS-level keyboard events and the async pipeline.

  This component is architecturally critical and often misunderstood. pynput runs its keyboard listener on a dedicated OS thread — not
  on the asyncio event loop. The daemon maintains a reference to the running event loop (loop = asyncio.get_event_loop() at line 158)
  and uses asyncio.run_coroutine_threadsafe(run_pipeline(...), loop) to schedule pipeline execution from the pynput thread.

  The hotkey parsing (_parse_hotkey, line 161) converts user-facing strings like "ctrl+shift+p" into frozenset of pynput key objects.
  Matching uses activate_combo.issubset(frozenset(current_keys)) — a subset check, not equality — which correctly handles modifier keys
  held while pressing the trigger.

  Pipeline deduplication at line 197: if pipeline_task is None or pipeline_task.done() prevents stacking multiple pipeline runs if the
  user triggers the hotkey rapidly.

  Interacts with: All other components (it orchestrates the full pipeline in run_pipeline()), pynput library, asyncio event loop.

  ---
  Component 2: Terminal Monitor (terminal/monitor.py)

  Responsibility: Capture a frozen snapshot of the terminal state using whichever backend is available.

  This is the most complex component — 711 lines. It solves the problem that there is no universal way to read terminal state across
  environments.

  The ABC contract (TerminalBackend, line 72): Every backend must implement snapshot() → TerminalState and is_available() → bool. The
  _detect_git_branch() method is provided on the base class because all backends need it — it reads .git/HEAD directly (no subprocess)
  by walking up the directory tree from the CWD.

  Four backend implementations:

  TmuxBackend (line 376): Checks $TMUX env var for availability. In snapshot(), runs three blocking operations concurrently via
  asyncio.gather + run_in_executor: tmux capture-pane (screen buffer), tmux display-message × 5 (session metadata), and
  _read_shell_history. Returns a full TerminalState including screen buffer — the richest data.

  ITerm2Backend (line 467): macOS-only, requires the iterm2 pip package. Uses iterm2.run_until_complete() — a blocking call inside an
  async def. This is a threading hazard: it will block the event loop while connecting to iTerm2. All session variables are fetched
  concurrently via asyncio.gather inside the iTerm2 connection.

  ShellHookBackend (line 243): The universal option. Reads a JSON state file written by a shell hook that's installed into
  .zshrc/.bashrc/fish config. The hook itself (embedded as a raw string at lines 177–240) uses printf + sed to write JSON on every
  command. The backend finds the most recently modified state-{pid}.json file, supplementing it with shell history for up to 5 commands.

  GenericBackend (line 584): Always available. Uses os.getppid() to find the parent process (the shell that launched the daemon), then
  reads its CWD from /proc/{pid}/cwd (Linux) or lsof -p {pid} (macOS). No screen buffer — only history.

  Auto-detection (detect_backend, line 660): Tries backends in priority order: tmux → iTerm2 → shell_hook → generic. First
  is_available() == True wins. GenericBackend always returns True, so there is always a fallback.

  Key data structure: TerminalState (line 51) — frozen dataclass. Fields: screen_buffer, cwd, shell, last_commands: list[CommandRecord],
   running_process, git_branch, hostname, username, session_id, backend, captured_at. Immutability is enforced via
  @dataclass(frozen=True).

  ---
  Component 3: Voice Capture + Transcription (voice/capture.py, voice/transcribe.py)

  Responsibility: Convert microphone audio to a text transcript.

  VoiceCapture (line 32 of capture.py) handles the raw audio pipeline. It uses sounddevice.InputStream with a C-level callback that
  posts frames to an asyncio.Queue via call_soon_threadsafe — another thread boundary, similar to the pynput bridge.

  VAD logic (_record_with_vad, line 77): Two phases:

  1. Calibration (first 0.5s): Computes average RMS energy of ambient noise. Sets threshold to max(noise_floor × 3, 300). This makes the
   system adapt to the user's environment automatically.
  2. Detection: Frame-by-frame (30ms each, 16kHz mono). If energy > threshold: speech. Once speech has started, count consecutive silent
   frames. When silence exceeds silence_threshold_sec / 0.03 frames (default: ~33 frames = 1 second), recording ends.

  The 1-second minimum recording check (len(audio_data) < SAMPLE_RATE at line 61) silently discards any recording shorter than one
  second — including sub-second utterances.

  Audio is returned as WAV bytes (PCM int16, 16kHz, mono) via _to_wav(), written to an io.BytesIO buffer — never touches disk.

  Transcription strategies (transcribe.py): WhisperLocalEngine uses faster_whisper.WhisperModel with int8 quantization. WhisperAPIEngine
   posts WAV bytes to OpenAI's Whisper API. AppleSpeechEngine uses macOS SFSpeechRecognizer via pyobjc. All three return a
  TranscriptionResult dataclass with text: str and confidence: float | None.

  ---
  Component 4: Context Builder (terminal/context.py + terminal/error_patterns.py)

  Responsibility: Transform raw terminal state + voice transcript into a structured, LLM-ready ContextPayload.

  ContextBuilder.build() (line 84) does three things:
  1. Runs the ErrorDetectionEngine against terminal_state.screen_buffer
  2. Calls detect_project(terminal_state.cwd) to identify the project type
  3. Assembles everything into a frozen ContextPayload

  ContextBuilder.build_summary() (line 108) then flattens the payload into a plain dict[str, str] — this is what gets passed to
  META_PROMPT_TEMPLATE.format(**summary). The summary is the adapter between the rich domain objects and the string template.

  Error detection (ErrorDetectionEngine, error_patterns.py:51): 12 compiled regex patterns, each with named capture groups (file, line,
  column, code, message). Patterns cover TypeScript, ESLint, Python tracebacks, Python exceptions, Rust, Go, Node.js stack traces, Jest,
   pytest, generic error:/fatal:, Git conflicts, and permission errors.

  Deduplication key: (error_type, file, line, code) — same location with different messages collapses to first match.

  Project detection (detect_project, line 56): Walks up from CWD checking for 14 marker files. First match wins. Returns
  ProjectInfo(project_type, project_name, config_file). The priority is implicit in list order — package.json is checked before
  tsconfig.json, so a TypeScript project with both would be classified as nodejs, not typescript. This is a subtle design choice.

  ---
  Component 5: Prompt Builder (enhancer/prompt_builder.py)

  Responsibility: Render the meta-prompt that instructs the LLM.

  This is intentionally thin — 80 lines. The META_PROMPT_TEMPLATE (line 7) is a plain Python string with {key} format placeholders
  matching the keys in build_summary()'s output dict. build_meta_prompt() (line 52) is literally META_PROMPT_TEMPLATE.format(**summary)
  — a single line.

  The template encodes 8 rules for the LLM:
  1. Include specific file paths, error codes, line numbers
  2. Reference exact error messages
  3. Mention CWD and project type
  4. Max ~200 words
  5. Preserve user intent — do NOT add tasks
  6. Mention technology stack
  7. If no errors, focus on CWD/commands/request
  8. Write in second person

  The FALLBACK_TEMPLATE (line 67) is a simpler concatenation used when the LLM is unreachable — it produces a structured but unpolished
  prompt by just joining the key context fields.

  ---
  Component 6: LLM Client (enhancer/llm_client.py)

  Responsibility: Call the LLM with retry logic and graceful fallback.

  LLMClient wraps litellm's acompletion(). The model name is resolved with provider prefixes (ollama/llama3.2:8b,
  anthropic/claude-3.5-haiku, bare name for OpenAI) because litellm uses the prefix to route to the correct provider.

  Retry logic (line 100–154): Loop of 1 + max_retries attempts (default: 3 total). Exponential backoff: delay = 1.0 * (2^(attempt-1)).
  Error classification via _is_transient() (line 21): checks Python stdlib exception types, httpx exception types, status_code
  attribute, and keyword matching in the error message. Permanent errors (auth failure, invalid model) raise immediately without
  retrying.

  The two-message structure (line 120–132): System message constrains output format ("Output only the enhanced prompt"). User message
  carries the full meta-prompt with context. This separation means even if the user's voice input contains instructions that could
  confuse the LLM, the system role anchors the expected output format.

  The module-level enhance_prompt() function (line 174) creates a new LLMClient instance per call — no connection pooling. This is fine
  for a hotkey-triggered daemon (one call per trigger, infrequent) but would not scale to batch usage.

  ---
  Component 7: Delivery (delivery/clipboard.py, delivery/notification.py, delivery/iterm_paste.py)

  Responsibility: Put the enhanced prompt where the user can immediately use it.

  deliver_to_clipboard() tries platform-native tools in order: pbcopy (macOS subprocess), wl-copy (Wayland), xclip, xsel, then falls
  back to pyperclip. Each attempt is wrapped in a try/except — failure cascades to the next option.

  notify_enhanced_prompt() uses osascript on macOS (display notification "..." with title "...") and notify-send on Linux. Both are
  fire-and-forget subprocesses. The notification shows a truncated preview of the enhanced prompt (default: 100 chars, configurable).

  iterm_paste.py handles the optional direct-paste-into-terminal delivery mode via the iTerm2 Python API — only usable on macOS with
  iTerm2 running.

  ---
  5. EXECUTION FLOW

  The Complete Story of One Hotkey Press

  T=0ms — Boot:
  The user ran prompt-pulse start. load_config() read ~/.prompt-pulse/config.yaml into a validated AppConfig Pydantic model.
  asyncio.run(run_hotkey_daemon(config)) started the event loop. A pynput.keyboard.Listener started on a separate OS thread, polling for
   keyboard events. The process is now idle, consuming near-zero resources.

  T=0ms — Hotkey:
  The user presses Ctrl+Shift+P. on_press fires on the pynput thread. current_keys now contains {Key.ctrl, Key.shift, KeyCode('p')}. The
   subset check activate_combo.issubset(frozenset(current_keys)) passes. pipeline_task is None, so
  run_coroutine_threadsafe(run_pipeline(config, voice=True), loop) schedules the pipeline on the asyncio event loop.

  T=5ms — Terminal capture:
  create_backend("auto") probes: checks $TMUX env var (not set), checks for iterm2 package (not installed), checks for state-{pid}.json
  files in /tmp/prompt-pulse/ (found — the shell hook has been running). ShellHookBackend is selected.

  snapshot() reads the most recently modified state file (e.g., /tmp/prompt-pulse/state-43821.json), gets {"cwd": "/home/vinny/project",
   "last_command": "npm run build", "exit_code": 1, ...}. It supplements this with the last 5 entries from ~/.zsh_history. It reads
  .git/HEAD at /home/vinny/project/.git/HEAD and finds ref: refs/heads/feature/auth-refactor. Returns a frozen TerminalState.

  T=10ms — Voice listening:
  notify_listening() fires a desktop notification ("PromptPulse is listening..."). VoiceCapture starts sounddevice.InputStream at 16kHz
  mono. Audio frames arrive every 30ms via the PortAudio callback. The first 16 frames (~500ms) are used for noise calibration. The
  noise floor is measured at ~120 RMS, threshold set to max(360, 300) = 360.

  T=600ms — User speaks:
  "Fix the build error in the auth module." Frame energies spike above 360. speech_started = True. Frames accumulate.

  T=3100ms — Silence:
  The user stops speaking. Silence frame counter reaches 33 (1 second). Recording ends. np.concatenate(frames) produces a 40,000-sample
  array (2.5 seconds of speech). _to_wav() encodes it to WAV bytes in memory (never touches disk).

  T=4600ms — Transcription:
  WhisperLocalEngine loads faster_whisper.WhisperModel("base.en", compute_type="int8"). Transcribes: "Fix the build error in the auth
  module." Returns TranscriptionResult(text="Fix the build error in the auth module.", confidence=0.94).

  T=4700ms — Context build:
  ContextBuilder().build(terminal_state, voice_transcript="Fix the build error in the auth module.") is called.

  ErrorDetectionEngine.detect("") runs all 12 regex patterns against the screen buffer. The screen buffer is empty (shell_hook backend
  has no screen buffer), so no errors are detected.

  detect_project("/home/vinny/project") finds package.json → ProjectInfo(project_type="nodejs", project_name="project",
  config_file="...").

  A frozen ContextPayload is assembled.

  build_summary(context) flattens it to a dict: {"voice_transcript": "Fix the build error...", "cwd": "/home/vinny/project",
  "git_branch": "feature/auth-refactor", "last_commands": "$ npm run build (exit 1)", "detected_errors": "none detected",
  "project_type": "nodejs", ...}.

  T=4710ms — Prompt construction:
  build_meta_prompt(context, summary) calls META_PROMPT_TEMPLATE.format(**summary). The resulting string is ~800 chars — the full
  meta-prompt with all context embedded.

  build_fallback_prompt(summary) constructs the backup template string in case the LLM fails.

  T=4720ms — LLM call:
  LLMClient(config).complete(meta_prompt) calls litellm.acompletion(model="ollama/llama3.2:8b", messages=[system, user],
  temperature=0.3, max_tokens=500). litellm sends a POST to localhost:11434/api/chat.

  Ollama processes the prompt. ~2.5 seconds later, returns: "Fix the Node.js build failure in the auth module. The last command npm run
  build exited with code 1 on branch feature/auth-refactor. Working directory: /home/vinny/project. Check the build output for
  TypeScript compilation errors or missing dependencies, focusing on the auth module source files."

  T=7300ms — Delivery:
  deliver_to_clipboard(enhanced) runs subprocess.run(["pbcopy"], ...) (macOS) or the Linux equivalent. The enhanced prompt is now on the
   clipboard.

  notify_enhanced_prompt(enhanced) fires an OS notification with the first 100 chars as preview.

  console.print(Panel(enhanced, ...)) renders the result in the terminal.

  T=7310ms — Done:
  run_pipeline() returns. pipeline_task.done() is now True. The daemon is ready for the next hotkey press.

  ---
  6. DATA FLOW

  The Transformation Chain

  INPUTS
    Keyboard event (OS)
    Microphone audio (PortAudio → numpy int16 array)
    Shell state file (/tmp/prompt-pulse/state-{pid}.json)
    Shell history (~/.zsh_history)
    Git HEAD (.git/HEAD file)
    User config (~/.prompt-pulse/config.yaml)

  STEP 1: Audio → WAV bytes
    np.ndarray (int16, 16kHz, mono)
    → energy-based VAD (RMS calculation)
    → filtered audio frames
    → wave.open() encoding
    → bytes (WAV container, never written to disk)

  STEP 2: WAV bytes → transcript
    bytes
    → faster_whisper.WhisperModel.transcribe()
    → TranscriptionResult { text: str, confidence: float }
    → str (transcript)

  STEP 3: Shell state + history → TerminalState (frozen)
    JSON file → dict
    .zsh_history → list[CommandRecord]
    .git/HEAD → str (branch name)
    → TerminalState (frozen dataclass, all fields str/list/None)

  STEP 4: TerminalState + transcript → ContextPayload (frozen)
    TerminalState + transcript
    → ErrorDetectionEngine.detect(screen_buffer)  [regex → list[DetectedError]]
    → detect_project(cwd)  [filesystem walk → ProjectInfo]
    → ContextPayload (frozen, contains TerminalState + DetectedErrors + ProjectInfo)

  STEP 5: ContextPayload → dict
    ContextPayload
    → ContextBuilder.build_summary()
    → dict[str, str]  (flat string representation of all context)

  STEP 6: dict → meta-prompt string
    dict[str, str]
    → META_PROMPT_TEMPLATE.format(**summary)
    → str (~800 chars, complete LLM prompt)

  STEP 7: meta-prompt → enhanced prompt
    str
    → litellm.acompletion() → LLM API
    → response.choices[0].message.content.strip()
    → str (~100-200 words, the enhanced prompt)

  OUTPUTS
    Clipboard (pbcopy / xclip / wl-copy)
    OS notification (osascript / notify-send)
    Terminal display (rich Panel)
    Optional: ~/.prompt-pulse/last-prompt.txt

  State That Persists Between Runs

  Only two things persist between pipeline executions:

  1. ~/.prompt-pulse/config.yaml — loaded once at startup, held in memory as AppConfig
  2. /tmp/prompt-pulse/state-{pid}.json — written by the shell on every command, read once per pipeline run

  Everything else — audio, TerminalState, ContextPayload, the LLM response — is ephemeral. No database, no logs of what was enhanced, no
   cache.

  ---
  7. KEY TECHNOLOGIES USED

  ┌────────────────┬──────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────┐
  │   Technology   │       Role       │                                         Why chosen                                          │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Python 3.11+   │ Primary language │ iTerm2's official scripting API is Python-only; asyncio needed for concurrent               │
  │                │                  │ terminal/audio capture; rich ML/audio ecosystem                                             │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Typer          │ CLI framework    │ Built on Click; adds Rich integration for colored output and help formatting;               │
  │                │                  │ no_args_is_help=True makes the CLI self-documenting without extra code                      │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │                │ Config           │ Provides Literal types for constrained fields (e.g., provider: Literal["ollama", "openai",  │
  │ Pydantic v2    │ validation       │ "anthropic"]); resolve_api_key() pattern for env var substitution; fail-fast on startup     │
  │                │                  │ with bad config                                                                             │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ sounddevice    │ Microphone       │ Wraps PortAudio (cross-platform); provides C-level callback-based streaming; supports async │
  │                │ recording        │  queue bridge pattern used here                                                             │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ numpy          │ Audio processing │ RMS energy calculation: sqrt(mean(frame^2)) — one line. Also required by sounddevice for    │
  │                │                  │ dtype handling                                                                              │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ faster-whisper │ Speech-to-text   │ Local, offline, private; int8 quantized for speed; no API key required; base.en model is    │
  │                │                  │ ~145MB and accurate for developer vocabulary                                                │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ litellm        │ LLM abstraction  │ Single acompletion() interface across Ollama, OpenAI, Anthropic, and 100+ other providers;  │
  │                │                  │ handles provider-specific auth and API formats internally                                   │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │                │                  │ Cross-platform keyboard listener (macOS + Linux); runs on dedicated OS thread; the only     │
  │ pynput         │ Global hotkeys   │ library that intercepts key events system-wide without X11/Wayland specifics in application │
  │                │                  │  code                                                                                       │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ httpx          │ HTTP client      │ Used only for the Ollama health check and _is_transient() exception detection; litellm uses │
  │                │ (limited)        │  it internally too                                                                          │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Rich           │ Terminal output  │ Panel, Console, RichHandler — all used for the user-facing display; the [all] typer extra   │
  │                │                  │ brings it in anyway                                                                         │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ uv             │ Package manager  │ Rust-based, significantly faster than pip for the heavy ML dependency tree (numpy,          │
  │                │                  │ sounddevice, faster-whisper)                                                                │
  ├────────────────┼──────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────┤
  │ hatchling      │ Build backend    │ Modern, zero-config build system; works cleanly with src/ layout                            │
  └────────────────┴──────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  8. IMPORTANT DESIGN DECISIONS

  Decision 1: Frozen Dataclasses for All Domain Objects

  Every domain object in the pipeline (CommandRecord, TerminalState, DetectedError, ProjectInfo, ContextPayload) is a
  @dataclass(frozen=True). This is not incidental — it's a response to the threading model. The pynput listener thread and the asyncio
  event loop share no mutable state. Data flows one direction: the thread schedules a coroutine, the coroutine builds immutable objects,
   the immutable objects flow through the pipeline. Python's GIL prevents data races on reference reads, but frozen dataclasses make the
   immutability contract explicit and enforced by the runtime.

  Decision 2: run_coroutine_threadsafe as the Thread Bridge

  The choice to use pynput + asyncio.run_coroutine_threadsafe rather than a simpler approach (like asyncio.run() per hotkey in a new
  thread) is deliberate. A single long-lived event loop means:
  - All async operations share the loop (no thread-per-hotkey overhead)
  - pipeline_task.done() check prevents concurrent pipeline runs
  - All async resources (subprocess calls, HTTP connections) are managed by one scheduler

  The alternative — creating a new event loop per hotkey press — would either block the pynput thread (preventing hotkey detection
  during pipeline execution) or require a thread pool.

  Decision 3: Late Imports Inside Pipeline Functions

  All heavy imports (litellm, sounddevice, pynput, faster_whisper) are deferred inside run_pipeline() and run_hotkey_daemon() (main.py
  lines 41-56, 146). prompt-pulse --help completes in ~200ms because it never imports numpy or litellm. This is a deliberate startup
  optimization — the import cost of the ML stack is only paid when the pipeline actually runs.

  Decision 4: Strategy Pattern Over Conditional Branches

  Each variable concern (terminal backend, transcription engine, LLM provider, delivery method) is encapsulated in a class hierarchy
  rather than handled by if backend == "tmux": branches scattered through the pipeline. This means:
  - Adding a new terminal backend requires one new class implementing TerminalBackend + one entry in the factory dict
  - The pipeline code (run_pipeline) never changes when new backends are added
  - Each backend is independently testable

  Decision 5: Template Fallback Instead of Hard Failure

  build_fallback_prompt() (prompt_builder.py:77) exists so that LLM failure never surfaces to the user as an empty clipboard. The
  fallback produces a structured concatenation of voice transcript + context fields — not as polished as LLM enhancement, but far better
   than nothing. Combined with the retry logic in LLMClient, this means the user almost always gets something useful.

  Decision 6: Shell Hook State File Over Subprocess

  Rather than running ps -ef, lsof, or inspecting /proc to reconstruct terminal state, the shell hook approach has the shell write its
  own state to a JSON file after every command. This is opt-in but yields precise data (exact CWD, exact last command, exact exit code)
  that no amount of process inspection can match. The tradeoff: it requires a one-time hook installation (prompt-pulse install-hook).

  Decision 7: Git Branch Read from .git/HEAD Directly

  _detect_git_branch() (monitor.py:89) reads .git/HEAD as a text file rather than running git rev-parse --abbrev-ref HEAD. This avoids
  spawning a subprocess, works offline, works in environments where git isn't in $PATH, and cannot trigger any git hooks. The only gap:
  it doesn't handle git worktree (which puts HEAD in a different location). This tradeoff prioritizes speed and zero subprocess
  overhead.

  ---
  9. DEPENDENCY RELATIONSHIPS

  AppConfig (config.py)
      └── consumed by ALL components
           (every component receives config or a sub-config)

  main.py (pipeline orchestrator)
      ├── depends on → terminal/monitor.py (create_backend, TerminalState)
      ├── depends on → voice/capture.py (VoiceCapture)
      ├── depends on → voice/transcribe.py (create_engine)
      ├── depends on → terminal/context.py (ContextBuilder)
      ├── depends on → enhancer/prompt_builder.py (build_meta_prompt, build_fallback_prompt)
      ├── depends on → enhancer/llm_client.py (enhance_prompt)
      └── depends on → delivery/* (deliver_to_clipboard, notify_*)

  terminal/context.py
      ├── depends on → terminal/monitor.py (TerminalState)
      └── depends on → terminal/error_patterns.py (ErrorDetectionEngine)

  enhancer/llm_client.py
      ├── depends on → config.py (LLMConfig)
      └── depends on → litellm (external)

  enhancer/prompt_builder.py
      └── depends on → terminal/context.py (ContextPayload)

  voice/capture.py
      └── depends on → sounddevice, numpy (external)

  voice/transcribe.py
      └── depends on → faster_whisper / openai / pyobjc (external, strategy-dependent)

  terminal/monitor.py
      └── depends on → iterm2 (optional external)

  No circular dependencies. The dependency graph is strictly acyclic: orchestrator → pipeline stages → data structures. Config flows
  into every layer but is never modified. Domain objects (TerminalState, ContextPayload) are produced upstream and consumed downstream —
   never the reverse.

  ---
  10. CONFIGURATION & ENVIRONMENT

  Config Loading (config.py:67–82)

  Three-level fallback:
  1. Explicit path from --config CLI flag
  2. ~/.prompt-pulse/config.yaml (default user config)
  3. config.example.yaml from the source tree (fallback for fresh installs)
  4. AppConfig() with all defaults (if nothing else exists)

  AppConfig is a Pydantic BaseModel — on load, AppConfig(**raw_dict) validates all fields. Invalid values (e.g., provider: "gemini")
  raise ValidationError at startup, not during pipeline execution.

  Environment Variable Resolution

  LLMConfig.resolve_api_key() (line 38) handles the ${VAR} pattern. It's a 4-line hand-rolled expander — not a full template engine.
  Only works at the top level of the api_key field; nested env vars elsewhere in config are not substituted.

  State File Location

  STATE_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "prompt-pulse" (monitor.py:32). On systems with XDG_RUNTIME_DIR set
  (standard on Linux with systemd), state files live in the runtime directory (tmpfs, cleaned on logout). On macOS (no XDG), they live
  in /tmp/prompt-pulse/.

  Docker

  The Dockerfile is a three-stage build (base → builder → runtime). Key decisions:
  - libportaudio2 installed in base stage — required by sounddevice
  - uv sync --frozen --no-dev --no-install-project first (dependency layer caches independently of source changes)
  - Non-root user appuser in runtime stage
  - ENTRYPOINT ["prompt-pulse"] with CMD ["--help"] — the container image is primarily for distribution, not for running the daemon
  (voice capture in a container without device passthrough is impractical)

  CI/CD

  The CI matrix runs 6 parallel jobs (2 OS × 3 Python versions). Linux jobs install libportaudio2 as a system dependency; macOS relies
  on the GitHub runner's pre-installed PortAudio. Release is tag-triggered with OIDC trusted publishing to PyPI (no stored API token).
  Docker multi-arch build (linux/amd64,linux/arm64) publishes to GHCR.

  ---
  11. HOW TO RUN THE PROJECT

  Prerequisites

  # macOS: PortAudio is pre-installed
  # Linux: sudo apt install libportaudio2 xclip libnotify-bin

  # Install uv (fast Python package manager)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  Setup

  git clone https://github.com/disencd/prompt-pulse.git
  cd prompt-pulse

  # Install with dev dependencies
  uv sync --extra dev

  # Initialize config directory (~/.prompt-pulse/config.yaml)
  uv run prompt-pulse init

  # Install shell hook (captures CWD, last command, exit code)
  uv run prompt-pulse install-hook
  # Restart shell or: source ~/.prompt-pulse/hook.zsh

  Configure LLM

  For local (private, free):
  brew install ollama && ollama pull llama3.2:8b
  # config.yaml: llm.provider: ollama (default — no changes needed)

  For Gemini (planned Cloud Run):
  export GEMINI_API_KEY=your_key
  # config.yaml: provider: gemini, api_key: ${GEMINI_API_KEY}

  Run

  # One-shot text enhancement (quickest test)
  uv run prompt-pulse enhance "fix the build error"

  # Full daemon with hotkeys
  uv run prompt-pulse start

  # Show what context would be captured right now
  uv run prompt-pulse context

  Test

  uv run pytest tests/ -v --tb=short       # All tests
  uv run pytest tests/test_error_patterns.py -v  # Single file
  uv run ruff check src/ tests/            # Lint
  uv run ruff format src/ tests/           # Format

  Entry Point Trace

  CLI invocation → pyproject.toml script entry → main.py:app()
  → typer dispatches to start() / enhance() / context() / install_hook() / init()
  → start() calls asyncio.run(run_hotkey_daemon(config))
  → daemon blocks on asyncio.sleep(1) loop until KeyboardInterrupt

  ---
  12. POTENTIAL IMPROVEMENTS

  Critical Bugs to Fix First

  1. LLMConfig.provider missing "gemini" literal (config.py:32):
  The documentation and architecture have been updated to use Gemini, but Literal["ollama", "openai", "anthropic"] in Pydantic will
  throw a ValidationError the moment someone sets provider: gemini. This must be extended to Literal["ollama", "openai", "anthropic",
  "gemini"] and the _resolve_model_name() method in llm_client.py must handle the gemini case — or better, a new enhancement_client.py
  making HTTP calls to Cloud Run must be wired in.

  2. whispercpp vs faster-whisper dependency mismatch (pyproject.toml:14):
  pyproject.toml declares whispercpp>=0.0.17 but voice/transcribe.py imports faster_whisper. These are different packages. whispercpp
  should be replaced with faster-whisper>=1.0 in the dependencies.

  3. iterm2.run_until_complete() blocks the event loop (monitor.py:572):
  This is a synchronous blocking call inside async def snapshot(). It will freeze the entire asyncio event loop during the iTerm2
  connection handshake (which involves an HTTP upgrade to WebSocket). Should be wrapped in loop.run_in_executor(None,
  iterm2.run_until_complete, _capture).

  Architecture Improvements

  4. Cloud Run enhancement_client.py is unimplemented:
  The architecture was updated in documentation but the actual src/prompt_pulse/enhancer/enhancement_client.py doesn't exist.
  run_pipeline() in main.py still calls enhance_prompt() which calls litellm directly. The HTTP client to Cloud Run needs to be written
  and wired into the pipeline dispatch logic.

  5. DEFAULT_CONFIG path breaks in wheel installation (config.py:14):
  Path(__file__).parent.parent.parent / "config.example.yaml" works from the source tree but the file is not included in the wheel (it's
   outside src/prompt_pulse/). Either move config.example.yaml inside the package (e.g., src/prompt_pulse/data/config.example.yaml) and
  use importlib.resources to access it, or use package_data in pyproject.toml.

  6. TmuxBackend runs 5 separate subprocesses for session info (monitor.py:437–458):
  _tmux_session_info() calls tmux display-message five times, once per variable. A single call with a combined format string (e.g., tmux
   display-message -p "#{session_name}|#{pane_id}|#{pane_current_path}|...") would be both faster and more atomic.

  7. Shell hook JSON generation via printf+sed is fragile (monitor.py:190-194):
  Commands containing backslashes, newlines, Unicode outside ASCII, or embedded double-quotes will produce invalid JSON. The hook reads
  json.loads() with a silent fallback on JSONDecodeError (monitor.py:270-272), so failures are invisible. A more robust approach would
  base64-encode the command string before embedding it.

  Testing Gaps

  8. No integration tests for the full pipeline:
  test_prompt_pulse.py only tests template rendering. There are no tests that exercise run_pipeline() end-to-end with mocked backends,
  no tests for the retry logic under simulated LLM failure, and no tests for the thread bridge (run_coroutine_threadsafe). The most
  critical code path in the system has zero test coverage.

  9. No test for the _find_state_file multi-terminal race (monitor.py:313):
  The "most recently modified state file" heuristic is untested for the scenario of multiple concurrent shells. A test fixture with
  multiple state files at different mtimes would clarify the intended behavior.

  10. No property-based testing for ErrorDetectionEngine:
  The 12 regex patterns are only tested against handcrafted examples. ANSI escape codes in screen buffer output (the most likely
  real-world corruption) are never tested. hypothesis could generate plausible terminal output variants systematically.

  Scalability & Operational Improvements

  11. Whisper model loading on every transcription call:
  WhisperLocalEngine.transcribe() implicitly loads the model on first call via WhisperModel(self._model_size, ...). If the model is not
  cached by faster-whisper, this adds 1-2 seconds to the first hotkey press. The model should be loaded eagerly at daemon startup and
  held in memory, not reconstructed per-call.

  12. No observability:
  There are no metrics, no structured log output that could be parsed, and no way to know how often the LLM fallback is triggered vs.
  successful LLM calls. For a tool that sits in the background and silently degrades, this makes debugging user complaints ("it's not
  working") difficult. Even a simple ~/.prompt-pulse/stats.json with success/failure counters would help.