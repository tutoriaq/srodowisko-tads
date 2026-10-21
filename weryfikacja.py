"""Weryfikacja rezultatów ćwiczeń 2 (Podstawy Flask).

Plik należy umieścić w katalogu projektu srodowisko-tads (obok katalogu app/ lub
pliku app.py) i uruchamiać przy aktywnym środowisku wirtualnym:

    python weryfikacja.py

Skrypt nie zmienia żadnych plików. Sprawdza stan projektu oraz zachowanie aplikacji:
żądania wysyłane są bezpośrednio do obiektu aplikacji (test_client), więc serwer nie
musi być uruchomiony. Można go uruchamiać po każdym zadaniu — liczba sprawdzeń
zgodnych powinna rosnąć. Nazwy w raporcie zapisano bez znaków diakrytycznych,
aby były czytelne w każdej konsoli.
"""

import csv
import importlib
import importlib.util
import logging
import re
import subprocess
import sys
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

def czytaj(sciezka):
    plik = KORZEN / sciezka
    return plik.read_text(encoding="utf-8") if plik.is_file() else ""


def polecenie_git(*argumenty):
    try:
        wynik = subprocess.run(
            ["git", *argumenty], capture_output=True, text=True, cwd=KORZEN
        )
    except OSError:
        return None
    return wynik.stdout.strip() if wynik.returncode == 0 else None


def zaladuj_aplikacje():
    """Zwraca (aplikacja, opis układu) albo (None, powód niepowodzenia)."""
    try:
        modul = importlib.import_module("app")
    except Exception as blad:  # noqa: BLE001 — raport ma wskazać każdą przyczynę
        return None, f"import app: {type(blad).__name__}: {blad}"
    if hasattr(modul, "create_app"):
        try:
            return modul.create_app(), "pakiet app z funkcja create_app"
        except Exception as blad:  # noqa: BLE001
            return None, f"create_app(): {type(blad).__name__}: {blad}"
    obiekt = getattr(modul, "app", None)
    if obiekt is not None and hasattr(obiekt, "test_client"):
        return obiekt, "modul app.py z obiektem app"
    return None, "modul app nie zawiera obiektu app ani funkcji create_app"


def sciezka_danych():
    aplikacja = STAN["aplikacja"]
    if aplikacja is not None and aplikacja.config.get("SCIEZKA_DANYCH"):
        return str(aplikacja.config["SCIEZKA_DANYCH"])
    return str(KORZEN / "dane" / "zamowienia.csv")


def modul_uslug():
    """Odnajduje moduł warstwy usług: app.services albo services w katalogu głównym."""
    for nazwa in ("app.services", "services"):
        if importlib.util.find_spec(nazwa.split(".")[0]) is None:
            continue
        try:
            return importlib.import_module(nazwa)
        except ModuleNotFoundError:
            continue
    raise Brak("brak pliku services.py (ani app/services.py)")


def fabryka():
    modul = importlib.import_module("app")
    if not hasattr(modul, "create_app"):
        raise Brak("brak funkcji create_app w pakiecie app")
    return modul.create_app


def zadanie(adres, **opcje):
    return STAN["klient"].get(adres, **opcje)


def wymagana_aplikacja():
    if STAN["klient"] is None:
        raise Brak(f"aplikacja niedostepna: {STAN['uklad']}")


# ------------------------------------------------------------------ zadanie 1

@sprawdzenie(1, "Flask dostepny w srodowisku")
def _():
    spec = importlib.util.find_spec("flask")
    if spec is None:
        return False, "brak pakietu flask"
    from importlib import metadata

    return True, metadata.version("flask")


@sprawdzenie(1, "requirements.txt zawiera Flask i python-dotenv")
def _():
    tresc = czytaj("requirements.txt").lower()
    zgodne = "flask" in tresc and "python-dotenv" in tresc
    return zgodne, "ok" if zgodne else "brak pozycji w pliku"


@sprawdzenie(1, "Plik .gitignore wyklucza .env")
def _():
    wpisy = [w.strip() for w in czytaj(".gitignore").splitlines()]
    zgodne = ".env" in wpisy
    return zgodne, ".gitignore" if zgodne else "brak wpisu .env"


@sprawdzenie(1, "Aplikacja Flask daje sie zaladowac")
def _():
    return STAN["aplikacja"] is not None, STAN["uklad"]


@sprawdzenie(1, "Adres / zwraca kod 200")
def _():
    wymagana_aplikacja()
    kod = zadanie("/").status_code
    return kod == 200, kod


@sprawdzenie(1, "Adres / zwraca tekst Panel wskaznikow")
def _():
    wymagana_aplikacja()
    tresc = zadanie("/").get_data(as_text=True)
    return "Panel wskaźników" in tresc, tresc[:40]


# ------------------------------------------------------------------ zadanie 2

