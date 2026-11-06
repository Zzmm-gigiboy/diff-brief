"""Thin Gemini client for summarization."""

from __future__ import annotations

import os

from google import genai

from diff_brief.utils import trim_content

DEFAULT_MODEL = "gemini-2.5-flash"


def generate_summary(content: str, system_prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    content = trim_content(content)
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\nInput:\n{content}"}],
                }
            ],
        )
        return response.text or "No response received."
    except Exception as exc:
        raise RuntimeError(f"Gemini API request failed ({model_name}): {exc}") from exc
