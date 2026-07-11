import logging
import sys
from datetime import datetime
from typing import Optional


class StructuredFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self._batch_context: dict = {}

    def set_batch_context(self, **kwargs):
        self._batch_context.update(kwargs)

    def clear_batch_context(self):
        self._batch_context.clear()

    def format(self, record):
        ts = datetime.utcfromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        ctx = " ".join(
            f"[{k}={v}]" for k, v in sorted(self._batch_context.items()) if v is not None
        )
        prefix = f"{ts} [{record.levelname}] {ctx}" if ctx else f"{ts} [{record.levelname}]"
        return f"{prefix} {record.getMessage()}"


class EtlLogger:
    _handlers_initialized = False

    def __init__(self, source_name: str):
        self.source_name = source_name
        self._formatter = StructuredFormatter()
        self._logger = logging.getLogger(f"etl.{source_name}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        self._init_handlers()

    def _init_handlers(self):
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(self._formatter)
            self._logger.addHandler(handler)

    def _ctx(self, **extra) -> dict:
        ctx = {"source": self.source_name}
        ctx.update(extra)
        return ctx

    def set_batch(self, batch_id: int):
        self._formatter.set_batch_context(batch=batch_id, source=self.source_name)

    def clear_batch(self):
        self._formatter.clear_batch_context()

    def info(self, message: str, **ctx):
        self._formatter.set_batch_context(**self._ctx(**ctx))
        self._logger.info(message)
        self._formatter.clear_batch_context()

    def warn(self, message: str, **ctx):
        self._formatter.set_batch_context(**self._ctx(**ctx))
        self._logger.warning(message)
        self._formatter.clear_batch_context()

    def error(self, message: str, **ctx):
        self._formatter.set_batch_context(**self._ctx(**ctx))
        self._logger.error(message)
        self._formatter.clear_batch_context()

    def debug(self, message: str, **ctx):
        self._formatter.set_batch_context(**self._ctx(**ctx))
        self._logger.debug(message)
        self._formatter.clear_batch_context()

    def exception(self, message: str, exc_info=True, **ctx):
        self._formatter.set_batch_context(**self._ctx(**ctx))
        self._logger.exception(message, exc_info=exc_info)
        self._formatter.clear_batch_context()

    def row_summary(self, row_index: int, action: str, model: Optional[str] = None,
                    official_id: Optional[str] = None, reason: Optional[str] = None):
        parts = [f"row={row_index}", f"action={action}"]
        if model:
            parts.append(f"model={model}")
        if official_id:
            parts.append(f"id={official_id}")
        if reason:
            parts.append(f"reason={reason}")
        self.info(" | ".join(parts), row=row_index, action=action)
