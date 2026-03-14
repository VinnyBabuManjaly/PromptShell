"""Terminal screenshot capture — captures the active terminal window as PNG.

Prefers window-only capture (focused window at hotkey time) over full screen,
falling back to full screen when window capture is unavailable.

Tool priority per platform:
- macOS:          screencapture -l <window_id>  → screencapture (full screen)
- Linux/GNOME:    gnome-screenshot -w           → gnome-screenshot (full screen)
- Linux/Wayland:  grim (full screen only — no window capture without wlr-foreign-toplevel)
- Linux/X11:      scrot -u (focused window)     → scrot (full screen)

All tools write to a temp file. Stdout-based capture is avoided because
wlroots-style piping (grim -) fails on GNOME's Mutter compositor.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import platform
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB guard
_CAPTURE_TIMEOUT = 5.0  # seconds

# Each entry is a command template where "__OUTPUT__" is replaced with the temp file path.
# Window-capture commands are listed before full-screen fallbacks.
_MACOS_CANDIDATES = [
    ["screencapture", "-x", "-o", "__OUTPUT__"],  # active window only (-o = no shadow)
    ["screencapture", "-x", "__OUTPUT__"],  # full screen fallback
]

_LINUX_CANDIDATES = [
    ["gnome-screenshot", "-w", "--delay=0", "-f", "__OUTPUT__"],  # GNOME active window
    ["gnome-screenshot", "-f", "__OUTPUT__"],  # GNOME full screen fallback
    ["scrot", "-u", "-z", "__OUTPUT__"],  # X11 focused window
    ["scrot", "__OUTPUT__"],  # X11 full screen fallback
    ["grim", "__OUTPUT__"],  # wlroots full screen
    ["import", "-window", "root", "__OUTPUT__"],  # ImageMagick fallback
]


def _get_candidates() -> list[list[str]]:
    system = platform.system()
    if system == "Darwin":
        return _MACOS_CANDIDATES
    if system == "Linux":
        return _LINUX_CANDIDATES
    return []


async def capture_screenshot() -> bytes | None:
    """Capture a PNG screenshot. Tries each available tool in priority order."""
    candidates = _get_candidates()
    if not candidates:
        logger.warning("Screenshot capture not supported on %s", platform.system())
        return None

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = Path(f.name)

    try:
        for template in candidates:
            tool = template[0]
            if not shutil.which(tool):
                continue

            cmd = [tmp_path.as_posix() if arg == "__OUTPUT__" else arg for arg in template]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(proc.communicate(), timeout=_CAPTURE_TIMEOUT)
            except TimeoutError:
                logger.warning("Screenshot tool %s timed out after %.1fs", tool, _CAPTURE_TIMEOUT)
                continue
            except OSError as e:
                logger.debug("Screenshot tool %s failed to start: %s", tool, e)
                continue

            no_output = (
                proc.returncode != 0 or not tmp_path.exists() or tmp_path.stat().st_size == 0
            )
            if no_output:
                logger.debug(
                    "Screenshot tool %s produced no output (exit %d)", tool, proc.returncode
                )
                continue

            data = tmp_path.read_bytes()
            if len(data) > _MAX_SIZE_BYTES:
                logger.warning(
                    "Screenshot too large (%d bytes > %d limit), skipping",
                    len(data),
                    _MAX_SIZE_BYTES,
                )
                return None

            logger.debug("Screenshot captured with %s (%d bytes)", tool, len(data))
            return data

        available = [c[0] for c in candidates if shutil.which(c[0])]
        if available:
            logger.warning("Screenshot tools found (%s) but all failed", ", ".join(available))
        else:
            logger.warning(
                "No screenshot tool available — install gnome-screenshot, grim, or scrot"
            )
        return None
    finally:
        tmp_path.unlink(missing_ok=True)


def encode_screenshot(png_bytes: bytes) -> str:
    """Base64-encode PNG bytes to an ASCII string suitable for JSON transport."""
    return base64.b64encode(png_bytes).decode("ascii")


async def capture_screenshot_b64() -> str | None:
    """Capture a screenshot and return it base64-encoded, or None on failure."""
    png_bytes = await capture_screenshot()
    if png_bytes is None:
        return None
    return encode_screenshot(png_bytes)