@sprawdzenie(2, "Zbior dane/zamowienia.csv zgodny z trescia cwiczen")
def _():
    sciezka = KORZEN / "dane" / "zamowienia.csv"
    if not sciezka.is_file():
        return False, "brak pliku dane/zamowienia.csv"
    with open(sciezka, encoding="utf-8", newline="") as plik:
        wiersze = list(csv.DictReader(plik))
    przychod = round(sum(float(w["przychod"]) for w in wiersze), 2)
    koszt = round(sum(float(w["koszt"]) for w in wiersze), 2)
    regiony = sorted({w["region"] for w in wiersze})
    zgodne = (len(wiersze), przychod, koszt, regiony) == (8, 108850.0, 82100.0, ["CZ", "DE", "PL"])
    return zgodne, f"{len(wiersze)} wierszy, przychod {przychod}, koszt {koszt}"


@sprawdzenie(2, "Modul services nie importuje biblioteki Flask")
def _():
    modul = modul_uslug()
    zrodlo = Path(modul.__file__).read_text(encoding="utf-8")
    zawiera = re.search(r"^\s*(from|import)\s+flask", zrodlo, re.MULTILINE)
    return zawiera is None, modul.__name__


@sprawdzenie(2, "dostepne_regiony zwraca CZ, DE, PL")
def _():
    wynik = modul_uslug().dostepne_regiony(sciezka_danych())
    return list(wynik) == ["CZ", "DE", "PL"], list(wynik)


@sprawdzenie(2, "policz_wskazniki dla regionu PL")
def _():
    w = modul_uslug().policz_wskazniki(sciezka_danych(), "PL")
    oczekiwane = (3, 37900.0, 27900.0, 0.2639)
    otrzymane = (w["liczba_zamowien"], w["przychod"], w["koszt"], w["marza"])
    return otrzymane == oczekiwane, otrzymane


@sprawdzenie(2, "policz_wskazniki dla calego zbioru")
def _():
    w = modul_uslug().policz_wskazniki(sciezka_danych())
    oczekiwane = (8, 108850.0, 82100.0, 0.2458)
    otrzymane = (w["liczba_zamowien"], w["przychod"], w["koszt"], w["marza"])
    return otrzymane == oczekiwane, otrzymane


@sprawdzenie(2, "Region bez zamowien: marza 0.0 bez wyjatku")
def _():
    w = modul_uslug().policz_wskazniki(sciezka_danych(), "XX")
    return w["marza"] == 0.0, w["marza"]


@sprawdzenie(2, "Adres /kpi zwraca tekst HTML z kodem 200")
def _():
    wymagana_aplikacja()
    odp = zadanie("/kpi")
    zgodne = odp.status_code == 200 and odp.mimetype == "text/html"
    return zgodne, f"{odp.status_code} {odp.mimetype}"


@sprawdzenie(2, "Adres /kpi?region=PL zawiera region i marze")
def _():
    wymagana_aplikacja()
    tresc = zadanie("/kpi?region=PL").get_data(as_text=True)
    zgodne = "PL" in tresc and ("26.39" in tresc or "0.2639" in tresc)
    return zgodne, tresc[:60]


@sprawdzenie(2, "Adres /api/kpi?region=PL zwraca poprawny JSON")
def _():
    wymagana_aplikacja()
    odp = zadanie("/api/kpi?region=PL")
    if odp.mimetype != "application/json":
        return False, f"{odp.status_code} {odp.mimetype}"
    dane = odp.get_json()
    zgodne = odp.status_code == 200 and dane.get("marza") == 0.2639 and dane.get("liczba_zamowien") == 3
    return zgodne, dane


@sprawdzenie(2, "API: region PL daje 200, nieznany region XX daje 404")
def _():
    wymagana_aplikacja()
    kody = (zadanie("/api/kpi?region=PL").status_code, zadanie("/api/kpi?region=XX").status_code)
    return kody == (200, 404), kody


@sprawdzenie(2, "Panel: region PL daje 200, nieznany region XX daje 404")
def _():
    wymagana_aplikacja()
    kody = (zadanie("/kpi?region=PL").status_code, zadanie("/kpi?region=XX").status_code)
    return kody == (200, 404), kody


@sprawdzenie(2, "Odpowiedz 404 zawiera opis przyczyny z kodem regionu")
def _():
    wymagana_aplikacja()
    odp = zadanie("/kpi?region=XX")
    tresc = odp.get_data(as_text=True)
    return odp.status_code == 404 and "XX" in tresc, "opis w tresci" if "XX" in tresc else "brak opisu w tresci"


# ------------------------------------------------------------------ zadanie 3

@sprawdzenie(3, "Pakiet app z funkcja create_app (bez pliku app.py)")
def _():
    pakiet = (KORZEN / "app" / "__init__.py").is_file()
    modul = (KORZEN / "app.py").is_file()
    return pakiet and not modul, ("pakiet app/" if pakiet else "brak pakietu") + (", istnieje app.py" if modul else "")


