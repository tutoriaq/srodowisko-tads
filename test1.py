import platform
import shutil
import subprocess
import sys
from pathlib import Path

def wersja_polecenia(polecenie):
    """Zwraca pierwszy wiersz wyniku polecenia albo None, gdy brak programu."""
    if shutil.which(polecenie[0]) is None:
        return None
    wynik = subprocess.run(polecenie, capture_output=True, text=True)
    tresc = (wynik.stdout + wynik.stderr).strip().splitlines()
    return tresc[0] if tresc else ""

def zbierz_sprawdzenia():
    w = sys.version_info
    gitignore = Path(".gitignore")
    return [
        ("Wersja Pythona 3.10 lub nowsza", f"{w.major}.{w.minor}.{w.micro}", (w.major, w.minor) >= (3, 10)),
        ("Srodowisko wirtualne aktywne", Path(sys.prefix).name, sys.prefix != sys.base_prefix),
        ("Katalog srodowiska nazwany .venv", Path(sys.prefix).name, Path(sys.prefix).name == ".venv"),
        ("Git dostepny w systemie", wersja_polecenia(["git", "--version"]) or "brak", shutil.which("git") is not None),
        ("Repozytorium zainicjalizowane", ".git", Path(".git").is_dir()),
        ("Plik requirements.txt istnieje", "requirements.txt", Path("requirements.txt").is_file()),
        ("Plik .gitignore wyklucza .venv", ".gitignore", gitignore.is_file() and ".venv" in gitignore.read_text(encoding="utf-8")),
    ]

def main():
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Interpreter: {sys.executable}")
    print("-" * 66)
    sprawdzenia = zbierz_sprawdzenia()
    zgodne = 0
    for opis, wartosc, ok in sprawdzenia:
        znacznik = "OK " if ok else "BLAD"
        print(f"[{znacznik}] {opis:34s} {wartosc}")
        zgodne += 1 if ok else 0
    print("-" * 66)
    print(f"Sprawdzenia srodowiska: {zgodne}/{len(sprawdzenia)}")
    return 0 if zgodne == len(sprawdzenia) else 1

if __name__ == "__main__":
    sys.exit(main())
#pusty komentarz - test