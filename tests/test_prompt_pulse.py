"""Tests for the prompt builder templates."""

from prompt_shell.enhancer.prompt_builder import (
    build_fallback_prompt,
    build_meta_prompt,
)


def _make_summary(**overrides):
    """Helper to build a summary dict."""
    defaults = {
        "voice_transcript": "fix the error",
        "cwd": "/home/user/project",
        "shell": "/bin/zsh",
        "git_branch": "main",
        "running_process": None,
        "last_commands": "$ npm run build (exit 1)",
        "detected_errors": "typescript_compilation TS2345 at src/app.ts:10 — type mismatch",
        "screen_buffer_last_50": "error TS2345: type mismatch",
        "project_type": "typescript",
        "project_name": "my-project",
    }
    defaults.update(overrides)
    return defaults


def test_meta_prompt_contains_voice_transcript():
    summary = _make_summary()
    prompt = build_meta_prompt(summary)
    assert "fix the error" in prompt
    assert "TS2345" in prompt
    assert "/home/user/project" in prompt


def test_meta_prompt_contains_context():
    summary = _make_summary(
        cwd="/app/backend",
        git_branch="feature/auth",
        project_type="python",
    )
    prompt = build_meta_prompt(summary)
    assert "/app/backend" in prompt
    assert "feature/auth" in prompt
    assert "python" in prompt


def test_fallback_prompt():
    summary = _make_summary()
    fallback = build_fallback_prompt(summary)
    assert "fix the error" in fallback
    assert "/home/user/project" in fallback
    assert "TS2345" in fallback


def test_fallback_prompt_no_errors():
    summary = _make_summary(detected_errors="none detected")
    fallback = build_fallback_prompt(summary)
    assert "none detected" in fallback


def test_meta_prompt_screenshot_only_includes_strong_directive():
    """When screen_buffer is empty but screenshot exists, use strong OCR directive."""
    summary = _make_summary(screen_buffer_last_50="", screenshot_b64="abc123")
    prompt = build_meta_prompt(summary)
    assert "No terminal text buffer was captured" in prompt
    assert "ONLY source of terminal content" in prompt
    assert "Transcribe all error messages" in prompt


def test_meta_prompt_screenshot_with_buffer_uses_simple_hint():
    """When both screen_buffer and screenshot exist, use the simple hint."""
    summary = _make_summary(
        screen_buffer_last_50="error TS2345: type mismatch",
        screenshot_b64="abc123",
    )
    prompt = build_meta_prompt(summary)
    assert "Terminal screenshot attached" in prompt
    assert "No terminal text buffer was captured" not in prompt


def test_meta_prompt_no_screenshot_no_buffer():
    """When neither screenshot nor buffer exists, no screenshot directive appears."""
    summary = _make_summary(screen_buffer_last_50="", screenshot_b64=None)
    prompt = build_meta_prompt(summary)
    assert "No terminal text buffer was captured" not in prompt
    assert "Terminal screenshot attached" not in prompt
