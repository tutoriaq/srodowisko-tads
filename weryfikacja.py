"""Weryfikacja rezultatów ćwiczeń 3 (Routing i obsługa żądań HTTP).

Plik należy umieścić w katalogu projektu srodowisko-tads (obok katalogu app/)
i uruchamiać przy aktywnym środowisku wirtualnym:

    python weryfikacja_cw3.py

Skrypt nie zmienia żadnych plików. Sprawdza zachowanie aplikacji: żądania wysyłane
są bezpośrednio do obiektu aplikacji (test_client), więc serwer nie musi być
uruchomiony; zapisane w trakcie sprawdzania raporty istnieją tylko w pamięci procesu
skryptu. Można go uruchamiać po każdym zadaniu — liczba sprawdzeń zgodnych powinna
rosnąć. Nazwy w raporcie zapisano bez znaków diakrytycznych, aby były czytelne
w każdej konsoli.
"""

import importlib
import importlib.util
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

def zaladuj_aplikacje():
    """Zwraca (aplikacja, opis układu) albo (None, powód niepowodzenia)."""
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


def kody(*zadania):
    return tuple(z.status_code for z in zadania)


def plik_istnieje(sciezka):
    if not (KORZEN / sciezka).is_file():
        raise Brak(f"brak pliku {sciezka}")


# ------------------------------------------------------------------ zadanie 1

@sprawdzenie(1, "Adresy z cwiczen 2 dzialaja: /, /kpi, /api/kpi")
def _():
    wyniki = kody(zadanie("/"), zadanie("/kpi?region=PL"), zadanie("/api/kpi?region=PL"))
    return wyniki == (200, 200, 200), wyniki


@sprawdzenie(1, "services: zapisz_raport i raporty_roku")
def _():
    plik_istnieje("app/services.py")
    uslugi = importlib.import_module("app.services")
    uslugi.zapisz_raport(2029, "PL")
    raporty = uslugi.raporty_roku(2029)
    return raporty == [{"rok": 2029, "region": "PL"}], raporty


@sprawdzenie(1, "Konwerter region zarejestrowany w mapie adresow")
def _():
    plik_istnieje("app/converters.py")
    wymagana_aplikacja()
    zarejestrowany = "region" in STAN["aplikacja"].url_map.converters
    return zarejestrowany, "tak" if zarejestrowany else "brak konwertera region"


@sprawdzenie(1, "Konwerter: match dopasowuje /regiony/XX, odrzuca /regiony/pl")
def _():
    from werkzeug.exceptions import NotFound

    wymagana_aplikacja()
    dopasowanie = STAN["aplikacja"].url_map.bind("localhost")
    try:
        endpoint = dopasowanie.match("/regiony/XX", "GET")[0]
    except NotFound:
        endpoint = "brak dopasowania"
    try:
        dopasowanie.match("/regiony/pl", "GET")
        malymi = "dopasowano"
    except NotFound:
        malymi = "odrzucono"
    return (endpoint, malymi) == ("panel.region", "odrzucono"), (endpoint, malymi)


@sprawdzenie(1, "Panel regionu: PL 200; pl, POL, XX daja 404")
def _():
    wyniki = kody(zadanie("/regiony/PL"), zadanie("/regiony/pl"), zadanie("/regiony/POL"), zadanie("/regiony/XX"))
    return wyniki == (200, 404, 404, 404), wyniki


@sprawdzenie(1, "Raport: /raporty/ i /raporty/2027 daja 200")
def _():
    wyniki = kody(zadanie("/raporty/"), zadanie("/raporty/2027"))
    return wyniki == (200, 200), wyniki


@sprawdzenie(1, "Zakres roku w adresie: 2031, 2019 i abc daja 404")
def _():
    wyniki = kody(zadanie("/raporty/2027"), zadanie("/raporty/2031"), zadanie("/raporty/2019"), zadanie("/raporty/abc"))
    return wyniki == (200, 404, 404, 404), wyniki


@sprawdzenie(1, "Adres /raporty/2026 przekierowuje (308) na /raporty/")
def _():
    odp = zadanie("/raporty/2026")
    lokalizacja = (odp.headers.get("Location") or "").replace("http://localhost", "")
    return (odp.status_code, lokalizacja) == (308, "/raporty/"), (odp.status_code, lokalizacja)


@sprawdzenie(1, "Dwie reguly dla jednego punktu koncowego panel.raport")
def _():
    wymagana_aplikacja()
    reguly = [str(r) for r in STAN["aplikacja"].url_map.iter_rules() if r.endpoint == "panel.raport"]
    return len(reguly) == 2, sorted(reguly)


# ------------------------------------------------------------------ zadanie 2

@sprawdzenie(2, "Adres /raporty/nowy: GET 200, DELETE 405")
def _():
    wyniki = kody(zadanie("/raporty/nowy"), zadanie("/raporty/nowy", "DELETE"))
    return wyniki == (200, 405), wyniki


@sprawdzenie(2, "Zapis POST rok=2027, region=PL: 303 i Location /raporty/2027")
def _():
    odp = zadanie("/raporty/nowy", "POST", data={"rok": "2027", "region": "PL"})
    lokalizacja = (odp.headers.get("Location") or "").replace("http://localhost", "")
    return (odp.status_code, lokalizacja) == (303, "/raporty/2027"), (odp.status_code, lokalizacja)


@sprawdzenie(2, "Raport 2027 po zapisie: Zapisane raporty: 1")
def _():
    tresc = zadanie("/raporty/2027").get_data(as_text=True)
    return "Zapisane raporty: 1" in tresc, tresc[:46]


