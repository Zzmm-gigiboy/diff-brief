"""Unit and integration tests for diff_brief.git (git subprocess wrappers and diff cascade)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from diff_brief.git import (
    IGNORED_PATTERNS,
    _exclude_pathspecs,
    get_staged_or_recent_diff,
    get_todays_commit_log,
    run_git_command,
)


class TestExcludePathspecs:
    def test_exclude_pathspecs_formatting(self) -> None:
        pathspecs = _exclude_pathspecs()
        assert len(pathspecs) == len(IGNORED_PATTERNS)
        for pattern, spec in zip(IGNORED_PATTERNS, pathspecs):
            assert spec == f":(exclude){pattern}"

    def test_contains_essential_ignored_patterns(self) -> None:
        pathspecs = _exclude_pathspecs()
        assert ":(exclude)package-lock.json" in pathspecs
        assert ":(exclude)yarn.lock" in pathspecs
        assert ":(exclude)poetry.lock" in pathspecs
        assert ":(exclude)*.min.js" in pathspecs
        assert ":(exclude)*.svg" in pathspecs


class TestRunGitCommand:
    def test_run_git_command_success(self) -> None:
        mock_res = MagicMock(stdout="  commit 123456\n")
        with patch("subprocess.run", return_value=mock_res) as mock_run:
            out = run_git_command(["status", "--short"])
            assert out == "commit 123456"
            mock_run.assert_called_once_with(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                check=True,
            )

    def test_run_git_command_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("git binary not found")):
            out = run_git_command(["status"])
            assert out == ""
            captured = capsys.readouterr()
            assert "Git error: git executable not found on PATH." in captured.err

    def test_run_git_command_called_process_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        error = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "diff"],
            stderr="fatal: not a git repository (or any of the parent directories): .git\n",
        )
        with patch("subprocess.run", side_effect=error):
            out = run_git_command(["diff"])
            assert out == ""
            captured = capsys.readouterr()
            assert "fatal: not a git repository" in captured.err

    def test_run_git_command_called_process_error_empty_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "diff"],
            stderr=None,
        )
        with patch("subprocess.run", side_effect=error):
            out = run_git_command(["diff"])
            assert out == ""
            captured = capsys.readouterr()
            assert "Git error:" in captured.err


class TestDiffCascade:
    def test_cascade_tier_1_staged(self) -> None:
        with patch("diff_brief.git.run_git_command") as mock_git:
            mock_git.side_effect = ["diff --staged content"]

            result = get_staged_or_recent_diff()
            assert result == "diff --staged content"
            assert mock_git.call_count == 1
            args = mock_git.call_args[0][0]
            assert args[0] == "diff"
            assert args[1] == "--staged"

    def test_cascade_tier_2_unstaged(self) -> None:
        with patch("diff_brief.git.run_git_command") as mock_git:
            # Staged is empty, unstaged returns content
            mock_git.side_effect = ["", "diff unstaged content"]

            result = get_staged_or_recent_diff()
            assert result == "diff unstaged content"
            assert mock_git.call_count == 2
            # First call was staged
            assert mock_git.call_args_list[0][0][0][1] == "--staged"
            # Second call was unstaged
            assert mock_git.call_args_list[1][0][0] == ["diff", "--", ".", *_exclude_pathspecs()]

    def test_cascade_tier_3_previous_commit(self) -> None:
        with patch("diff_brief.git.run_git_command") as mock_git:
            # Staged is empty, unstaged is empty, HEAD~1 returns content
            mock_git.side_effect = ["", "", "diff HEAD~1 content"]

            result = get_staged_or_recent_diff()
            assert result == "diff HEAD~1 content"
            assert mock_git.call_count == 3
            assert mock_git.call_args_list[2][0][0] == [
                "diff",
                "HEAD~1",
                "--",
                ".",
                *_exclude_pathspecs(),
            ]

    def test_cascade_all_empty(self) -> None:
        with patch("diff_brief.git.run_git_command") as mock_git:
            mock_git.side_effect = ["", "", ""]

            result = get_staged_or_recent_diff()
            assert result == ""
            assert mock_git.call_count == 3

    def test_get_todays_commit_log(self) -> None:
        with patch("diff_brief.git.run_git_command", return_value="abc1234 - feat: test (Dev)") as mock_git:
            log = get_todays_commit_log()
            assert log == "abc1234 - feat: test (Dev)"
            mock_git.assert_called_once_with(
                [
                    "log",
                    "--since=midnight",
                    "--pretty=format:%h - %s (%an)",
                    "--no-merges",
                ]
            )


class TestRealGitRepoIntegration:
    """Authentic end-to-end integration tests using an ephemeral git repository."""

    def test_real_git_staged_diff_and_exclusions(
        self, real_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(real_git_repo)

        # Create a tracked file change and stage it
        code_file = real_git_repo / "main.py"
        code_file.write_text("print('hello world')\n", encoding="utf-8")
        subprocess.run(["git", "add", "main.py"], cwd=real_git_repo, check=True)

        # Create an ignored file (e.g. package-lock.json) and stage it
        lock_file = real_git_repo / "package-lock.json"
        lock_file.write_text('{"lockfileVersion": 3}\n', encoding="utf-8")
        subprocess.run(["git", "add", "package-lock.json"], cwd=real_git_repo, check=True)

        diff = get_staged_or_recent_diff()
        assert "main.py" in diff
        assert "print('hello world')" in diff
        # Lockfile must be excluded by pathspec
        assert "package-lock.json" not in diff

    def test_real_git_unstaged_diff_fallback(
        self, real_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(real_git_repo)

        # Modify hello.txt without staging
        hello_file = real_git_repo / "hello.txt"
        hello_file.write_text("modified content\n", encoding="utf-8")

        diff = get_staged_or_recent_diff()
        assert "hello.txt" in diff
        assert "+modified content" in diff

    def test_real_git_head_minus_1_fallback(
        self, real_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(real_git_repo)

        # Commit an update so working directory is clean
        hello_file = real_git_repo / "hello.txt"
        hello_file.write_text("second commit content\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-am", "Second commit"], cwd=real_git_repo, check=True)

        # Working tree is clean, so it should fall back to HEAD~1
        diff = get_staged_or_recent_diff()
        assert "hello.txt" in diff
        assert "+second commit content" in diff
