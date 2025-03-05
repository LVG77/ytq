from typer.testing import CliRunner
from ytq.cli import app


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "ytq version" in result.output
