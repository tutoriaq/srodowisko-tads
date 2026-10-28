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


def policz_wskazniki(sciezka: str, region: str = None) -> dict:
    zamowienia = wczytaj_zamowienia(sciezka)

    if region:
        zamowienia = [z for z in zamowienia if z["region"] == region]

    liczba_zamowien = len(zamowienia)
    przychod = sum(z["przychod"] for z in zamowienia)
    koszt = sum(z["koszt"] for z in zamowienia)

    if przychod == 0:
        marza = 0.0
    else:
        marza = round((przychod - koszt) / przychod, 4)

    return {
        "region": region,
        "liczba_zamowien": liczba_zamowien,
        "przychod": float(przychod),
        "koszt": float(koszt),
        "marza": marza,
    }

lista_RAPORTY = []

def zapisz_raport(rok: int, region: str):
    lista_RAPORTY.append({"rok": rok, "region": region})

def raporty_roku(rok: int) -> list:
    return [r for r in lista_RAPORTY if r["rok"] == rok]