@sprawdzenie(2, "Zapis za rok domyslny: Location /raporty/ (adres kanoniczny)")
def _():
    odp = zadanie("/raporty/nowy", "POST", data={"rok": "2026", "region": "DE"})
    lokalizacja = (odp.headers.get("Location") or "").replace("http://localhost", "")
    return (odp.status_code, lokalizacja) == (303, "/raporty/"), (odp.status_code, lokalizacja)


@sprawdzenie(2, "Dane niepoprawne: rok=abc i nieznany region daja 400")
def _():
    wyniki = kody(
        zadanie("/raporty/nowy", "POST", data={"rok": "abc", "region": "PL"}),
        zadanie("/raporty/nowy", "POST", data={"rok": "2027", "region": "XX"}),
    )
    return wyniki == (400, 400), wyniki


@sprawdzenie(2, "Rok poza zakresem (2045) daje 422")
def _():
    kod = zadanie("/raporty/nowy", "POST", data={"rok": "2045", "region": "PL"}).status_code
    return kod == 422, kod


@sprawdzenie(2, "Adres wycofany /stary-panel: 301 i Location /kpi")
def _():
    odp = zadanie("/stary-panel")
    lokalizacja = (odp.headers.get("Location") or "").replace("http://localhost", "")
    return (odp.status_code, lokalizacja) == (301, "/kpi"), (odp.status_code, lokalizacja)


@sprawdzenie(2, "validators.py: funkcja parametr_int")
def _():
    plik_istnieje("app/validators.py")
    modul = importlib.import_module("app.validators")
    return callable(getattr(modul, "parametr_int", None)), "parametr_int"


@sprawdzenie(2, "API: brak roku 400, abc 400, 2040 422, 2027 200")
def _():
    wyniki = kody(
        zadanie("/api/raporty"),
        zadanie("/api/raporty?rok=abc"),
        zadanie("/api/raporty?rok=2040"),
        zadanie("/api/raporty?rok=2027"),
    )
    return wyniki == (400, 400, 422, 200), wyniki


# ------------------------------------------------------------------ zadanie 3

@sprawdzenie(3, "Naglowek X-Czas-Ms w odpowiedziach 200 i 404")
def _():
    odp_ok, odp_404 = zadanie("/"), zadanie("/nie-ma-takiego-adresu")
    zgodne = "X-Czas-Ms" in odp_ok.headers and "X-Czas-Ms" in odp_404.headers and odp_404.status_code == 404
    return zgodne, (odp_ok.headers.get("X-Czas-Ms"), odp_404.headers.get("X-Czas-Ms"))


@sprawdzenie(3, "decorators.py: wymagany_parametr zachowuje nazwe widoku")
def _():
    plik_istnieje("app/decorators.py")
    wymagana_aplikacja()
    widok = STAN["aplikacja"].view_functions.get("api.raporty")
    if widok is None:
        raise Brak("brak punktu koncowego api.raporty")
    return widok.__name__ == "raporty", widok.__name__


@sprawdzenie(3, "API: brak roku daje 400 i dokument JSON (blad, kod)")
def _():
    odp = zadanie("/api/raporty")
    dane = odp.get_json(silent=True) or {}
    zgodne = odp.status_code == 400 and dane.get("kod") == 400 and bool(dane.get("blad"))
    return zgodne, f"{odp.status_code} {odp.mimetype}"


@sprawdzenie(3, "API: rok=2040 daje 422 i dokument JSON z kodem 422")
def _():
    odp = zadanie("/api/raporty?rok=2040")
    dane = odp.get_json(silent=True) or {}
    return (odp.status_code, dane.get("kod")) == (422, 422), f"{odp.status_code} {odp.mimetype}"


@sprawdzenie(3, "Poza API: blad jako tekst HTML z kodem w <h1>")
def _():
    odp = zadanie("/regiony/XX")
    zgodne = odp.status_code == 404 and odp.mimetype == "text/html" and "<h1>404</h1>" in odp.get_data(as_text=True)
    return zgodne, f"{odp.status_code} {odp.mimetype}"


@sprawdzenie(3, "Odpowiedz HTML nie powtarza wartosci z adresu")
def _():
    odp = zadanie("/kpi?region=%3Cb%3EPL%3C%2Fb%3E")
    tresc = odp.get_data(as_text=True)
    zgodne = odp.status_code == 404 and "<h1>404</h1>" in tresc and "<b>" not in tresc
    return zgodne, odp.status_code


@sprawdzenie(3, "Przekierowanie 308 zachowane mimo wspolnej procedury bledow")
def _():
    procedura_dziala = "<h1>404</h1>" in zadanie("/regiony/XX").get_data(as_text=True)
    odp = zadanie("/raporty/2026")
    zgodne = procedura_dziala and odp.status_code == 308 and "<h1>308</h1>" not in odp.get_data(as_text=True)
    return zgodne, odp.status_code if procedura_dziala else "brak wspolnej procedury bledow"


@sprawdzenie(3, "Interfejs pod /api i /api/v2 (blueprinty api i api_v2)")
def _():
    wymagana_aplikacja()
    nazwy = sorted(n for n in STAN["aplikacja"].blueprints if n.startswith("api"))
    wyniki = kody(zadanie("/api/raporty?rok=2027"), zadanie("/api/v2/raporty?rok=2027"))
    return nazwy == ["api", "api_v2"] and wyniki == (200, 200), (nazwy, wyniki)


# --------------------------------------------------------------------- raport

def main():
    STAN["aplikacja"], STAN["uklad"] = zaladuj_aplikacje()
    if STAN["aplikacja"] is not None:
        STAN["klient"] = STAN["aplikacja"].test_client()

    print("Weryfikacja cwiczen 3")
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
        szczegol = str(szczegol).replace("\n", " ")[:42]
        print(f"[{'OK  ' if zgodne else 'BLAD'}] Z{numer} {opis:60s} {szczegol}")
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
