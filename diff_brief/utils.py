"""Diff sanitization, token budgeting, and clipboard helpers."""

from __future__ import annotations

MAX_DIFF_CHARS = 60_000


def trim_content(content: str, max_chars: int = MAX_DIFF_CHARS) -> str:
    """Truncate large diffs so LLM calls stay within a rough token budget."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[...diff truncated for length...]"


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard; raise RuntimeError on failure."""
    try:
        import pyperclip
    except ImportError as exc:
        raise RuntimeError(
            "pyperclip is not installed. Reinstall with: pip install pyperclip"
        ) from exc

    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        raise RuntimeError(
            "Clipboard unavailable on this system. "
            "Install a clipboard tool or omit --copy."
        ) from exc
