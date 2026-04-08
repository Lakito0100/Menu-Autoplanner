Menüplaner - Anleitung
=======================

Dies ist ein lokal ausführbares Python-Tool zum wöchentlichen Planen von
Mahlzeiten mit Rezeptdatenbank, automatischer Einkaufsliste und
Punkte-Berechnung.


Voraussetzungen
---------------
- Python 3.x (z. B. über Anaconda installiert)
- Tkinter (meist in Python enthalten)
- pandas
- openpyxl

Alternativ: Fertige Windows-Anwendung `Menueplaner_win.exe` nutzen –
kein Python erforderlich.


Installation (Python)
---------------------
1. Stelle sicher, dass Python installiert ist.
2. Installiere die benötigten Bibliotheken:

   pip install pandas openpyxl

3. Lege folgende Dateien in denselben Ordner:
   - `menu_planer.py`   (Hauptprogramm)
   - `Rezepte.xlsx`     (Rezeptdatenbank)


Starten der Anwendung
----------------------
- Windows (Script):  Doppelklick auf `start_menu_planer.bat`
- Windows (EXE):     Doppelklick auf `Menueplaner_win.exe`
- Manuell:           python menu_planer.py


Funktionen im Überblick
------------------------

1. Wochenplanung
   - 7 Tage (Montag bis Sonntag), je 3 Mahlzeiten (Frühstück, Mittag, Abend)
   - Pro Mahlzeit wählbar: Kategorie, Rezept und Personenanzahl
   - Suchfunktion im Rezept-Dropdown (live filtern während der Eingabe)

2. Punkte
   - Live-Berechnung der Tagespunkte basierend auf gewählten Rezepten
   - Punktesumme pro Tag wird direkt in der Oberfläche angezeigt

3. Einkaufsliste
   - Automatische Zusammenfassung aller Zutaten aus dem Wochenplan
   - Mengen werden proportional zur eingegebenen Personenanzahl skaliert
   - Interaktives Fenster mit folgenden Optionen:
     * Artikel als "vorhanden" (erledigt) markieren
     * Eigene Artikel manuell hinzufügen
     * Liste als formatierten Text in die Zwischenablage kopieren
     * Einkaufsliste als Excel-Datei exportieren
   - Status (abgehakte Artikel, eigene Einträge) wird zwischen Sitzungen
     gespeichert

4. Rezeptverwaltung (CRUD)
   - Über den Button "Rezepte verwalten" erreichbar
   - Alle Rezepte anzeigen mit Suchfunktion und Scrollansicht
   - Neues Rezept hinzufügen:
     * Name, Kategorie, Punkte und Portionen angeben
     * Beliebig viele Zutatenzeilen dynamisch hinzufügen oder entfernen
   - Bestehendes Rezept bearbeiten (alle Felder inkl. Zutaten)
   - Rezept löschen (mit Bestätigungsdialog)

5. Session-Speicherung
   - Der aktuelle Wochenplan (gewählte Rezepte und Personenanzahl)
     sowie der Status der Einkaufsliste werden automatisch in
     `session.json` gespeichert
   - Beim nächsten Start wird die letzte Sitzung automatisch
     wiederhergestellt

6. Export
   - Exportiert eine Excel-Datei mit zwei Tabellenblättern:
     * `Wochenplan`: Übersicht aller Mahlzeiten mit Personenanzahl
       und Tagespunkten
     * `Einkaufsliste`: Aggregierte Zutatenliste mit Status


Rezeptdatenbank (Rezepte.xlsx)
-------------------------------
Die Datei `Rezepte.xlsx` enthält alle verfügbaren Rezepte.

Wichtige Spalten:
- `Rezeptname`:  Name des Rezepts
- `Punkte`:      Punkte für das gesamte Rezept
- `Kategorie`:   z. B. Suppe, Bowls, Spaghetti etc.
- `Portionen`:   Für wie viele Personen das Rezept ausgelegt ist
- `Zutat 1` bis `Zutat n`: Zutaten im Format:

    [Menge] [Einheit] [Name]
    Beispiel: 500 g Hackfleisch
              1,5 l Gemüsebrühe
              2 Eier         (ohne Einheit möglich)

Hinweise zum Format:
- Mengen mit Komma oder Punkt erlaubt: "1,5" oder "1.5"
- Einheit ist optional
- Ungültige Formate werden mit "1x [Name]" als Standardwert ersetzt


Windows EXE erstellen
----------------------
Um eine eigenständige Windows-Anwendung zu erstellen:

1. Führe `build_exe.bat` aus.
2. Die fertige Datei befindet sich danach unter `dist\Menueplaner.exe`.
3. Die Datei `Rezepte.xlsx` muss im selben Ordner wie die EXE liegen.

Voraussetzung: PyInstaller wird automatisch durch das Script installiert.
