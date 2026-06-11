#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Menueplaner - Linux Build"
echo "============================================"
echo

# python3 prüfen
if ! command -v python3 &>/dev/null; then
    echo "FEHLER: python3 nicht gefunden."
    echo "Bitte installieren:  sudo apt install python3 python3-pip"
    exit 1
fi

# pip3 prüfen
if ! command -v pip3 &>/dev/null; then
    echo "FEHLER: pip3 nicht gefunden."
    echo "Bitte installieren:  sudo apt install python3-pip"
    exit 1
fi

echo "Verwende: $(python3 --version)"
echo

# Abhängigkeiten installieren
echo "Installiere Abhängigkeiten..."
pip3 install --upgrade pyinstaller pandas openpyxl

echo
echo "Baue Menueplaner ..."
python3 -m PyInstaller --onefile --windowed --name "Menueplaner" \
    --collect-all pandas \
    --collect-all openpyxl \
    menu_planer.py

echo
echo "============================================"
echo "Fertig! Die App liegt unter: dist/Menueplaner"
echo "Wichtig: Rezepte.xlsx muss im selben Ordner"
echo "         wie die App liegen!"
echo "============================================"
