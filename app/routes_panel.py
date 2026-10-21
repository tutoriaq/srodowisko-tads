from flask import Blueprint, abort, current_app, request
from app.services import dostepne_regiony, policz_wskazniki

panel_bp = Blueprint("panel", __name__)


@panel_bp.get("/")
def index():
    return "Panel wskaźników"


@panel_bp.get("/kpi")
def kpi():
    path = current_app.config["SCIEZKA_DANYCH"]
    region = request.args.get("region")
    regiony = dostepne_regiony(path)

    if region and region not in regiony:
        abort(404, description=f"Nieznany region: {region}")

    stats = policz_wskazniki(path, region)
    current_app.logger.info(
        "Obliczono wskaźniki dla regionu %s", stats["region"]
    )

    marza_pct = f"{stats['marza']:.2%}"
    reg_label = region if region else "Wszystkie"

    return f"<h1>wskaźniki: {reg_label}</h1><p>marża: {marza_pct}</p>"