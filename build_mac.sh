#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  Menueplaner - macOS Build"
echo "============================================"
echo

# Python ermitteln
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "FEHLER: Python nicht gefunden. Bitte Python 3 installieren."
    echo "Tipp: https://www.python.org/downloads/macos/"
    exit 1
fi

# Tkinter prüfen (bei Homebrew-Python ein eigenes Paket)
if ! $PYTHON -c "import tkinter" &>/dev/null; then
    echo "FEHLER: Tkinter fehlt."
    echo "Homebrew:  brew install python-tk"
    echo "Oder Python von https://www.python.org/downloads/macos/ installieren."
    exit 1
fi

echo "Verwende: $PYTHON ($(${PYTHON} --version))"
echo

# Eigene virtuelle Umgebung: Homebrew-Python erlaubt kein "pip install"
# in das System-Python (PEP 668, "externally-managed-environment").
if [ ! -x .venv/bin/python ]; then
    echo "Erstelle virtuelle Umgebung (.venv) ..."
    $PYTHON -m venv .venv
fi
PYTHON=.venv/bin/python

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install --upgrade pyinstaller -r requirements.txt

echo
echo "Baue Menueplaner.app ..."
# Unter macOS ist --onefile zusammen mit --windowed veraltet (PyInstaller 6)
# und startet langsam – daher ein normales .app-Bundle.
$PYTHON -m PyInstaller --noconfirm --windowed --name "Menueplaner" \
    --collect-all pandas \
    --collect-all openpyxl \
    menu_planer.py

# Rezeptdatenbank neben die App legen (eine vorhandene wird nicht überschrieben)
if [ ! -f dist/Rezepte.xlsx ]; then
    cp Rezepte.xlsx dist/
fi

echo
echo "============================================"
echo "Fertig! Die App liegt unter: dist/Menueplaner.app"
echo "Wichtig: Rezepte.xlsx muss im selben Ordner"
echo "         wie Menueplaner.app liegen (bereits kopiert)."
echo "============================================"
