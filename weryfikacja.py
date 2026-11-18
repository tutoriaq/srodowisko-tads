"""Weryfikacja rezultatów ćwiczeń 5 (Formularze i interakcja użytkownika).

Plik należy umieścić w katalogu projektu srodowisko-tads (obok katalogu app/)
i uruchamiać przy aktywnym środowisku wirtualnym:

    python verify_ex5.py

Skrypt nie zmienia żadnych plików. Żądania wysyła bezpośrednio do obiektu aplikacji
(test_client), więc serwer nie musi być uruchomiony; zapisane w trakcie sprawdzania
raporty istnieją tylko w pamięci procesu skryptu. Token CSRF pobierany jest z dokumentu
formularza, tak jak robi to przeglądarka. Można uruchamiać skrypt po każdym zadaniu —
liczba sprawdzeń zgodnych powinna rosnąć. Nazwy w raporcie zapisano bez znaków
diakrytycznych, aby były czytelne w każdej konsoli.
"""

import importlib
import importlib.util
import io
import re
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
CSV_POPRAWNY = b"data,region,przychod,koszt\n2026-01-08,PL,1,1\n2026-01-09,DE,2,1\n"


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


def token(adres):
    """Pobiera token CSRF z dokumentu formularza (pusty tekst, gdy go brak)."""
    dopasowanie = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', tresc(zadanie(adres)))
    return dopasowanie.group(1) if dopasowanie else ""


def wyslij(adres, dane, z_tokenem=True, **opcje):
    dane = dict(dane)
    if z_tokenem:
        dane["csrf_token"] = token(adres)
    return zadanie(adres, "POST", data=dane, **opcje)


def plik(adres, nazwa, zawartosc, typ="text/csv", z_tokenem=True):
    dane = {"csrf_token": token(adres) if z_tokenem else ""}
    if nazwa is not None:
        dane["plik"] = (io.BytesIO(zawartosc), nazwa, typ)
    return zadanie(adres, "POST", data=dane, content_type="multipart/form-data")


def lokalizacja(odp):
    return (odp.headers.get("Location") or "").replace("http://localhost", "")


def plik_istnieje(sciezka):
    if not (KORZEN / sciezka).is_file():
        raise Brak(f"brak pliku {sciezka}")
    return (KORZEN / sciezka).read_text(encoding="utf-8")


def formularz(nazwa_klasy):
    """Zwraca instancję formularza z app.forms utworzoną w kontekście żądania."""
    if not (KORZEN / "app" / "forms.py").is_file():
        raise Brak("brak pliku app/forms.py")
    forms = importlib.import_module("app.forms")
    klasa = getattr(forms, nazwa_klasy, None)
    if klasa is None:
        raise Brak(f"brak klasy {nazwa_klasy} w app/forms.py")
    wymagana_aplikacja()
    with STAN["aplikacja"].test_request_context("/kpi?region=PL"):
        return klasa()


def sciezka_danych():
    return STAN["aplikacja"].config["SCIEZKA_DANYCH"]


# ------------------------------------------------------------------ zadanie 1

@sprawdzenie(1, "Flask-WTF zainstalowany i zapisany w requirements.txt")
def _():
    from importlib import metadata

    try:
        wersja = metadata.version("flask-wtf")
    except metadata.PackageNotFoundError:
        return False, "brak pakietu Flask-WTF w srodowisku"
    zapisany = "flask-wtf" in (KORZEN / "requirements.txt").read_text(encoding="utf-8").lower()
    return zapisany, f"{wersja}" if zapisany else "brak wpisu w requirements.txt"


@sprawdzenie(1, "Konfiguracja: WTF_I18N_ENABLED wylaczone")
def _():
    wymagana_aplikacja()
    wartosc = STAN["aplikacja"].config.get("WTF_I18N_ENABLED")
    return wartosc is False, wartosc


@sprawdzenie(1, "Makro pole w macros.html obok makr kafelek i ocena")
def _():
    zrodlo = plik_istnieje("app/templates/macros.html")
    brakujace = [n for n in ("pole", "kafelek", "ocena") if not re.search(r"\{%-?\s*macro\s+" + n + r"\s*\(", zrodlo)]
    return not brakujace, "pole, kafelek, ocena" if not brakujace else "brak makr: " + ", ".join(brakujace)


