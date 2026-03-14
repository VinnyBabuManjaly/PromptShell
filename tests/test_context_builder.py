"""Tests for the context builder."""

from prompt_shell.terminal.context import ContextBuilder
from prompt_shell.terminal.monitor import CommandRecord, TerminalState


def test_build_context_with_errors():
    state = TerminalState(
        screen_buffer="src/app.ts(10,1): error TS1005: ';' expected.\nnpm ERR! code 1",
        cwd="/tmp/test-project",
        shell="/bin/zsh",
        last_commands=[CommandRecord(command="npm run build", exit_code=1)],
    )
    builder = ContextBuilder()
    ctx = builder.build(state, voice_transcript="fix the build error")
    assert ctx.voice_transcript == "fix the build error"
    assert len(ctx.detected_errors) >= 1
    assert ctx.detected_errors[0].code == "TS1005"


def test_build_summary():
    state = TerminalState(
        screen_buffer="all tests passed",
        cwd="/home/user/project",
        shell="/bin/zsh",
        last_commands=[CommandRecord(command="pytest", exit_code=0)],
        git_branch="main",
    )
    builder = ContextBuilder()
    ctx = builder.build(state, voice_transcript="run the linter")
    summary = builder.build_summary(ctx)
    assert summary["voice_transcript"] == "run the linter"
    assert summary["cwd"] == "/home/user/project"
    assert summary["git_branch"] == "main"
    assert "$ pytest (exit 0)" in summary["last_commands"]
    assert summary["detected_errors"] == "none detected"


def test_empty_context():
    builder = ContextBuilder()
    ctx = builder.build(TerminalState())
    summary = builder.build_summary(ctx)
    assert summary["cwd"] == ""
    assert summary["detected_errors"] == "none detected"


def test_build_includes_screenshot_b64_when_provided():
    builder = ContextBuilder()
    ctx = builder.build(TerminalState(), screenshot_b64="abc123")
    assert ctx.screenshot_b64 == "abc123"


def test_build_screenshot_b64_defaults_to_none():
    builder = ContextBuilder()
    ctx = builder.build(TerminalState())
    assert ctx.screenshot_b64 is None


def test_build_summary_includes_screenshot_b64():
    builder = ContextBuilder()
    ctx = builder.build(TerminalState(), screenshot_b64="abc123")
    summary = builder.build_summary(ctx)
    assert summary["screenshot_b64"] == "abc123"


def test_build_summary_screenshot_b64_is_none_when_absent():
    builder = ContextBuilder()
    ctx = builder.build(TerminalState())
    summary = builder.build_summary(ctx)
    assert summary["screenshot_b64"] is None
