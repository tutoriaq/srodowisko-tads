from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from app.services import (
    dostepne_regiony,
    policz_wskazniki,
    raporty_roku,
    zapisz_raport,
    zestawienie_regionow,
)

panel_bp = Blueprint("panel", __name__)

ROK_DOMYSLNY = 2026


@panel_bp.get("/")
def index():
    return redirect(url_for("panel.kpi"))


@panel_bp.get("/kpi")
def kpi():
    path = current_app.config["SCIEZKA_DANYCH"]
    region = request.args.get("region")
    regiony = dostepne_regiony(path)

    if region and region not in regiony:
        abort(404, description=f"Nieznany region: {region}")[cite: 7]

    stats = policz_wskazniki(path, region)
    zestawienie = zestawienie_regionow(path)[cite: 4]

    return render_template(
        "panel.html",
        wskazniki=stats,
        zestawienie=zestawienie
    )[cite: 4]


@panel_bp.get("/regiony/<kod>")
def region(kod):
    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)

    if kod not in regiony:
        abort(404, description=f"Nieznany region: {kod}")[cite: 7]

    stats = policz_wskazniki(path, kod)
    zestawienie = zestawienie_regionow(path)[cite: 4]

    return render_template(
        "panel.html",
        wskazniki=stats,
        zestawienie=zestawienie
    )[cite: 4]


@panel_bp.get("/raporty/", defaults={"rok": ROK_DOMYSLNY})
@panel_bp.get("/raporty/<int(min=2020, max=2030):rok>")
def raport(rok):
    raporty = raporty_roku(rok)
    return render_template("report.html", rok=rok, zapisane=raporty)[cite: 6]


@panel_bp.route("/raporty/nowy", methods=["GET", "POST"])
def nowy_raport():
    if request.method == "GET":
        return "Instrukcja zapisu raportu"

    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)

    rok_raw = request.form.get("rok", type=int)
    region_val = request.form.get("region")

    if rok_raw is None or region_val not in regiony:
        abort(400, description="Niepoprawne dane formularza")

    if not (2020 <= rok_raw <= 2030):
        abort(422, description="Rok poza zakresem 2020-2030")

    zapisz_raport(rok_raw, region_val)
    return redirect(url_for("panel.raport", rok=rok_raw), code=303)


@panel_bp.get("/stary-panel")
def stary_panel():
    return redirect(url_for("panel.kpi"), code=301)