@sprawdzenie(3, "Pliki pakietu: config, services, routes_panel, routes_api")
def _():
    brakujace = [n for n in ("config", "services", "routes_panel", "routes_api") if not (KORZEN / "app" / f"{n}.py").is_file()]
    return not brakujace, "komplet" if not brakujace else "brak: " + ", ".join(brakujace)


@sprawdzenie(3, "config.py: Config, RozwojowaConfig, KONFIGURACJE")
def _():
    if not (KORZEN / "app" / "config.py").is_file():
        raise Brak("brak pliku app/config.py")
    config = importlib.import_module("app.config")
    zgodne = (
        all(hasattr(config.Config, a) for a in ("SECRET_KEY", "SCIEZKA_DANYCH", "DEBUG"))
        and config.Config.DEBUG is False
        and config.RozwojowaConfig.DEBUG is True
        and {"rozwojowa", "produkcyjna"} <= set(config.KONFIGURACJE)
    )
    return zgodne, sorted(config.KONFIGURACJE)


@sprawdzenie(3, "create_app('rozwojowa'): DEBUG wlaczony")
def _():
    wartosc = fabryka()("rozwojowa").config["DEBUG"]
    return wartosc is True, wartosc


@sprawdzenie(3, "create_app('produkcyjna'): DEBUG wylaczony")
def _():
    wartosc = fabryka()("produkcyjna").config["DEBUG"]
    return wartosc is False, wartosc


@sprawdzenie(3, ".env.example wymienia zmienne bez wartosci klucza")
def _():
    linie = [l.strip() for l in czytaj(".env.example").splitlines()]
    zgodne = "SECRET_KEY=" in linie and any(l.startswith("FLASK_DEBUG=") for l in linie)
    return zgodne, ".env.example" if czytaj(".env.example") else "brak pliku"


@sprawdzenie(3, "Plik .env zawiera klucz SECRET_KEY (min. 32 znaki)")
def _():
    for linia in czytaj(".env").splitlines():
        if linia.startswith("SECRET_KEY="):
            dlugosc = len(linia.split("=", 1)[1].strip())
            return dlugosc >= 32, f"dlugosc {dlugosc}"
    return False, "brak wpisu SECRET_KEY w .env"


@sprawdzenie(3, "Plik .env nie jest sledzony przez Git")
def _():
    if not (KORZEN / ".env").is_file():
        raise Brak("brak pliku .env")
    sledzone = polecenie_git("ls-files", ".env")
    if sledzone is None:
        return False, "brak repozytorium Git"
    return sledzone == "", "nie sledzony" if sledzone == "" else "sledzony"


@sprawdzenie(3, "Aplikacja wczytuje SECRET_KEY ze srodowiska")
def _():
    wymagana_aplikacja()
    return bool(STAN["aplikacja"].config.get("SECRET_KEY")), "niepusty" if STAN["aplikacja"].config.get("SECRET_KEY") else "pusty"


@sprawdzenie(3, "Zarejestrowane blueprinty: api i panel")
def _():
    wymagana_aplikacja()
    nazwy = sorted(STAN["aplikacja"].blueprints)
    return nazwy == ["api", "panel"], nazwy


@sprawdzenie(3, "Adresy: /api/kpi z przedrostkiem, widoki api.kpi i panel.kpi")
def _():
    wymagana_aplikacja()
    aplikacja = STAN["aplikacja"]
    wzorce = {str(r) for r in aplikacja.url_map.iter_rules()}
    widoki = set(aplikacja.view_functions)
    zgodne = "/api/kpi" in wzorce and {"api.kpi", "panel.kpi"} <= widoki
    return zgodne, sorted(w for w in widoki if w.endswith(".kpi"))


@sprawdzenie(3, "Poziom dziennika aplikacji ustawiony na INFO")
def _():
    wymagana_aplikacja()
    poziom = STAN["aplikacja"].logger.level
    return poziom == logging.INFO, logging.getLevelName(poziom)


@sprawdzenie(3, "Widok /kpi zapisuje w dzienniku komunikat INFO z regionem")
def _():
    wymagana_aplikacja()

    class Zbieracz(logging.Handler):
        def __init__(self):
            super().__init__(level=logging.DEBUG)
            self.rekordy = []

        def emit(self, rekord):
            self.rekordy.append(rekord)

    zbieracz = Zbieracz()
    dziennik = STAN["aplikacja"].logger
    dziennik.addHandler(zbieracz)
    try:
        zadanie("/kpi?region=PL")
    finally:
        dziennik.removeHandler(zbieracz)
    info = [r for r in zbieracz.rekordy if r.levelno == logging.INFO and "PL" in r.getMessage()]
    return bool(info), info[0].getMessage() if info else "brak komunikatu INFO z regionem PL"


# --------------------------------------------------------------------- raport

def main():
    STAN["aplikacja"], STAN["uklad"] = zaladuj_aplikacje()
    if STAN["aplikacja"] is not None:
        STAN["klient"] = STAN["aplikacja"].test_client()

    print("Weryfikacja cwiczen 2")
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
        szczegol = str(szczegol).replace("\n", " ")[:46]
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
