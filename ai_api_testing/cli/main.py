import typer

from ai_api_testing.utils.logger import logger

app = typer.Typer(no_args_is_help=True)


@app.callback()
def callback():
    """Awesome API testing tool."""


@app.command()
def ping():
    """Ping the API."""
    logger.info("Pong")


@app.command()
def extract_specs():
    """Extract API specs."""
    logger.info("Extracting specs")


if __name__ == "__main__":
    app()
