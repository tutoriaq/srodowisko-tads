from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
    flash,
)
from app.services import (
    dostepne_regiony,
    policz_wskazniki,
    raporty_roku,
    zapisz_raport,
    zestawienie_regionow,
    wykaz_raportow,
    wczytaj_zbior,  # <--- TUTAJ DODANO IMPORT
)
from app.forms import FiltrForm, RaportForm, ZbiorForm
from datetime import date
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed, FileField, FileRequired

panel_bp = Blueprint("panel", __name__)

ROK_DOMYSLNY = 2026


@panel_bp.get("/")
def index():
    return redirect(url_for("panel.kpi"))


@panel_bp.get("/kpi")
def kpi():
    path = current_app.config["SCIEZKA_DANYCH"]
    formularz = FiltrForm(request.args)
    regiony = dostepne_regiony(path)
    
    # Konfiguracja listy wyboru regionów (pusta opcja + dostępne regiony)
    formularz.region.choices = [("", "wszystkie")] + [(r, r) for r in regiony]

    region = rok = None
    if formularz.validate():
        region = formularz.region.data or None
        rok = formularz.rok.data or None
    else:
        flash("Kryteria zawężenia zostały pominięte", "warning")

    stats = policz_wskazniki(path, region, rok)
    zestawienie = zestawienie_regionow(path)

    return render_template(
        "panel.html",
        formularz=formularz,
        wskazniki=stats,
        zestawienie=zestawienie,
        dzisiaj=date.today()
    )


@panel_bp.get("/regiony/<kod>")
def region(kod):
    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)

    if kod not in regiony:
        abort(404, description=f"Nieznany region: {kod}")

    stats = policz_wskazniki(path, kod)
    zestawienie = zestawienie_regionow(path)

    return render_template(
        "panel.html",
        wskazniki=stats,
        zestawienie=zestawienie,
        dzisiaj=date.today()
    )


@panel_bp.get("/raporty/", defaults={"rok": ROK_DOMYSLNY})
@panel_bp.get("/raporty/<int(min=2020, max=2030):rok>")
def raport(rok):
    raporty = raporty_roku(rok)
    return render_template("report.html", rok=rok, zapisane=raporty)


@panel_bp.route("/raporty/nowy", methods=["GET", "POST"])
def nowy_raport():
    path = current_app.config["SCIEZKA_DANYCH"]
    regiony = dostepne_regiony(path)

    istniejace = {(r["rok"], r["region"]) for r in wykaz_raportow()}
    formularz = RaportForm(istniejace=istniejace)
    formularz.region.choices = [(r, r) for r in regiony]

    if formularz.validate_on_submit():
        zapisz_raport(formularz.rok.data, formularz.region.data, formularz.uwagi.data)
        flash(f"Raport za rok {formularz.rok.data} zapisany", "success")
        return redirect(url_for("panel.raport", rok=formularz.rok.data), code=303)

    status = 422 if formularz.errors else 200
    return render_template("new_report.html", formularz=formularz), status


@panel_bp.get("/stary-panel")
def stary_panel():
    return redirect(url_for("panel.kpi"), code=301)


@panel_bp.route("/wczytaj", methods=["GET", "POST"])
def wczytaj():
    formularz = ZbiorForm()
    if formularz.validate_on_submit():
        plik = formularz.plik.data
        nazwa = secure_filename(plik.filename)
        try:
            liczba = wczytaj_zbior(plik.stream)
            flash(f"Wczytano {liczba} zamówień z pliku {nazwa}", "success")
            return redirect(url_for("panel.wczytaj"), 303)
        except ValueError as blad:
            formularz.plik.errors.append(f"Niepoprawna zawartość: {blad}")

    status = 422 if formularz.errors else 200
    return render_template("upload.html", formularz=formularz), status