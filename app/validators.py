# app/validators.py
from flask import abort, request


def parametr_int(nazwa: str, minimum: int, maksimum: int) -> int:
    # Pobieramy słownik z argumentami zapytania
    args = request.args if request else {}

    if nazwa not in args:
        abort(400, description=f"Brak parametru {nazwa}")

    val_raw = args.get(nazwa)
    try:
        val = int(val_raw)
    except (ValueError, TypeError):
        abort(400, description=f"Parametr {nazwa} nie jest liczbą")

    if not (minimum <= val <= maksimum):
        abort(422, description=f"Parametr {nazwa} poza zakresem {minimum}-{maksimum}")

    return val