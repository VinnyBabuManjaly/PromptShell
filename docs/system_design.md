# PromptShell — System Design

## 1. High-Level Architecture
```mermaid
flowchart TB
    subgraph INPUT["1 · Trigger"]
        HK["Hotkey<br/><i>Ctrl+Alt+E - starts voice + capture</i>"]
        CLI["CLI<br/><i>prompt-shell enhance 'text'</i>"]
    end

    subgraph CAPTURE["2 · Multimodal Context Agent"]
        TM["Terminal State Monitor<br/><i>tmux · iTerm2 · shell hook · generic</i>"]
        SS["Vision Capture<br/><i>terminal screenshot (PNG)</i>"]
        VR["Speech-to-Text (Whisper AI)<br/><i>hotkey only . local transcription</i>"]
    end

    subgraph BUILD["3 · Build"]
        CB["Context Aggregator<br/><i>error detection · project detection</i>"]
    end

    subgraph ENHANCE["4 · AI Enhancement"]
        EC["AI Orchestrator"]
    end

    subgraph GCP["☁️ Google Cloud AI Platform"]
        CR["Cloud Run - Serverless API"]
        PB["Prompt Engineering Engine"]
        GM["Gemini 2.5 Flash Lite<br/><i>Multimodal AI (text + vision)</i>"]
    end

    subgraph FALLBACK["Offline AI Fallback"]
        LLM["Local AI Model<br/><i>Ollama</i>"]
        TPL["Template Generator"]
    end

    subgraph OUTPUT["5 · Deliver"]
        DL["Clipboard · File · iTerm2 Paste<br/><i>+ Desktop Notification</i>"]
    end

    HK --> TM & SS & VR
    CLI --> TM & SS
    CLI -. "text input" .-> CB

    TM --> CB
    SS --> CB
    VR --> CB

    CB --> EC

    EC -- "Multimodal API Request" --> CR
    CR --> PB --> GM
    GM --> CR
    CR -- "AI-Enhanced Prompt" --> EC

    EC -. "Cloud Run unreachable" .-> LLM
    LLM -. "LLM unavailable" .-> TPL

    LLM -- "AI-Enhanced Prompt" --> EC
    TPL -- "Fallback Prompt" --> EC

    EC --> DL
```
---

## 2. End-to-End Pipeline Sequence

```mermaid
sequenceDiagram
    actor User
    participant HK as Hotkey Daemon
    participant SC as Vision Capture
    participant VC as Speech-to-Text
    participant TR as Whisper AI
    participant TM as Terminal State Monitor
    participant CB as Context Aggregator
    participant EC as AI Orchestrator
    participant CR as Cloud Run (Serverless API)
    participant GM as Gemini 2.5 Flash Lite (Multimodal AI)
    participant DL as Delivery Engine

    User->>HK: Ctrl+Alt+E

    par Concurrent capture
        HK->>TM: snapshot()
        Note over TM: tmux / iTerm2 / shell_hook / generic
        HK->>SC: capture_screenshot_b64()
        Note over SC: screencapture / grim / scrot
        HK->>VC: start_recording()
        Note over VC: sounddevice 16kHz mono
    end

    User->>VC: speaks "fix the error"
    VC-->>VC: VAD detects 1s silence
    VC->>TR: raw audio frames
    TR-->>VC: transcript: "fix the error"

    TM-->>CB: TerminalState
    SC-->>CB: screenshot_b64 (PNG)
    VC-->>CB: voice_transcript

    CB->>CB: detect_errors(screen_buffer)
    CB->>CB: detect_project(cwd)
    CB-->>EC: summary dict

    EC->>CR: Multimodal API Request (JSON)
    Note over EC,CR: voice_transcript, cwd, screen_buffer,<br/>detected_errors, screenshot_b64, ...

    CR->>CR: Prompt Engineering Engine
    Note over CR: Step 1: read screenshot<br/>Step 2: classify intent<br/>Step 3: write enhanced prompt

    CR->>GM: generate_content([text_part, image_part])
    GM-->>CR: enhanced prompt text

    CR-->>EC: AI-Enhanced Prompt

    alt Cloud Run unreachable
        EC->>EC: fall back to Local AI Model (Ollama)
        alt LLM unavailable
            EC->>EC: fall back to Template Generator
        end
    end

    EC-->>DL: enhanced_prompt
    DL->>User: clipboard (pbcopy / wl-copy)
    DL->>User: desktop notification
```

---

## 3. Terminal Backend Auto-Detection

