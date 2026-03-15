# PromptShell — System Design

## 1. High-Level Architecture
```mermaid
flowchart TB
    subgraph USER["👤 Developer"]
        HK["Hotkey<br/>Ctrl+Alt+E"]
        MIC["🎙️ Microphone<br/>(voice command)"]
        CB["📋 Clipboard<br/>(enhanced prompt)"]
    end

    subgraph LOCAL["🖥️ Local Machine (macOS / Linux)"]
        direction TB

        subgraph CAPTURE["Context Capture (concurrent)"]
            TM["Terminal Monitor<br/>4 backends"]
            SC["Screenshot Capture<br/>grim / scrot / screencapture"]
            VC["Voice Capture<br/>sounddevice + VAD"]
            TR["Transcription<br/>faster-whisper (local)"]
        end

        subgraph CORE["Core Pipeline"]
            ED["Error Detection Engine<br/>12+ regex pattern families"]
            PD["Project Detector<br/>package.json / Cargo.toml / go.mod"]
            CB2["Context Builder<br/>ContextPayload"]
            EC["Enhancement Client<br/>httpx async POST"]
        end

        subgraph FALLBACK["Local Fallback"]
            LC["LLM Client<br/>litellm -> Ollama / OpenAI / Anthropic"]
            TPL["Template Builder<br/>(no LLM)"]
        end

        subgraph DELIVER["Delivery"]
            DEL["Delivery Engine"]
            NOTIF["Notification<br/>osascript / notify-send"]
        end
    end

    subgraph GCP["☁️ Google Cloud Platform"]
        subgraph CR["Cloud Run Service"]
            API["FastAPI<br/>POST /enhance<br/>GET /health"]
            PB["Meta-Prompt Builder<br/>3-step template"]
            GC["Google GenAI SDK<br/>google-genai"]
        end
        GEMINI["Gemini 2.5 Flash Lite<br/>(multimodal: text + image)"]
        SM["Secret Manager<br/>GEMINI_API_KEY"]
        AR["Artifact Registry<br/>Docker image"]
    end

    HK --> CAPTURE
    MIC --> VC
    VC --> TR
    TM --> CB2
    SC --> CB2
    TR --> CB2
    ED --> CB2
    PD --> CB2
    TM --> ED
    TM --> PD

    CB2 --> EC
    EC --> API
    API --> PB
    PB --> GC
    GC --> GEMINI
    GEMINI --> GC
    GC --> API
    API --> EC

    EC --> LC
    LC --> TPL

    EC --> DEL
    LC --> DEL
    TPL --> DEL
    DEL --> CB
    DEL --> NOTIF

    SM -.-> CR
    AR -.-> CR
```
---

## 2. End-to-End Pipeline Sequence

```mermaid
sequenceDiagram
    actor User
    participant HK as Hotkey Daemon
    participant SC as Screenshot Capture
    participant VC as Voice Capture
    participant TR as Transcription
    participant TM as Terminal Monitor
    participant CB as Context Builder
    participant EC as Enhancement Client
    participant CR as Cloud Run
    participant GM as Gemini 2.5 Flash Lite
    participant DL as Delivery Engine

    User->>HK: Ctrl+Alt+E

    par Concurrent capture
        HK->>SC: capture_screenshot()
        Note over SC: grim / scrot / screencapture
        HK->>VC: start_recording()
        Note over VC: sounddevice 16kHz mono
        HK->>TM: snapshot()
        Note over TM: tmux / iterm2 / shell_hook / generic
    end

    User->>VC: speaks "fix the error"
    VC-->>VC: VAD detects 1s silence
    VC->>TR: raw audio frames
    TR-->>VC: transcript: "fix the error"

    SC-->>CB: screenshot_b64 (PNG, base64)
    TM-->>CB: TerminalState
    VC-->>CB: voice_transcript

    CB->>CB: detect_errors(screen_buffer)
    CB->>CB: detect_project(cwd)
    CB-->>EC: ContextPayload

    EC->>CR: POST /enhance (JSON)
    Note over EC,CR: {voice_transcript, cwd, screen_buffer,<br/>detected_errors, screenshot_b64, ...}

    CR->>CR: build_meta_prompt(payload)
    Note over CR: Step 1: read screenshot<br/>Step 2: classify intent<br/>Step 3: write enhanced prompt

    CR->>GM: generate_content([text_part, image_part])
    GM-->>CR: enhanced prompt text

    CR-->>EC: {"enhanced_prompt": "Fix TypeScript..."}
    EC-->>DL: enhanced_prompt

    DL->>User: pbcopy / wl-copy → clipboard
    DL->>User: desktop notification (preview)
```

---

## 3. Terminal Backend Auto-Detection

