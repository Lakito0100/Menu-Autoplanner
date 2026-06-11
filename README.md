# Menüplaner

[![Version](https://img.shields.io/badge/Version-1.1.0-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

Ein lokales Python-Werkzeug zur wöchentlichen Menüplanung mit Rezeptdatenbank,
automatischer Einkaufsliste und Punkte-Berechnung.

---

## Funktionen

- **Wochenplanung** – 7 Tage × 3 Mahlzeiten (Frühstück, Mittag, Abend) mit Kategorie- und Rezeptauswahl sowie Personenanzahl pro Mahlzeit
- **Rezeptsuche** – Live-Filterung im Dropdown während der Eingabe
- **Punkte** – Tagespunkte werden automatisch berechnet und angezeigt
- **Einkaufsliste** – Alle Zutaten automatisch aggregiert, mengenproportional skaliert nach Personenanzahl; Artikel als „vorhanden" markierbar, einzeln löschbar, manuell ergänzbar oder als Gesamtliste zurücksetzbar
- **Export** – Wochenplan + Einkaufsliste als Excel-Datei (`.xlsx`) mit zwei Tabellenblättern
- **Zwischenablage** – Einkaufsliste oder Wochenplan als formatierten Text kopieren
- **Rezeptverwaltung (CRUD)** – Rezepte direkt in der App hinzufügen, bearbeiten und löschen
- **Sitzungsspeicherung** – Der aktuelle Wochenplan und der Status der Einkaufsliste werden automatisch gespeichert und beim nächsten Start wiederhergestellt

---

## Voraussetzungen

- Python 3.8 oder neuer (Tkinter ist in der Standardbibliothek enthalten)
- `pandas`
- `openpyxl`

---

## Installation

### Option A – Python (alle Betriebssysteme)

```bash
# 1. Repository klonen oder als ZIP herunterladen
git clone https://github.com/Lakito0100/Menu-Autoplanner.git
cd Menu-Autoplanner

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Anwendung starten
python menu_planer.py
```

Unter Windows kann alternativ die Batchdatei verwendet werden:

```
start_menu_planer.bat
```

### Option B – Windows EXE (kein Python erforderlich)

Die fertige Windows-Anwendung steht auf der
[Releases-Seite](https://github.com/Lakito0100/Menu-Autoplanner/releases)
zum Download bereit.

1. `Menueplaner_win.exe` herunterladen
2. Die Datei `Rezepte.xlsx` aus dem Repository in denselben Ordner legen
3. Doppelklick auf `Menueplaner_win.exe`

### Option C – Selbst kompilieren (macOS / Linux)

> **Hinweis:** Die Build-Skripte für macOS und Linux wurden nicht offiziell
> getestet. Bei Problemen empfehlen wir Option A (Python-Skript direkt starten).

**macOS:**

```bash
./build_mac.sh
```

Die fertige App liegt danach unter `dist/Menueplaner`.

**Linux:**

```bash
./build_linux.sh
```

Die fertige Datei liegt danach unter `dist/Menueplaner`.

In beiden Fällen muss `Rezepte.xlsx` im selben Ordner wie die kompilierte App liegen.

---

## Bedienung

1. **Rezept auswählen** – Kategorie im linken Dropdown wählen, dann Rezept im rechten Dropdown (oder direkt tippen zum Suchen)
2. **Personenanzahl** – Zahl rechts neben dem Rezept eingeben; Zutatenmengen werden automatisch skaliert
3. **Einkaufsliste** – Schaltfläche „Einkaufsliste anzeigen" öffnet die aggregierte Liste; Artikel können abgehakt oder ergänzt werden
4. **Export** – „Einkaufsliste + Wochenplan exportieren" speichert eine `.xlsx`-Datei
5. **Rezepte verwalten** – Über die gleichnamige Schaltfläche lassen sich Rezepte hinzufügen, bearbeiten und löschen

---

## Rezeptdatenbank (`Rezepte.xlsx`)

Die Datei enthält folgende Spalten:

| Spalte | Beschreibung |
|--------|-------------|
| `Rezeptname` | Name des Rezepts |
| `Kategorie` | z. B. Suppe, Bowls, Pasta |
| `Punkte` | Punkte für das Gesamtrezept |
| `Portionen` | Personenanzahl, für die das Rezept ausgelegt ist |
| `Zutat 1` … `Zutat n` | Zutaten im Format `Menge Einheit Name` |

**Format der Zutaten:**

```
500 g Hackfleisch
1,5 l Gemüsebrühe
2 Eier
```

- Mengen mit Komma oder Punkt möglich (`1,5` oder `1.5`)
- Einheit ist optional
- Ungültige Formate werden als `1x [Name]` interpretiert

---

## App selbst kompilieren

| Plattform | Skript | Output |
|-----------|--------|--------|
| Windows | `build_exe.bat` | `dist\Menueplaner.exe` |
| macOS | `./build_mac.sh` | `dist/Menueplaner` |
| Linux | `./build_linux.sh` | `dist/Menueplaner` |

PyInstaller wird durch die Skripte automatisch installiert.
Die Datei `Rezepte.xlsx` muss sich im selben Ordner wie die kompilierte App befinden.

> **Hinweis:** Die macOS- und Linux-Skripte wurden nicht offiziell getestet.

---

## Projektstruktur

| Datei | Beschreibung |
|-------|-------------|
| `menu_planer.py` | Hauptprogramm (GUI und Logik) |
| `Rezepte.xlsx` | Rezeptdatenbank — muss im gleichen Ordner wie die App liegen |
| `session.json` | Wird automatisch erstellt; speichert Wochenplan und Einkaufslisten-Status |
| `requirements.txt` | Python-Abhängigkeiten für `pip install -r requirements.txt` |
| `build_exe.bat` | Windows Build-Skript → `dist\Menueplaner.exe` |
| `build_mac.sh` | macOS Build-Skript → `dist/Menueplaner` |
| `build_linux.sh` | Linux Build-Skript → `dist/Menueplaner` |
| `Menueplaner.spec` | PyInstaller-Konfigurationsdatei — nicht manuell bearbeiten |

---

## Versionsverlauf

| Version | Neuerungen |
|---------|-----------|
| **v1.1.0** | Einkaufsliste: Eintrag löschen, Liste zurücksetzen; Wochenplan als Text kopieren; Bug-Fixes (Fehlerbehandlung bei Datei-I/O, Session-Validierung, Mausrad-Scrolling) |
| **v1.0.0** | Erstveröffentlichung |

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