@sprawdzenie(1, "FormularzBazowy z komunikatami po polsku i FiltrForm")
def _():
    forms = importlib.import_module("app.forms") if (KORZEN / "app" / "forms.py").is_file() else None
    if forms is None:
        raise Brak("brak pliku app/forms.py")
    bazowy = getattr(forms, "FormularzBazowy", None)
    if bazowy is None or not hasattr(forms, "FiltrForm"):
        raise Brak("brak klasy FormularzBazowy lub FiltrForm")
    jezyki = list(getattr(bazowy.Meta, "locales", []) or [])
    return jezyki == ["pl"], jezyki


@sprawdzenie(1, "FiltrForm: pola region i rok, bez tokenu CSRF")
def _():
    f = formularz("FiltrForm")
    pola = sorted(n for n in f._fields)
    zgodne = "region" in pola and "rok" in pola and "csrf_token" not in pola
    return zgodne, pola


@sprawdzenie(1, "services: policz_wskazniki z parametrem rok")
def _():
    wymagana_aplikacja()
    uslugi = importlib.import_module("app.services")
    pusty = uslugi.policz_wskazniki(sciezka_danych(), None, 2025)
    de = uslugi.policz_wskazniki(sciezka_danych(), "DE", 2026)
    wynik = (pusty["liczba_zamowien"], pusty["marza"], de["liczba_zamowien"])
    return wynik == (0, 0.0, 3), wynik


@sprawdzenie(1, "GET /kpi: 200 i formularz z polami region oraz rok")
def _():
    odp = zadanie("/kpi")
    html = tresc(odp)
    zgodne = odp.status_code == 200 and 'name="region"' in html and 'name="rok"' in html
    return zgodne, odp.status_code


@sprawdzenie(1, "Filtr region=DE, rok=2026: wartosci zachowane w formularzu")
def _():
    html = tresc(zadanie("/kpi?region=DE&rok=2026"))
    zgodne = bool(re.search(r"<option[^>]*selected[^>]*value=\"DE\"|<option[^>]*value=\"DE\"[^>]*selected", html)) and 'value="2026"' in html
    return zgodne, "DE wybrane, rok 2026" if zgodne else "brak zachowanych wartosci"


@sprawdzenie(1, "Nieznany region: 200 i komunikat flash o pominieciu kryteriow")
def _():
    odp = zadanie("/kpi?region=XX")
    zgodne = odp.status_code == 200 and "Kryteria zawężenia zostały pominięte" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(1, "Rok poza zakresem: komunikat przy polu i zachowana wartosc")
def _():
    odp = zadanie("/kpi?rok=1900")
    html = tresc(odp)
    zgodne = odp.status_code == 200 and "Zakres 2020-2030" in html and 'value="1900"' in html
    return zgodne, odp.status_code


@sprawdzenie(1, "Panel z cwiczen 4 zachowany: tytul, nawigacja, kafelki")
def _():
    status, html = 0, ""
    odp = zadanie("/kpi?region=PL"); status, html = odp.status_code, tresc(odp)
    tytul = re.search(r"<title>([^<]*)</title>", html)
    zgodne = (status == 200 and bool(tytul) and tytul.group(1).strip() == "Wskaźniki: PL · TADS"
              and html.count('class="kafelek"') == 4 and 'href="/regiony/DE"' in html)
    return zgodne, tytul.group(1).strip() if tytul else status


@sprawdzenie(1, "Komunikat flash jest jednokrotny; filtr bez tokenu")
def _():
    pierwszy = tresc(zadanie("/kpi?region=XX"))
    po = tresc(zadanie("/kpi"))
    zgodne = "Kryteria zawężenia" in pierwszy and "Kryteria zawężenia" not in po and "csrf_token" not in po
    return zgodne, "wyswietlony raz, potem zuzyty" if zgodne else "komunikat nie wyswietlony raz albo powtorzony"


# ------------------------------------------------------------------ zadanie 2

