#!/usr/bin/env bash
# Startet den Menüplaner unter Linux und macOS.
# Beim ersten Start wird eine virtuelle Umgebung (.venv) mit den
# benötigten Paketen angelegt.
set -e
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
    echo "FEHLER: python3 nicht gefunden. Bitte Python 3 installieren."
    exit 1
fi

if ! python3 -c "import tkinter" &>/dev/null; then
    echo "FEHLER: Tkinter fehlt."
    echo "  Debian/Ubuntu:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  macOS/Homebrew: brew install python-tk"
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "Erster Start: richte virtuelle Umgebung ein ..."
    if ! python3 -m venv .venv; then
        echo "FEHLER: venv konnte nicht erstellt werden."
        echo "  Debian/Ubuntu:  sudo apt install python3-venv"
        exit 1
    fi
    .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python menu_planer.py
