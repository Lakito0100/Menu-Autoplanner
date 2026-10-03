"""Laden der Rezeptdatenbank (Rezepte.xlsx)."""
import math

import pandas as pd
import pytest

from conftest import REZEPTE_DATEI


def schreibe_rezepte(ordner, zeilen):
    pd.DataFrame(zeilen).to_excel(ordner / "Rezepte.xlsx", index=False)


def test_mitgelieferte_rezepte_werden_geladen(app):
    original = pd.read_excel(REZEPTE_DATEI)
    assert len(app.rezept_infos) == original["Rezeptname"].nunique()
    for label, info in app.rezept_infos.items():
        assert label.startswith(info["rezeptname"])
        assert label.endswith(" Pkt)")
        assert info["portionen"] > 0
        assert math.isfinite(info["punkte"])
        assert label in app.rezepte_by_kategorie[info["kategorie"]]
        assert app.label_by_name[info["rezeptname"]] == label


def test_alle_zutaten_der_datenbank_sind_parsebar(app):
    for info in app.rezept_infos.values():
        for z in info["zutaten"]:
            assert z["zutat"], z
            assert z["menge"] is None or z["menge"] > 0, z


def test_beispielrezept(app):
    info = app.rezept_infos[app.label("Spaghetti mit Fenchel")]
    assert info["kategorie"] == "Pasta"
    assert info["punkte"] == 10
    assert info["portionen"] == 1
    zutaten = {(z["zutat"], z["einheit"]): z["menge"] for z in info["zutaten"]}
    assert zutaten[("trockene Vollkornspaghetti", "g")] == 50
    assert zutaten[("Salz, Pfeffer", "")] is None


def test_sonderfaelle_in_excel(app_ordner, starte_app):
    schreibe_rezepte(app_ordner, [
        {"Rezeptname": "Normal", "Kategorie": "Test", "Punkte": 4, "Portionen": 2, "Zutat 1": "200 g Reis"},
        {"Rezeptname": None, "Kategorie": "Test", "Punkte": 1},                     # leere Zeile
        {"Rezeptname": "   ", "Kategorie": "Test", "Punkte": 1},                    # nur Leerzeichen
        {"Rezeptname": 123, "Kategorie": "Test", "Punkte": "abc", "Portionen": 0},  # Zahl als Name
        {"Rezeptname": "Unendlich", "Kategorie": "Test", "Punkte": float("inf"), "Zutat 1": "   "},
        {"Rezeptname": "Komma", "Kategorie": None, "Punkte": "2,5", "Portionen": "1,5"},
        {"Rezeptname": "Normal", "Kategorie": "Doppelt", "Punkte": 99},            # doppelter Name
    ])
    app = starte_app()
    assert sorted(app.label_by_name) == ["123", "Komma", "Normal", "Unendlich"]
    assert app.rezept_infos["123 (0 Pkt)"]["portionen"] == 1.0
    assert app.rezept_infos["Unendlich (0 Pkt)"]["zutaten"] == []
    komma = app.rezept_infos["Komma (2.5 Pkt)"]
    assert komma["kategorie"] == "Allgemein"
    assert komma["portionen"] == 1.5
    assert app.rezept_infos["Normal (4 Pkt)"]["kategorie"] == "Test"
    assert "Doppelt" not in app.rezepte_by_kategorie


def test_nur_pflichtspalte(app_ordner, starte_app):
    schreibe_rezepte(app_ordner, [{"Rezeptname": "Minimal"}])
    app = starte_app()
    info = app.rezept_infos["Minimal (0 Pkt)"]
    assert info["kategorie"] == "Allgemein"
    assert info["portionen"] == 1.0


def test_fehlende_rezeptdatei_beendet_mit_meldung(app_ordner, starte_app, dialoge):
    (app_ordner / "Rezepte.xlsx").unlink()
    with pytest.raises(SystemExit) as e:
        starte_app()
    assert e.value.code == 1
    assert dialoge.letzte()[0] == "showerror"
    assert "Rezepte.xlsx" in dialoge.letzte()[1][1]


def test_kaputte_rezeptdatei_beendet_mit_meldung(app_ordner, starte_app, dialoge):
    (app_ordner / "Rezepte.xlsx").write_bytes(b"keine Excel-Datei")
    with pytest.raises(SystemExit):
        starte_app()
    assert dialoge.letzte()[1][0] == "Fehler beim Laden"


def test_finde_rezept_label(app):
    label = app.label("Spaghetti mit Fenchel")
    name = app.rezept_infos[label]["rezeptname"]
    assert app.finde_rezept_label(label) == label
    assert app.finde_rezept_label(name) == label
    assert app.finde_rezept_label(f"{name} (99 Pkt)") == label  # veraltete Punkte
    assert app.finde_rezept_label("veraltet", name) == label
    assert app.finde_rezept_label("gibt es nicht") == ""
    assert app.finde_rezept_label("") == ""


def tk_der_einmal_fehlschlaegt(monkeypatch):
    """Simuliert den sporadischen Windows-Fehler beim ersten Tk-Start."""
    import time
    import tkinter as tk
    echtes_tk = tk.Tk
    versuche = []

    def tk_mit_fehler(*a, **k):
        versuche.append(1)
        if len(versuche) == 1:
            raise tk.TclError('invalid command name "tcl_findLibrary"')
        return echtes_tk(*a, **k)

    monkeypatch.setattr(tk, "Tk", tk_mit_fehler)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    return versuche


def test_start_uebersteht_voruebergehenden_tk_fehler(starte_app, monkeypatch):
    versuche = tk_der_einmal_fehlschlaegt(monkeypatch)
    app = starte_app()
    assert len(versuche) == 2
    assert app.rezept_infos


def test_fehlermeldung_uebersteht_voruebergehenden_tk_fehler(app_ordner, starte_app, dialoge, monkeypatch):
    """Regression (CI Windows): das Fehlerfenster startete Tk ohne Wiederholung."""
    (app_ordner / "Rezepte.xlsx").unlink()
    versuche = tk_der_einmal_fehlschlaegt(monkeypatch)
    with pytest.raises(SystemExit) as e:
        starte_app()
    assert e.value.code == 1
    assert len(versuche) == 2
    assert dialoge.letzte()[1][0] == "Rezeptdatei fehlt"
