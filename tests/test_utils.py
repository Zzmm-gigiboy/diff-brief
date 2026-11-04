"""Unit tests for diff_brief.utils (token trimming and clipboard helpers)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from diff_brief.utils import MAX_DIFF_CHARS, copy_to_clipboard, trim_content


class TestTrimContent:
    def test_trim_content_under_limit(self) -> None:
        short_text = "def hello():\n    return 'world'\n"
        assert trim_content(short_text) == short_text

    def test_trim_content_exact_limit(self) -> None:
        exact_text = "a" * MAX_DIFF_CHARS
        assert trim_content(exact_text, max_chars=MAX_DIFF_CHARS) == exact_text

    def test_trim_content_exceeds_limit_default(self) -> None:
        long_text = "x" * (MAX_DIFF_CHARS + 500)
        trimmed = trim_content(long_text)

        expected_prefix = "x" * MAX_DIFF_CHARS
        expected_sentinel = "\n\n[...diff truncated for length...]"
        assert trimmed == expected_prefix + expected_sentinel
        assert len(trimmed) == MAX_DIFF_CHARS + len(expected_sentinel)

    def test_trim_content_custom_limit(self) -> None:
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        trimmed = trim_content(text, max_chars=10)
        assert trimmed == "ABCDEFGHIJ\n\n[...diff truncated for length...]"

    def test_trim_content_empty_string(self) -> None:
        assert trim_content("") == ""


class TestCopyToClipboard:
    def test_copy_to_clipboard_success(self) -> None:
        with patch("pyperclip.copy") as mock_copy:
            copy_to_clipboard("test-content")
            mock_copy.assert_called_once_with("test-content")

    def test_copy_to_clipboard_missing_module(self) -> None:
        with patch.dict(sys.modules, {"pyperclip": None}):
            with pytest.raises(RuntimeError, match="pyperclip is not installed"):
                copy_to_clipboard("test-content")

    def test_copy_to_clipboard_headless_pyperclip_exception(self) -> None:
        import pyperclip

        with patch("pyperclip.copy", side_effect=pyperclip.PyperclipException("No display")):
            with pytest.raises(RuntimeError, match="Clipboard unavailable on this system"):
                copy_to_clipboard("test-content")
