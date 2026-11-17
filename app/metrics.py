"""Métricas Prometheus compatibles con varios workers de Gunicorn (modo multiproceso)."""

import os
import time

from flask import Blueprint, Flask, Response, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)

REQUESTS = Counter(
    "http_requests_total", "Peticiones HTTP atendidas", ["method", "endpoint", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "Latencia de las peticiones HTTP", ["method", "endpoint"]
)

bp = Blueprint("metrics", __name__)


@bp.get("/metrics")
def metrics() -> Response:
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = REGISTRY
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


def init_metrics(app: Flask) -> None:
    @app.before_request
    def _start_timer() -> None:
        g.start_time = time.perf_counter()

    @app.after_request
    def _record(response: Response) -> Response:
        # Se etiqueta por regla de ruta (/api/notes/<int:note_id>), no por URL: cardinalidad acotada
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        if endpoint != "/metrics":
            elapsed = time.perf_counter() - g.get("start_time", time.perf_counter())
            LATENCY.labels(request.method, endpoint).observe(elapsed)
            REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
        return response

    app.register_blueprint(bp)
