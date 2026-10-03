#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  Menueplaner - Linux Build"
echo "============================================"
echo

# python3 prüfen
if ! command -v python3 &>/dev/null; then
    echo "FEHLER: python3 nicht gefunden."
    echo "Bitte installieren, z.B.:  sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

# Tkinter prüfen (bei vielen Distributionen ein eigenes Paket)
if ! python3 -c "import tkinter" &>/dev/null; then
    echo "FEHLER: Tkinter fehlt."
    echo "Bitte installieren, z.B.:"
    echo "  Debian/Ubuntu:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    exit 1
fi

echo "Verwende: $(python3 --version)"
echo

# Eigene virtuelle Umgebung: neuere Distributionen erlauben kein
# "pip install" in das System-Python (PEP 668, "externally-managed-environment").
if [ ! -x .venv/bin/python ]; then
    echo "Erstelle virtuelle Umgebung (.venv) ..."
    if ! python3 -m venv .venv; then
        echo "FEHLER: venv konnte nicht erstellt werden."
        echo "Debian/Ubuntu:  sudo apt install python3-venv"
        exit 1
    fi
fi
PYTHON=.venv/bin/python

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install --upgrade pyinstaller -r requirements.txt

echo
echo "Baue Menueplaner ..."
$PYTHON -m PyInstaller --noconfirm --onefile --windowed --name "Menueplaner" \
    --collect-all pandas \
    --collect-all openpyxl \
    menu_planer.py

# Rezeptdatenbank neben die App legen (eine vorhandene wird nicht überschrieben)
if [ ! -f dist/Rezepte.xlsx ]; then
    cp Rezepte.xlsx dist/
fi

echo
echo "============================================"
echo "Fertig! Die App liegt unter: dist/Menueplaner"
echo "Wichtig: Rezepte.xlsx muss im selben Ordner"
echo "         wie die App liegen (bereits kopiert)."
echo "============================================"
