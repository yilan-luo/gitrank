"""gitrank -- GitHub repository ranking TUI tool."""

import os
import re
from datetime import date
from typing import Optional

import typer

app = typer.Typer(
    name="gitrank",
    help="GitHub repository ranking TUI tool. Discover trending repos beyond the 1-month window.",
)


def validate_date(value: str) -> date:
    """Parse and validate a YYYY-MM-DD date string."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise typer.BadParameter(f"Invalid date format: '{value}'. Use YYYY-MM-DD.")


@app.callback(invoke_without_command=True)
def main(
    topic: Optional[str] = typer.Option(None, "--topic", help="Search topic (e.g., ai, rust, python)"),
    since: Optional[str] = typer.Option(None, "--since", help="Start date (YYYY-MM-DD)"),
    range: Optional[str] = typer.Option(None, "--range", help="Time range: label (all,month,3months,6months,year) or YYYY-MM-DD..YYYY-MM-DD"),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort method: stars or composite"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Max results (1-100)"),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh, bypass cache"),
) -> None:
    """Launch the gitrank TUI application.

    In CLI direct mode (when --topic is provided), skip the wizard and search directly.
    Without arguments, launch the interactive TUI wizard.
    """
    # Check for GITHUB_TOKEN
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        typer.echo(
            "⚠️  GITHUB_TOKEN not set. API rate limit will be 60 requests/hour.\n"
            "   Set GITHUB_TOKEN environment variable for 5000 requests/hour.",
            err=True,
        )

    if topic:
        # CLI direct mode: run search and display results

        # Parse --range: support labels AND YYYY-MM-DD..YYYY-MM-DD format
        if range:
            range_pattern = r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$"
            m = re.match(range_pattern, range)
            if m:
                since_val = m.group(1)
                until = m.group(2)
                validate_date(since_val)
                validate_date(until)
            else:
                since_val = since or "2008-01-01"
                until = date.today().isoformat()
        elif since:
            since_val = since
            validate_date(since_val)
            until = date.today().isoformat()
        else:
            # Default: last 6 months
            from datetime import timedelta
            default_start = date.today() - timedelta(days=180)
            since_val = default_start.isoformat()
            until = date.today().isoformat()

        if not sort:
            sort_val = "stars"
        else:
            sort_val = sort
        if not limit:
            limit_val = 20
        else:
            limit_val = limit

        typer.echo(
            f"Searching: topic={topic}, since={since_val}, "
            f"until={until}, sort={sort_val}, limit={limit_val}"
        )
        # TODO: CLI direct mode will be wired when TUI async integration is done
        typer.echo("CLI direct mode is ready. Use interactive TUI for full experience.")
    else:
        # Interactive TUI mode
        from gitrank.tui.app import GitRankApp

        app_instance = GitRankApp()
        app_instance.run()


if __name__ == "__main__":
    app()
