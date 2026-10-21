import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SCIEZKA_DANYCH = BASE_DIR / "dane" / "zamowienia.csv"
    DEBUG = False


class RozwojowaConfig(Config):
    DEBUG = True


class ProdukcyjnaConfig(Config):
    DEBUG = False


KONFIGURACJE = {
    "rozwojowa": RozwojowaConfig,
    "produkcyjna": ProdukcyjnaConfig,
}