"""Argument parsing and command routing for diff-brief."""

from __future__ import annotations

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from diff_brief.git import get_staged_or_recent_diff, get_todays_commit_log
from diff_brief.llm import generate_summary
from diff_brief.prompts import PR_SYSTEM_PROMPT, STANDUP_SYSTEM_PROMPT
from diff_brief.utils import copy_to_clipboard

load_dotenv()

app = typer.Typer(help="diff-brief: Instant terminal standups and PR descriptions")
console = Console()


def _maybe_copy(result: str, copy: bool) -> None:
    if not copy:
        return
    try:
        copy_to_clipboard(result)
        console.print("\n[dim]✔ Copied to clipboard[/dim]")
    except RuntimeError as exc:
        console.print(f"\n[yellow]Clipboard skipped: {exc}[/yellow]")


@app.command()
def pr(
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy result to clipboard"),
) -> None:
    """Generate a clean PR description from current git diff."""
    with console.status("[bold green]Inspecting git diff..."):
        diff = get_staged_or_recent_diff()

    if not diff:
        console.print(
            "[yellow]No staged, unstaged, or recent commit diffs found.[/yellow]"
        )
        raise typer.Exit(1)

    with console.status("[bold cyan]Generating PR description..."):
        try:
            result = generate_summary(diff, PR_SYSTEM_PROMPT)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    console.print(Markdown(result))
    _maybe_copy(result, copy)


@app.command()
def standup(
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy result to clipboard"),
) -> None:
    """Generate daily standup bullets from today's commits and working diff."""
    with console.status("[bold green]Gathering daily git activity..."):
        logs = get_todays_commit_log()
        diff = get_staged_or_recent_diff()
        combined = f"TODAY'S COMMITS:\n{logs}\n\nACTIVE WORKING DIFF:\n{diff}"

    if not logs and not diff:
        console.print("[yellow]No commits or active changes recorded today.[/yellow]")
        raise typer.Exit(1)

    with console.status("[bold cyan]Synthesizing standup notes..."):
        try:
            result = generate_summary(combined, STANDUP_SYSTEM_PROMPT)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1) from exc

    console.print(Markdown(result))
    _maybe_copy(result, copy)


if __name__ == "__main__":
    app()
