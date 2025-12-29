"""Logger configuration for AR-INFRA CLI."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Get or create a configured logger instance.

    Creates a logger with INFO level and console output formatting.
    If the logger already has handlers, returns it as-is to avoid duplicate handlers.

    Args:
        name: Name for the logger, typically __name__ of the calling module

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
