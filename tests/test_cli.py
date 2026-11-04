"""Tests for diff_brief.cli Typer application."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from diff_brief.cli import app

runner = CliRunner()


class TestCliPrCommand:
    def test_pr_success_default_output(self, sample_pr_diff: str) -> None:
        mock_summary = "## Summary of Changes\n- Add auth validation"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary) as mock_gen:
            result = runner.invoke(app, ["pr"])
            assert result.exit_code == 0
            assert "Summary of Changes" in result.stdout
            assert "Add auth validation" in result.stdout
            mock_gen.assert_called_once()

    def test_pr_success_with_plain_flag(self, sample_pr_diff: str) -> None:
        mock_summary = "## Summary of Changes\n- Plain output test"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary):
            result = runner.invoke(app, ["pr", "--plain"])
            assert result.exit_code == 0
            assert "## Summary of Changes" in result.stdout
            assert "- Plain output test" in result.stdout

    def test_pr_success_with_short_plain_flag(self, sample_pr_diff: str) -> None:
        mock_summary = "Plain short flag test"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary):
            result = runner.invoke(app, ["pr", "-p"])
            assert result.exit_code == 0
            assert "Plain short flag test" in result.stdout

    def test_pr_with_copy_flag_success(self, sample_pr_diff: str) -> None:
        mock_summary = "## Summary of Changes\n- Copied content"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary), \
             patch("diff_brief.cli.copy_to_clipboard") as mock_copy:
            result = runner.invoke(app, ["pr", "--copy"])
            assert result.exit_code == 0
            assert "Copied to clipboard" in result.stdout
            mock_copy.assert_called_once_with(mock_summary)

    def test_pr_with_short_copy_flag_success(self, sample_pr_diff: str) -> None:
        mock_summary = "Short copy flag content"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary), \
             patch("diff_brief.cli.copy_to_clipboard") as mock_copy:
            result = runner.invoke(app, ["pr", "-c"])
            assert result.exit_code == 0
            assert "Copied to clipboard" in result.stdout
            mock_copy.assert_called_once_with(mock_summary)

    def test_pr_clipboard_failure_degrades_gracefully(self, sample_pr_diff: str) -> None:
        mock_summary = "Summary text"
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary), \
             patch("diff_brief.cli.copy_to_clipboard", side_effect=RuntimeError("xclip not found")):
            result = runner.invoke(app, ["pr", "--copy"])
            # Command should still exit successfully
            assert result.exit_code == 0
            assert "Clipboard skipped: xclip not found" in result.stdout

    def test_pr_no_diff_found_exits_code_1(self) -> None:
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=""):
            result = runner.invoke(app, ["pr"])
            assert result.exit_code == 1
            assert "No staged, unstaged, or recent commit diffs found." in result.stdout

    def test_pr_missing_api_key_exits_code_1(self, sample_pr_diff: str) -> None:
        with patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", side_effect=ValueError("GEMINI_API_KEY environment variable is missing.")):
            result = runner.invoke(app, ["pr"])
            assert result.exit_code == 1
            assert "GEMINI_API_KEY environment variable is missing." in result.stdout


class TestCliStandupCommand:
    def test_standup_success_with_commits_and_diff(
        self, sample_commit_log: str, sample_pr_diff: str
    ) -> None:
        mock_summary = "- **Done:** Finished auth logic\n- **In Progress:** None"
        with patch("diff_brief.cli.get_todays_commit_log", return_value=sample_commit_log), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary) as mock_gen:
            result = runner.invoke(app, ["standup"])
            assert result.exit_code == 0
            assert "Done:" in result.stdout
            assert "Finished auth logic" in result.stdout

            combined_arg = mock_gen.call_args[0][0]
            assert "TODAY'S COMMITS:\n" in combined_arg
            assert sample_commit_log in combined_arg
            assert "ACTIVE WORKING DIFF:\n" in combined_arg
            assert sample_pr_diff in combined_arg

    def test_standup_with_commits_only(self, sample_commit_log: str) -> None:
        mock_summary = "- **Done:** Only commits today"
        with patch("diff_brief.cli.get_todays_commit_log", return_value=sample_commit_log), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=""), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary):
            result = runner.invoke(app, ["standup"])
            assert result.exit_code == 0
            assert "Only commits today" in result.stdout

    def test_standup_with_diff_only(self, sample_pr_diff: str) -> None:
        mock_summary = "- **In Progress:** Only uncommitted diff today"
        with patch("diff_brief.cli.get_todays_commit_log", return_value=""), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=sample_pr_diff), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary):
            result = runner.invoke(app, ["standup"])
            assert result.exit_code == 0
            assert "Only uncommitted diff today" in result.stdout

    def test_standup_with_copy_and_plain_flags(self, sample_commit_log: str) -> None:
        mock_summary = "- **Done:** Standup plain copy test"
        with patch("diff_brief.cli.get_todays_commit_log", return_value=sample_commit_log), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=""), \
             patch("diff_brief.cli.generate_summary", return_value=mock_summary), \
             patch("diff_brief.cli.copy_to_clipboard") as mock_copy:
            result = runner.invoke(app, ["standup", "-c", "-p"])
            assert result.exit_code == 0
            assert "- **Done:** Standup plain copy test" in result.stdout
            assert "Copied to clipboard" in result.stdout
            mock_copy.assert_called_once_with(mock_summary)

    def test_standup_no_activity_today_exits_code_1(self) -> None:
        with patch("diff_brief.cli.get_todays_commit_log", return_value=""), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=""):
            result = runner.invoke(app, ["standup"])
            assert result.exit_code == 1
            assert "No commits or active changes recorded today." in result.stdout

    def test_standup_missing_api_key_exits_code_1(self, sample_commit_log: str) -> None:
        with patch("diff_brief.cli.get_todays_commit_log", return_value=sample_commit_log), \
             patch("diff_brief.cli.get_staged_or_recent_diff", return_value=""), \
             patch("diff_brief.cli.generate_summary", side_effect=ValueError("Missing API key")):
            result = runner.invoke(app, ["standup"])
            assert result.exit_code == 1
            assert "Missing API key" in result.stdout


class TestCliHelpAndRouting:
    def test_main_help_output(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "diff-brief: Instant terminal standups and PR descriptions" in result.stdout
        assert "pr" in result.stdout
        assert "standup" in result.stdout

    def test_pr_help_output(self) -> None:
        result = runner.invoke(app, ["pr", "--help"])
        assert result.exit_code == 0
        assert "--copy" in result.stdout
        assert "-c" in result.stdout
        assert "--plain" in result.stdout
        assert "-p" in result.stdout

    def test_standup_help_output(self) -> None:
        result = runner.invoke(app, ["standup", "--help"])
        assert result.exit_code == 0
        assert "--copy" in result.stdout
        assert "-c" in result.stdout
        assert "--plain" in result.stdout
        assert "-p" in result.stdout
