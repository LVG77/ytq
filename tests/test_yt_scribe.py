from typer.testing import CliRunner
from yt_scribe.cli import app


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "CLI Version" in result.output
