import logging
import json
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formats log records into a clean, structured JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # If extra dictionary context was passed, merge it into our JSON
        if hasattr(record, "extra_context"):
            log_payload.update(record.extra_context)  # type: ignore

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging() -> logging.Logger:
    """Configures the root logging framework for the system harness."""
    logger = logging.getLogger("intonation_pipeline")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logging()
