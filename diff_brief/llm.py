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

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=[
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\nInput:\n{content}"}],
            }
        ],
    )
    return response.text or "No response received."
