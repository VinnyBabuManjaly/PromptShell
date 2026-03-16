"""Main entry point — CLI, hotkey system, and pipeline orchestrator."""

from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import logging
from dataclasses import replace
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from prompt_shell.config import AppConfig, init_config_dir, load_config

app = typer.Typer(
    name="prompt-shell",
    help="Voice-activated terminal-aware prompt enhancer for AI coding assistants.",
    no_args_is_help=True,
)
console = Console()

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


async def run_pipeline(
    config: AppConfig,
    voice: bool = True,
    clipboard_input: bool = False,
    transcript: str | None = None,
) -> str | None:
    """Execute the full enhancement pipeline.

    1. Capture terminal context (auto-detects backend)
    2. Capture voice input (or read clipboard)
    3. Build context payload
    4. Enhance prompt via LLM
    5. Deliver result
    """
    from prompt_shell.delivery.clipboard import deliver_to_clipboard, read_from_clipboard
    from prompt_shell.delivery.notification import (
        notify_enhanced_prompt,
        notify_error,
        notify_listening,
    )
    from prompt_shell.enhancer.enhancement_client import enhance_with_fallback
    from prompt_shell.enhancer.prompt_builder import build_fallback_prompt
    from prompt_shell.terminal.context import ContextBuilder
    from prompt_shell.terminal.monitor import TerminalState, create_backend
    from prompt_shell.voice.capture import VoiceCapture
    from prompt_shell.voice.transcribe import create_engine

    logger = logging.getLogger(__name__)

    # --- Step 1: Terminal context + screenshot (concurrent) ---
    terminal_state = TerminalState()
    try:
        backend = create_backend(
            backend_type=config.terminal.backend,
            screen_buffer_lines=config.terminal.screen_buffer_lines,
        )
        console.print(f"[dim]Terminal backend: {backend.name}[/]")
        terminal_state = await backend.snapshot()
    except Exception as e:
        logger.warning("Terminal context capture failed: %s (continuing without it)", e)

    # Launch screenshot capture concurrently — it completes while voice is recording.
    screenshot_task: asyncio.Task[str | None] | None = None
    if config.terminal.capture_screenshot:
        from prompt_shell.terminal.screenshot import capture_screenshot_b64

        screenshot_task = asyncio.create_task(capture_screenshot_b64())

    # --- Step 2: Voice / clipboard input ---
    # When transcript is pre-supplied (e.g., direct text from CLI), skip capture.
    if transcript is None:
        transcript = ""
    if transcript:
        pass  # already have input
    elif voice:
        await notify_listening()
        capture = VoiceCapture(
            silence_threshold_sec=config.voice.silence_threshold_sec,
            max_duration_sec=config.voice.max_duration_sec,
            vad_aggressiveness=config.voice.vad_aggressiveness,
        )
        console.print("[bold cyan]Listening...[/] Speak now (press Ctrl+C to cancel)")
        wav_bytes = await capture.capture()

        if wav_bytes:
            console.print("[dim]Transcribing...[/]")
            engine = create_engine(
                engine_type=config.voice.engine,
                model_size=config.voice.whisper_model,
                api_key=config.llm.resolve_api_key(),
            )
            result = await engine.transcribe(wav_bytes)
            transcript = result.text
            console.print(f"[green]Heard:[/] {transcript}")
        else:
            console.print("[yellow]No speech detected.[/]")
            await notify_error("No speech detected")
            return None
    elif clipboard_input:
        transcript = await read_from_clipboard()
        if not transcript.strip():
            console.print("[yellow]Clipboard is empty.[/]")
            return None
        console.print(f"[green]Clipboard:[/] {transcript[:80]}...")

    # --- Step 3: Build context ---
    screenshot_b64: str | None = None
    if screenshot_task is not None:
        try:
            screenshot_b64 = await screenshot_task
            if screenshot_b64:
                logger.debug("Screenshot captured (%d b64 chars)", len(screenshot_b64))
        except Exception as e:
            logger.warning("Screenshot capture failed: %s (continuing without it)", e)

    # When the backend didn't capture a screen buffer (shell_hook, generic), try
    # OCR on the screenshot to populate it.  This enables error detection and gives
    # the LLM structured text alongside the image.
    if screenshot_b64 and not terminal_state.screen_buffer:
        logger.info(
            "Backend '%s' captured no screen_buffer — attempting OCR fallback",
            terminal_state.backend,
        )
        from prompt_shell.terminal.ocr import ocr_screenshot

        try:
            ocr_text = await ocr_screenshot(base64.b64decode(screenshot_b64))
            if ocr_text:
                terminal_state = replace(terminal_state, screen_buffer=ocr_text)
                logger.info("Screen buffer populated from OCR (%d chars)", len(ocr_text))
            else:
                logger.info("OCR returned no text")
        except Exception as e:
            logger.warning("OCR fallback failed: %s", e)

    builder = ContextBuilder()
    context = builder.build(
        terminal_state, voice_transcript=transcript, screenshot_b64=screenshot_b64
    )
    summary = builder.build_summary(context)

    # --- Step 4: Enhance via LLM ---
    console.print("[dim]Enhancing prompt...[/]")
    fallback = build_fallback_prompt(summary)

    used_fallback = False
    try:
        result = await enhance_with_fallback(summary, config.llm, fallback_text=fallback)
        enhanced = result.text
        used_fallback = result.used_fallback
        if used_fallback:
            console.print(f"[yellow]LLM unavailable ({result.error}), using template fallback.[/]")
    except Exception:
        logger.warning("LLM unavailable, using template fallback")
        enhanced = fallback
        used_fallback = True

    # --- Step 5: Deliver ---
    console.print(Panel(enhanced, title="Enhanced Prompt", border_style="green"))

    if config.delivery.method == "clipboard":
        await deliver_to_clipboard(enhanced)
    elif config.delivery.method == "file":
        from prompt_shell.delivery.file import deliver_to_file

        await deliver_to_file(enhanced, config.delivery.output_file)

    if config.delivery.show_notification:
        await notify_enhanced_prompt(
            enhanced,
            preview_chars=config.delivery.notification_preview_chars,
            used_fallback=used_fallback,
        )

    return enhanced


