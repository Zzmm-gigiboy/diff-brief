"""Pytest configuration and shared fixtures for diff-brief."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Provide a dummy Gemini API key in the environment."""
    key = "test-api-key-1234567890abcdef"
    monkeypatch.setenv("GEMINI_API_KEY", key)
    return key


@pytest.fixture
def clean_gemini_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure GEMINI_API_KEY is not set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture
def sample_pr_diff() -> str:
    """Realistic unified diff fixture for testing PR summarization."""
    return (
        "diff --git a/services/auth.py b/services/auth.py\n"
        "index 1234567..89abcdef 100644\n"
        "--- a/services/auth.py\n"
        "+++ b/services/auth.py\n"
        "@@ -10,6 +10,12 @@ def verify_token(token: str) -> bool:\n"
        "+    if not token:\n"
        "+        return False\n"
        "+    # Support Bearer token prefix\n"
        "+    if token.startswith('Bearer '):\n"
        "+        token = token[7:]\n"
        "     return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])\n"
    )


@pytest.fixture
def sample_commit_log() -> str:
    """Realistic git log output fixture."""
    return (
        "a1b2c3d - feat(auth): add Bearer prefix normalization (Alice Smith)\n"
        "e4f5g6h - fix(tokens): handle empty token strings cleanly (Bob Jones)"
    )


@pytest.fixture
def mock_genai_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock the google.genai.Client and its generate_content response."""
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "## Summary of Changes\n"
        "- Added Bearer token normalization\n"
        "\n"
        "## Key Architectural Updates\n"
        "- Strips 'Bearer ' prefix before JWT decoding in auth.py\n"
        "\n"
        "## Testing Instructions\n"
        "- Run pytest tests/test_auth.py\n"
    )
    mock_client_instance.models.generate_content.return_value = mock_response

    mock_client_class = MagicMock(return_value=mock_client_instance)
    monkeypatch.setattr("diff_brief.llm.genai.Client", mock_client_class)
    return mock_client_instance


@pytest.fixture
def real_git_repo(tmp_path: Path) -> Path:
    """Create a temporary real git repository with initial commit."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    def run_git(*args: str) -> str:
        res = subprocess.run(
            ["git", *args],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    run_git("init")
    run_git("config", "user.name", "Test Committer")
    run_git("config", "user.email", "committer@example.com")

    # Initial file and commit
    hello_file = repo_dir / "hello.txt"
    hello_file.write_text("initial content\n", encoding="utf-8")
    run_git("add", "hello.txt")
    run_git("commit", "-m", "Initial commit")

    return repo_dir
