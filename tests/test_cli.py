"""
Tests for the CLI functionality.
"""
import pytest
from typer.testing import CliRunner
from yt_scribe.cli import app

runner = CliRunner()

def test_version():
    """Test the --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "yt-scribe version" in result.stdout