# ---------------------------------------------------------------------------
# Hotkey Daemon
# ---------------------------------------------------------------------------


async def run_hotkey_daemon(config: AppConfig) -> None:
    """Start the global hotkey listener daemon."""
    from pynput import keyboard

    logger = logging.getLogger(__name__)
    console.print("[bold green]PromptShell started[/]")
    console.print(f"  Backend:      {config.terminal.backend}")
    console.print(f"  Activate:     {config.hotkeys.activate}")
    console.print(f"  Context only: {config.hotkeys.context_only}")
    console.print(f"  Re-enhance:   {config.hotkeys.re_enhance}")
    console.print(f"  Cancel:       {config.hotkeys.cancel}")
    console.print()
    console.print("[dim]Press Ctrl+C to stop.[/]")

    loop = asyncio.get_running_loop()
    pipeline_future: concurrent.futures.Future | None = None
    # Mutable reference so the hotkey thread can cancel the running asyncio task.
    _active_task: list[asyncio.Task | None] = [None]

    def _parse_hotkey(hotkey_str: str):
        """Parse a hotkey string like 'ctrl+shift+p' into pynput format."""
        parts = hotkey_str.lower().split("+")
        combo = set()
        for part in parts:
            part = part.strip()
            if part in ("ctrl", "control"):
                combo.add(keyboard.Key.ctrl)
            elif part in ("shift",):
                combo.add(keyboard.Key.shift)
            elif part in ("alt", "option"):
                combo.add(keyboard.Key.alt)
            elif part in ("cmd", "command", "super"):
                combo.add(keyboard.Key.cmd)
            elif part == "escape":
                combo.add(keyboard.Key.esc)
            elif len(part) == 1:
                combo.add(keyboard.KeyCode.from_char(part))
            else:
                logger.warning("Unknown key in hotkey: %s", part)
        return frozenset(combo)

    activate_combo = _parse_hotkey(config.hotkeys.activate)
    context_combo = _parse_hotkey(config.hotkeys.context_only)
    re_enhance_combo = _parse_hotkey(config.hotkeys.re_enhance)
    cancel_combo = _parse_hotkey(config.hotkeys.cancel)

    current_keys: set = set()

    async def _run_tracked(coro):
        """Run a pipeline coroutine and register the task for cancellation."""
        task = asyncio.current_task()
        _active_task[0] = task
        try:
            return await coro
        finally:
            _active_task[0] = None

    def on_press(key):
        nonlocal pipeline_future
        prev_pressed = frozenset(current_keys)
        current_keys.add(key)
        pressed = frozenset(current_keys)

        if _combo_just_completed(activate_combo, prev_pressed, pressed):
            logger.info("Hotkey: activate")
            if pipeline_future is None or pipeline_future.done():
                pipeline_future = asyncio.run_coroutine_threadsafe(
                    _run_tracked(run_pipeline(config, voice=True)), loop
                )

        elif _combo_just_completed(context_combo, prev_pressed, pressed):
            logger.info("Hotkey: context_only")
            if pipeline_future is None or pipeline_future.done():
                pipeline_future = asyncio.run_coroutine_threadsafe(
                    _run_tracked(run_pipeline(config, voice=False, clipboard_input=True)), loop
                )

        elif _combo_just_completed(re_enhance_combo, prev_pressed, pressed):
            logger.info("Hotkey: re_enhance")
            if pipeline_future is None or pipeline_future.done():
                pipeline_future = asyncio.run_coroutine_threadsafe(
                    _run_tracked(run_pipeline(config, voice=False, clipboard_input=True)), loop
                )

        elif _combo_just_completed(cancel_combo, prev_pressed, pressed):
            logger.info("Hotkey: cancel")
            task = _active_task[0]
            if task and not task.done():
                loop.call_soon_threadsafe(task.cancel)

    def on_release(key):
        current_keys.discard(key)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        listener.stop()


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


