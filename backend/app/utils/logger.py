import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import json

try:
    from pythonjsonlogger.json import JsonFormatter
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    try:
        from pythonjsonlogger import jsonlogger
        JsonFormatter = jsonlogger.JsonFormatter
        JSON_LOGGER_AVAILABLE = True
    except ImportError:
        JSON_LOGGER_AVAILABLE = False


class CustomStructuredJsonFormatter(logging.Formatter):
    """
    Fallback high-performance structured JSON formatter
    when pythonjsonlogger is not installed or for consistent schema.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include contextual exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if passed in extra={}
        for key, val in record.__dict__.items():
            if key not in ("args", "asctime", "created", "exc_info", "exc_text", "filename",
                           "funcName", "id", "levelname", "levelno", "lineno", "module",
                           "msecs", "message", "msg", "name", "pathname", "process",
                           "processName", "relativeCreated", "stack_info", "thread", "threadName"):
                try:
                    json.dumps(val)
                    log_obj[key] = val
                except (TypeError, OverflowError):
                    log_obj[key] = str(val)

        return json.dumps(log_obj)


def setup_logger(name: str = "CropHealthAI") -> logging.Logger:
    """
    Sets up a logger with structured JSON formatting and size-based log rotation.
    """
    from backend.app.config import settings

    logger = logging.getLogger(name)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    if not logger.handlers:
        # Determine Formatter
        if JSON_LOGGER_AVAILABLE:
            formatter = JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s"
            )
        else:
            formatter = CustomStructuredJsonFormatter()

        # 1. Console Stream Handler (Stdout for Docker / Kubernetes container logs)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(log_level)
        logger.addHandler(stream_handler)

        # 2. Rotating File Handler
        try:
            log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", settings.LOG_DIR))
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "crophealth.log")

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=settings.LOG_ROTATION_MAX_BYTES,
                backupCount=settings.LOG_ROTATION_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            logger.addHandler(file_handler)
        except Exception as e:
            # If filesystem permissions prevent file logging, warn on stdout
            sys.stderr.write(f"Warning: Could not initialize rotating file logger: {e}\n")

    return logger


logger = setup_logger()
