"""Cloud Run enhancement service — FastAPI + Gemini 2.0 Flash."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gemini_client import create_client, generate_enhanced_prompt
from prompt_builder import build_meta_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is required")
    return create_client(api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PromptShell Cloud Run service starting")
    _get_gemini_client()  # Fail fast if API key is missing
    yield
    logger.info("PromptShell Cloud Run service stopping")


app = FastAPI(
    title="PromptShell Enhancement Service",
    description="Enhances developer prompts using Gemini 2.0 Flash",
    version="0.1.0",
    lifespan=lifespan,
)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


class EnhanceRequest(BaseModel):
    voice_transcript: str
    cwd: str = ""
    shell: str = ""
    git_branch: str | None = None
    last_commands: str = ""
    detected_errors: str = ""
    screen_buffer_last_50: str = ""
    project_type: str = "unknown"
    project_name: str = "unknown"
    screenshot_b64: str | None = None


class EnhanceResponse(BaseModel):
    enhanced_prompt: str


@app.post("/enhance", response_model=EnhanceResponse)
async def enhance(request: EnhanceRequest) -> EnhanceResponse:
    """Enhance a developer prompt using terminal context and Gemini."""
    try:
        client = _get_gemini_client()
        meta_prompt = build_meta_prompt(request.model_dump())
        enhanced = generate_enhanced_prompt(
            client, meta_prompt, model=GEMINI_MODEL, screenshot_b64=request.screenshot_b64
        )
        logger.info("Enhanced prompt (%d chars)", len(enhanced))
        return EnhanceResponse(enhanced_prompt=enhanced)
    except RuntimeError as e:
        logger.error("Configuration error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Enhancement failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Gemini call failed: {e}")


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "ok"}
