"""Sondas de salud para Docker, balanceadores y Kubernetes."""

from flask import Blueprint, jsonify
from sqlalchemy import text

from .extensions import db

bp = Blueprint("health", __name__)


@bp.get("/healthz")
def liveness():
    """Liveness: el proceso responde. No toca dependencias externas."""
    return jsonify(status="ok")


@bp.get("/readyz")
def readiness():
    """Readiness: la app puede atender tráfico (la base de datos responde)."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de BD = no listo
        return jsonify(status="unavailable", database=type(exc).__name__), 503
    return jsonify(status="ready", database="ok")
