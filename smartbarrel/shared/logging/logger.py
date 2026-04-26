"""JSON structured logger with trace_id propagation."""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = trace_id_var.get()
        if trace_id:
            payload["trace_id"] = trace_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in {"args", "msg", "levelname", "name", "exc_info", "exc_text",
                      "stack_info", "lineno", "funcName", "created", "msecs",
                      "relativeCreated", "thread", "threadName", "processName",
                      "process", "pathname", "filename", "module", "levelno"}:
                continue
            if not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str = "INFO", service_name: str = "smartbarrel") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    logging.getLogger(service_name).setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
