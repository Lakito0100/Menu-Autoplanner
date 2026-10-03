"""Rezeptverwaltung: Laden, Speichern, Umbenennen, Löschen (inkl. pandas-3-Regression)."""
import pandas as pd

MO_MI = "Montag_Mittagessen"
SPAGHETTI = "Spaghetti mit Fenchel"
SPAGHETTI_NAME = "(4WPP S.45) Spaghetti mit Fenchel und Parmesan"


def excel(app):
    return pd.read_excel(app.REZEPTE_FILE)


def zeile(app, name):
    daten = excel(app)
    treffer = daten[daten["Rezeptname"] == name]
    assert len(treffer) == 1, f"{name}: {len(treffer)} Zeilen"
    return treffer.iloc[0]


def zutaten_der_zeile(z):
    return [str(v) for k, v in z.items() if str(k).startswith("Zutat") and pd.notna(v)]


def speichern(app, win):
    app.dialoge.meldungen.clear()
    app.button(win, "Speichern").invoke()
    app.update()
    return app.dialoge.letzte()


def test_rezeptliste_natuerlich_sortiert(app):
    win = app.oeffne_verwaltung()
    lb = [w for w in app.alle_widgets(win) if w.winfo_class() == "Listbox"][0]
    eintraege = list(lb.get(0, "end"))
    assert len(eintraege) == len(app.rezept_infos)
    assert eintraege.index(app.label("S.20)")) < eintraege.index(app.label("S.101)"))


