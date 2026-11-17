"""Fábrica de la aplicación Flask."""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import db
from .log import configure_logging, init_request_logging
from .metrics import init_metrics


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    configure_logging(app.config["LOG_LEVEL"])
    # Confía en un solo proxy (Nginx) para IP real, esquema y host
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)

    from .health import bp as health_bp
    from .notes import bp as notes_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(notes_bp, url_prefix="/api/notes")
    init_metrics(app)
    init_request_logging(app)

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException):
        return jsonify(error=err.name, detail=err.description), err.code

    @app.cli.command("init-db")
    def init_db() -> None:
        """Crea las tablas (lo ejecuta el servicio `migrate` antes de arrancar la app)."""
        db.create_all()
        app.logger.info("tablas creadas")

    return app
