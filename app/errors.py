# app/errors.py
from flask import jsonify, request
from werkzeug.exceptions import HTTPException


def zarejestruj_obsluge_bledow(app):
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        if request.path.startswith("/api"):
            return jsonify({"blad": e.description, "kod": e.code}), e.code

        return (
            f"<h1>{e.code}</h1><p>Żądanie nie mogło zostać zrealizowane</p>",
            e.code,
        )