"""Meta-prompt template engine — constructs the LLM prompt from context."""

from __future__ import annotations

_PREAMBLE = """\
You are preparing a prompt that will be pasted directly into an AI coding assistant \
(GitHub Copilot, Cursor, Claude Code, or similar). Your output IS the prompt — make \
it precise, actionable, and self-contained.

STEP 1 — READ THE SCREENSHOT (if a terminal screenshot is attached)
Extract all visible information before reading the text context:
- Read every error message, stack trace, and warning exactly as written — do not paraphrase
- Note the file path and line number referenced in error output or editor tabs
- Note any highlighted text, dialog boxes, or the active cursor position
- The screenshot is ground truth — if it conflicts with the text context, trust the screenshot

STEP 2 — CLASSIFY INTENT
Identify the primary intent from the voice command and context:
  fix_error    — user wants a specific error or bug resolved
  explain      — user wants code or output explained
  refactor     — user wants code restructured without changing behavior
  add_feature  — user wants new functionality added
  write_test   — user wants tests written
  debug        — user wants help diagnosing a problem with no clear error yet

If the voice command is vague ("fix it", "help", "what's wrong", "look at this"), \
infer the most likely intent from the terminal context (error output, last command exit \
code, screen content). Do NOT include the classification in the output — use it only to \
guide the structure and tone of the enhanced prompt.

STEP 3 — WRITE THE ENHANCED PROMPT
Use this structure:
  Line 1:  One imperative sentence stating the exact task. Start with a verb.
  Line 2:  (blank)
  Lines 3+: Diagnostic context that helps the AI assistant solve the problem:
           - Exact error message with file path and line number (quote verbatim)
           - The command that failed and its exit code
           - Your analysis: what likely caused the error and where to look
           - Relevant files, functions, or variables involved
           - Working directory and project type when relevant to the fix
           - Git branch only if the task is branch-specific

Rules:
- Write in second person: "Fix...", "Explain...", "Add...", "Refactor..."
- Quote error messages verbatim — never rephrase or summarise them
- Add your diagnosis: identify the root cause, relevant code paths, and likely fix
- The output must be MORE useful than the raw error — if you would just copy the error, \
you are not adding value. Synthesize the error with the project context to guide the fix.
- Do not add tasks the user did not request

Context priority — higher sources override lower when they conflict:
  1. Terminal screenshot  — visual ground truth, what the user sees right now
  2. Terminal output buffer  — raw text of recent terminal output
  3. Regex-detected errors   — structured extraction (may miss some errors)
  4. Working directory / project / branch — background context only

---

RAW VOICE COMMAND:
{voice_transcript}

---

TERMINAL CONTEXT:"""

_FOOTER = (
    "\n---\n\n"
    "OUTPUT: Write ONLY the enhanced prompt. "
    "No explanation, no preamble, no meta-commentary."
)


def build_meta_prompt(summary: dict) -> str:
    """Render the meta-prompt, including only context sections that have signal."""
    sections: list[str] = [_PREAMBLE.format(voice_transcript=summary.get("voice_transcript", ""))]

    cwd = summary.get("cwd", "")
    project_type = summary.get("project_type", "unknown")
    project_name = summary.get("project_name", "unknown")
    git_branch = summary.get("git_branch", "unknown")
    shell = summary.get("shell", "")
    running_process = summary.get("running_process", "")

    if cwd:
        sections.append(f"- Working directory: {cwd}")
    if project_type != "unknown":
        sections.append(f"- Project type: {project_type} ({project_name})")
    if git_branch not in ("", "unknown"):
        sections.append(f"- Git branch: {git_branch}")
    if shell:
        sections.append(f"- Shell: {shell}")
    if running_process:
        sections.append(f"- Running process: {running_process}")

    last_commands = summary.get("last_commands", "none")
    if last_commands and last_commands != "none":
        sections.append(f"\nRecent commands:\n{last_commands}")

    detected_errors = summary.get("detected_errors", "none detected")
    if detected_errors and detected_errors != "none detected":
        sections.append(f"\nDetected errors:\n{detected_errors}")

    screen_buffer = summary.get("screen_buffer_last_50", "").strip()
    if screen_buffer:
        sections.append(f"\nTerminal output (last 50 lines):\n```\n{screen_buffer}\n```")

    # When screen buffer is empty but a screenshot exists, the model must extract
    # all terminal content from the image.  Give it a strong directive.
    if summary.get("screenshot_b64"):
        if not screen_buffer:
            sections.append(
                "\nIMPORTANT: No terminal text buffer was captured. The screenshot is "
                "your ONLY source of terminal content. You MUST:\n"
                "1. Read every line of terminal output visible in the screenshot\n"
                "2. Transcribe all error messages, stack traces, and command output verbatim\n"
                '3. Use the transcribed text as if it were the "Terminal output" section\n'
                "Do not produce a vague or generic prompt — extract the specifics from "
                "the screenshot."
            )
        sections.append("\n[Terminal screenshot attached — apply Step 1 analysis above]")

    sections.append(_FOOTER)
    return "\n".join(sections)


def build_context_only_prompt(summary: dict) -> str:
    """Build a prompt when there's no voice input — enhance clipboard text."""
    merged = {
        **summary,
        "voice_transcript": summary.get("voice_transcript", "(from clipboard)"),
    }
    return build_meta_prompt(merged)


# Simplified fallback template for when LLM is unavailable
FALLBACK_TEMPLATE = """\
{voice_transcript}

Context:
- CWD: {cwd}
- Branch: {git_branch}
- Last commands: {last_commands}
- Errors: {detected_errors}"""


def build_fallback_prompt(summary: dict) -> str:
    """Build a template-based enhanced prompt without LLM (fallback)."""
    return FALLBACK_TEMPLATE.format(**summary).strip()
