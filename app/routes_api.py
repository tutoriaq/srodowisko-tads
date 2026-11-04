from flask import Blueprint, abort, current_app, jsonify, request
from app.decorators import wymagany_parametr
from app.services import (
    dostepne_regiony,
    policz_wskazniki,
    raporty_roku,
)
from app.validators import parametr_int

api_bp = Blueprint("api", __name__)


@api_bp.get("/kpi")
def kpi():
    path = current_app.config["SCIEZKA_DANYCH"]
    region = request.args.get("region")
    regiony = dostepne_regiony(path)

    # Walidacja regionu dla API: jeśli przekazano nieznany kod, rzucamy 404[cite: 7]
    if region and region not in regiony:
        abort(404, description=f"Nieznany region: {region}")

    stats = policz_wskazniki(path, region)
    return jsonify(stats)


@api_bp.get("/raporty")
@wymagany_parametr("rok")
def raporty():
    rok = parametr_int("rok", 2020, 2030)
    dane = raporty_roku(rok)
    return jsonify(rok=rok, raporty=dane)