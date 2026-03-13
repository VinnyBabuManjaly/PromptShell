"""Meta-prompt template engine — constructs the LLM prompt from context."""

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

---

RAW VOICE COMMAND:
{voice_transcript}

---

TERMINAL CONTEXT:"""

_FOOTER = "\n---\n\nOUTPUT: Write ONLY the enhanced prompt. No explanation, no preamble."


def build_meta_prompt(summary: dict) -> str:
    """Render the meta-prompt, including only context sections that have signal."""
    sections: list[str] = [_PREAMBLE.format(voice_transcript=summary.get("voice_transcript", ""))]

    cwd = summary.get("cwd", "")
    project_type = summary.get("project_type", "unknown")
    project_name = summary.get("project_name", "unknown")
    git_branch = summary.get("git_branch", "unknown")
    shell = summary.get("shell", "")
    running_process = summary.get("running_process", "")

    # Core location — always include if we have cwd
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

    # Recent commands — only if non-trivial
    last_commands = summary.get("last_commands", "none")
    if last_commands and last_commands != "none":
        sections.append(f"\nRecent commands:\n{last_commands}")

    # Errors — only if detected
    detected_errors = summary.get("detected_errors", "none detected")
    if detected_errors and detected_errors != "none detected":
        sections.append(f"\nDetected errors:\n{detected_errors}")

    # Screen buffer — only if it contains content beyond whitespace
    screen_buffer = summary.get("screen_buffer_last_50", "").strip()
    if screen_buffer:
        sections.append(f"\nTerminal output (last 50 lines):\n```\n{screen_buffer}\n```")

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
