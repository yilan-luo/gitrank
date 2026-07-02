"""Test CLI entry point: parameters, date validation, token detection, direct mode."""

import os

import pytest
from typer.testing import CliRunner

from gitrank.main import app

runner = CliRunner()


class TestCLIHelp:
    """Tests for the --help output."""

    def test_gitrank_help(self) -> None:
        """Verify `gitrank --help` exits with code 0 and shows all CLI options."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0, (
            f"gitrank --help exited with {result.exit_code}\n"
            f"stderr: {result.stderr}"
        )
        # Key options that should appear in help
        assert "--topic" in result.stdout, (
            f"Expected '--topic' in help output, got:\n{result.stdout}"
        )
        assert "--since" in result.stdout, (
            f"Expected '--since' in help output, got:\n{result.stdout}"
        )
        assert "--range" in result.stdout, (
            f"Expected '--range' in help output, got:\n{result.stdout}"
        )
        assert "--sort" in result.stdout, (
            f"Expected '--sort' in help output, got:\n{result.stdout}"
        )
        assert "--limit" in result.stdout, (
            f"Expected '--limit' in help output, got:\n{result.stdout}"
        )
        assert "--refresh" in result.stdout, (
            f"Expected '--refresh' in help output, got:\n{result.stdout}"
        )


class TestCLIDirectMode:
    """Tests for the CLI direct mode (when --topic is provided)."""

    def test_cli_direct_mode_basic(self) -> None:
        """Invoke with --topic ai --since 2025-01-01 --sort stars."""
        result = runner.invoke(
            app,
            ["--topic", "ai", "--since", "2025-01-01", "--sort", "stars"],
        )
        assert result.exit_code == 0
        assert "Searching" in result.stdout or "CLI direct mode" in result.stdout

    def test_cli_direct_mode_with_all_options(self) -> None:
        """Invoke with all available CLI options."""
        result = runner.invoke(
            app,
            [
                "--topic", "rust",
                "--since", "2025-06-01",
                "--range", "all",
                "--sort", "composite",
                "--limit", "10",
                "--refresh",
            ],
        )
        assert result.exit_code == 0
        assert "Searching" in result.stdout or "CLI direct mode" in result.stdout


class TestCLIDateValidation:
    """Tests for date format validation."""

    def test_cli_invalid_date_format(self) -> None:
        """Invalid date format raises an error."""
        result = runner.invoke(
            app,
            ["--topic", "ai", "--since", "not-a-date"],
        )
        assert result.exit_code != 0
        # Typer/Click catches BadParameter inside the callback and exits with code 2.
        # The error message goes through Click's error path which may not reach
        # CliRunner's stdout/stderr capture when raised inside a callback body.
        assert result.exit_code == 2  # Click's standard exit code for parameter errors


class TestCLITokenDetection:
    """Tests for GITHUB_TOKEN detection and warning."""

    def test_cli_missing_token_warning(self) -> None:
        """Without GITHUB_TOKEN, check warning output."""
        # Ensure GITHUB_TOKEN is not set for this test
        old_token = os.environ.pop("GITHUB_TOKEN", None)
        try:
            result = runner.invoke(app, ["--topic", "ai"])
            assert result.exit_code == 0
            # Warning should appear when token is not set
            assert "GITHUB_TOKEN" in result.stdout or "GITHUB_TOKEN" in result.stderr, (
                f"Expected GITHUB_TOKEN warning, got stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        finally:
            if old_token is not None:
                os.environ["GITHUB_TOKEN"] = old_token

    def test_cli_with_token_no_warning(self) -> None:
        """With GITHUB_TOKEN set, no warning should appear."""
        os.environ["GITHUB_TOKEN"] = "test_token_12345"
        try:
            result = runner.invoke(app, ["--topic", "ai"])
            assert result.exit_code == 0
            # When token IS set, the warning text should NOT appear in output
            # (CliRunner mixes stderr into stdout by default)
            warning_text = "GITHUB_TOKEN not set"
            assert warning_text not in result.stdout, (
                f"Unexpected warning in stdout:\n{result.stdout}"
            )
        finally:
            del os.environ["GITHUB_TOKEN"]
