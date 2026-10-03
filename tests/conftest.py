"""Gemeinsame Hilfsmittel für die Tests.

Die App (menu_planer.py) baut beim Import sofort ihre Oberfläche auf. Für jeden
Test wird sie deshalb in einem eigenen temporären Ordner (mit eigener
Rezepte.xlsx und session.json) frisch gestartet – ohne mainloop und mit
abgefangenen Dialogen, damit nichts blockiert.

Unter Linux brauchen die Tests ein Display, z.B.:  xvfb-run -a python -m pytest
"""
import os
import runpy
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import pytest

REPO = Path(__file__).resolve().parent.parent
APP_DATEI = REPO / "menu_planer.py"
REZEPTE_DATEI = REPO / "Rezepte.xlsx"


class Dialoge:
    """Ersetzt Messageboxen: zeichnet sie auf, askyesno antwortet mit `ja`."""

    def __init__(self):
        self.meldungen = []
        self.fragen = []
        self.ja = True

    def letzte(self):
        return self.meldungen[-1] if self.meldungen else None

    def arten(self):
        return [art for art, _ in self.meldungen]


class App:
    """Zugriff auf eine laufende App-Instanz und Hilfsfunktionen zur Bedienung."""

    def __init__(self, g, verzeichnis, dialoge):
        self.g = g  # die echten Modul-Globals der App
        self.verzeichnis = Path(verzeichnis)
        self.dialoge = dialoge
        self.speichern_als = None  # Rückgabewert von asksaveasfilename
        g["asksaveasfilename"] = lambda **kw: self.speichern_als or ""

    def __getattr__(self, name):
        try:
            return self.g[name]
        except KeyError:
            raise AttributeError(name)

    # ── allgemeine Hilfen ─────────────────────────────────────────────────
    def update(self):
        self.root.update()

    @staticmethod
    def alle_widgets(w):
        yield w
        for c in w.winfo_children():
            yield from App.alle_widgets(c)

    def fenster(self):
        """Das zuletzt geöffnete Unterfenster (Einkaufsliste/Rezeptverwaltung)."""
        tops = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
        assert tops, "kein Unterfenster offen"
        return tops[-1]

    def button(self, win, text):
        treffer = [w for w in self.alle_widgets(win)
                   if w.winfo_class() == "TButton" and w.cget("text") == text]
        assert treffer, f"Button '{text}' nicht gefunden"
        return treffer[0]

    def widgets(self, win, klasse):
        return [w for w in self.alle_widgets(win) if w.winfo_class() == klasse]

    def taste(self, widget, sequenz):
        """Tastatur-Events gehen in Tk an das fokussierte Widget – daher erst fokussieren."""
        widget.focus_force()
        for _ in range(10):
            self.update()
            if widget.focus_get() == widget:
                break
        else:
            pytest.skip("Tastaturfokus in dieser Umgebung nicht verfügbar")
        widget.event_generate(sequenz)
        self.update()

    def schliesse(self, win):
        """Schliessen wie über das Fenster-X."""
        win.tk.call(win.protocol("WM_DELETE_WINDOW"))
        self.update()

    # ── Wochenplan ────────────────────────────────────────────────────────
    def label(self, teil_name):
        treffer = [l for l in self.rezept_infos if teil_name in l]
        assert treffer, f"kein Rezept mit '{teil_name}'"
        return treffer[0]

    def waehle_kategorie(self, key, kategorie):
        self.auswahl_kat[key].set(kategorie)
        self.auswahl_kat[key].event_generate("<<ComboboxSelected>>")
        self.update()

    def waehle_rezept(self, key, teil_name):
        box = self.auswahl_rezept[key]
        box.set(self.label(teil_name))
        box.event_generate("<<ComboboxSelected>>")
        self.update()

    def setze_personen(self, key, wert):
        e = self.anzahl_personen[key]
        e.delete(0, tk.END)
        e.insert(0, str(wert))

    # ── Einkaufsliste ─────────────────────────────────────────────────────
    def oeffne_einkaufsliste(self):
        self.zeige_einkaufsliste()
        self.update()
        win = self.fenster()
        return win, self.widgets(win, "Treeview")[0]

    @staticmethod
    def zeilen(tree):
        return [tuple(tree.item(i, "values")) for i in tree.get_children()]

    # ── Rezeptverwaltung ──────────────────────────────────────────────────
    def oeffne_verwaltung(self, teil_name=None):
        self.oeffne_rezeptverwaltung()
        self.update()
        win = self.fenster()
        if teil_name:
            self.waehle_in_liste(win, teil_name)
        return win

    def waehle_in_liste(self, win, teil_name):
        lb = [w for w in self.alle_widgets(win) if isinstance(w, tk.Listbox)][0]
        idx = [i for i in range(lb.size()) if teil_name in lb.get(i)]
        assert idx, f"'{teil_name}' nicht in der Rezeptliste"
        lb.selection_clear(0, tk.END)
        lb.selection_set(idx[0])
        lb.event_generate("<<ListboxSelect>>")
        self.update()

    def formular(self, win):
        """Felder der Rezeptverwaltung: name, kategorie, punkte, portionen, zutaten."""
        entries = self.widgets(win, "TEntry")
        return {
            "name": entries[0],
            "kategorie": self.widgets(win, "TCombobox")[0],
            "punkte": entries[1],
            "portionen": entries[2],
            "zutaten": entries[3:],
        }

    @staticmethod
    def setze(feld, wert):
        feld.delete(0, tk.END)
        feld.insert(0, str(wert))


