"""Configuración de Gunicorn para contenedores."""

import os
import shutil

bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = 30
graceful_timeout = 20  # termina las peticiones en curso al recibir SIGTERM
keepalive = 5
max_requests = 1000  # recicla workers: evita fugas de memoria a largo plazo
max_requests_jitter = 100
worker_tmp_dir = "/tmp"  # noqa: S108 - tmpfs en memoria dentro del contenedor (read_only)
accesslog = None  # la app escribe su propio access log en JSON
errorlog = "-"


def on_starting(server):
    # Limpia métricas de una ejecución anterior (modo multiproceso de prometheus_client)
    path = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if path:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path, exist_ok=True)


def child_exit(server, worker):
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(worker.pid)
