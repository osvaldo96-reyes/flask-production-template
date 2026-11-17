"""Logs en JSON (una línea por evento) con el request id que asigna Nginx."""

import json
import logging
import sys
import time

from flask import Flask, Response, g, request


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        entry.update(getattr(record, "extra_fields", {}))
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)


def init_request_logging(app: Flask) -> None:
    log = logging.getLogger("http")

    @app.before_request
    def _request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID", "-")
        g.log_start = time.perf_counter()

    @app.after_request
    def _access_log(response: Response) -> Response:
        if request.path not in ("/healthz", "/metrics"):  # sin ruido de sondas
            log.info(
                "request",
                extra={
                    "extra_fields": {
                        "request_id": g.get("request_id", "-"),
                        "method": request.method,
                        "path": request.path,
                        "status": response.status_code,
                        "duration_ms": round(
                            (time.perf_counter() - g.get("log_start", 0)) * 1000, 1
                        ),
                        "remote_addr": request.remote_addr,
                    }
                },
            )
        response.headers["X-Request-ID"] = g.get("request_id", "-")
        return response