```mermaid
flowchart TD
    START([Daemon Startup]) --> PROBE

    PROBE["BackendDetector\nprobes in order"]

    PROBE --> T1{"tmux running?\n$TMUX set?"}
    T1 -->|Yes| TMUX["TmuxBackend\n✓ screen buffer\n✓ CWD\n✓ commands\n✓ exit codes via hook"]
    T1 -->|No| T2

    T2{"iTerm2 running?\niterm2 pkg installed?"}
    T2 -->|Yes| ITERM["ITerm2Backend\n✓ screen buffer\n✓ CWD\n✓ commands\n✓ exit codes\n⚠ macOS only"]
    T2 -->|No| T3

    T3{"shell_state.json\nexists?"}
    T3 -->|Yes| HOOK["ShellHookBackend\n✗ screen buffer\n✓ CWD\n✓ commands\n✓ exit codes"]
    T3 -->|No| T4

    T4["GenericBackend\n✗ screen buffer\n✓ CWD (proc/lsof)\n✓ history\n✗ exit codes\n(always available)"]

    TMUX --> POLL
    ITERM --> POLL
    HOOK --> POLL
    T4 --> POLL

    POLL["Poll every 2s\n→ TerminalState cache"]
    POLL --> TRIG{"hotkey\ntrigger?"}
    TRIG -->|Yes| SNAP["snapshot() →\nfrozen TerminalState"]
    TRIG -->|No| POLL
```

---

## 4. Multimodal Gemini Request Construction

```mermaid
flowchart LR
    subgraph INPUT["ContextPayload"]
        VT["voice_transcript\n'fix the error'"]
        SB["screen_buffer\n(last 50 lines)"]
        DE["detected_errors\nTS2345 src/auth.ts:42"]
        CWD["cwd / git_branch\nproject_type"]
        SS["screenshot_b64\nPNG base64"]
    end

    subgraph BUILDER["Meta-Prompt Builder"]
        S1["STEP 1\nRead screenshot\nas ground truth"]
        S2["STEP 2\nClassify intent\nfix_error / explain /\nrefactor / add_feature /\nwrite_test / debug"]
        S3["STEP 3\nWrite enhanced prompt\nimperative sentence\n+ exact specifics"]
    end

    subgraph GENAI["Google GenAI SDK"]
        P1["Part.from_text\n(meta-prompt)"]
        P2["Part.from_bytes\n(PNG image)\nmime_type=image/png"]
        REQ["client.models\n.generate_content(\n  model,\n  contents=[P1, P2]\n)"]
    end

    subgraph OUTPUT["Enhanced Prompt"]
        EP["Fix the TypeScript error TS2345\nin src/auth/middleware.ts:42 —\nArgument of type 'string' is not\nassignable to parameter of type\n'AuthToken'.\nCommand: npm run build (exit 1)\nBranch: feature/auth-refactor"]
    end

    INPUT --> BUILDER
    BUILDER --> P1
    SS --> P2
    P1 --> REQ
    P2 --> REQ
    REQ --> OUTPUT
```

---

## 5. Error Detection Engine

```mermaid
flowchart TD
    BUF["screen_buffer\n(raw terminal text)"]

    BUF --> EDE["ErrorDetectionEngine\n.detect(screen_buffer)"]

    EDE --> R1["TypeScript\nTS\\d+ error"]
    EDE --> R2["Python Traceback\nTraceback (most recent call last)"]
    EDE --> R3["Rust compiler\nerror\\[E\\d+\\]"]
    EDE --> R4["Go\n\\.go:\\d+:\\d+:"]
    EDE --> R5["Node.js\n(TypeError|ReferenceError)"]
    EDE --> R6["Jest / pytest\nFAILED | FAILED test"]
    EDE --> R7["ESLint\nError: .* rule"]
    EDE --> R8["Git conflict\n<<<<<<< HEAD"]
    EDE --> R9["Permission\n(EACCES|Permission denied)"]
    EDE --> R10["Segfault\nSegmentation fault"]
    EDE --> R11["cargo test\ntest .* FAILED"]
    EDE --> R12["HTTP / network\n(404|500|ECONNREFUSED)"]

    R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11 & R12 --> OUT

    OUT["DetectedError[]\n{error_type, code, file, line, message}"]
    OUT --> CB["Context Builder\n→ ContextPayload.detected_errors"]
```

---

## 6. Graceful Degradation Chain

```mermaid
flowchart TD
    START["Enhancement Request"] --> CR

    CR{"Cloud Run\nreachable?"}
    CR -->|Yes, 2xx| OK["✅ Gemini-enhanced prompt\n(multimodal, structured)"]
    CR -->|No / 5xx| RETRY["Retry once\n(exponential backoff)"]
    RETRY --> CR2{"Retry\nsucceeded?"}
    CR2 -->|Yes| OK
    CR2 -->|No| LOCAL

    LOCAL{"Local LLM\nconfigured?\n(litellm)"}
    LOCAL -->|Yes| OLLAMA["🦙 Local LLM\n(Ollama / llama3.2:8b)\nor OpenAI / Anthropic"]
    LOCAL -->|No| TPL

    OLLAMA --> OLLOK{"LLM\nresponded?"}
    OLLOK -->|Yes| OK2["✅ Local LLM-enhanced prompt\n(no cloud dependency)"]
    OLLOK -->|No| TPL

    TPL["📄 Template fallback\nbuild_fallback_prompt(summary)\nno LLM required"]
    TPL --> OK3["✅ Template prompt\n(always succeeds)"]

    OK --> DEL["Delivery Engine\n→ Clipboard + Notification"]
    OK2 --> DEL
    OK3 --> DEL
```

