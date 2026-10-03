"""Plattformabhängiges Oberflächenverhalten: Fenstergrösse, Mausrad, Unterfenster."""
import sys
import tkinter as tk

import pytest

MO_FR = "Montag_Frühstück"


def test_hauptfenster_passt_zu_inhalt_und_bildschirm(app):
    root = app.root
    app.update()
    inhalt = app.scroll_frame.winfo_reqwidth()
    assert root.winfo_width() >= min(inhalt, root.winfo_screenwidth() - 40)
    assert root.winfo_height() <= root.winfo_screenheight()
    assert root.winfo_width() <= root.winfo_screenwidth()


@pytest.mark.parametrize("oeffnen", ["zeige_einkaufsliste", "oeffne_rezeptverwaltung"])
def test_unterfenster_zeigen_ihren_ganzen_inhalt(app, oeffnen):
    app.g[oeffnen]()
    app.update()
    win = app.fenster()
    assert win.winfo_width() >= min(win.winfo_reqwidth(), win.winfo_screenwidth() - 40)
    assert win.winfo_height() <= win.winfo_screenheight()
    assert str(win.transient()) == str(app.root)


def test_zutatenzeilen_inkl_loeschbutton_sichtbar(app):
    win = app.oeffne_verwaltung()
    canvas = [w for w in app.alle_widgets(win) if isinstance(w, tk.Canvas)][0]
    zeilen = canvas.winfo_children()[0]
    assert int(canvas.cget("width")) >= zeilen.winfo_reqwidth()


def kleines_fenster(app):
    app.root.geometry("900x300")  # Inhalt muss scrollbar sein
    app.update()
    app.canvas.yview_moveto(0)
    app.update()


def mausrad_runter(widget):
    if sys.platform.startswith("linux") and tk.TkVersion < 9:
        widget.event_generate("<Button-5>")
    else:
        widget.event_generate("<MouseWheel>", delta=-120)


@pytest.mark.parametrize("feld", ["auswahl_kat", "auswahl_rezept", "anzahl_personen"])
def test_mausrad_ueber_feldern_scrollt_seite_statt_wert_zu_aendern(app, feld):
    """Regression: ttk.Combobox wechselte beim Scrollen den Wert."""
    app.waehle_kategorie(MO_FR, "Pasta")
    kleines_fenster(app)
    widget = app.g[feld][MO_FR]
    vorher = widget.get()
    mausrad_runter(widget)
    app.update()
    assert widget.get() == vorher
    assert app.canvas.yview()[0] > 0


@pytest.mark.parametrize("event, kwargs", [
    ("<MouseWheel>", {"delta": -120}),  # Windows
    ("<MouseWheel>", {"delta": -1}),    # macOS / Touchpad
    ("<MouseWheel>", {"delta": -360}),  # schnelles Drehen
    ("<Button-5>", {}),                 # Linux (X11, Tk 8.6)
])
def test_mausrad_varianten(app, event, kwargs):
    kleines_fenster(app)
    label = [w for w in app.scroll_frame.winfo_children() if w.winfo_class() == "TLabel"][0]
    label.event_generate(event, **kwargs)
    app.update()
    assert app.canvas.yview()[0] > 0


def test_mausrad_nach_oben(app):
    kleines_fenster(app)
    app.canvas.yview_moveto(1)
    app.update()
    unten = app.canvas.yview()[0]
    label = [w for w in app.scroll_frame.winfo_children() if w.winfo_class() == "TLabel"][0]
    label.event_generate("<MouseWheel>", delta=120)
    app.update()
    assert app.canvas.yview()[0] < unten


def test_mausrad_ohne_scrollbaren_inhalt_tut_nichts(app):
    app.root.geometry("1400x2000")
    app.update()
    if app.canvas.yview() != (0.0, 1.0):
        pytest.skip("Bildschirm zu klein, Inhalt passt nicht komplett")
    label = [w for w in app.scroll_frame.winfo_children() if w.winfo_class() == "TLabel"][0]
    label.event_generate("<MouseWheel>", delta=-120)
    app.update()
    assert app.canvas.yview() == (0.0, 1.0)


def test_mausrad_in_rezeptverwaltung(app):
    win = app.oeffne_verwaltung("Spaghetti mit Fenchel")
    canvas = [w for w in app.alle_widgets(win) if isinstance(w, tk.Canvas)][0]
    assert canvas in app._scroll_canvases
    for _ in range(30):
        app.button(win, "+ Zutat hinzufügen").invoke()
    app.update()
    canvas.yview_moveto(0)
    app.formular(win)["zutaten"][0].event_generate("<MouseWheel>", delta=-120)
    app.update()
    assert canvas.yview()[0] > 0
    win.destroy()
    app.update()
    assert canvas not in app._scroll_canvases


def test_unterfenster_ist_modal(app):
    win, _ = app.oeffne_einkaufsliste()
    for _ in range(20):  # grab_set wird ggf. erst nach dem Anzeigen wiederholt
        app.update()
        if win.grab_current() is not None:
            break
        app.root.after(50)
    assert win.grab_current() == win
    app.schliesse(win)
    assert not win.winfo_exists()
