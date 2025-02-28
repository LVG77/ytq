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

def test_add_command():
    """Test the add command."""
    # TODO: Implement test with mocked core functions
    result = runner.invoke(app, ["add", "https://youtube.com/watch?v=sample"])
    assert result.exit_code == 0
    assert "Processing video" in result.stdout

def test_query_command():
    """Test the query command."""
    # TODO: Implement test with mocked db functions
    result = runner.invoke(app, ["query", "test query"])
    assert result.exit_code == 0
    assert "Searching for" in result.stdout

def test_reprocess_command():
    """Test the reprocess command."""
    # TODO: Implement test with mocked core functions
    result = runner.invoke(app, ["reprocess", "https://youtube.com/watch?v=sample"])
    assert result.exit_code == 0
    assert "Reprocessing video" in result.stdout

def test_summary_command():
    """Test the summary command."""
    # TODO: Implement test with mocked db functions
    result = runner.invoke(app, ["summary", "sample_id"])
    assert result.exit_code == 0
    assert "Displaying summary" in result.stdout
