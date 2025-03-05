"""
Tests for the CLI functionality.
"""
import pytest
from typer.testing import CliRunner
from ytq.cli import app

runner = CliRunner()

def test_version():
    """Test the --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "ytq version" in result.stdout