---

## 7. CI/CD and Deployment Pipeline

```mermaid
flowchart LR
    subgraph DEV["Developer"]
        CODE["git commit"]
        TAG["git tag v0.x.x\ngit push origin v0.x.x"]
    end

    subgraph GHA["GitHub Actions  (release.yml)"]
        direction TB
        V["validate\nruff lint + format check"]
        T["test\npytest (49 tests)"]
        B["build\nuv build wheel + sdist"]
        PP["publish-pypi\ntwine upload"]
        DCR["deploy-cloud-run\ngcloud builds submit\ngcloud run deploy\nimage tag: v0.x.x"]
        GR["github-release\ngh release create"]
        DK["docker\nbuild + push\nDockerHub image"]
    end

    subgraph GCP2["Google Cloud"]
        CB2["Cloud Build\nbuild container"]
        AR2["Artifact Registry\ngcr.io/.../prompt-shell-enhancer:v0.x.x"]
        CR2["Cloud Run\nprompt-shell-enhancer\n(live service)"]
        HC["Health check\nGET /health → 200"]
    end

    subgraph MANUAL["Manual Re-deploy\n(deploy-cloud-run.yml)"]
        WD["workflow_dispatch\n(secret rotation / hotfix)"]
    end

    CODE -->|push to main| V
    TAG --> V
    V --> T --> B --> PP --> DCR
    PP --> GR
    PP --> DK
    DCR --> CB2 --> AR2 --> CR2 --> HC

    WD --> CB2
```

---

## 8. Data Model

```mermaid
classDiagram
    class ContextPayload {
        +str timestamp
        +str voice_transcript
        +TerminalState terminal
        +DetectedError[] detected_errors
        +ProjectInfo project
        +str|None screenshot_b64
    }

    class TerminalState {
        +str cwd
        +str shell
        +str|None screen_buffer
        +CommandRecord[] last_commands
        +str|None git_branch
        +str|None running_process
    }

    class CommandRecord {
        +str command
        +int|None exit_code
        +str timestamp
    }

    class DetectedError {
        +str error_type
        +str|None code
        +str|None file
        +str|None line
        +str|None message
    }

    class ProjectInfo {
        +str|None project_type
        +str|None project_name
        +str|None config_file
    }

    class EnhanceRequest {
        +str voice_transcript
        +str cwd
        +str git_branch
        +str shell
        +str last_commands
        +str detected_errors
        +str screen_buffer_last_50
        +str project_type
        +str project_name
        +str|None screenshot_b64
    }

    ContextPayload "1" --> "1" TerminalState
    ContextPayload "1" --> "0..*" DetectedError
    ContextPayload "1" --> "1" ProjectInfo
    TerminalState "1" --> "0..*" CommandRecord
    ContextPayload ..> EnhanceRequest : serialized to
```

---

## 9. Component Responsibility Map

```mermaid
flowchart TD
    subgraph LOCAL2["Local Client  src/prompt_shell/"]
        M["main.py\nCLI + hotkey daemon\npipeline orchestrator"]

        subgraph T["terminal/"]
            MON["monitor.py\nTerminalBackend ABC\n+ 4 implementations"]
            CTX["context.py\nContextBuilder\nProjectInfo detection"]
            ERR["error_patterns.py\nErrorDetectionEngine\n12+ regex families"]
            SSHOT["screenshot.py\ncross-platform PNG\ncapture"]
        end

        subgraph VO["voice/"]
            CAP["capture.py\nsounddevice recording\nenergy-based VAD"]
            TRN["transcribe.py\nfaster-whisper (local)\nOpenAI API\nApple Speech"]
        end

        subgraph EN["enhancer/"]
            ECLI["enhancement_client.py\nhttpx async\nPOST /enhance"]
            PB["prompt_builder.py\nfallback template\n(no LLM)"]
            LC2["llm_client.py\nlitellm wrapper\nOllama / OpenAI / Anthropic"]
        end

        subgraph DV["delivery/"]
            CLP["clipboard.py\npbcopy / wl-copy / xclip"]
            ITP["iterm_paste.py\niTerm2 direct paste"]
            NOT["notification.py\nosascript / notify-send"]
        end

        CFG["config.py\nPydantic models\nYAML + env var substitution"]
    end

    subgraph CRS["Cloud Run  cloud_run_service/"]
        CRMAIN["main.py\nFastAPI app\nPOST /enhance\nGET /health"]
        CRPB["prompt_builder.py\n3-step meta-prompt\nrenderer"]
        CRGC["gemini_client.py\ngoogle-genai SDK\nmultimodal support"]
    end

    M --> T & VO & EN & DV & CFG
    CRMAIN --> CRPB --> CRGC
```
