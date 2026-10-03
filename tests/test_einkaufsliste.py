"""Einkaufsliste: Berechnung, Bearbeiten, Speichern des Zustands, Export."""
import json

import pandas as pd

MO_FR = "Montag_Frühstück"
MO_MI = "Montag_Mittagessen"
DI_AB = "Dienstag_Abendessen"


def als_dict(liste):
    return {(zutat, einheit): menge for menge, einheit, zutat in liste}


def test_leere_einkaufsliste(app):
    assert app.generate_list() == []


def test_mengen_werden_skaliert_und_zusammengefasst(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app.setze_personen(MO_MI, 2)
    app.waehle_rezept(DI_AB, "Spaghetti mit Fenchel")
    app.setze_personen(DI_AB, "1,5")
    liste = als_dict(app.generate_list())
    assert liste[("trockene Vollkornspaghetti", "g")] == "175"  # 50 g × 3,5 Personen
    assert liste[("Salz, Pfeffer", "")] == ""                    # ohne Menge, nicht skaliert
    assert len(liste) == len(app.rezept_infos[app.label("Spaghetti mit Fenchel")]["zutaten"])


def test_null_personen(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app.setze_personen(MO_MI, 0)
    assert als_dict(app.generate_list())[("trockene Vollkornspaghetti", "g")] == "0"


def test_portionen_werden_beruecksichtigt(app_ordner, starte_app):
    pd.DataFrame([{"Rezeptname": "Auflauf", "Kategorie": "Test", "Punkte": 8, "Portionen": 4,
                   "Zutat 1": "400 g Nudeln", "Zutat 2": "1 Zwiebel", "Zutat 3": "Salz"}]
                 ).to_excel(app_ordner / "Rezepte.xlsx", index=False)
    app = starte_app()
    app.waehle_rezept(MO_MI, "Auflauf")
    app.setze_personen(MO_MI, 2)
    assert als_dict(app.generate_list()) == {("Nudeln", "g"): "200", ("Zwiebel", ""): "0.5", ("Salz", ""): ""}


def test_fenster_zeigt_liste(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    win, tree = app.oeffne_einkaufsliste()
    zeilen = app.zeilen(tree)
    assert ("50", "g", "trockene Vollkornspaghetti", "") in zeilen
    assert len(zeilen) == len(app.generate_list())
    app.schliesse(win)


def test_bearbeiten_und_zustand_bleibt_erhalten(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    win, tree = app.oeffne_einkaufsliste()
    eintraege = tree.get_children()
    vorhanden = app.zeilen(tree)[0][2]
    geloescht = app.zeilen(tree)[1][2]
    anzahl = len(eintraege)

    tree.selection_set(eintraege[0])
    app.button(win, "Als vorhanden markieren").invoke()
    assert app.zeilen(tree)[0][3] == "✓ vorhanden"

    tree.selection_set(eintraege[1])
    app.button(win, "Eintrag löschen").invoke()

    menge, einheit, zutat = app.widgets(win, "TEntry")
    menge.insert(0, "2")
    einheit.insert(0, "Stk")
    zutat.insert(0, "Zitronen")
    app.taste(zutat, "<Return>")  # Enter fügt ebenfalls hinzu
    assert zutat.get() == ""
    assert app.zeilen(tree)[-1] == ("2", "Stk", "Zitronen", "+ zusätzlich")
    assert len(tree.get_children()) == anzahl

    app.schliesse(win)
    zustand = json.loads((app.verzeichnis / "session.json").read_text(encoding="utf-8"))["einkaufsliste"]
    assert any(v[0] == vorhanden for v in zustand["vorhanden"])
    assert any(g[0] == geloescht for g in zustand["geloescht"])
    assert zustand["zusaetzlich"] == [{"menge": "2", "einheit": "Stk", "zutat": "Zitronen"}]

    # Wiederöffnen: Zustand ist noch da, gelöschter Eintrag bleibt weg
    win, tree = app.oeffne_einkaufsliste()
    namen = [z[2] for z in app.zeilen(tree)]
    assert geloescht not in namen
    assert "Zitronen" in namen
    assert [z for z in app.zeilen(tree) if z[2] == vorhanden][0][3] == "✓ vorhanden"

    # Zurücksetzen stellt die ursprüngliche Liste wieder her
    app.button(win, "Liste zurücksetzen").invoke()
    zeilen = app.zeilen(tree)
    assert len(zeilen) == anzahl
    assert geloescht in [z[2] for z in zeilen]
    assert "Zitronen" not in [z[2] for z in zeilen]
    assert all(z[3] == "" for z in zeilen)
    app.schliesse(win)
    zustand = json.loads((app.verzeichnis / "session.json").read_text(encoding="utf-8"))["einkaufsliste"]
    assert zustand == {"vorhanden": [], "zusaetzlich": [], "geloescht": []}


def test_vorhanden_umschalten(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    win, tree = app.oeffne_einkaufsliste()
    erster = tree.get_children()[0]
    tree.selection_set(erster)
    app.button(win, "Als vorhanden markieren").invoke()
    app.button(win, "Als vorhanden markieren").invoke()
    assert app.zeilen(tree)[0][3] == ""
    app.schliesse(win)


def test_zusaetzliche_eintraege_nicht_als_vorhanden_markierbar(app):
    win, tree = app.oeffne_einkaufsliste()
    app.widgets(win, "TEntry")[2].insert(0, "Brot")
    app.button(win, "Hinzufügen").invoke()
    tree.selection_set(tree.get_children()[0])
    app.button(win, "Als vorhanden markieren").invoke()
    assert app.zeilen(tree) == [("", "", "Brot", "+ zusätzlich")]
    app.schliesse(win)


def test_leere_zutat_wird_nicht_hinzugefuegt(app):
    win, tree = app.oeffne_einkaufsliste()
    app.widgets(win, "TEntry")[0].insert(0, "3")
    app.button(win, "Hinzufügen").invoke()
    assert app.zeilen(tree) == []
    app.schliesse(win)


def test_als_text_kopieren(app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    win, tree = app.oeffne_einkaufsliste()
    tree.selection_set(tree.get_children()[0])
    app.button(win, "Als vorhanden markieren").invoke()
    app.button(win, "Als Text kopieren").invoke()
    zeilen = app.root.clipboard_get().splitlines()
    assert zeilen[0].endswith("  [✓ vorhanden]")
    assert "50 g trockene Vollkornspaghetti" in zeilen
    assert "Salz, Pfeffer" in zeilen
    app.schliesse(win)


def test_export_aus_fenster(app, tmp_path):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    win, tree = app.oeffne_einkaufsliste()
    app.speichern_als = str(tmp_path / "liste")
    app.button(win, "Als Excel exportieren").invoke()
    daten = pd.read_excel(tmp_path / "liste.xlsx")
    assert list(daten.columns) == ["Menge", "Einheit", "Zutat", "Status"]
    assert len(daten) == len(tree.get_children())
    assert daten.set_index("Zutat").loc["trockene Vollkornspaghetti", "Menge"] == 50
    app.schliesse(win)


def test_export_leerer_liste_warnt(app):
    win, _ = app.oeffne_einkaufsliste()
    app.button(win, "Als Excel exportieren").invoke()
    assert app.dialoge.letzte()[0] == "showwarning"
    app.schliesse(win)


def test_hauptexport_beruecksichtigt_status(app, tmp_path):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app._einkaufsliste_state.update({
        "vorhanden": [["Fenchelknolle", ""]],
        "geloescht": [["Salz, Pfeffer", ""]],
        "zusaetzlich": [{"menge": "1", "einheit": "", "zutat": "Brot"}],
    })
    app.speichern_als = str(tmp_path / "plan.xlsx")
    app.export_plan_und_einkaufsliste()
    liste = pd.read_excel(tmp_path / "plan.xlsx", sheet_name="Einkaufsliste").set_index("Zutat")
    assert liste.loc["Fenchelknolle", "Status"] == "✓ vorhanden"
    assert "Salz, Pfeffer" not in liste.index
    assert liste.loc["Brot", "Status"] == "+ zusätzlich"
