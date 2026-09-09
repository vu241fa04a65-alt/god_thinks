import logging
import sys
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

def setup_logger(name: str = "CropHealthAI") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler(sys.stdout)

        if JSON_LOGGER_AVAILABLE:
            formatter = JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(module)s %(message)s"
            )
        else:
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] in %(module)s: %(message)s"
            )

        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger

logger = setup_logger()
