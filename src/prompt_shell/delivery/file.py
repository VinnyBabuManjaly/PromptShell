"""File delivery — writes the enhanced prompt to a local file."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT_FILE = Path.home() / ".prompt-shell" / "last_prompt.txt"


async def deliver_to_file(text: str, output_file: Path = _DEFAULT_OUTPUT_FILE) -> bool:
    """Write *text* to *output_file*, creating parent directories as needed."""
    loop = asyncio.get_running_loop()

    def _write() -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(text, encoding="utf-8")

    try:
        await loop.run_in_executor(None, _write)
        logger.info("Enhanced prompt written to %s (%d chars)", output_file, len(text))
        return True
    except Exception:
        logger.exception("Failed to write enhanced prompt to %s", output_file)
        return False
