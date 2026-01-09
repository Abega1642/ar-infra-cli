import logging
import sys
from typing import ClassVar


class _ColorFormatter(logging.Formatter):
    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[90m",  # gray
        logging.INFO: "\033[34m",  # blue
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[31m",  # red
    }
    RESET: ClassVar[str] = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        level = f"{color}[{record.levelname}]{self.RESET}"
        message = record.getMessage()
        return f"{level} {message}"


def get_logger(_: str) -> logging.Logger:
    logger = logging.getLogger("ar-infra-cli")

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_ColorFormatter())

        logger.addHandler(handler)
        logger.propagate = False

    return logger
