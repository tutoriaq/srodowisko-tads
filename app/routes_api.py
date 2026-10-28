# app/routes_api.py
from flask import Blueprint, jsonify
from app.decorators import wymagany_parametr
from app.services import raporty_roku
from app.validators import parametr_int

api_bp = Blueprint("api", __name__)


@api_bp.get("/kpi")
def kpi():
    return jsonify({"stan": "ok"})


@api_bp.get("/raporty")
@wymagany_parametr("rok")
def raporty():
    rok = parametr_int("rok", 2020, 2030)
    dane = raporty_roku(rok)
    return jsonify(rok=rok, raporty=dane)