def test_rezept_laden_zeigt_originaltexte(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    f = app.formular(win)
    assert f["name"].get() == SPAGHETTI_NAME
    assert f["kategorie"].get() == "Pasta"
    assert f["punkte"].get() == "10"
    assert f["portionen"].get() == "1"
    assert [e.get() for e in f["zutaten"]] == zutaten_der_zeile(zeile(app, SPAGHETTI_NAME))


def test_speichern_ohne_aenderung_veraendert_nichts(app):
    vorher = zutaten_der_zeile(zeile(app, SPAGHETTI_NAME))
    win = app.oeffne_verwaltung(SPAGHETTI)
    assert speichern(app, win)[0] == "showinfo"
    assert zutaten_der_zeile(zeile(app, SPAGHETTI_NAME)) == vorher  # z.B. "Salz, Pfeffer" bleibt
    assert len(excel(app)) == 71


def test_kommapunkte_und_viele_zutaten(app):
    """Regression: mit pandas 3 schlug das Speichern hier mit TypeError fehl."""
    app.waehle_rezept(MO_MI, SPAGHETTI)
    win = app.oeffne_verwaltung(SPAGHETTI)
    f = app.formular(win)
    app.setze(f["punkte"], "11,5")
    for _ in range(45):
        app.button(win, "+ Zutat hinzufügen").invoke()
    f = app.formular(win)
    for i, e in enumerate(f["zutaten"]):
        if not e.get():
            e.insert(0, f"{i} g Testzutat {i}")
    assert speichern(app, win)[0] == "showinfo"
    z = zeile(app, SPAGHETTI_NAME)
    assert z["Punkte"] == 11.5
    assert len(zutaten_der_zeile(z)) == len(f["zutaten"]) > 40
    # Wochenplan behält das Rezept, obwohl sich das Label geändert hat
    assert app.auswahl_rezept[MO_MI].get() == f"{SPAGHETTI_NAME} (11.5 Pkt)"
    assert app.punkte_labels["Montag"]["text"] == "11.5 Pkt"


def test_zutat_entfernen(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    anzahl = len(app.formular(win)["zutaten"])
    loeschen = [b for b in app.widgets(win, "TButton") if b.cget("text") == "✕"]
    loeschen[0].invoke()
    app.update()
    assert len(app.formular(win)["zutaten"]) == anzahl - 1
    speichern(app, win)
    assert len(zutaten_der_zeile(zeile(app, SPAGHETTI_NAME))) == anzahl - 1


def test_umbenennen(app):
    app.waehle_rezept(MO_MI, SPAGHETTI)
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.setze(app.formular(win)["name"], "Spaghetti Neu")
    assert speichern(app, win)[0] == "showinfo"
    assert app.auswahl_rezept[MO_MI].get() == "Spaghetti Neu (10 Pkt)"
    assert SPAGHETTI_NAME not in app.label_by_name
    daten = excel(app)
    assert len(daten) == 71
    assert (daten["Rezeptname"] == "Spaghetti Neu").sum() == 1
    assert app.dialoge.fragen == []


def test_neues_rezept(app):
    win = app.oeffne_verwaltung()
    f = app.formular(win)
    app.setze(f["name"], "Testrezept")
    app.setze(f["punkte"], "3")
    f["zutaten"][0].insert(0, "200 g Reis")
    f["zutaten"][1].insert(0, "Salz")
    assert speichern(app, win)[0] == "showinfo"
    info = app.rezept_infos["Testrezept (3 Pkt)"]
    assert info["kategorie"] == "Allgemein"
    assert info["portionen"] == 1.0
    assert [z["text"] for z in info["zutaten"]] == ["200 g Reis", "Salz"]
    assert "Allgemein" in app.auswahl_kat[MO_MI]["values"]
    z = zeile(app, "Testrezept")
    assert zutaten_der_zeile(z) == ["200 g Reis", "Salz"]
    assert len(excel(app)) == 72


def test_neues_rezept_mit_bestehendem_namen_fragt_nach(app):
    win = app.oeffne_verwaltung()
    f = app.formular(win)
    app.setze(f["name"], SPAGHETTI_NAME)
    app.setze(f["punkte"], "1")
    app.dialoge.ja = False
    speichern(app, win)
    assert len(app.dialoge.fragen) == 1
    assert zeile(app, SPAGHETTI_NAME)["Punkte"] == 10  # nicht überschrieben

    app.dialoge.ja = True
    speichern(app, win)
    assert zeile(app, SPAGHETTI_NAME)["Punkte"] == 1
    assert len(excel(app)) == 71


def test_umbenennen_auf_bestehenden_namen(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.setze(app.formular(win)["name"], "(4WPP S.137) Penne all'arrabbiata")
    app.dialoge.ja = True
    speichern(app, win)
    daten = excel(app)
    assert len(daten) == 70
    assert (daten["Rezeptname"] == SPAGHETTI_NAME).sum() == 0
    assert (daten["Rezeptname"] == "(4WPP S.137) Penne all'arrabbiata").sum() == 1


def test_ungueltige_eingaben(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    f = app.formular(win)
    for feld, wert, meldung in [
        ("name", "  ", "Rezeptname darf nicht leer sein."),
        ("punkte", "viel", "Punkte müssen eine Zahl sein."),
        ("punkte", "inf", "Punkte müssen eine Zahl sein."),
        ("portionen", "0", "Portionen müssen eine Zahl grösser 0 sein."),
        ("portionen", "-1", "Portionen müssen eine Zahl grösser 0 sein."),
        ("portionen", "zwei", "Portionen müssen eine Zahl grösser 0 sein."),
    ]:
        app.waehle_in_liste(win, SPAGHETTI)  # Formular jeweils neu laden
        app.setze(f[feld], wert)
        art, (titel, text) = speichern(app, win)
        assert art == "showwarning", feld
        assert text == meldung
    assert zeile(app, SPAGHETTI_NAME)["Punkte"] == 10


def test_leere_portionen_bedeuten_eine(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.setze(app.formular(win)["portionen"], "")
    assert speichern(app, win)[0] == "showinfo"
    assert zeile(app, SPAGHETTI_NAME)["Portionen"] == 1


def test_lesefehler_ueberschreibt_datei_nicht(app):
    vorher = (app.verzeichnis / "Rezepte.xlsx").read_bytes()

    def kaputt():
        raise PermissionError("Datei ist in Excel geöffnet")

    app.g["_lese_rezepte_zum_bearbeiten"] = kaputt
    win = app.oeffne_verwaltung(SPAGHETTI)
    art, (titel, text) = speichern(app, win)
    assert art == "showerror"
    assert "in Excel geöffnet" in text
    assert (app.verzeichnis / "Rezepte.xlsx").read_bytes() == vorher


def test_schreibfehler_wird_gemeldet(app, monkeypatch):
    def kaputt(self, *a, **k):
        raise PermissionError("schreibgeschützt")

    monkeypatch.setattr(pd.DataFrame, "to_excel", kaputt)
    win = app.oeffne_verwaltung(SPAGHETTI)
    art, (titel, text) = speichern(app, win)
    assert art == "showerror"
    assert "schreibgeschützt" in text


def test_loeschen(app):
    app.waehle_rezept(MO_MI, SPAGHETTI)
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.dialoge.meldungen.clear()
    app.button(win, "Löschen").invoke()
    app.update()
    assert app.dialoge.letzte()[0] == "showinfo"
    assert len(excel(app)) == 70
    assert SPAGHETTI_NAME not in app.label_by_name
    # Der Platz im Wochenplan wird geleert (nicht durch ein anderes Rezept ersetzt)
    assert app.auswahl_rezept[MO_MI].get() == ""
    assert app.formular(win)["name"].get() == ""


def test_loeschen_abbrechen(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.dialoge.ja = False
    app.button(win, "Löschen").invoke()
    assert len(excel(app)) == 71


def test_loeschen_ohne_auswahl(app):
    win = app.oeffne_verwaltung()
    app.button(win, "Löschen").invoke()
    assert app.dialoge.letzte()[0] == "showwarning"


def test_neues_rezept_leert_formular(app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.button(win, "Neues Rezept").invoke()
    f = app.formular(win)
    assert f["name"].get() == f["punkte"].get() == f["portionen"].get() == ""
    assert f["kategorie"].get() == ""
    assert [e.get() for e in f["zutaten"]] == ["", "", ""]


def test_aenderungen_ueberleben_neustart(app, starte_app):
    win = app.oeffne_verwaltung(SPAGHETTI)
    app.setze(app.formular(win)["punkte"], "7")
    speichern(app, win)
    app.root.destroy()
    neu = starte_app()
    assert f"{SPAGHETTI_NAME} (7 Pkt)" in neu.rezept_infos
