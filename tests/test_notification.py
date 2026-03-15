"""Tests for notification helpers."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from prompt_shell.delivery.notification import notify_enhanced_prompt


async def test_notify_enhanced_prompt_default_subtitle():
    with patch(
        "prompt_shell.delivery.notification.show_notification", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        await notify_enhanced_prompt("my enhanced prompt")

    _, kwargs = mock.call_args
    assert kwargs["subtitle"] == "Copied to clipboard"


async def test_notify_enhanced_prompt_fallback_subtitle():
    with patch(
        "prompt_shell.delivery.notification.show_notification", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        await notify_enhanced_prompt("my prompt", used_fallback=True)

    _, kwargs = mock.call_args
    assert "fallback" in kwargs["subtitle"].lower()


async def test_notify_enhanced_prompt_no_fallback_subtitle_when_false():
    with patch(
        "prompt_shell.delivery.notification.show_notification", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        await notify_enhanced_prompt("my prompt", used_fallback=False)

    _, kwargs = mock.call_args
    assert "fallback" not in kwargs["subtitle"].lower()
