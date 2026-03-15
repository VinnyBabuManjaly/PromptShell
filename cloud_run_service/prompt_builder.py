"""Meta-prompt template engine for the Cloud Run enhancement service."""

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
code, screen content) and prepend [Inferred: <intent in one phrase>] to your output.

STEP 3 — WRITE THE ENHANCED PROMPT
Use this structure:
  Line 1:  One imperative sentence stating the exact task. Start with a verb.
  Line 2:  (blank)
  Line 3+: Only the specifics needed to act on the task:
           - Exact error message with file path and line number
           - The command that failed and its exit code if non-zero
           - Working directory and project type when relevant to the fix
           - Git branch only if the task is branch-specific

Rules:
- Write in second person: "Fix...", "Explain...", "Add...", "Refactor..."
- Copy error text verbatim — never rephrase or summarise error messages
- Omit any context that is not directly relevant to the task on line 1
- Do not add tasks the user did not request
- Be as concise as possible while preserving every specific needed to act on the task

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

_FOOTER = "\n---\n\nOUTPUT: Write ONLY the enhanced prompt. No explanation, no preamble, no meta-commentary."


def build_meta_prompt(request_data: dict) -> str:
    """Render the meta-prompt, including only context sections that have signal."""
    voice_transcript = request_data.get("voice_transcript", "")
    sections: list[str] = [_PREAMBLE.format(voice_transcript=voice_transcript)]

    cwd = request_data.get("cwd", "")
    project_type = request_data.get("project_type", "unknown")
    project_name = request_data.get("project_name", "unknown")
    git_branch = request_data.get("git_branch") or "unknown"
    shell = request_data.get("shell", "")

    if cwd:
        sections.append(f"- Working directory: {cwd}")
    if project_type != "unknown":
        sections.append(f"- Project type: {project_type} ({project_name})")
    if git_branch not in ("", "unknown"):
        sections.append(f"- Git branch: {git_branch}")
    if shell:
        sections.append(f"- Shell: {shell}")

    last_commands = request_data.get("last_commands", "none")
    if last_commands and last_commands not in ("none", ""):
        sections.append(f"\nRecent commands:\n{last_commands}")

    detected_errors = request_data.get("detected_errors", "none detected")
    if detected_errors and detected_errors not in ("none detected", ""):
        sections.append(f"\nDetected errors:\n{detected_errors}")

    screen_buffer = request_data.get("screen_buffer_last_50", "").strip()
    if screen_buffer:
        sections.append(f"\nTerminal output (last 50 lines):\n```\n{screen_buffer}\n```")

    # Tell Gemini explicitly that a screenshot is attached so it applies Step 1.
    if request_data.get("screenshot_b64"):
        sections.append("\n[Terminal screenshot attached — apply Step 1 analysis above]")

    sections.append(_FOOTER)
    return "\n".join(sections)
