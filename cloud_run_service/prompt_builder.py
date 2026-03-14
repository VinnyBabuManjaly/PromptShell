"""Meta-prompt template engine for the Cloud Run enhancement service."""

from __future__ import annotations

_PREAMBLE = """\
You are a prompt engineer specializing in developer productivity. Given a user's raw \
voice command and their terminal context, rewrite the command into a precise, actionable \
prompt suitable for an AI coding assistant.

Rules:
1. Include specific file paths, error codes, and line numbers from the terminal context
2. Reference the exact error messages visible in the terminal output
3. Mention the current working directory and project type when relevant
4. Keep the enhanced prompt concise but complete (max ~200 words)
5. Preserve the user's original intent — do NOT add new tasks they didn't request
6. If the terminal shows a specific technology stack, mention it
7. Write in second person ("Fix the..." not "The user wants...")
8. If a terminal screenshot is attached, use it to confirm visible error messages and identify any UI details the text context may have missed

---

RAW VOICE COMMAND:
{voice_transcript}

---

TERMINAL CONTEXT:"""

_FOOTER = "\n---\n\nOUTPUT: Write ONLY the enhanced prompt. No explanation, no preamble."


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

    sections.append(_FOOTER)
    return "\n".join(sections)