@sprawdzenie(2, "CSRFProtect zarejestrowany w aplikacji")
def _():
    wymagana_aplikacja()
    zarejestrowany = "csrf" in STAN["aplikacja"].extensions
    return zarejestrowany, "tak" if zarejestrowany else "brak CSRFProtect"


@sprawdzenie(2, "services: zapisz_raport z uwagami i wykaz_raportow")
def _():
    wymagana_aplikacja()
    uslugi = importlib.import_module("app.services")
    uslugi.zapisz_raport(2029, "CZ", "uwaga")
    wykaz = [r for r in uslugi.wykaz_raportow() if r["rok"] == 2029]
    return bool(wykaz) and wykaz[0].get("uwagi") == "uwaga", wykaz


@sprawdzenie(2, "RaportForm: pola i walidator wlasny validate_rok")
def _():
    f = formularz("RaportForm")
    pola = [n for n in ("rok", "region", "szczegoly", "uwagi", "zapisz") if n in f._fields]
    forms = importlib.import_module("app.forms")
    zgodne = len(pola) == 5 and hasattr(forms.RaportForm, "validate_rok")
    return zgodne, pola


@sprawdzenie(2, "GET /raporty/nowy: 200, pola formularza i token CSRF")
def _():
    odp = zadanie("/raporty/nowy")
    html = tresc(odp)
    brakujace = [n for n in ("csrf_token", "rok", "region", "szczegoly", "uwagi") if f'name="{n}"' not in html]
    return odp.status_code == 200 and not brakujace, odp.status_code if not brakujace else "brak pol: " + ", ".join(brakujace)


@sprawdzenie(2, "Poprawny zapis: 303 i Location /raporty/2027")
def _():
    if not token("/raporty/nowy"):
        raise Brak("brak tokenu CSRF w formularzu")
    odp = wyslij("/raporty/nowy", {"rok": "2027", "region": "PL", "uwagi": "Test"})
    return (odp.status_code, lokalizacja(odp)) == (303, "/raporty/2027"), (odp.status_code, lokalizacja(odp))


@sprawdzenie(2, "Po zapisie: komunikat flash i liczba raportow")
def _():
    html = tresc(zadanie("/raporty/2027"))
    zgodne = "Raport za rok 2027 zapisany" in html and "Zapisane raporty: 1" in html
    return zgodne, "komunikat i licznik" if zgodne else "brak komunikatu lub licznika"


@sprawdzenie(2, "Powtorzony raport: 422 i walidator wlasny")
def _():
    odp = wyslij("/raporty/nowy", {"rok": "2027", "region": "PL"})
    zgodne = odp.status_code == 422 and "Raport za ten rok i region już istnieje" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(2, "Rok 1900: 422, komunikat zakresu i zachowana wartosc")
def _():
    odp = wyslij("/raporty/nowy", {"rok": "1900", "region": "PL"})
    html = tresc(odp)
    zgodne = odp.status_code == 422 and "Zakres 2020-2030" in html and 'value="1900"' in html
    return zgodne, odp.status_code


@sprawdzenie(2, "Brak roku i nieznany region: 422 z komunikatami po polsku")
def _():
    brak = wyslij("/raporty/nowy", {"rok": "", "region": "PL"})
    region = wyslij("/raporty/nowy", {"rok": "2028", "region": "XX"})
    zgodne = (
        brak.status_code == 422 and "Pole jest wymagane" in tresc(brak)
        and region.status_code == 422 and "Nieprawidłowy wybór" in tresc(region)
    )
    return zgodne, (brak.status_code, region.status_code)


@sprawdzenie(2, "Uwagi dluzsze niz 200 znakow: 422")
def _():
    odp = wyslij("/raporty/nowy", {"rok": "2028", "region": "PL", "uwagi": "x" * 250})
    zgodne = odp.status_code == 422 and "Najwyżej 200 znaków" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(2, "Zapis bez tokenu CSRF: 400")
def _():
    odp = wyslij("/raporty/nowy", {"rok": "2028", "region": "PL"}, z_tokenem=False)
    return odp.status_code == 400, odp.status_code


