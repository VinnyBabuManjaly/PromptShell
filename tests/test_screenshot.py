"""Tests for terminal screenshot capture."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import AsyncMock, patch

from prompt_shell.terminal.screenshot import capture_screenshot_b64, encode_screenshot

# Minimal valid 1×1 white PNG (67 bytes)
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_proc(returncode: int = 0) -> AsyncMock:
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.returncode = returncode
    return proc


def _mock_exec_writing_file(content: bytes = _TINY_PNG, returncode: int = 0):
    """Return a side_effect for create_subprocess_exec that writes content to the output file."""

    async def _side_effect(*args, **kwargs):
        # Last positional arg is the output file path
        output_path = Path(args[-1])
        if content:
            output_path.write_bytes(content)
        return _make_proc(returncode=returncode)

    return _side_effect


async def test_returns_base64_string_on_success():
    with (
        patch("shutil.which", return_value="/usr/bin/gnome-screenshot"),
        patch("asyncio.create_subprocess_exec", side_effect=_mock_exec_writing_file()),
    ):
        result = await capture_screenshot_b64()

    assert result is not None
    assert isinstance(result, str)
    assert base64.b64decode(result) == _TINY_PNG


async def test_returns_none_when_no_tool_available():
    with patch("shutil.which", return_value=None):
        result = await capture_screenshot_b64()
    assert result is None


async def test_returns_none_on_subprocess_failure():
    with (
        patch("shutil.which", return_value="/usr/bin/gnome-screenshot"),
        patch(
            "asyncio.create_subprocess_exec",
            side_effect=_mock_exec_writing_file(content=b"", returncode=1),
        ),
    ):
        result = await capture_screenshot_b64()
    assert result is None


async def test_returns_none_on_subprocess_exception():
    with (
        patch("shutil.which", return_value="/usr/bin/gnome-screenshot"),
        patch("asyncio.create_subprocess_exec", side_effect=OSError("no device")),
    ):
        result = await capture_screenshot_b64()
    assert result is None


async def test_returns_none_when_output_exceeds_size_limit():
    large_content = b"x" * (11 * 1024 * 1024)
    with (
        patch("shutil.which", return_value="/usr/bin/gnome-screenshot"),
        patch(
            "asyncio.create_subprocess_exec",
            side_effect=_mock_exec_writing_file(content=large_content),
        ),
    ):
        result = await capture_screenshot_b64()
    assert result is None


async def test_returns_none_on_empty_output():
    with (
        patch("shutil.which", return_value="/usr/bin/gnome-screenshot"),
        patch(
            "asyncio.create_subprocess_exec",
            side_effect=_mock_exec_writing_file(content=b""),
        ),
    ):
        result = await capture_screenshot_b64()
    assert result is None


async def test_tries_next_tool_on_failure():
    """Falls through to the second candidate when the first fails."""
    call_count = 0

    async def _side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        output_path = Path(args[-1])
        if call_count == 1:
            # First tool fails — no file written
            return _make_proc(returncode=1)
        # Second tool succeeds
        output_path.write_bytes(_TINY_PNG)
        return _make_proc(returncode=0)

    with (
        patch("shutil.which", return_value="/usr/bin/tool"),
        patch("asyncio.create_subprocess_exec", side_effect=_side_effect),
    ):
        result = await capture_screenshot_b64()

    assert result is not None
    assert call_count == 2


def test_encode_screenshot_produces_valid_base64():
    result = encode_screenshot(b"fake png bytes")
    assert isinstance(result, str)
    assert "\n" not in result
    assert base64.b64decode(result) == b"fake png bytes"
