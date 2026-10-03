# Menüplaner

[![Version](https://img.shields.io/badge/Version-1.1.1-brightgreen.svg)]()
[![Tests](https://github.com/Lakito0100/Menu-Autoplanner/actions/workflows/tests.yml/badge.svg)](https://github.com/Lakito0100/Menu-Autoplanner/actions/workflows/tests.yml)
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

### Option B – Fertige App herunterladen (kein Python erforderlich)

Auf der [Releases-Seite](https://github.com/Lakito0100/Menu-Autoplanner/releases)
liegen beim jeweiligen Release unter **Assets** fertige Apps. Jedes Archiv enthält einen
Ordner `Menueplaner` mit der App **und** der `Rezepte.xlsx`:

| System | Datei | Starten |
|--------|-------|---------|
| Windows 10/11 | `Menueplaner_win.zip` | Entpacken, Doppelklick auf `Menueplaner.exe` |
| macOS (nur Apple Silicon, M1 oder neuer) | `Menueplaner_mac.zip` | Entpacken, `Menueplaner.app` per Rechtsklick → „Öffnen" starten |
| Linux (x86-64) | `Menueplaner_linux.tar.gz` | `tar -xzf Menueplaner_linux.tar.gz` und dann `./Menueplaner/Menueplaner` |

`Rezepte.xlsx` muss immer im selben Ordner wie die App bleiben (unter macOS neben
`Menueplaner.app`). Hinweise zu Sicherheitswarnungen stehen im Abschnitt
[Release erstellen](#release-erstellen).

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

## Tests

Die Tests (pytest) starten die App jeweils in einem temporären Ordner und prüfen
Wochenplan, Einkaufsliste, Export, Rezeptverwaltung, Sitzungsspeicherung und
plattformabhängiges Verhalten (Fenstergrösse, Mausrad).

```bash
pip install -r requirements-dev.txt
python -m pytest              # Windows / macOS
xvfb-run -a python -m pytest  # Linux ohne Bildschirm (z. B. Server)
```

Bei jedem Pull Request und jedem Push auf `main`/`development` laufen die Tests
automatisch über GitHub Actions auf **Windows, macOS und Linux** (Workflow
`.github/workflows/tests.yml`). Das Ergebnis steht im Pull Request unter „Checks".

Zusätzlich hat die App einen Selbsttest, der auch mit der kompilierten App
funktioniert: Mit `MENUEPLANER_SELBSTTEST=1` startet sie, probiert die
wichtigsten Funktionen aus und beendet sich mit Exit-Code 0 (ok). Das Ergebnis
steht in `selbsttest.log` im Programmordner.

---

## Release erstellen

Beim Veröffentlichen eines Releases auf GitHub baut der Workflow
`.github/workflows/release.yml` automatisch die Apps für Windows, macOS und Linux,
startet jede kompilierte App mit dem Selbsttest und hängt sie an das Release an.

1. **Version erhöhen:** `__version__` in `menu_planer.py` setzen (z. B. `"1.2.0"`),
   außerdem Versions-Badge und Versionsverlauf im README anpassen (prüft auch ein Test).
2. Änderungen über einen Pull Request nach `main` bringen und warten, bis die Tests grün sind.
3. Auf GitHub **Releases → „Draft a new release"** öffnen.
4. Bei **„Choose a tag"** den neuen Tag eingeben, genau `v` + Version (z. B. `v1.2.0`)
   → „Create new tag on publish". Als Ziel (Target) `main` wählen.
5. Titel und Beschreibung eintragen, dann **„Publish release"** klicken.
6. Unter **Actions → Release-Builds** läuft jetzt der Build (ca. 10–15 Minuten).
   Danach stehen beim Release unter **Assets** die Dateien `Menueplaner_win.zip`,
   `Menueplaner_mac.zip` und `Menueplaner_linux.tar.gz`.

Passt der Tag nicht zu `__version__`, oder schlägt der Selbsttest einer App fehl,
bricht der Workflow ab und es wird nichts hochgeladen. Das `selbsttest.log` steht
dann im Log des Schritts „Selbsttest". Nach einer Korrektur lässt sich der Build
über **Actions → Release-Builds → „Run workflow"** mit dem Tag erneut starten
(vorhandene Dateien werden ersetzt). Ohne Tag wird nur gebaut. Die Apps liegen dann
14 Tage lang als Artefakte in der Zusammenfassung des Workflow-Laufs, praktisch zum
Ausprobieren vor einem Release.

**Hinweise zu den fertigen Apps:**

- **Nicht signiert:** Die Apps haben keine kostenpflichtige Code-Signatur.
  - *Windows (SmartScreen):* „Der Computer wurde durch Windows geschützt" →
    „Weitere Informationen" → „Trotzdem ausführen".
  - *macOS (Gatekeeper):* Beim ersten Start Rechtsklick auf `Menueplaner.app` →
    „Öffnen". Ab macOS 15: nach dem ersten Versuch unter **Systemeinstellungen →
    Datenschutz & Sicherheit** auf „Dennoch öffnen" klicken. Alternativ im
    Terminal: `xattr -dr com.apple.quarantine Menueplaner.app`
- **macOS nur Apple Silicon:** Der Mac-Build entsteht auf einem Apple-Silicon-Runner
  (arm64) und läuft nur auf Macs mit M1-Chip oder neuer. Auf Intel-Macs bitte
  `./start_menu_planer.sh` (Option A) verwenden oder mit `./build_mac.sh` selbst bauen.
- **Linux:** Gebaut auf Ubuntu 22.04 – läuft damit auch auf älteren Distributionen
  (ungefähr ab Ubuntu 22.04, Debian 12, Fedora 36).

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
| `tests/`, `pytest.ini` | Automatische Tests (pytest) |
| `requirements-dev.txt` | Abhängigkeiten für die Tests |
| `.github/workflows/tests.yml` | Tests auf Windows, macOS und Linux bei jedem Pull Request |
| `.github/workflows/release.yml` | Baut und testet die Apps bei jedem Release und hängt sie an |
| `Menueplaner.spec` | PyInstaller-Konfigurationsdatei — nicht manuell bearbeiten |

---

## Versionsverlauf

| Version | Neuerungen |
|---------|-----------|
| **v1.1.1** | Linux/macOS-Unterstützung verbessert (Fenstergrösse, Mausrad, Build- und Startskripte); Kompatibilität mit pandas 3; automatische Tests und Release-Builds für alle drei Systeme; zahlreiche Bug-Fixes (Rezept bearbeiten/umbenennen, Session-Speicherung beim Schliessen, gelöschte Einkaufslisten-Einträge, Zutaten-Erkennung) |
| **v1.1.0** | Einkaufsliste: Eintrag löschen, Liste zurücksetzen; Wochenplan als Text kopieren; Bug-Fixes (Fehlerbehandlung bei Datei-I/O, Session-Validierung, Mausrad-Scrolling) |
| **v1.0.0** | Erstveröffentlichung |

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
