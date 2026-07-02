"""gitrank -- GitHub repository ranking TUI tool."""

import typer

app = typer.Typer(
    name="gitrank",
    help="GitHub repository ranking TUI tool. Discover trending repos beyond the 1-month window.",
)


@app.callback(invoke_without_command=True)
def main() -> None:
    """Launch the gitrank TUI application."""
    print("gitrank v0.1.0 -- TUI coming soon. Run 'gitrank --help' for options.")


if __name__ == "__main__":
    app()
