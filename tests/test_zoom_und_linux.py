"""Zoom für HiDPI-/4K-Bildschirme und Linux-spezifisches Verhalten beim Beenden."""
import json
import os
import stat
import sys
import tkinter.font as tkfont

import pytest


@pytest.mark.parametrize("x11, env, xft, hoehe_px, hoehe_mm, erwartet", [
    (False, {}, None, 2160, 0, 1.0),                        # Windows/macOS skalieren selbst
    (True, {}, None, 1080, 300, 1.0),                       # Full HD
    (True, {}, None, 2160, 572, 2.0),                       # 4K, X meldet 96 dpi (XWayland)
    (True, {}, None, 2160, 196, 2.0),                       # 4K-Laptop mit echter Grösse (280 dpi)
    (True, {}, None, 2160, 336, 1.5),                       # 27"-4K-Monitor (163 dpi)
    (True, {}, None, 1440, 381, 1.0),                       # 1440p ohne glaubwürdige DPI
    (True, {"GDK_SCALE": "2"}, None, 1080, 300, 2.0),       # Desktop-Vorgabe hat Vorrang
    (True, {"GDK_SCALE": "2", "GDK_DPI_SCALE": "0.75"}, None, 2160, 572, 1.5),
    (True, {"QT_SCALE_FACTOR": "1.25"}, None, 2160, 572, 1.25),
    (True, {"GDK_SCALE": "abc"}, None, 1080, 300, 1.0),     # ungültig -> ignoriert
    (True, {}, 192.0, 1080, 300, 2.0),                      # Xft.dpi (GNOME/KDE)
    (True, {}, 144.0, 2160, 572, 1.5),
    (True, {}, 96.0, 2160, 572, 2.0),                       # Xft.dpi 96 sagt nichts aus
    (True, {"GDK_SCALE": "10"}, None, 1080, 300, 3.0),      # begrenzt
])
def test_auto_zoom(app, x11, env, xft, hoehe_px, hoehe_mm, erwartet):
    assert app.berechne_auto_zoom(x11, env, xft, hoehe_px, hoehe_mm) == erwartet


def test_startet_mit_automatischem_zoom(app):
    assert app._zoom["faktor"] == app.auto_zoom()
    assert app._zoom["gespeichert"] is None


def test_zoom_vergroessert_schriften_und_elemente(app):
    app.zoom_einstellen(1.0, speichern=False)
    normal = tkfont.nametofont("TkDefaultFont", root=app.root).cget("size")
    titel = app.SCHRIFT_TITEL.cget("size")
    zeile = int(app.ttk.Style(app.root).lookup("Treeview", "rowheight"))
    breite = app.scroll_frame.winfo_reqwidth()

    app.zoom_einstellen(2.0, speichern=False)
    app.update()
    assert abs(tkfont.nametofont("TkDefaultFont", root=app.root).cget("size")) == 2 * abs(normal)
    assert app.SCHRIFT_TITEL.cget("size") == 2 * titel
    assert int(app.ttk.Style(app.root).lookup("Treeview", "rowheight")) > zeile
    assert app.scroll_frame.winfo_reqwidth() > 1.5 * breite
    assert app.px(10) == 20

    # zurück auf 100 % ergibt wieder die ursprünglichen Werte
    app.zoom_einstellen(1.0, speichern=False)
    assert tkfont.nametofont("TkDefaultFont", root=app.root).cget("size") == normal
    assert app.SCHRIFT_TITEL.cget("size") == titel


def test_zoom_wird_gespeichert_und_wiederhergestellt(app, starte_app):
    app.zoom_einstellen(1.5)
    daten = json.loads((app.verzeichnis / "session.json").read_text(encoding="utf-8"))
    assert daten["einstellungen"] == {"zoom": 1.5}
    app.root.destroy()

    neu = starte_app()
    assert neu._zoom == {"faktor": 1.5, "gespeichert": 1.5}
    assert neu._zoom_var.get() == 1.5

    neu.zoom_einstellen(None)  # zurück auf automatisch
    daten = json.loads((neu.verzeichnis / "session.json").read_text(encoding="utf-8"))
    assert "einstellungen" not in daten
    assert neu._zoom["faktor"] == neu.auto_zoom()


@pytest.mark.parametrize("wert", ["gross", 99, 0.1, True, None, [2]])
def test_ungueltiger_gespeicherter_zoom_wird_ignoriert(app_ordner, starte_app, wert):
    (app_ordner / "session.json").write_text(json.dumps({"einstellungen": {"zoom": wert}}), encoding="utf-8")
    app = starte_app()
    assert app._zoom["gespeichert"] is None
    assert app._zoom["faktor"] == app.auto_zoom()


def test_zoom_ueber_umgebungsvariable(starte_app, monkeypatch):
    monkeypatch.setenv("MENUEPLANER_ZOOM", "1.75")
    app = starte_app()
    assert app._zoom["faktor"] == 1.75


def test_zoom_schritte(app):
    app.zoom_einstellen(1.0, speichern=False)
    app.zoom_schritt(1)
    assert app._zoom["faktor"] == 1.25
    app.zoom_einstellen(1.1, speichern=False)  # Zwischenwert -> nächste Stufe
    app.zoom_schritt(1)
    assert app._zoom["faktor"] == 1.25
    app.zoom_einstellen(3.0, speichern=False)
    app.zoom_schritt(1)
    assert app._zoom["faktor"] == 3.0          # obere Grenze
    app.zoom_einstellen(0.75, speichern=False)
    app.zoom_schritt(-1)
    assert app._zoom["faktor"] == 0.75         # untere Grenze


