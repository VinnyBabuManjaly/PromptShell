"""Cloud Run enhancement client — routes to Gemini via HTTP or falls back to litellm."""

from __future__ import annotations

import logging
import os

import httpx

from prompt_shell.config import LLMConfig
from prompt_shell.enhancer.llm_client import EnhanceResult, enhance_prompt
from prompt_shell.enhancer.prompt_builder import build_meta_prompt

logger = logging.getLogger(__name__)


def _resolve_env_var(value: str) -> str:
    """Expand ${ENV_VAR} references in a string."""
    if value and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, value)
    return value


async def enhance_via_cloud_run(
    summary: dict,
    cloud_run_url: str,
    timeout: float = 30.0,
) -> str:
    """POST summary to Cloud Run /enhance endpoint. Returns enhanced prompt string."""
    payload = {
        "voice_transcript": summary.get("voice_transcript", ""),
        "cwd": summary.get("cwd", ""),
        "shell": summary.get("shell", ""),
        "git_branch": summary.get("git_branch"),
        "last_commands": summary.get("last_commands", ""),
        "detected_errors": summary.get("detected_errors", ""),
        "screen_buffer_last_50": summary.get("screen_buffer_last_50", ""),
        "project_type": summary.get("project_type", "unknown"),
        "project_name": summary.get("project_name", "unknown"),
    }

    url = cloud_run_url.rstrip("/") + "/enhance"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data["enhanced_prompt"]


async def enhance_with_fallback(
    summary: dict,
    config: LLMConfig,
    fallback_text: str | None = None,
) -> EnhanceResult:
    """Try Cloud Run (if gemini provider + url set), fall back to litellm or template."""
    resolved_url = config.resolve_cloud_run_url() if config.provider == "gemini" else None
    if resolved_url:
        try:
            text = await enhance_via_cloud_run(summary, resolved_url)
            return EnhanceResult(text=text)
        except Exception as e:
            logger.warning("Cloud Run failed: %s — falling back to litellm", e)

    meta_prompt = build_meta_prompt(summary)
    return await enhance_prompt(meta_prompt, config, fallback_text=fallback_text)
