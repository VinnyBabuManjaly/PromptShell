"""Cross-platform notification delivery.

- macOS: osascript (AppleScript)
- Linux: notify-send (libnotify)
- Fallback: console print
"""

from __future__ import annotations

import asyncio
import logging
import platform
import shutil
import subprocess

logger = logging.getLogger(__name__)


async def show_notification(
    title: str,
    message: str,
    subtitle: str | None = None,
    sound: bool = True,
) -> bool:
    """Show a desktop notification (cross-platform)."""
    loop = asyncio.get_running_loop()
    system = platform.system()

    if system == "Darwin":
        return await loop.run_in_executor(
            None, lambda: _notify_macos(title, message, subtitle, sound)
        )
    elif system == "Linux":
        return await loop.run_in_executor(None, lambda: _notify_linux(title, message, subtitle))
    else:
        # Fallback: just log it
        logger.info("Notification: %s — %s", title, message)
        return True


# AppleScript that reads all display values from argv, never from interpolated source.
# argv: (1) title  (2) message  (3) subtitle — empty string if absent  (4) "1" = play sound
_MACOS_NOTIFY_SCRIPT = """\
on run argv
    set notifTitle    to item 1 of argv
    set notifMsg      to item 2 of argv
    set notifSubtitle to item 3 of argv
    set playSound     to item 4 of argv
    if notifSubtitle is not "" then
        if playSound is "1" then
            display notification notifMsg with title notifTitle subtitle notifSubtitle sound name "Glass"
        else
            display notification notifMsg with title notifTitle subtitle notifSubtitle
        end if
    else
        if playSound is "1" then
            display notification notifMsg with title notifTitle sound name "Glass"
        else
            display notification notifMsg with title notifTitle
        end if
    end if
end run
"""


def _notify_macos(title: str, message: str, subtitle: str | None, sound: bool) -> bool:
    """macOS notification via osascript.

    Values are passed as argv arguments — never interpolated into the script
    source — so no AppleScript injection is possible regardless of content.
    """
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                _MACOS_NOTIFY_SCRIPT,
                title,
                message,
                subtitle or "",
                "1" if sound else "0",
            ],
            capture_output=True,
            timeout=5,
        )
        logger.debug("macOS notification shown: %s", title)
        return True

    except subprocess.TimeoutExpired:
        logger.warning("macOS notification timed out")
        return False
    except FileNotFoundError:
        logger.warning("osascript not available")
        return False
    except Exception:
        logger.exception("Failed to show macOS notification")
        return False


def _notify_linux(title: str, message: str, subtitle: str | None) -> bool:
    """Linux notification via notify-send (libnotify)."""
    if not shutil.which("notify-send"):
        logger.debug("notify-send not available, skipping notification")
        return False

    try:
        body = message
        if subtitle:
            body = f"{subtitle}\n{message}"

        subprocess.run(
            [
                "notify-send",
                "--app-name=PromptShell",
                "--expire-time=5000",
                title,
                body,
            ],
            capture_output=True,
            timeout=5,
        )
        logger.debug("Linux notification shown: %s", title)
        return True

    except subprocess.TimeoutExpired:
        logger.warning("notify-send timed out")
        return False
    except Exception:
        logger.exception("Failed to show Linux notification")
        return False


async def notify_enhanced_prompt(enhanced_prompt: str, preview_chars: int = 100) -> bool:
    """Show a notification that the prompt has been enhanced."""
    preview = enhanced_prompt[:preview_chars]
    if len(enhanced_prompt) > preview_chars:
        preview += "..."

    return await show_notification(
        title="Prompt Enhanced",
        subtitle="Copied to clipboard",
        message=preview,
    )


async def notify_error(error_message: str) -> bool:
    """Show an error notification."""
    return await show_notification(
        title="PromptShell",
        subtitle="Error",
        message=error_message,
        sound=True,
    )


async def notify_fallback(error_message: str) -> bool:
    """Notify the user that the LLM failed and a fallback was used."""
    return await show_notification(
        title="PromptShell",
        subtitle="LLM unavailable — used template fallback",
        message=error_message,
        sound=True,
    )


async def notify_listening() -> bool:
    """Show a notification that the service is listening."""
    return await show_notification(
        title="PromptShell",
        message="Listening... speak now",
        sound=False,
    )
