from flask import Blueprint, abort, current_app, jsonify, request
from app.services import dostepne_regiony, policz_wskazniki

api_bp = Blueprint("api", __name__)


@api_bp.get("/kpi")
def kpi_json():
    path = current_app.config["SCIEZKA_DANYCH"]
    region = request.args.get("region")
    regiony = dostepne_regiony(path)

    if region and region not in regiony:
        abort(404, description=f"Nieznany region: {region}")

    stats = policz_wskazniki(path, region)
    return jsonify(stats)