import csv


def wczytaj_zamowienia(sciezka: str) -> list[dict]:
    zamowienia = []
    with open(sciezka, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            zamowienia.append({
                "data": row["data"],
                "region": row["region"],
                "przychod": float(row["przychod"]),
                "koszt": float(row["koszt"]),
            })
    return zamowienia


def dostepne_regiony(sciezka: str) -> list[str]:
    zamowienia = wczytaj_zamowienia(sciezka)
    return sorted(list({z["region"] for z in zamowienia}))


def policz_wskazniki(sciezka: str, region: str = None, rok: int = None) -> dict:
    zamowienia = wczytaj_zamowienia(sciezka)

    # Filtrowanie po roku i regionie przed obliczeniami
    if rok:
        zamowienia = [z for z in zamowienia if str(z["data"]).startswith(str(rok))]
    if region:
        zamowienia = [z for z in zamowienia if z["region"] == region]

    liczba_zamowien = len(zamowienia)
    przychod = sum(z["przychod"] for z in zamowienia)
    koszt = sum(z["koszt"] for z in zamowienia)

    if not zamowienia:
        return {
            "region": region if region else "wszystkie",
            "liczba_zamowien": 0,
            "przychod": 0.0,
            "koszt": 0.0,
            "marza": 0.0,
        }

    if przychod == 0:
        marza = 0.0
    else:
        marza = round((przychod - koszt) / przychod, 4)

    return {
        "region": region if region else "wszystkie",
        "liczba_zamowien": liczba_zamowien,
        "przychod": float(przychod),
        "koszt": float(koszt),
        "marza": marza,
    }


lista_RAPORTY = []


def zapisz_raport(rok: int, region: str, uwagi: str = ""):
    lista_RAPORTY.append({"rok": rok, "region": region, "uwagi": uwagi})


def wykaz_raportow() -> list:
    return lista_RAPORTY


def raporty_roku(rok: int) -> list:
    return [r for r in lista_RAPORTY if r["rok"] == rok]


def zestawienie_regionow(sciezka):
    """Zwraca listę słowników/obiektów ze wskaźnikami dla wszystkich regionów posortowanych alfabetycznie."""
    kody = sorted(dostepne_regiony(sciezka))
    return [policz_wskazniki(sciezka, kod) for kod in kody]

import io

def wczytaj_zbior(strumien) -> int:
    try:
        zawartosc = strumien.read()
        if isinstance(zawartosc, bytes):
            tekst = zawartosc.decode("utf-8")
        else:
            tekst = str(zawartosc)
    except (UnicodeDecodeError, AttributeError) as e:
        raise ValueError("Niepoprawna zawartość pliku (brak wsparcia dla formatu/kodowania)") from e

    f = io.StringIO(tekst)
    reader = csv.DictReader(f)
    
    wymagane_kolumny = {"data", "region", "przychod", "koszt"}
    pola_naglowka = set(reader.fieldnames or [])
    
    brakujace = wymagane_kolumny - pola_naglowka
    if brakujace:
        brak_str = ", ".join(sorted(brakujace))
        raise ValueError(f"brak kolumn: {brak_str}")
        
    wiersze = list(reader)
    return len(wiersze)