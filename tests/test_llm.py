"""Unit tests for diff_brief.llm (Gemini client and prompt generation)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from diff_brief.llm import DEFAULT_MODEL, generate_summary
from diff_brief.prompts import PR_SYSTEM_PROMPT, STANDUP_SYSTEM_PROMPT
from diff_brief.utils import MAX_DIFF_CHARS


class TestGenerateSummary:
    def test_missing_api_key_raises_value_error(self, clean_gemini_env: None) -> None:
        with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is missing"):
            generate_summary("diff content", PR_SYSTEM_PROMPT)

    def test_client_initialization_and_payload_structure(
        self, mock_gemini_api_key: str, sample_pr_diff: str
    ) -> None:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "## Generated PR Summary"
        mock_client.models.generate_content.return_value = mock_response

        with patch("diff_brief.llm.genai.Client", return_value=mock_client) as mock_client_cls:
            output = generate_summary(sample_pr_diff, PR_SYSTEM_PROMPT)

            assert output == "## Generated PR Summary"
            mock_client_cls.assert_called_once_with(api_key=mock_gemini_api_key)

            mock_client.models.generate_content.assert_called_once()
            _, kwargs = mock_client.models.generate_content.call_args
            assert kwargs["model"] == DEFAULT_MODEL
            assert kwargs["model"] == "gemini-2.5-flash"

            expected_prompt = f"{PR_SYSTEM_PROMPT}\n\nInput:\n{sample_pr_diff}"
            assert kwargs["contents"] == [
                {
                    "role": "user",
                    "parts": [{"text": expected_prompt}],
                }
            ]

    def test_standup_prompt_payload_structure(
        self, mock_gemini_api_key: str, sample_commit_log: str
    ) -> None:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "- **Done:** Completed auth fixes"
        mock_client.models.generate_content.return_value = mock_response

        with patch("diff_brief.llm.genai.Client", return_value=mock_client):
            output = generate_summary(sample_commit_log, STANDUP_SYSTEM_PROMPT)

            assert output == "- **Done:** Completed auth fixes"
            _, kwargs = mock_client.models.generate_content.call_args
            expected_prompt = f"{STANDUP_SYSTEM_PROMPT}\n\nInput:\n{sample_commit_log}"
            assert kwargs["contents"] == [
                {
                    "role": "user",
                    "parts": [{"text": expected_prompt}],
                }
            ]

    def test_content_is_trimmed_before_calling_llm(
        self, mock_gemini_api_key: str
    ) -> None:
        oversized_diff = "diff --git a/big.py b/big.py\n+" + ("Z" * (MAX_DIFF_CHARS + 2000))
        mock_client = MagicMock()
        mock_response = MagicMock(text="Summary of large diff")
        mock_client.models.generate_content.return_value = mock_response

        with patch("diff_brief.llm.genai.Client", return_value=mock_client):
            output = generate_summary(oversized_diff, PR_SYSTEM_PROMPT)
            assert output == "Summary of large diff"

            _, kwargs = mock_client.models.generate_content.call_args
            prompt_sent = kwargs["contents"][0]["parts"][0]["text"]
            assert "[...diff truncated for length...]" in prompt_sent
            # The diff part should not exceed trimmed length
            assert len(oversized_diff) > MAX_DIFF_CHARS

    def test_none_response_text_fallback(
        self, mock_gemini_api_key: str
    ) -> None:
        mock_client = MagicMock()
        mock_response = MagicMock(text=None)
        mock_client.models.generate_content.return_value = mock_response

        with patch("diff_brief.llm.genai.Client", return_value=mock_client):
            output = generate_summary("some diff", PR_SYSTEM_PROMPT)
            assert output == "No response received."

    def test_empty_response_text_fallback(
        self, mock_gemini_api_key: str
    ) -> None:
        mock_client = MagicMock()
        mock_response = MagicMock(text="")
        mock_client.models.generate_content.return_value = mock_response

        with patch("diff_brief.llm.genai.Client", return_value=mock_client):
            output = generate_summary("some diff", PR_SYSTEM_PROMPT)
            assert output == "No response received."