@app.command()
def start(
    config_file: Path | None = typer.Option(None, "--config", "-c", help="Path to config.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
):
    """Start the PromptShell daemon with global hotkeys."""
    _setup_logging(verbose)
    config = load_config(config_file)
    try:
        asyncio.run(run_hotkey_daemon(config))
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/]")


@app.command()
def enhance(
    text: str | None = typer.Argument(None, help="Text to enhance (or omit for voice)"),
    config_file: Path | None = typer.Option(None, "--config", "-c"),
    voice: bool = typer.Option(False, "--voice", help="Use voice input"),
    clipboard: bool = typer.Option(False, "--clipboard", help="Enhance clipboard contents"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Run a single enhancement (no daemon)."""
    _setup_logging(verbose)
    config = load_config(config_file)

    if text:
        asyncio.run(run_pipeline(config, voice=False, transcript=text))
    elif voice:
        asyncio.run(run_pipeline(config, voice=True))
    elif clipboard:
        asyncio.run(run_pipeline(config, voice=False, clipboard_input=True))
    else:
        console.print("[yellow]Provide text, --voice, or --clipboard[/]")
        raise typer.Exit(1)


@app.command()
def context(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of screen buffer lines"),
    backend: str = typer.Option("auto", "--backend", "-b", help="Terminal backend"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Capture and display current terminal context (no enhancement)."""
    _setup_logging(verbose)

    async def _run():
        from prompt_shell.terminal.context import ContextBuilder
        from prompt_shell.terminal.monitor import create_backend

        try:
            be = create_backend(backend_type=backend, screen_buffer_lines=lines)
            console.print(f"[dim]Using backend: {be.name}[/]")
            state = await be.snapshot()
        except Exception as e:
            console.print(f"[red]Failed to capture terminal context:[/] {e}")
            raise typer.Exit(1)

        builder = ContextBuilder()
        ctx = builder.build(state)
        summary = builder.build_summary(ctx)

        console.print(
            Panel(
                "\n".join(
                    f"[cyan]{k}:[/] {v}" for k, v in summary.items() if k != "screen_buffer_last_50"
                ),
                title=f"Terminal Context (backend: {be.name})",
                border_style="blue",
            )
        )
        if state.screen_buffer:
            console.print(
                Panel(
                    state.screen_buffer[-2000:],
                    title="Screen Buffer (last lines)",
                    border_style="dim",
                )
            )
        if summary.get("detected_errors") != "none detected":
            console.print(
                Panel(
                    summary["detected_errors"],
                    title="Detected Errors",
                    border_style="red",
                )
            )

    asyncio.run(_run())


@app.command()
def install_hook(
    shell: str = typer.Option(
        "",
        "--shell",
        help="Shell type (zsh/bash/fish). Auto-detects if empty.",
    ),
):
    """Install the shell hook for terminal state capture.

    This adds a lightweight precmd/preexec hook to your shell that writes
    CWD, last command, and exit code to a state file. Works with any terminal.
    """
    from prompt_shell.terminal.monitor import ShellHookBackend

    hook_file = ShellHookBackend.install_hook(shell)
    console.print(f"[green]Shell hook installed:[/] {hook_file}")
    console.print("[dim]Restart your shell or run:[/]")
    console.print(f"  source {hook_file}")


@app.command()
def install_service(
    enable: bool = typer.Option(True, "--enable/--no-enable", help="Enable and start the service."),
):
    """Install PromptShell as a systemd user service.

    Creates ~/.config/systemd/user/prompt-shell.service and optionally
    enables + starts it so it runs automatically on login.

    API keys and environment variables are read from ~/.prompt-shell/env
    (create this file if it doesn't exist).
    """
    import shutil
    import subprocess

    binary = shutil.which("prompt-shell")
    if not binary:
        console.print(
            "[red]prompt-shell binary not found in PATH.[/] "
            "Install with: uv tool install prompt-shell"
        )
        raise typer.Exit(1)

    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = service_dir / "prompt-shell.service"

    env_file = Path.home() / ".prompt-shell" / "env"
    if not env_file.exists():
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_file.write_text(
            "# PromptShell environment variables\n"
            "# Add your API keys here — one per line, KEY=value format.\n"
            "# Example:\n"
            "# GEMINI_API_KEY=your_key_here\n"
        )
        console.print(f"[green]Created env file:[/] {env_file}")
        console.print("[yellow]Add your GEMINI_API_KEY to that file before starting.[/]")

    unit = f"""\
[Unit]
Description=PromptShell — voice-activated terminal prompt enhancer
Documentation=https://github.com/VinnyBabuManjaly/PromptShell
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart={binary} start
Restart=on-failure
RestartSec=5s
EnvironmentFile=-{env_file}

[Install]
WantedBy=graphical-session.target
"""

    service_file.write_text(unit)
    console.print(f"[green]Service file written:[/] {service_file}")

    if enable:
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "prompt-shell"], check=True)
            console.print("[green]Service enabled and started.[/]")
            console.print("[dim]Check status with:[/] systemctl --user status prompt-shell")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]systemctl failed:[/] {e}")
            console.print("[dim]Start manually with:[/] systemctl --user start prompt-shell")
    else:
        console.print("[dim]Enable manually with:[/]")
        console.print("  systemctl --user daemon-reload")
        console.print("  systemctl --user enable --now prompt-shell")


@app.command()
def init():
    """Initialize configuration directory (~/.prompt-shell/)."""
    config_dir = init_config_dir()
    console.print(f"[green]Config directory initialized:[/] {config_dir}")
    console.print(f"[dim]Edit config at:[/] {config_dir / 'config.yaml'}")
    console.print()
    console.print("[dim]Recommended next step — install the shell hook:[/]")
    console.print("  prompt-shell install-hook")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _combo_just_completed(
    combo: frozenset,
    prev_pressed: frozenset,
    current_pressed: frozenset,
) -> bool:
    """Return True only when *combo* is satisfied for the first time with this key press.

    This implements leading-edge detection: the combo fires exactly once when
    the last required key is pressed, not on auto-repeat or when unrelated keys
    are added while the combo is already held.
    """
    return combo.issubset(current_pressed) and not combo.issubset(prev_pressed)


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


if __name__ == "__main__":
    app()
