"""Tests for the Cloud Run enhancement client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from prompt_shell.config import LLMConfig
from prompt_shell.enhancer.enhancement_client import (
    enhance_via_cloud_run,
    enhance_with_fallback,
)
from prompt_shell.enhancer.llm_client import EnhanceResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SUMMARY = {
    "voice_transcript": "fix the error",
    "cwd": "/app",
    "shell": "zsh",
    "git_branch": "main",
    "last_commands": "npm run build",
    "detected_errors": "TS2345 in src/index.ts:42",
    "screen_buffer_last_50": "Error: type mismatch",
    "project_type": "typescript",
    "project_name": "my-app",
    "running_process": "node",
}

_CLOUD_RUN_URL = "https://prompt-shell-abc123-uc.a.run.app"


# ---------------------------------------------------------------------------
# enhance_via_cloud_run
# ---------------------------------------------------------------------------


class TestEnhanceViaCloudRun:
    async def test_success(self, httpx_mock):
        httpx_mock.add_response(
            json={"enhanced_prompt": "Fix TS2345 in src/index.ts:42"},
        )
        result = await enhance_via_cloud_run(_SUMMARY, _CLOUD_RUN_URL)
        assert result == "Fix TS2345 in src/index.ts:42"

    async def test_http_error_raises(self, httpx_mock):
        httpx_mock.add_response(status_code=500, text="Internal Server Error")
        with pytest.raises(Exception):
            await enhance_via_cloud_run(_SUMMARY, _CLOUD_RUN_URL)

    async def test_sends_correct_fields(self, httpx_mock):
        httpx_mock.add_response(json={"enhanced_prompt": "ok"})
        await enhance_via_cloud_run(_SUMMARY, _CLOUD_RUN_URL)
        request = httpx_mock.get_requests()[0]
        import json

        body = json.loads(request.content)
        assert body["voice_transcript"] == "fix the error"
        assert body["cwd"] == "/app"
        assert body["git_branch"] == "main"


# ---------------------------------------------------------------------------
# enhance_with_fallback
# ---------------------------------------------------------------------------


class TestEnhanceWithFallback:
    async def test_uses_cloud_run_when_gemini(self, httpx_mock):
        httpx_mock.add_response(json={"enhanced_prompt": "Enhanced via Cloud Run"})
        config = LLMConfig(
            provider="gemini", model="gemini-2.0-flash", cloud_run_url=_CLOUD_RUN_URL
        )
        result = await enhance_with_fallback(_SUMMARY, config, fallback_text="fallback")
        assert result.text == "Enhanced via Cloud Run"
        assert result.used_fallback is False

    async def test_skips_cloud_run_for_ollama(self):
        config = LLMConfig(provider="ollama", model="llama3.2:8b")
        with patch(
            "prompt_shell.enhancer.enhancement_client.enhance_prompt",
            new_callable=AsyncMock,
        ) as mock_enhance:
            mock_enhance.return_value = EnhanceResult(text="litellm result")
            result = await enhance_with_fallback(_SUMMARY, config, fallback_text="fallback")
        assert result.text == "litellm result"
        mock_enhance.assert_called_once()

    async def test_falls_back_on_cloud_run_failure(self, httpx_mock):
        httpx_mock.add_response(status_code=503, text="Service Unavailable")
        config = LLMConfig(
            provider="gemini", model="gemini-2.0-flash", cloud_run_url=_CLOUD_RUN_URL
        )
        with patch(
            "prompt_shell.enhancer.enhancement_client.enhance_prompt",
            new_callable=AsyncMock,
        ) as mock_enhance:
            mock_enhance.return_value = EnhanceResult(text="litellm fallback")
            result = await enhance_with_fallback(_SUMMARY, config, fallback_text="template")
        assert result.text == "litellm fallback"
        mock_enhance.assert_called_once()

    async def test_skips_cloud_run_when_no_url(self):
        config = LLMConfig(provider="gemini", model="gemini-2.0-flash", cloud_run_url=None)
        with patch(
            "prompt_shell.enhancer.enhancement_client.enhance_prompt",
            new_callable=AsyncMock,
        ) as mock_enhance:
            mock_enhance.return_value = EnhanceResult(text="litellm result")
            result = await enhance_with_fallback(_SUMMARY, config, fallback_text="fallback")
        assert result.text == "litellm result"
        mock_enhance.assert_called_once()
