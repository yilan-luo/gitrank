"""Test project skeleton: verify the CLI app shows help text via in-process runner."""

from typer.testing import CliRunner

from gitrank.main import app

runner = CliRunner()


def test_gitrank_help() -> None:
    """Verify `gitrank --help` exits with code 0 and produces help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, (
        f"gitrank --help exited with {result.exit_code}\n"
        f"stderr: {result.stderr}"
    )
    assert "--help" in result.stdout, (
        f"Expected '--help' in help output, got:\n{result.stdout}"
    )
