from loguru import logger

from ai_api_testing.utils.logger import app_logger


def test_logger():
    """Test that the logger works as expected."""
    # Pytest fixture caplog to capturing log messages
    log_messages = []
    logger.add(lambda msg: log_messages.append(msg), format="{message}")

    # Test different log levels
    app_logger.info("Some message")
    app_logger.warning("Warning message")
    app_logger.error("Error message")
    app_logger.debug("Last debug message")

    assert len(log_messages) == 4
    assert "Last debug message" in log_messages[-1]
