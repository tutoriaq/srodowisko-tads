from datetime import date


def liczba(wartosc, miejsca=0):
    tekst = f"{wartosc:,.{miejsca}f}"
    return tekst.replace(",", "\u00a0").replace(".", ",")


def zl(wartosc):
    return f"{liczba(wartosc, 2)}\u00a0zł"


def procent(wartosc, miejsca=1):
    return f"{wartosc * 100:.{miejsca}f}".replace(".", ",") + "%"


def data_pl(wartosc):
    """Przyjmuje obiekt date albo tekst RRRR-MM-DD; zwraca DD.MM.RRRR."""
    if isinstance(wartosc, str):
        wartosc = date.fromisoformat(wartosc)
    return wartosc.strftime("%d.%m.%Y")


def zarejestruj_filtry(app):
    for funkcja in (liczba, zl, procent, data_pl):
        app.add_template_filter(funkcja, funkcja.__name__)