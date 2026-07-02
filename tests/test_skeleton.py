"""Test project skeleton: verify the project installs and the CLI shows help text."""

import subprocess
import sys
from pathlib import Path


def test_gitrank_help() -> None:
    """Verify `gitrank --help` exits with code 0 and produces help text."""
    # The gitrank script is installed alongside the Python interpreter
    scripts_dir = Path(sys.executable).parent / "Scripts"
    gitrank_exe = scripts_dir / "gitrank.exe"

    result = subprocess.run(
        [str(gitrank_exe), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"gitrank --help exited with {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert "--help" in result.stdout, (
        f"Expected '--help' in help output, got:\n{result.stdout}"
    )