@sprawdzenie(2, "Pola formularza renderowane makrem pole")
def _():
    html = tresc(wyslij("/raporty/nowy", {"rok": "1900", "region": "PL"}))
    zgodne = 'class="pole blad"' in html and 'class="komunikat-pola"' in html
    return zgodne, "div.pole.blad i komunikat-pola" if zgodne else "brak struktury makra"


# ------------------------------------------------------------------ zadanie 3

@sprawdzenie(3, "ZbiorForm z polem plik typu FileField")
def _():
    f = formularz("ZbiorForm")
    from flask_wtf.file import FileField

    zgodne = "plik" in f._fields and isinstance(f.plik, FileField)
    return zgodne, type(f._fields.get("plik")).__name__


@sprawdzenie(3, "GET /wczytaj: 200, multipart/form-data i token CSRF")
def _():
    odp = zadanie("/wczytaj")
    html = tresc(odp)
    zgodne = odp.status_code == 200 and "multipart/form-data" in html and 'name="csrf_token"' in html and 'name="plik"' in html
    return zgodne, odp.status_code


@sprawdzenie(3, "Poprawny CSV: 303 i komunikat flash z liczba zamowien")
def _():
    odp = plik("/wczytaj", "zbior.csv", CSV_POPRAWNY)
    html = tresc(zadanie("/wczytaj"))
    zgodne = odp.status_code == 303 and "Wczytano 2 zamówień z pliku zbior.csv" in html
    return zgodne, (odp.status_code, "komunikat" if "Wczytano 2" in html else "brak komunikatu")


@sprawdzenie(3, "Nazwa w komunikacie przechodzi przez secure_filename")
def _():
    plik("/wczytaj", "raport roczny (1).csv", CSV_POPRAWNY)
    html = tresc(zadanie("/wczytaj"))
    zgodne = "z pliku raport_roczny_1.csv" in html
    return zgodne, "raport_roczny_1.csv" if zgodne else "nazwa bez przetworzenia"


@sprawdzenie(3, "Brak pliku: 422 i komunikat FileRequired")
def _():
    odp = plik("/wczytaj", None, b"")
    zgodne = odp.status_code == 422 and "Wskaż plik do wczytania" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(3, "Plik .txt: 422 i komunikat FileAllowed")
def _():
    odp = plik("/wczytaj", "zbior.txt", b"abc", "text/plain")
    zgodne = odp.status_code == 422 and "Dopuszczalny jest wyłącznie format CSV" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(3, "Bajty binarne w pliku .csv: 422 i niepoprawna zawartosc")
def _():
    odp = plik("/wczytaj", "zbior.csv", bytes([0xFF, 0xFE, 0x00, 0x80, 0x81]) * 4)
    zgodne = odp.status_code == 422 and "Niepoprawna zawartość" in tresc(odp)
    return zgodne, odp.status_code


@sprawdzenie(3, "Plik bez wymaganych kolumn: 422 i wykaz brakujacych")
def _():
    odp = plik("/wczytaj", "zbior.csv", b"a,b\n1,2\n")
    html = tresc(odp)
    zgodne = odp.status_code == 422 and "brak kolumn" in html and "przychod" in html
    return zgodne, odp.status_code


@sprawdzenie(3, "Limit MAX_CONTENT_LENGTH: 1 MiB w konfiguracji")
def _():
    wymagana_aplikacja()
    limit = STAN["aplikacja"].config.get("MAX_CONTENT_LENGTH")
    return limit == 1024 * 1024, limit


@sprawdzenie(3, "Plik ok. 2 MiB: odpowiedz 413")
def _():
    duzy = b"data,region,przychod,koszt\n" + b"2026-01-01,PL,1,1\n" * 120000
    odp = plik("/wczytaj", "duzy.csv", duzy)
    return odp.status_code == 413, odp.status_code


# --------------------------------------------------------------------- raport

def main():
    STAN["aplikacja"], STAN["uklad"] = zaladuj_aplikacje()
    if STAN["aplikacja"] is not None:
        STAN["klient"] = STAN["aplikacja"].test_client()

    print("Weryfikacja cwiczen 5")
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
