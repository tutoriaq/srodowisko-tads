from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException


def obsluz_blad(blad):
    # Pobieramy kod i opis błędu
    if isinstance(blad, HTTPException):
        kod = blad.code
        opis = blad.description
    else:
        kod = 500
        opis = "Wewnętrzny błąd serwera"

    # Dla zapytań pod ścieżki /api używamy jsonify, aby wymusić typ application/json[cite: 7, 18]
    if request.path.startswith("/api"):
        return jsonify({"blad": opis, "kod": kod}), kod

    # Dla standardowych widoków zwracamy szablon HTML z kodem statusu[cite: 7]
    return render_template("errors/error.html", kod=kod, opis=opis), kod


def zarejestruj_obsluge_bledow(app):
    app.register_error_handler(HTTPException, obsluz_blad)
    app.register_error_handler(Exception, obsluz_blad)