# Menüplaner

[![Version](https://img.shields.io/badge/Version-1.1.1-brightgreen.svg)]()
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

- Python 3.8 oder neuer mit Tkinter
  - Windows / macOS (python.org-Installer): Tkinter ist bereits enthalten
  - Linux: meist separates Paket, z. B. `sudo apt install python3-tk python3-venv` (Debian/Ubuntu) oder `sudo dnf install python3-tkinter` (Fedora)
  - macOS mit Homebrew-Python: `brew install python-tk`
- `pandas`
- `openpyxl` (3.1 oder neuer)

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

Unter **Linux und macOS** heisst der Befehl meist `python3`, und neuere Systeme
erlauben kein `pip install` ins System-Python („externally-managed-environment").
Am einfachsten ist das Startskript – es legt beim ersten Start automatisch eine
virtuelle Umgebung (`.venv`) mit allen Paketen an:

```bash
./start_menu_planer.sh
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

Die fertige App liegt danach unter `dist/Menueplaner.app`.
Da sie nicht signiert ist, beim ersten Start per Rechtsklick → „Öffnen" starten.

**Linux:**

```bash
./build_linux.sh
```

Die fertige Datei liegt danach unter `dist/Menueplaner`.

Die Skripte verwenden eine eigene virtuelle Umgebung (`.venv`) und kopieren
`Rezepte.xlsx` automatisch nach `dist/`. Die Datei muss im selben Ordner wie die
kompilierte App liegen (unter macOS neben `Menueplaner.app`).

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

- Mengen mit Komma, Punkt oder als Bruch möglich (`1,5`, `1.5`, `1/2`)
- Einheit ist optional; erkannt werden gängige Einheiten wie `g`, `kg`, `ml`, `l`, `EL`, `TL`, `Msp`, `Prise`, `Stück`, `Scheibe`, `Dose`, `Bund`, `Handvoll` …
  Alles andere gehört zum Namen (`1 rote Zwiebel` → Menge 1, Zutat „rote Zwiebel")
- Zutaten ohne Menge (z. B. `Salz, Pfeffer`) erscheinen ohne Mengenangabe in der Einkaufsliste

---

## App selbst kompilieren

| Plattform | Skript | Output |
|-----------|--------|--------|
| Windows | `build_exe.bat` | `dist\Menueplaner.exe` |
| macOS | `./build_mac.sh` | `dist/Menueplaner.app` |
| Linux | `./build_linux.sh` | `dist/Menueplaner` |

PyInstaller wird durch die Skripte automatisch installiert.
Die Datei `Rezepte.xlsx` muss sich im selben Ordner wie die kompilierte App befinden.

> **Hinweis:** Das Linux-Skript wurde unter Ubuntu 24.04 getestet, das macOS-Skript
> noch nicht auf einem echten Mac.

---

## Projektstruktur

| Datei | Beschreibung |
|-------|-------------|
| `menu_planer.py` | Hauptprogramm (GUI und Logik) |
| `Rezepte.xlsx` | Rezeptdatenbank — muss im gleichen Ordner wie die App liegen |
| `session.json` | Wird automatisch erstellt; speichert Wochenplan und Einkaufslisten-Status. Ist der Programmordner schreibgeschützt, liegt sie unter `%APPDATA%\Menueplaner` (Windows), `~/Library/Application Support/Menueplaner` (macOS) bzw. `~/.config/Menueplaner` (Linux) |
| `requirements.txt` | Python-Abhängigkeiten für `pip install -r requirements.txt` |
| `start_menu_planer.bat` | Startet das Python-Skript unter Windows |
| `start_menu_planer.sh` | Startet das Python-Skript unter Linux/macOS (richtet `.venv` automatisch ein) |
| `build_exe.bat` | Windows Build-Skript → `dist\Menueplaner.exe` |
| `build_mac.sh` | macOS Build-Skript → `dist/Menueplaner` |
| `build_linux.sh` | Linux Build-Skript → `dist/Menueplaner` |
| `Menueplaner.spec` | PyInstaller-Konfigurationsdatei — nicht manuell bearbeiten |

---

## Versionsverlauf

| Version | Neuerungen |
|---------|-----------|
| **v1.1.1** | Linux/macOS-Unterstützung verbessert (Fenstergrösse, Mausrad, Build- und Startskripte); Kompatibilität mit pandas 3; zahlreiche Bug-Fixes (Rezept bearbeiten/umbenennen, Session-Speicherung beim Schliessen, gelöschte Einkaufslisten-Einträge, Zutaten-Erkennung) |
| **v1.1.0** | Einkaufsliste: Eintrag löschen, Liste zurücksetzen; Wochenplan als Text kopieren; Bug-Fixes (Fehlerbehandlung bei Datei-I/O, Session-Validierung, Mausrad-Scrolling) |
| **v1.0.0** | Erstveröffentlichung |

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
