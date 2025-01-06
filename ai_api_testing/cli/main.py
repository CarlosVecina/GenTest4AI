import asyncio
from typing import Annotated

import typer

from ai_api_testing.agents.agent_specs_extractor import main
from ai_api_testing.utils.logger import logger

app = typer.Typer(no_args_is_help=True)
specs_app = typer.Typer(no_args_is_help=True)
app.add_typer(specs_app, name="specs")


@app.callback()
def callback():
    """Awesome API testing tool."""


@app.command()
def ping():
    """Ping the API."""
    logger.info("Pong")


@specs_app.command()
def extract(url: Annotated[str, typer.Argument(help="The URL of the API to extract specs from")]):
    """Extract API specs."""
    logger.info(f"Extracting specs from {url}")
    asyncio.run(main(url))


if __name__ == "__main__":
    app()
