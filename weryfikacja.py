"""Weryfikacja rezultatów ćwiczeń 4 (Szablony HTML i system Jinja2).

Plik należy umieścić w katalogu projektu srodowisko-tads (obok katalogu app/)
i uruchamiać przy aktywnym środowisku wirtualnym:

    python verify_ex4.py

Skrypt nie zmienia żadnych plików. Żądania wysyła bezpośrednio do obiektu aplikacji
(test_client), więc serwer nie musi być uruchomiony; zapisane w trakcie sprawdzania
raporty istnieją tylko w pamięci procesu skryptu. Można go uruchamiać po każdym
zadaniu — liczba sprawdzeń zgodnych powinna rosnąć. Nazwy w raporcie zapisano bez
znaków diakrytycznych, aby były czytelne w każdej konsoli.
"""

import importlib
import re
import sys
from datetime import date
from pathlib import Path

KORZEN = Path(__file__).resolve().parent
sys.path.insert(0, str(KORZEN))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

try:  # odpowiednik wczytywania pliku .env przez polecenie flask
    from dotenv import load_dotenv

    load_dotenv(KORZEN / ".env")
except ImportError:
    pass

TWARDA = "\u00a0"


class Brak(Exception):
    """Brak elementu wymaganego przez sprawdzenie; komunikat trafia do raportu."""


STAN = {"aplikacja": None, "uklad": None, "klient": None}
SPRAWDZENIA = []


def sprawdzenie(zadanie, opis):
    """Rejestruje funkcję sprawdzającą; funkcja zwraca (zgodne, szczegół)."""

    def dekorator(funkcja):
        SPRAWDZENIA.append((zadanie, opis, funkcja))
        return funkcja

    return dekorator


# ---------------------------------------------------------------- narzędzia

def zaladuj_aplikacje():
    try:
        modul = importlib.import_module("app")
    except Exception as blad:  # noqa: BLE001 — raport ma wskazać każdą przyczynę
        return None, f"import app: {type(blad).__name__}: {blad}"
    if not hasattr(modul, "create_app"):
        return None, "pakiet app nie zawiera funkcji create_app"
    try:
        return modul.create_app(), "pakiet app z funkcja create_app"
    except Exception as blad:  # noqa: BLE001
        return None, f"create_app(): {type(blad).__name__}: {blad}"


def wymagana_aplikacja():
    if STAN["klient"] is None:
        raise Brak(f"aplikacja niedostepna: {STAN['uklad']}")


def zadanie(adres, metoda="GET", **opcje):
    wymagana_aplikacja()
    return getattr(STAN["klient"], metoda.lower())(adres, **opcje)


def tresc(odp):
    return odp.get_data(as_text=True)


def zrodlo(sciezka):
    plik = KORZEN / "app" / "templates" / sciezka
    if not plik.is_file():
        raise Brak(f"brak pliku app/templates/{sciezka}")
    return plik.read_text(encoding="utf-8")


def filtr(nazwa):
    wymagana_aplikacja()
    funkcja = STAN["aplikacja"].jinja_env.filters.get(nazwa)
    if funkcja is None:
        raise Brak(f"brak filtru {nazwa}")
    return funkcja


def filtr_wlasny(nazwa):
    """Filtry wbudowane (np. 'length') nie liczą się jako filtry własne."""
    funkcja = filtr(nazwa)
    if getattr(funkcja, "__module__", "").startswith("jinja2"):
        raise Brak(f"filtr {nazwa} nie jest filtrem wlasnym")
    return funkcja


def panel(adres):
    odp = zadanie(adres)
    return odp.status_code, tresc(odp)


# ------------------------------------------------------------------ zadanie 1

@sprawdzenie(1, "Arkusz styles.css serwowany: 200 i text/css")
def _():
    odp = zadanie("/static/styles.css")
    return (odp.status_code, odp.mimetype) == (200, "text/css"), (odp.status_code, odp.mimetype)


@sprawdzenie(1, "Szablony: base, macros, panel, partials/navigation i messages")
def _():
    brakujace = [n for n in ("base.html", "macros.html", "panel.html", "partials/navigation.html", "partials/messages.html")
                 if not (KORZEN / "app" / "templates" / n).is_file()]
    return not brakujace, "komplet" if not brakujace else "brak: " + ", ".join(brakujace)


