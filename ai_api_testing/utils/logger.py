import sys

from loguru import logger

# Remove any existing handlers to start fresh
logger.remove()

DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

logger.add(
    sys.stderr,
    colorize=True,
    format=DEFAULT_FORMAT,
    level="INFO",
)

app_logger = logger.bind(name="ai-api-testing")
