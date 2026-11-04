"""Unit tests for diff_brief.prompts (system prompt structure and compliance)."""

from __future__ import annotations

from diff_brief.prompts import PR_SYSTEM_PROMPT, STANDUP_SYSTEM_PROMPT


class TestPrompts:
    def test_pr_system_prompt_structure(self) -> None:
        assert "## Summary of Changes" in PR_SYSTEM_PROMPT
        assert "## Key Architectural Updates" in PR_SYSTEM_PROMPT
        assert "## Testing Instructions" in PR_SYSTEM_PROMPT
        assert "Do not output preamble" in PR_SYSTEM_PROMPT

    def test_standup_system_prompt_structure(self) -> None:
        assert "- **Done:**" in STANDUP_SYSTEM_PROMPT
        assert "- **In Progress:**" in STANDUP_SYSTEM_PROMPT
        assert "- **Context/Notes:**" in STANDUP_SYSTEM_PROMPT
        assert "Professional, concise bullet points only" in STANDUP_SYSTEM_PROMPT
