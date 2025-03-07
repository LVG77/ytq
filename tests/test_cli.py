"""
Tests for the CLI functionality.
"""
import pytest
from typer.testing import CliRunner
# import ytq
from ytq.cli import app

runner = CliRunner()

def fake_get_video(video_id: str):
    # Return a dummy video object if the video_id matches our test case
    if video_id == "-t12345":
        return {
            "title": "Test Video",
            "author": "Tester",
            "url": f"https://youtube.com/watch?v={video_id}",
            "tldr": "Test TL;DR",
            "video_description": "Test description",
            "summary": "Test summary",
            "tags": ["test"],
            "upload_date": "20220101",  # YYYYMMDD
            "duration": 125,
            "view_count": 1000,
            "processed_at": "today",
        }
    return None

def test_summary_with_video_id_starting_with_dash(monkeypatch):
    # Override the db.get_video function in the CLI module
    monkeypatch.setattr("ytq.db.get_video", fake_get_video)
    
    # Invoke the summary command with a video ID that starts with "-"
    result = runner.invoke(app, ["summary", "-t12345"])
    
    # Check that the command executed successfully (exit code 0)
    assert result.exit_code == 0, result.output
    # Verify that our dummy video's details appear in the output
    assert "Test Video" in result.output
    assert "Tester" in result.output

def test_delete_with_video_id_starting_with_dash(monkeypatch):
    monkeypatch.setattr("ytq.db.delete_video", fake_get_video)
    
    # Invoke the summary command with a video ID that starts with "-"
    result = runner.invoke(app, ["delete", "-t12345"])
    
    # Check that the command executed successfully (exit code 0)
    assert result.exit_code == 0, result.output
    # Verify that our dummy video's details appear in the output
    assert "Video with ID '-t12345' deleted from the database." in result.output

def test_version():
    """Test the --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "ytq version" in result.stdout