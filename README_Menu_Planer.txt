Menüplaner - Anleitung
=======================

Dies ist ein lokal ausführbares Python-Tool zum wöchentlichen Planen von Mahlzeiten mit Rezeptdatenbank und automatischer Einkaufsliste.

Voraussetzungen
---------------
- Python 3.x (z. B. über Anaconda installiert)
- Tkinter (meist in Python enthalten)
- pandas
- openpyxl

Installation
------------
1. Stelle sicher, dass du Python installiert hast.
2. Stelle sicher, dass `pandas` und `openpyxl` installiert sind:
   Öffne eine Konsole und gib ein:

   pip install pandas openpyxl

3. Lege die folgenden Dateien in denselben Ordner:
   - `menu_planer.py` (Hauptprogramm)
   - `Rezepte.xlsx` (Rezeptdatenbank)

Verwendung
----------
1. Starte das Programm mit Doppelklick auf die "start_menu_planer" Datei
   (oder manuell mit: python menu_planer.py)

2. Wähle für jeden Tag und jede Mahlzeit:
   - Eine Kategorie
   - Ein Rezept aus dieser Kategorie
   - Die Anzahl Personen, die mitessen

3. Im unteren Bereich kannst du:
   - Die Einkaufsliste + Wochenplan als Excel exportieren
   - Das Programm sauber beenden

Rezeptdatenbank (Excel)
------------------------
Die Datei `Rezepte.xlsx` enthält alle verfügbaren Rezepte.

Wichtige Spalten:
- `Rezeptname`: Name des Rezepts
- `Punkte`: Anzahl Punkte nach WW
- `Kategorie`: z. B. Suppe, Bowls, Spaghetti etc.
- `Portionen`: Für wie viele Personen das Rezept gedacht ist
- `Zutat 1` bis `Zutat n`: Zutaten in folgendem Format:

    [Menge] [Einheit] [Name]
    Beispiel: 500 g Hackfleisch

Formate:
- Mengen mit Komma oder Punkt erlaubt: "1,5 l" oder "1.5 l"
- Optional auch: "2 Eier" (ohne Einheit)
- Ungültige Formate werden mit Standardwert ersetzt

Erzeugte Excel-Datei
---------------------
Beim Export entstehen zwei Tabellenblätter:
- `Wochenplan`: Übersicht über Frühstück, Mittagessen und Abendessen + Personen
- `Einkaufsliste`: Zusammengefasste Mengen aller benötigten Zutaten