def test_ansicht_menue(app):
    menue = app.root.nametowidget(app.root.cget("menu"))
    assert menue.entrycget(0, "label") == "Ansicht"
    ansicht = menue.nametowidget(menue.entrycget(0, "menu"))
    labels = [ansicht.entrycget(i, "label") for i in range(ansicht.index("end") + 1)
              if ansicht.type(i) != "separator"]
    assert labels[:3] == ["Grösser", "Kleiner", "Automatisch"]
    assert "200 %" in labels
    app.zoom_einstellen(1.0, speichern=False)
    ansicht.invoke(labels.index("200 %") + 1)  # +1 wegen Trennlinie
    assert app._zoom["faktor"] == 2.0


@pytest.mark.parametrize("taste, erwartet", [("plus", 1.25), ("minus", 0.75), ("0", None)])
def test_tastenkuerzel(app, taste, erwartet):
    app.zoom_einstellen(1.0, speichern=False)
    app.taste(app.auswahl_kat["Montag_Frühstück"], f"<{app._modifikator}-{taste}>")
    assert app._zoom["faktor"] == (app.auto_zoom() if erwartet is None else erwartet)


def test_einkaufsliste_spalten_wachsen_mit(app):
    app.zoom_einstellen(2.0, speichern=False)
    win, tree = app.oeffne_einkaufsliste()
    assert int(tree.column("Zutat", "width")) >= 600  # 300 px × 2 (ggf. gestreckt)
    app.schliesse(win)


def test_unterfenster_passen_bei_zoom_auf_bildschirm(app):
    app.zoom_einstellen(3.0, speichern=False)
    for oeffnen in (app.zeige_einkaufsliste, app.oeffne_rezeptverwaltung):
        oeffnen()
        app.update()
        win = app.fenster()
        assert win.winfo_width() <= win.winfo_screenwidth()
        assert win.winfo_height() <= win.winfo_screenheight()
        win.destroy()
    assert app.root.winfo_width() <= app.root.winfo_screenwidth()


def test_eingabefelder_uebernehmen_keine_systemauswahl(app):
    """Unter X11 würde sonst jede Textauswahl die PRIMARY-Auswahl belegen."""
    for widget in (app.auswahl_kat["Montag_Frühstück"], app.auswahl_rezept["Montag_Frühstück"],
                   app.anzahl_personen["Montag_Frühstück"]):
        assert not int(widget.cget("exportselection"))


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="nur unter X11")
def test_beenden_gibt_zwischenablage_frei(app):
    app.waehle_rezept("Montag_Frühstück", "Overnight Oats")
    app.copy_wochenplan()
    assert "Overnight Oats" in app.root.clipboard_get()
    app._auswahl_freigeben()
    with pytest.raises(app.tk.TclError):  # Zwischenablage ist jetzt leer
        app.root.clipboard_get()


@pytest.mark.skipif(sys.platform in ("win32", "darwin"), reason="nur unter X11")
def test_fremde_zwischenablage_wird_nicht_geloescht(app):
    app.root.clipboard_clear()
    app.root.clipboard_append("von einem anderen Programm")  # nicht über die App kopiert
    app._auswahl_freigeben()
    assert app.root.clipboard_get() == "von einem anderen Programm"


def test_temporaere_dateien_sind_versteckt(app, monkeypatch):
    ersetzt = []
    echtes_replace = os.replace

    def replace(quelle, ziel):
        ersetzt.append((os.path.basename(quelle), os.path.basename(ziel)))
        echtes_replace(quelle, ziel)

    monkeypatch.setattr(os, "replace", replace)
    app.save_session()
    win = app.oeffne_verwaltung("Spaghetti mit Fenchel")
    app.button(win, "Speichern").invoke()
    assert [z for _, z in ersetzt] == ["session.json", "Rezepte.xlsx"]
    assert all(q.startswith(".") for q, _ in ersetzt), ersetzt
    assert not [p for p in app.verzeichnis.iterdir() if p.name.startswith(".")]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-Dateirechte")
def test_rezeptdatei_behaelt_dateirechte(app):
    datei = app.verzeichnis / "Rezepte.xlsx"
    os.chmod(datei, 0o664)
    win = app.oeffne_verwaltung("Spaghetti mit Fenchel")
    app.button(win, "Speichern").invoke()
    assert stat.S_IMODE(os.stat(datei).st_mode) == 0o664


def test_abgebrochenes_speichern_laesst_rezeptdatei_unveraendert(app, monkeypatch):
    import pandas as pd
    vorher = (app.verzeichnis / "Rezepte.xlsx").read_bytes()

    def halb_geschrieben(self, pfad, *a, **k):
        with open(pfad, "wb") as f:
            f.write(b"kaputt")
        raise OSError("Datenträger voll")

    monkeypatch.setattr(pd.DataFrame, "to_excel", halb_geschrieben)
    win = app.oeffne_verwaltung("Spaghetti mit Fenchel")
    app.button(win, "Speichern").invoke()
    assert app.dialoge.letzte()[0] == "showerror"
    assert (app.verzeichnis / "Rezepte.xlsx").read_bytes() == vorher
    assert not [p for p in app.verzeichnis.iterdir() if p.name.startswith(".")]
