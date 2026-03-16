"""Screenshot OCR — extracts terminal text from a PNG screenshot via Tesseract.

Used as a fallback to populate screen_buffer when the terminal backend cannot
capture scrollback text directly (e.g. shell_hook or generic backends on Linux).
Degrades silently when Tesseract is not installed.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_OCR_TIMEOUT = 5.0  # seconds


def is_tesseract_available() -> bool:
    """Return True if the tesseract binary is on PATH."""
    return shutil.which("tesseract") is not None


async def ocr_screenshot(png_bytes: bytes) -> str | None:
    """Extract text from a terminal screenshot using Tesseract OCR.

    Returns the extracted text, or None if Tesseract is not installed,
    the subprocess fails, or no text is found.
    """
    if not is_tesseract_available():
        logger.debug("Tesseract not available for OCR fallback")
        return None

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        tmp_input = Path(f.name)

    try:
        proc = await asyncio.create_subprocess_exec(
            "tesseract",
            str(tmp_input),
            "stdout",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=_OCR_TIMEOUT)
        text = stdout.decode("utf-8", errors="replace").strip()
        if text:
            logger.debug("OCR extracted %d characters from screenshot", len(text))
            return text
        return None
    except (TimeoutError, OSError) as e:
        logger.debug("OCR failed: %s", e)
        return None
    finally:
        tmp_input.unlink(missing_ok=True)
