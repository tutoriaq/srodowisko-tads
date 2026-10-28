from flask import Blueprint, abort, current_app, redirect, request, url_for
from app.services import dostepne_regiony, policz_wskazniki, raporty_roku, zapisz_raport

panel_bp = Blueprint("panel", __name__)

ROK_DOMYSLNY = 2026


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


@panel_bp.get("/regiony/<region:kod>")
def region(kod):
    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)

    if kod not in regiony:
        abort(404, description=f"Nieznany region: {kod}")
    
    stats = policz_wskazniki(path, kod)
    liczba = stats.get("zamowienia", 0)
    
    return f"<h1>Region {kod}</h1><p>Zamówień: {liczba}</p>"


@panel_bp.get("/raporty/", defaults={"rok": ROK_DOMYSLNY})
@panel_bp.get("/raporty/<int(min=2020, max=2030):rok>")
def raport(rok):
    raporty = raporty_roku(rok)
    n = len(raporty)
    return f"<h1>Raport {rok}</h1><p>Zapisane raporty: {n}</p>"


@panel_bp.route("/raporty/nowy", methods=["GET", "POST"])
def nowy_raport():
    if request.method == "GET":
        return "Instrukcja zapisu raportu"
    
    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)
    
    rok_raw = request.form.get("rok", type=int)
    region_val = request.form.get("region")

    # Walidacja danych formularza
    if rok_raw is None or region_val not in regiony:
        abort(400, description="Niepoprawne dane formularza")
    
    if not (2020 <= rok_raw <= 2030):
        abort(422, description="Rok poza zakresem 2020-2030")

    zapisz_raport(rok_raw, region_val)
    return redirect(url_for("panel.raport", rok=rok_raw), code=303)


@panel_bp.get("/stary-panel")
def stary_panel():
    return redirect(url_for("panel.kpi"), code=301)