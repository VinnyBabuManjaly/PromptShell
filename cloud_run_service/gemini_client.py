"""Gemini 2.0 Flash client using the Google GenAI SDK."""

from __future__ import annotations

import google.genai as genai


def create_client(api_key: str) -> genai.Client:
    """Create an authenticated Google GenAI client."""
    return genai.Client(api_key=api_key)


def generate_enhanced_prompt(
    client: genai.Client,
    meta_prompt: str,
    model: str = "gemini-2.0-flash",
) -> str:
    """Call Gemini to produce an enhanced developer prompt."""
    response = client.models.generate_content(
        model=model,
        contents=meta_prompt,
    )
    return response.text.strip()
