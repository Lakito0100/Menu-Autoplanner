# Menüplaner

[![Version](https://img.shields.io/badge/Version-1.1.1-brightgreen.svg)]()
[![Tests](https://github.com/Lakito0100/Menu-Autoplanner/actions/workflows/tests.yml/badge.svg)](https://github.com/Lakito0100/Menu-Autoplanner/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

Wochenplanung mit Rezeptdatenbank, automatischer Einkaufsliste und Punkte-Berechnung.

- 7 Tage × 3 Mahlzeiten mit Rezeptsuche und Personenanzahl
- Tagespunkte werden automatisch berechnet
- Einkaufsliste: Mengen werden nach Personen skaliert und zusammengefasst; Einträge abhaken, löschen, ergänzen
- Export als Excel (Wochenplan + Einkaufsliste) oder als Text in die Zwischenablage
- Rezepte direkt in der App anlegen, bearbeiten und löschen
- Der aktuelle Plan wird beim Beenden gespeichert und beim nächsten Start wiederhergestellt
- Anzeige-Zoom für hochauflösende Bildschirme: Menü „Ansicht" oder Strg + / Strg − / Strg 0 (macOS: Cmd). Auf 4K-Bildschirmen unter Linux wird automatisch vergrössert

## Download

Fertige Apps gibt es auf der [Releases-Seite](https://github.com/Lakito0100/Menu-Autoplanner/releases)
unter **Assets**. Jedes Archiv enthält die App und `Rezepte.xlsx`. Beide müssen im selben Ordner bleiben.

| System | Datei | Starten |
|--------|-------|---------|
| Windows 10/11 | `Menueplaner_win.zip` | entpacken, `Menueplaner.exe` doppelklicken |
| macOS (nur Apple Silicon, M1 oder neuer) | `Menueplaner_mac.zip` | entpacken, `Menueplaner.app` per Rechtsklick → „Öffnen" |
| Linux (x86-64) | `Menueplaner_linux.tar.gz` | `tar -xzf Menueplaner_linux.tar.gz && ./Menueplaner/Menueplaner` |

Die Apps sind nicht signiert:

- **Windows:** Bei der SmartScreen-Warnung „Weitere Informationen" → „Trotzdem ausführen".
- **macOS:** Rechtsklick → „Öffnen". Ab macOS 15 stattdessen unter Systemeinstellungen → Datenschutz & Sicherheit → „Dennoch öffnen".

## Mit Python starten

Voraussetzung ist Python 3.8+ mit Tkinter. Unter Linux z. B. `sudo apt install python3-tk python3-venv`, mit Homebrew-Python `brew install python-tk`.

```bash
git clone https://github.com/Lakito0100/Menu-Autoplanner.git
cd Menu-Autoplanner
./start_menu_planer.sh          # Linux/macOS – richtet beim ersten Start .venv ein
start_menu_planer.bat           # Windows (vorher: pip install -r requirements.txt)
```

## Selbst kompilieren

| System | Skript | Ergebnis |
|--------|--------|----------|
| Windows | `build_exe.bat` | `dist\Menueplaner.exe` |
| macOS | `./build_mac.sh` | `dist/Menueplaner.app` |
| Linux | `./build_linux.sh` | `dist/Menueplaner` |

Die Skripte installieren PyInstaller selbst und kopieren `Rezepte.xlsx` nach `dist/`.

## Rezeptdatenbank (`Rezepte.xlsx`)

Spalten: `Rezeptname`, `Kategorie`, `Punkte` (für das ganze Rezept), `Portionen`, `Zutat 1` … `Zutat n`.

Zutaten im Format `Menge Einheit Name`, z. B. `500 g Hackfleisch`, `1,5 l Brühe`, `1/2 TL Zimt`, `2 Eier`.
Einheit und Menge sind optional. Zutaten ohne Menge (z. B. `Salz, Pfeffer`) stehen ohne Mengenangabe auf der Einkaufsliste.

## Versionsverlauf

| Version | Neuerungen |
|---------|-----------|
| **v1.1.1** | Bessere Linux/macOS-Unterstützung, Zoom für HiDPI/4K-Bildschirme, Kompatibilität mit pandas 3, automatische Tests und Release-Builds, zahlreiche Bug-Fixes |
| **v1.1.0** | Einkaufsliste: Eintrag löschen, Liste zurücksetzen; Wochenplan als Text kopieren |
| **v1.0.0** | Erstveröffentlichung |

## Lizenz

[MIT](LICENSE)