@sprawdzenie(1, "panel.html dziedziczy po base.html, bez wlasnego naglowka")
def _():
    kod = zrodlo("panel.html")
    zgodne = bool(re.search(r"\{%-?\s*extends\s+[\"']base\.html[\"']", kod)) and "<html" not in kod.lower()
    return zgodne, "extends base.html" if zgodne else "brak extends lub wlasny <html>"


@sprawdzenie(1, "Uklad wspolny: arkusz przez url_for, nav, main i footer")
def _():
    status, html = panel("/kpi?region=PL")
    elementy = ['href="/static/styles.css"', "<nav>", "<main>", "<footer>"]
    brakujace = [e for e in elementy if e not in html]
    return status == 200 and not brakujace, status if not brakujace else "brak: " + ", ".join(brakujace)


@sprawdzenie(1, "Tytul z bloku: <title>Wskazniki: PL · TADS</title>")
def _():
    status, html = panel("/kpi?region=PL")
    tytul = re.search(r"<title>([^<]*)</title>", html)
    zgodne = bool(tytul) and tytul.group(1).strip() == "Wskaźniki: PL · TADS"
    return zgodne, tytul.group(1).strip() if tytul else "brak <title>"


@sprawdzenie(1, "Cztery kafelki wygenerowane makrem kafelek")
def _():
    liczba = panel("/kpi?region=PL")[1].count('class="kafelek"')
    return liczba == 4, liczba


@sprawdzenie(1, "Tabela regionow: oceny z makra (CZ niska, DE norma, PL wysoka)")
def _():
    oceny = re.findall(r'class="ocena (\w+)"', panel("/kpi")[1])
    return oceny == ["niska", "norma", "wysoka"], oceny


@sprawdzenie(1, "Panel regionu /regiony/DE: naglowek Wskazniki: DE")
def _():
    status, html = panel("/regiony/DE")
    return status == 200 and "<h1>Wskaźniki: DE</h1>" in html, status


@sprawdzenie(1, "Makro ocena: parametr cel z wartoscia domyslna")
def _():
    wymagana_aplikacja()
    szablon = STAN["aplikacja"].jinja_env.from_string(
        '{% from "macros.html" import ocena %}{{ ocena(0.22) }}|{{ ocena(0.22, 0.2) }}'
    )
    wynik = szablon.render()
    domyslny, wlasny = wynik.split("|")
    zgodne = "w normie" in domyslny and "powyżej celu" in wlasny
    return zgodne, wynik.replace("\n", " ")[:40]


# ------------------------------------------------------------------ zadanie 2

@sprawdzenie(2, "Filtry wlasne zarejestrowane: zl, procent, liczba, data_pl")
def _():
    nazwy = ("zl", "procent", "liczba", "data_pl")
    wymagana_aplikacja()
    brakujace = [n for n in nazwy if n not in STAN["aplikacja"].jinja_env.filters]
    return not brakujace, "komplet" if not brakujace else "brak: " + ", ".join(brakujace)


@sprawdzenie(2, "Filtr liczba: 1234567.5 z jednym miejscem → 1 234 567,5")
def _():
    wynik = filtr_wlasny("liczba")(1234567.5, 1)
    return wynik == f"1{TWARDA}234{TWARDA}567,5", repr(wynik)


@sprawdzenie(2, "Filtr zl: 37900 → 37 900,00 zl (twarde spacje)")
def _():
    wynik = filtr_wlasny("zl")(37900)
    return wynik == f"37{TWARDA}900,00{TWARDA}zł", repr(wynik)


@sprawdzenie(2, "Filtr procent: 0.2639 → 26,4% oraz 26,39% dla dwoch miejsc")
def _():
    f = filtr_wlasny("procent")
    wynik = (f(0.2639), f(0.2639, 2))
    return wynik == ("26,4%", "26,39%"), wynik


