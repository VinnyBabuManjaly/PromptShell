"""Gemini 2.0 Flash client using the Google GenAI SDK."""

from __future__ import annotations

import base64

import google.genai as genai


def create_client(api_key: str) -> genai.Client:
    """Create an authenticated Google GenAI client."""
    return genai.Client(api_key=api_key)


def generate_enhanced_prompt(
    client: genai.Client,
    meta_prompt: str,
    model: str = "gemini-2.0-flash",
    screenshot_b64: str | None = None,
) -> str:
    """Call Gemini to produce an enhanced developer prompt.

    When screenshot_b64 is provided the call is multimodal: the terminal
    screenshot is attached as an inline PNG so Gemini Vision can see the
    exact screen state alongside the text context.
    """
    if screenshot_b64:
        contents = [
            genai.types.Part.from_text(text=meta_prompt),
            genai.types.Part.from_bytes(
                data=base64.b64decode(screenshot_b64),
                mime_type="image/png",
            ),
        ]
    else:
        contents = meta_prompt

    response = client.models.generate_content(model=model, contents=contents)
    return response.text.strip()
