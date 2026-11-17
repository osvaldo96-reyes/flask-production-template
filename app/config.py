"""Configuración 12-factor: todo sale de variables de entorno."""

import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # descarta conexiones muertas (reinicios de la BD)
        "pool_recycle": 1800,
    }
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    JSON_SORT_KEYS = False