@sprawdzenie(2, "Filtr data_pl: obiekt date i tekst RRRR-MM-DD → 08.01.2026")
def _():
    f = filtr_wlasny("data_pl")
    wynik = (f(date(2026, 1, 8)), f("2026-01-08"))
    return wynik == ("08.01.2026", "08.01.2026"), wynik


@sprawdzenie(2, "Kafelek Przychod dla PL: 37 900,00 zl")
def _():
    html = panel("/kpi?region=PL")[1]
    zgodne = f"<b>37{TWARDA}900,00{TWARDA}zł</b>" in html.replace("\n", "").replace("  ", "")
    return zgodne, "kafelek z filtrem zl" if zgodne else "brak sformatowanej kwoty"


@sprawdzenie(2, "Marza PL: 26,4% w kafelku i w tabeli")
def _():
    liczba = panel("/kpi?region=PL")[1].count("26,4%")
    return liczba >= 2, liczba


@sprawdzenie(2, "Procesor kontekstu: nawigacja z regionami CZ, DE, PL")
def _():
    html = panel("/kpi")[1]
    brakujace = [k for k in ("CZ", "DE", "PL") if f'href="/regiony/{k}"' not in html]
    return not brakujace, "komplet" if not brakujace else "brak: " + ", ".join(brakujace)


@sprawdzenie(2, "Procesor kontekstu: stopka z biezacym rokiem")
def _():
    html = panel("/kpi")[1]
    stopka = re.search(r"<footer>(.*?)</footer>", html, re.S)
    rok = str(date.today().year)
    zgodne = bool(stopka) and rok in stopka.group(1)
    return zgodne, rok if zgodne else "brak roku w stopce"


@sprawdzenie(2, "Aktywny region wyrozniony w nawigacji")
def _():
    def aktywne(adres):
        html = panel(adres)[1]
        return re.findall(r'<a[^>]*class="aktywna"[^>]*>\s*(\w+)\s*</a>', html)
    wynik = (aktywne("/regiony/DE"), aktywne("/kpi?region=PL"))
    return wynik == (["DE"], ["PL"]), wynik


@sprawdzenie(2, "Data w panelu w formacie DD.MM.RRRR (Stan na dzien)")
def _():
    html = panel("/kpi")[1]
    dopasowanie = re.search(r"Stan na dzień (\d{2}\.\d{2}\.\d{4})", html)
    zgodne = bool(dopasowanie) and dopasowanie.group(1) == date.today().strftime("%d.%m.%Y")
    return zgodne, dopasowanie.group(1) if dopasowanie else "brak daty"


@sprawdzenie(2, "Filtry wbudowane: Regiony w zbiorze: 3 (CZ, DE, PL)")
def _():
    html = panel("/kpi")[1]
    zgodne = "Regiony w zbiorze: 3 (CZ, DE, PL)" in html
    return zgodne, "tak" if zgodne else "brak wiersza z liczba regionow"


# ------------------------------------------------------------------ zadanie 3

def zapisz(rok, region):
    odp = zadanie("/raporty/nowy", "POST", data={"rok": str(rok), "region": region})
    return odp


@sprawdzenie(3, "Zapis raportu: 303 i komunikat flash na stronie raportu")
def _():
    odp = zapisz(2027, "PL")
    lokalizacja = (odp.headers.get("Location") or "").replace("http://localhost", "")
    html = tresc(zadanie("/raporty/2027"))
    komunikat = '<p class="komunikat sukces">Raport za rok 2027 został zapisany</p>'
    zgodne = (odp.status_code, lokalizacja) == (303, "/raporty/2027") and komunikat in html
    return zgodne, (odp.status_code, "komunikat" if komunikat in html else "brak komunikatu")


@sprawdzenie(3, "Komunikat flash widoczny raz, potem zuzyty")
def _():
    zapisz(2028, "DE")
    pierwszy = tresc(zadanie("/raporty/2028"))
    drugi = tresc(zadanie("/raporty/2028"))
    zgodne = "został zapisany" in pierwszy and "został zapisany" not in drugi
    return zgodne, "raz" if zgodne else "komunikat nie wyswietlony raz"


