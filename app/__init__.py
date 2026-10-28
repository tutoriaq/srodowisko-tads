# app/__init__.py
import logging
import time
from flask import Flask, g
from app.config import KONFIGURACJE
from app.converters import RegionConverter
from app.errors import zarejestruj_obsluge_bledow


def create_app(nazwa_konfiguracji="rozwojowa"):
    app = Flask(__name__)
    app.config.from_object(KONFIGURACJE[nazwa_konfiguracji])
    app.logger.setLevel(logging.INFO)

    # 1. Rejestracja konwertera (PRZED register_blueprint)
    app.url_map.converters["region"] = RegionConverter

    # 2. Procedury cyklu żądania (X-Czas-Ms)
    @app.before_request
    def start_timer():
        g.start_time = time.perf_counter()

    @app.after_request
    def add_time_header(response):
        if hasattr(g, "start_time"):
            elapsed_ms = (time.perf_counter() - g.start_time) * 1000
            response.headers["X-Czas-Ms"] = f"{elapsed_ms:.2f}"
        return response

    # 3. Rejestracja błędów
    zarejestruj_obsluge_bledow(app)

    # 4. Rejestracja blueprintów (w tym wersjonowanie api_v2)
    from app.routes_api import api_bp
    from app.routes_panel import panel_bp

    app.register_blueprint(panel_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(api_bp, url_prefix="/api/v2", name="api_v2")

    return app