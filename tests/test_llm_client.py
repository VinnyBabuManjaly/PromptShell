"""Tests for LLM client — retry logic, transient/permanent error handling, fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prompt_shell.config import LLMConfig
from prompt_shell.enhancer.llm_client import (
    EnhanceResult,
    LLMClient,
    _is_transient,
    enhance_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides) -> LLMConfig:
    defaults = {"provider": "openai", "model": "gpt-4o-mini", "api_key": "sk-test"}
    defaults.update(overrides)
    return LLMConfig(**defaults)


def _mock_response(text: str) -> MagicMock:
    """Build a mock litellm response."""
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# _is_transient
# ---------------------------------------------------------------------------


class TestIsTransient:
    def test_connection_error(self):
        assert _is_transient(ConnectionError("refused")) is True

    def test_timeout_error(self):
        assert _is_transient(TimeoutError("timed out")) is True

    def test_os_error(self):
        assert _is_transient(OSError("network unreachable")) is True

    def test_rate_limit_in_message(self):
        exc = RuntimeError("rate limit exceeded, retry after 1s")
        assert _is_transient(exc) is True

    def test_timeout_in_message(self):
        exc = RuntimeError("request timed out")
        assert _is_transient(exc) is True

    def test_status_code_429(self):
        exc = RuntimeError("too many requests")
        exc.status_code = 429
        assert _is_transient(exc) is True

    def test_status_code_503(self):
        exc = RuntimeError("service unavailable")
        exc.status_code = 503
        assert _is_transient(exc) is True

    def test_permanent_auth_error(self):
        exc = RuntimeError("invalid api key")
        exc.status_code = 401
        assert _is_transient(exc) is False

    def test_plain_value_error(self):
        assert _is_transient(ValueError("bad input")) is False


# ---------------------------------------------------------------------------
# LLMClient.complete — retry behaviour
# ---------------------------------------------------------------------------


class TestLLMClientRetry:
    async def test_succeeds_first_try(self):
        config = _make_config()
        client = LLMClient(config, max_retries=2, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_response("enhanced text")
            result = await client.complete("test prompt")

        assert result == "enhanced text"
        assert mock.call_count == 1

    async def test_retries_on_transient_then_succeeds(self):
        config = _make_config()
        client = LLMClient(config, max_retries=2, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                ConnectionError("refused"),
                _mock_response("recovered"),
            ]
            result = await client.complete("test prompt")

        assert result == "recovered"
        assert mock.call_count == 2

    async def test_retries_exhausted_raises(self):
        config = _make_config()
        client = LLMClient(config, max_retries=2, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = ConnectionError("refused")

            with pytest.raises(ConnectionError):
                await client.complete("test prompt")

        # 1 initial + 2 retries = 3 attempts
        assert mock.call_count == 3

    async def test_permanent_error_no_retry(self):
        config = _make_config()
        client = LLMClient(config, max_retries=2, retry_delay=0)

        perm_error = RuntimeError("invalid api key")
        perm_error.status_code = 401

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = perm_error

            with pytest.raises(RuntimeError, match="invalid api key"):
                await client.complete("test prompt")

        # Should not retry permanent errors.
        assert mock.call_count == 1

    async def test_no_retries_when_max_zero(self):
        config = _make_config()
        client = LLMClient(config, max_retries=0, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = ConnectionError("refused")

            with pytest.raises(ConnectionError):
                await client.complete("test prompt")

        assert mock.call_count == 1


# ---------------------------------------------------------------------------
# enhance_prompt — fallback & EnhanceResult
# ---------------------------------------------------------------------------


class TestEnhancePrompt:
    async def test_success_returns_result(self):
        config = _make_config()

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_response("enhanced")
            result = await enhance_prompt("meta", config)

        assert isinstance(result, EnhanceResult)
        assert result.text == "enhanced"
        assert result.used_fallback is False
        assert result.error is None

    async def test_fallback_on_error(self):
        config = _make_config()

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = ConnectionError("refused")
            result = await enhance_prompt("meta", config, fallback_text="fallback text")

        assert isinstance(result, EnhanceResult)
        assert result.text == "fallback text"
        assert result.used_fallback is True
        assert "refused" in result.error

    async def test_raises_without_fallback(self):
        config = _make_config()

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("bad")

            with pytest.raises(RuntimeError, match="bad"):
                await enhance_prompt("meta", config, fallback_text=None)

    async def test_fallback_on_permanent_error(self):
        config = _make_config()
        perm = RuntimeError("invalid model")
        perm.status_code = 404

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = perm
            result = await enhance_prompt("meta", config, fallback_text="safe")

        assert result.used_fallback is True
        assert "invalid model" in result.error


# ---------------------------------------------------------------------------
# LLMClient.complete — multimodal (screenshot) support
# ---------------------------------------------------------------------------


class TestLLMClientMultimodal:
    async def test_sends_text_only_when_no_screenshot(self):
        config = _make_config()
        client = LLMClient(config, max_retries=0, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_response("enhanced")
            await client.complete("my prompt", screenshot_b64=None)

        messages = mock.call_args.kwargs["messages"]
        user_content = messages[1]["content"]
        assert user_content == "my prompt"

    async def test_sends_multimodal_content_when_screenshot_provided(self):
        config = _make_config()
        client = LLMClient(config, max_retries=0, retry_delay=0)

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_response("enhanced")
            await client.complete("my prompt", screenshot_b64="abc123")

        messages = mock.call_args.kwargs["messages"]
        user_content = messages[1]["content"]
        assert isinstance(user_content, list)
        assert user_content[0] == {"type": "text", "text": "my prompt"}
        assert user_content[1]["type"] == "image_url"
        assert "abc123" in user_content[1]["image_url"]["url"]

    async def test_enhance_prompt_passes_screenshot_to_complete(self):
        config = _make_config()

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_response("enhanced")
            await enhance_prompt("meta", config, screenshot_b64="imgdata")

        messages = mock.call_args.kwargs["messages"]
        user_content = messages[1]["content"]
        assert isinstance(user_content, list)
        assert user_content[0]["type"] == "text"
        assert user_content[1]["type"] == "image_url"


# ---------------------------------------------------------------------------
# LLMClient._resolve_model_name — provider prefix mapping
# ---------------------------------------------------------------------------


class TestResolveModelName:
    def test_resolve_model_ollama(self):
        config = LLMConfig(provider="ollama", model="llama3.2:8b")
        client = LLMClient(config)
        assert client._model_name == "ollama/llama3.2:8b"

    def test_resolve_model_openai(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        client = LLMClient(config)
        assert client._model_name == "gpt-4o-mini"

    def test_resolve_model_anthropic(self):
        config = LLMConfig(provider="anthropic", model="claude-3-5-haiku-20241022")
        client = LLMClient(config)
        assert client._model_name == "anthropic/claude-3-5-haiku-20241022"

    def test_resolve_model_gemini(self):
        config = LLMConfig(provider="gemini", model="gemini-2.5-flash-lite")
        client = LLMClient(config)
        assert client._model_name == "gemini/gemini-2.5-flash-lite"