```mermaid
flowchart TD
    START([Daemon Startup]) --> PROBE

    PROBE["detect_backend()<br/>probes in priority order"]

    PROBE --> T1{"$TMUX set<br/>and tmux binary exists?"}
    T1 -->|Yes| TMUX["TmuxBackend<br/>✓ screen buffer<br/>✓ CWD<br/>✓ commands<br/>✓ exit codes via hook"]
    T1 -->|No| T2

    T2{"macOS + iTerm2<br/>+ iterm2 pkg installed?"}
    T2 -->|Yes| ITERM["ITerm2Backend<br/>✓ screen buffer<br/>✓ CWD<br/>✓ commands<br/>✓ exit codes"]
    T2 -->|No| T3

    T3{"state-PID.json<br/>exists in STATE_DIR?"}
    T3 -->|Yes| HOOK["ShellHookBackend<br/>✗ screen buffer<br/>✓ CWD<br/>✓ commands<br/>✓ exit codes"]
    T3 -->|No| T4

    T4["GenericBackend<br/>✗ screen buffer<br/>✓ CWD (proc/lsof)<br/>✓ history<br/>✗ exit codes<br/>(always available)"]

    TMUX --> SNAP
    ITERM --> SNAP
    HOOK --> SNAP
    T4 --> SNAP

    SNAP["snapshot()<br/>→ frozen TerminalState"]
```

---

## 4. Multimodal Gemini Request Construction

```mermaid
flowchart LR
    subgraph INPUT["ContextPayload (summary dict)"]
        VT["voice_transcript<br/>'fix the error'"]
        SB["screen_buffer_last_50<br/>(last 50 lines)"]
        DE["detected_errors<br/>TS2345 src/auth.ts:42"]
        CWD["cwd · git_branch<br/>project_type"]
        SS["screenshot_b64<br/>PNG base64"]
    end

    subgraph BUILDER["Prompt Engineering Engine (Cloud Run)"]
        S1["STEP 1<br/>Read screenshot<br/>as ground truth"]
        S2["STEP 2<br/>Classify intent<br/>fix_error / explain /<br/>refactor / add_feature /<br/>write_test / debug"]
        S3["STEP 3<br/>Write enhanced prompt<br/>imperative sentence<br/>+ exact specifics"]
    end

    subgraph GENAI["Google GenAI SDK"]
        P1["Part.from_text<br/>(meta-prompt)"]
        P2["Part.from_bytes<br/>(PNG image)<br/>mime_type=image/png"]
        REQ["client.models<br/>.generate_content(<br/>  model,<br/>  contents=[P1, P2]<br/>)"]
    end

    subgraph OUTPUT["Response"]
        EP["AI-Enhanced Prompt<br/>(plain text string)"]
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
    BUF["screen_buffer<br/>(raw terminal text)"]

    BUF --> EDE["ErrorDetectionEngine<br/>.detect(screen_buffer)"]

    EDE --> R1["TypeScript<br/>TS\\d+ error"]
    EDE --> R2["Python Traceback<br/>Traceback (most recent call last)"]
    EDE --> R3["Rust compiler<br/>error\\[E\\d+\\]"]
    EDE --> R4["Go<br/>\\.go:\\d+:\\d+:"]
    EDE --> R5["Node.js<br/>(TypeError|ReferenceError)"]
    EDE --> R6["Jest / pytest<br/>FAILED | FAILED test"]
    EDE --> R7["ESLint<br/>Error: .* rule"]
    EDE --> R8["Git conflict<br/><<<<<<< HEAD"]
    EDE --> R9["Permission<br/>(EACCES|Permission denied)"]
    EDE --> R10["Segfault<br/>Segmentation fault"]
    EDE --> R11["cargo test<br/>test .* FAILED"]
    EDE --> R12["HTTP / network<br/>(404|500|ECONNREFUSED)"]

    R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 & R11 & R12 --> OUT

    OUT["DetectedError[]<br/>{error_type, code, file, line, column, message, severity}"]
    OUT --> CB["Context Aggregator<br/>→ ContextPayload.detected_errors"]
```

---

## 6. Graceful Degradation Chain

```mermaid
flowchart TD
    START["AI Orchestrator<br/>enhance_with_fallback()"] --> HAS_URL

    HAS_URL{"provider == gemini<br/>and cloud_run_url set?"}
    HAS_URL -->|Yes| CR["Multimodal API Request<br/>to Cloud Run"]
    HAS_URL -->|No| LOCAL

    CR --> CROK{"Cloud Run<br/>responded 2xx?"}
    CROK -->|Yes| OK["✅ Gemini AI-Enhanced Prompt<br/>(multimodal, structured)"]
    CROK -->|No| LOCAL["Local AI Model<br/>Ollama via litellm"]

    LOCAL --> LLMOK{"LLM responded<br/>after retries?"}
    LLMOK -->|Yes| OK2["✅ Local AI-Enhanced Prompt"]
    LLMOK -->|No| TPL

    TPL["📄 Template Generator<br/>build_fallback_prompt(summary)<br/>always succeeds"]
    TPL --> OK3["✅ Fallback Prompt"]

    OK --> EC["AI Orchestrator<br/>returns EnhanceResult"]
    OK2 --> EC
    OK3 --> EC

    EC --> DEL["Delivery Engine<br/>→ Clipboard + Notification"]
```

