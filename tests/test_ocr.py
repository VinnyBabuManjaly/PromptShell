"""Tests for terminal screenshot OCR extraction."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from prompt_shell.terminal.ocr import is_tesseract_available, ocr_screenshot

# Minimal valid 1x1 white PNG (67 bytes)
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_proc(stdout: bytes = b"", returncode: int = 0) -> AsyncMock:
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(stdout, b""))
    proc.returncode = returncode
    return proc


async def test_returns_none_when_tesseract_not_installed():
    with patch("shutil.which", return_value=None):
        result = await ocr_screenshot(_TINY_PNG)
    assert result is None


async def test_returns_text_from_screenshot():
    expected = "error TS2345: type mismatch at src/app.ts:10"

    async def _mock_exec(*args, **kwargs):
        return _make_proc(stdout=expected.encode())

    with (
        patch("shutil.which", return_value="/usr/bin/tesseract"),
        patch("asyncio.create_subprocess_exec", side_effect=_mock_exec),
    ):
        result = await ocr_screenshot(_TINY_PNG)

    assert result == expected


async def test_returns_none_on_empty_output():
    async def _mock_exec(*args, **kwargs):
        return _make_proc(stdout=b"   \n  ")

    with (
        patch("shutil.which", return_value="/usr/bin/tesseract"),
        patch("asyncio.create_subprocess_exec", side_effect=_mock_exec),
    ):
        result = await ocr_screenshot(_TINY_PNG)

    assert result is None


async def test_returns_none_on_subprocess_error():
    with (
        patch("shutil.which", return_value="/usr/bin/tesseract"),
        patch("asyncio.create_subprocess_exec", side_effect=OSError("not found")),
    ):
        result = await ocr_screenshot(_TINY_PNG)
    assert result is None


async def test_returns_none_on_timeout():
    async def _mock_exec(*args, **kwargs):
        proc = AsyncMock()
        proc.communicate = AsyncMock(side_effect=TimeoutError)
        return proc

    with (
        patch("shutil.which", return_value="/usr/bin/tesseract"),
        patch("asyncio.create_subprocess_exec", side_effect=_mock_exec),
        patch("asyncio.wait_for", side_effect=TimeoutError),
    ):
        result = await ocr_screenshot(_TINY_PNG)

    assert result is None


def test_is_tesseract_available_true():
    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        assert is_tesseract_available() is True


def test_is_tesseract_available_false():
    with patch("shutil.which", return_value=None):
        assert is_tesseract_available() is False
