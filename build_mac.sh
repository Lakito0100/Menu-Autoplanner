#!/usr/bin/env bash
set -e

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

echo "Verwende: $PYTHON ($(${PYTHON} --version))"
echo

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
$PYTHON -m pip install --upgrade pyinstaller pandas openpyxl

echo
echo "Baue Menueplaner ..."
$PYTHON -m PyInstaller --onefile --windowed --name "Menueplaner" \
    --collect-all pandas \
    --collect-all openpyxl \
    menu_planer.py

echo
echo "============================================"
echo "Fertig! Die App liegt unter: dist/Menueplaner"
echo "Wichtig: Rezepte.xlsx muss im selben Ordner"
echo "         wie die App liegen!"
echo "============================================"