@pytest.fixture
def dialoge(monkeypatch):
    d = Dialoge()
    for art in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(messagebox, art,
                            lambda *a, _art=art, **k: d.meldungen.append((_art, a)))

    def askyesno(*a, **k):
        d.fragen.append(a)
        return d.ja

    monkeypatch.setattr(messagebox, "askyesno", askyesno)
    return d


@pytest.fixture
def app_ordner(tmp_path):
    """Leerer App-Ordner mit Programm und Original-Rezepte.xlsx."""
    ordner = tmp_path / "app"
    ordner.mkdir()
    shutil.copy(APP_DATEI, ordner / "menu_planer.py")
    shutil.copy(REZEPTE_DATEI, ordner / "Rezepte.xlsx")
    return ordner


@pytest.fixture
def starte_app(app_ordner, dialoge, monkeypatch):
    """Fabrik: starte_app() startet die App (auch mehrmals, z.B. für Neustarts)."""
    monkeypatch.setattr(tk.Tk, "mainloop", lambda self, n=0: None)
    monkeypatch.delenv("MENUEPLANER_SELBSTTEST", raising=False)
    for var in ("MENUEPLANER_ZOOM", "GDK_SCALE", "GDK_DPI_SCALE", "QT_SCALE_FACTOR"):
        monkeypatch.delenv(var, raising=False)
    gestartet = []

    def starte(ordner=None):
        ordner = Path(ordner or app_ordner)
        ergebnis = runpy.run_path(str(ordner / "menu_planer.py"), run_name="menu_planer_test")
        g = ergebnis["beenden"].__globals__  # run_path liefert nur eine Kopie
        app = App(g, ordner, dialoge)
        gestartet.append(app)
        app.update()
        return app

    yield starte

    for app in gestartet:
        try:
            app.root.destroy()
        except tk.TclError:
            pass  # schon zerstört (z.B. durch beenden())


@pytest.fixture
def app(starte_app):
    return starte_app()


def pytest_report_header(config):
    import pandas
    import openpyxl
    return (f"Tk {tk.TkVersion}, pandas {pandas.__version__}, openpyxl {openpyxl.__version__}, "
            f"DISPLAY={os.environ.get('DISPLAY', '-')}")
