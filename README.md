# Menüplaner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

> **Hinweis:** Die Punkte-Spalte ist generisch und kann für beliebige Ernährungsprogramme
> verwendet werden. Dieses Projekt steht in keiner Verbindung zur WW International, Inc.
> „Weight Watchers" ist eine eingetragene Marke der WW International, Inc.

Ein lokales Python-Werkzeug zur wöchentlichen Menüplanung mit Rezeptdatenbank,
automatischer Einkaufsliste und Punkte-Berechnung.

---

## Funktionen

- **Wochenplanung** – 7 Tage × 3 Mahlzeiten (Frühstück, Mittag, Abend) mit Kategorie- und Rezeptauswahl sowie Personenanzahl pro Mahlzeit
- **Rezeptsuche** – Live-Filterung im Dropdown während der Eingabe
- **Punkte** – Tagespunkte werden automatisch berechnet und angezeigt
- **Einkaufsliste** – Alle Zutaten automatisch aggregiert, mengenproportional skaliert nach Personenanzahl; Artikel als „vorhanden" markierbar oder manuell ergänzbar
- **Export** – Wochenplan + Einkaufsliste als Excel-Datei (`.xlsx`) mit zwei Tabellenblättern
- **Zwischenablage** – Einkaufsliste als formatierten Text kopieren
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

## Windows-EXE selbst erstellen

```bat
build_exe.bat
```

Die fertige Datei liegt danach unter `dist\Menueplaner.exe`.
PyInstaller wird durch das Skript automatisch installiert.
Die Datei `Rezepte.xlsx` muss sich im selben Ordner wie die EXE befinden.

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
