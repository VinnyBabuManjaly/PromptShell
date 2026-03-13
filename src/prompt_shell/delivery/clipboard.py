"""Cross-platform clipboard delivery.

- macOS: pbcopy / pbpaste
- Linux: xclip, xsel, or wl-copy (Wayland)
- Fallback: pyperclip
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil

logger = logging.getLogger(__name__)


def _find_clipboard_cmd() -> tuple[list[str], list[str]] | None:
    """Find available clipboard copy/paste commands.

    Returns (copy_cmd, paste_cmd) or None.
    """
    system = platform.system()

    if system == "Darwin":
        return (["pbcopy"], ["pbpaste"])

    if system == "Linux":
        # Wayland
        if shutil.which("wl-copy"):
            return (["wl-copy"], ["wl-paste"])
        # X11 — xclip
        if shutil.which("xclip"):
            return (
                ["xclip", "-selection", "clipboard"],
                ["xclip", "-selection", "clipboard", "-o"],
            )
        # X11 — xsel
        if shutil.which("xsel"):
            return (
                ["xsel", "--clipboard", "--input"],
                ["xsel", "--clipboard", "--output"],
            )

    return None


async def deliver_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard."""
    cmds = _find_clipboard_cmd()

    if cmds:
        copy_cmd, _ = cmds
        try:
            env = {**os.environ, "LANG": "en_US.UTF-8"}
            process = await asyncio.create_subprocess_exec(
                *copy_cmd,
                stdin=asyncio.subprocess.PIPE,
                env=env,
            )
            await process.communicate(input=text.encode("utf-8"))
            if process.returncode == 0:
                logger.info("Enhanced prompt copied to clipboard (%d chars)", len(text))
                return True
            else:
                logger.error("Clipboard command failed with exit code %d", process.returncode)
        except Exception:
            logger.exception("Clipboard command failed")

    # Fallback to pyperclip
    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info("Enhanced prompt copied to clipboard via pyperclip (%d chars)", len(text))
        return True
    except Exception:
        logger.error("No clipboard mechanism available")
        return False


async def read_from_clipboard() -> str:
    """Read the current clipboard contents."""
    cmds = _find_clipboard_cmd()

    if cmds:
        _, paste_cmd = cmds
        try:
            env = {**os.environ, "LANG": "en_US.UTF-8"}
            process = await asyncio.create_subprocess_exec(
                *paste_cmd,
                stdout=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode("utf-8")
        except Exception:
            pass

    # Fallback to pyperclip
    try:
        import pyperclip

        return pyperclip.paste()
    except Exception:
        return ""