@sprawdzenie(3, "Strona raportu z szablonu: tytul i licznik zapisanych raportow")
def _():
    html = tresc(zadanie("/raporty/2027"))
    tytul = re.search(r"<title>([^<]*)</title>", html)
    zgodne = bool(tytul) and tytul.group(1).strip() == "Raport 2027 · TADS" and "Zapisane raporty: 1" in html
    return zgodne, tytul.group(1).strip() if tytul else "brak <title>"


@sprawdzenie(3, "Blad 404 dla przegladarki: strona z szablonu")
def _():
    odp = zadanie("/kpi?region=XX")
    html = tresc(odp)
    tytul = re.search(r"<title>([^<]*)</title>", html)
    zgodne = (
        odp.status_code == 404 and bool(tytul) and tytul.group(1).strip() == "Błąd 404 · TADS"
        and "<h1>404</h1>" in html and "<p>Nieznany region: XX</p>" in html
    )
    return zgodne, odp.status_code


@sprawdzenie(3, "Strona bledu zachowuje nawigacje i stopke")
def _():
    html = tresc(zadanie("/kpi?region=XX"))
    zgodne = "<nav>" in html and "<footer>" in html and "<h1>404</h1>" in html
    return zgodne, "nav i footer" if zgodne else "brak ukladu wspolnego"


@sprawdzenie(3, "Blad 404 w /api: dokument JSON obok strony HTML")
def _():
    html = tresc(zadanie("/kpi?region=XX"))
    odp = zadanie("/api/kpi?region=XX")
    dane = odp.get_json(silent=True) or {}
    zgodne = (
        "<h1>404</h1>" in html and "<p>Nieznany region: XX</p>" in html
        and odp.status_code == 404 and dane.get("kod") == 404 and bool(dane.get("blad"))
    )
    return zgodne, f"{odp.status_code} {odp.mimetype}"


@sprawdzenie(3, "Escapowanie: region=<script> daje encje, bez znacznika")
def _():
    odp = zadanie("/kpi?region=%3Cscript%3E")
    html = tresc(odp)
    zgodne = odp.status_code == 404 and "&lt;script&gt;" in html and "<script>" not in html
    return zgodne, odp.status_code


@sprawdzenie(3, "Nieistniejacy adres: strona bledu z nawigacja, bez wyjatku")
def _():
    odp = zadanie("/nie-ma-takiego-adresu")
    html = tresc(odp)
    zgodne = odp.status_code == 404 and "<h1>404</h1>" in html and "<nav>" in html
    return zgodne, odp.status_code


# --------------------------------------------------------------------- raport

def main():
    STAN["aplikacja"], STAN["uklad"] = zaladuj_aplikacje()
    if STAN["aplikacja"] is not None:
        STAN["klient"] = STAN["aplikacja"].test_client()

    print("Weryfikacja cwiczen 4")
    print(f"Katalog: {KORZEN}")
    print(f"Uklad aplikacji: {STAN['uklad']}")
    razem = {}
    biezace = None
    for numer, opis, funkcja in SPRAWDZENIA:
        if numer != biezace:
            print("-" * 74)
            biezace = numer
        try:
            zgodne, szczegol = funkcja()
        except Exception as blad:  # noqa: BLE001 — każdy wyjątek to wynik niezgodny
            zgodne = False
            szczegol = str(blad) if isinstance(blad, Brak) else f"{type(blad).__name__}: {blad}"
        zgodne = bool(zgodne)
        szczegol = str(szczegol).replace("\n", " ")[:40]
        print(f"[{'OK  ' if zgodne else 'BLAD'}] Z{numer} {opis:62s} {szczegol}")
        razem.setdefault(numer, []).append(zgodne)
    print("-" * 74)
    for numer in sorted(razem):
        print(f"Zadanie {numer}: {sum(razem[numer])}/{len(razem[numer])}")
    zgodne = sum(sum(w) for w in razem.values())
    wszystkie = sum(len(w) for w in razem.values())
    print(f"Sprawdzenia zakonczone powodzeniem: {zgodne}/{wszystkie}")
    return 0 if zgodne == wszystkie else 1


if __name__ == "__main__":
    sys.exit(main())
