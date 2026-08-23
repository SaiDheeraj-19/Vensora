import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# Context variable to hold correlation IDs
import contextvars
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('correlation_id', default='')

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output structured JSON logs.
    Automatically injects correlation_id if present in context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Inject correlation ID if available
        corr_id = correlation_id_var.get()
        if corr_id:
            log_obj["correlation_id"] = corr_id

        # Include exception traceback if present
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
            
        # Add any extra kwargs passed to the logger
        if hasattr(record, "extra"):
            log_obj.update(record.extra) # type: ignore

        return json.dumps(log_obj)

def setup_logging(level: int = logging.INFO):
    """
    Configure the root logger to output JSON to stdout.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers (e.g. uvicorn defaults) if necessary
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    # Optional: adjust specific library verbosity
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
