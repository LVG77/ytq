import typer
from typing_extensions import Annotated

__version__ = "0.1.0"

app = typer.Typer()

def version_callback(value: bool):
    if value:
        print("yt-scribe CLI Version: {}".format(__version__))
        raise typer.Exit()

@app.command()
def main(
    name: Annotated[str, typer.Argument(help="Your name")],
    version: Annotated[bool, typer.Option("--version", callback=version_callback, is_eager=True)] = None
):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
