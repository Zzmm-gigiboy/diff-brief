"""Subprocess wrappers for git diff and git log."""

from __future__ import annotations

import subprocess
import sys

IGNORED_PATTERNS = [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "*.min.js",
    "*.svg",
    "*.lock",
]


def _exclude_pathspecs() -> list[str]:
    return [f":(exclude){pattern}" for pattern in IGNORED_PATTERNS]


def run_git_command(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        sys.stderr.write("Git error: git executable not found on PATH.\n")
        return ""
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or "").strip() or str(exc)
        sys.stderr.write(f"Git error: {err}\n")
        return ""


def get_staged_or_recent_diff() -> str:
    excludes = _exclude_pathspecs()

    # 1. Staged diff first
    diff = run_git_command(["diff", "--staged", "--", ".", *excludes])
    if diff:
        return diff

    # 2. Unstaged working tree
    diff = run_git_command(["diff", "--", ".", *excludes])
    if diff:
        return diff

    # 3. Fall back to previous commit
    return run_git_command(["diff", "HEAD~1", "--", ".", *excludes])


def get_todays_commit_log() -> str:
    return run_git_command(
        [
            "log",
            "--since=midnight",
            "--pretty=format:%h - %s (%an)",
            "--no-merges",
        ]
    )