---

## 7. CI/CD and Deployment Pipeline

```mermaid
flowchart LR
    subgraph DEV["Developer"]
        TAG["git tag v0.x.x<br/>git push origin v0.x.x"]
    end

    subgraph GHA["GitHub Actions (release.yml)"]
        direction TB
        V["validate<br/>ruff lint + format check"]
        T["test<br/>pytest"]
        B["build<br/>uv build wheel + sdist"]
        PP["publish-pypi<br/>twine upload"]
        DCR["deploy-cloud-run<br/>gcloud builds submit<br/>gcloud run deploy<br/>image tag: v0.x.x"]
        GR["github-release<br/>gh release create"]
        DK["docker<br/>build + push image"]
    end

    subgraph GCP2["Google Cloud"]
        CB2["Cloud Build<br/>build container"]
        AR2["Artifact Registry<br/>gcr.io/.../prompt-shell-enhancer:v0.x.x"]
        CR2["Cloud Run<br/>prompt-shell-enhancer"]
        HC["Health check<br/>GET /health → 200"]
    end

    subgraph MANUAL["Manual Re-deploy<br/>(deploy-cloud-run.yml)"]
        WD["workflow_dispatch<br/>(secret rotation / hotfix)"]
    end

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
        +str screen_buffer
        +str cwd
        +str shell
        +CommandRecord[] last_commands
        +str|None running_process
        +str|None git_branch
        +str|None hostname
        +str|None username
        +str|None session_id
        +str backend
        +str captured_at
    }

    class CommandRecord {
        +str command
        +int|None exit_code
        +str|None working_directory
        +str|None timestamp
    }

    class DetectedError {
        +str error_type
        +str|None code
        +str|None file
        +int|None line
        +int|None column
        +str message
        +str severity
    }

    class ProjectInfo {
        +str|None project_type
        +str|None project_name
        +str|None config_file
    }

    class EnhanceRequest {
        +str voice_transcript
        +str cwd
        +str shell
        +str|None git_branch
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
    subgraph LOCAL2["Local Client — src/prompt_shell/"]
        M["main.py<br/>CLI + hotkey daemon<br/>AI pipeline orchestrator"]

        subgraph T["terminal/ — Multimodal Context Agent"]
            MON["monitor.py<br/>Terminal State Monitor<br/>+ 4 backend implementations"]
            CTX["context.py<br/>Context Aggregator<br/>+ ProjectInfo detection"]
            ERR["error_patterns.py<br/>Error Detection Engine<br/>12+ regex families"]
            SSHOT["screenshot.py<br/>Vision Capture<br/>cross-platform PNG"]
        end

        subgraph VO["voice/ — Speech-to-Text"]
            CAP["capture.py<br/>sounddevice recording<br/>energy-based VAD"]
            TRN["transcribe.py<br/>Whisper AI (local)<br/>OpenAI API · Apple Speech"]
        end

        subgraph EN["enhancer/ — AI Enhancement"]
            ECLI["enhancement_client.py<br/>AI Orchestrator<br/>+ fallback routing"]
            PBL["prompt_builder.py<br/>Template Generator<br/>(offline fallback)"]
            LC2["llm_client.py<br/>Local AI Model<br/>Ollama · retries"]
        end

        subgraph DV["delivery/"]
            CLP["clipboard.py<br/>pbcopy · wl-copy · xclip"]
            ITP["iterm_paste.py<br/>iTerm2 direct paste"]
            FIL["file.py<br/>file delivery"]
            NOT["notification.py<br/>osascript · notify-send"]
        end

        CFG["config.py<br/>Pydantic models<br/>YAML + env var substitution"]
    end

    subgraph CRS["☁️ Google Cloud AI Platform — cloud_run_service/"]
        CRMAIN["main.py<br/>Cloud Run — Serverless API<br/>POST /enhance · GET /health"]
        CRPB["prompt_builder.py<br/>Prompt Engineering Engine"]
        CRGC["gemini_client.py<br/>Gemini 2.5 Flash Lite<br/>Multimodal AI"]
    end

    M --> T & VO & EN & DV & CFG
    CRMAIN --> CRPB --> CRGC
```
