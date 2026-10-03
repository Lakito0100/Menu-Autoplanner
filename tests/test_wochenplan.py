"""Wochenplan: Auswahl, Suche, Punkte, Personen, Kopieren und Export."""
import pandas as pd
import pytest

MO_FR = "Montag_Frühstück"
MO_MI = "Montag_Mittagessen"
MO_AB = "Montag_Abendessen"


def test_grundaufbau(app):
    assert len(app.auswahl_kat) == 7 * 3
    assert set(app.punkte_labels) == set(app.tage)
    for key in app.auswahl_kat:
        assert app.auswahl_kat[key].get() == ""
        assert app.auswahl_rezept[key].get() == ""
        assert app.anzahl_personen[key].get() == "1"
    assert all(l["text"] == "0.0 Pkt" for l in app.punkte_labels.values())


def test_kategorie_waehlt_erstes_rezept(app):
    app.waehle_kategorie(MO_FR, "Pasta")
    assert app.auswahl_rezept[MO_FR].get() == app.rezepte_by_kategorie["Pasta"][0]
    assert list(app.auswahl_rezept[MO_FR]["values"]) == app.rezepte_by_kategorie["Pasta"]


def test_kategoriewechsel_behaelt_passendes_rezept(app):
    app.waehle_rezept(MO_FR, "Penne all'arrabbiata")
    app.waehle_kategorie(MO_FR, "Pasta")
    assert "Penne" in app.auswahl_rezept[MO_FR].get()


def test_rezeptwahl_setzt_kategorie(app):
    app.waehle_rezept(MO_FR, "Linsensuppe mit Pute")
    assert app.auswahl_kat[MO_FR].get() == "Suppen"


def test_suche_filtert_rezepte(app):
    box = app.auswahl_rezept[MO_FR]
    box.set("tofu")
    app.taste(box, "<KeyRelease>")
    werte = list(box["values"])
    assert werte and all("tofu" in w.lower() for w in werte)
    # mit Kategorie wird nur innerhalb der Kategorie gesucht
    app.auswahl_kat[MO_FR].set("Suppen")
    box.set("e")
    app.taste(box, "<KeyRelease>")
    assert set(box["values"]) <= set(app.rezepte_by_kategorie["Suppen"])


def test_tagespunkte(app):
    app.waehle_rezept(MO_FR, "Overnight Oats mit Pfirsich")  # 5 Pkt
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")        # 10 Pkt
    assert app.punkte_labels["Montag"]["text"] == "15.0 Pkt"
    assert app.punkte_labels["Dienstag"]["text"] == "0.0 Pkt"


def test_punkte_pro_portion(app_ordner, starte_app):
    pd.DataFrame([{"Rezeptname": "Auflauf", "Kategorie": "Test", "Punkte": 12, "Portionen": 4,
                   "Zutat 1": "400 g Nudeln"}]).to_excel(app_ordner / "Rezepte.xlsx", index=False)
    app = starte_app()
    app.waehle_rezept(MO_AB, "Auflauf")
    assert app.punkte_labels["Montag"]["text"] == "3.0 Pkt"


@pytest.mark.parametrize("eingabe, erwartet", [
    ("2", 2.0), ("1,5", 1.5), (" 3 ", 3.0), ("0", 0.0), ("abc", 1.0), ("", 1.0), ("-2", 1.0), ("inf", 1.0),
])
def test_personen_eingabe(app, eingabe, erwartet):
    app.setze_personen(MO_FR, eingabe)
    assert app.get_personen(MO_FR) == erwartet


def test_wochenplan_als_text(app):
    app.waehle_rezept(MO_FR, "Overnight Oats mit Pfirsich")
    app.setze_personen(MO_FR, 2)
    app.copy_wochenplan()
    text = app.root.clipboard_get()
    assert text.startswith("── Montag ──")
    assert "  Frühstück: (4WPP S.20) Overnight Oats mit Pfirsich (2 Pers.)" in text
    assert "  Mittagessen: –" in text
    assert "── Sonntag ──" in text
    assert app.dialoge.letzte()[0] == "showinfo"


def test_export_wochenplan_und_einkaufsliste(app, tmp_path):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app.setze_personen(MO_MI, 2)
    app.speichern_als = str(tmp_path / "plan")  # ohne Endung
    app.export_plan_und_einkaufsliste()
    assert app.dialoge.letzte() == ("showinfo", ("Erfolg", "Wochenplan und Einkaufsliste exportiert."))
    blaetter = pd.read_excel(tmp_path / "plan.xlsx", sheet_name=None)
    assert list(blaetter) == ["Wochenplan", "Einkaufsliste"]
    plan = blaetter["Wochenplan"]
    assert list(plan.columns) == ["Tag", "Frühstück", "Mittagessen", "Abendessen", "Punkte"]
    assert plan.loc[0, "Mittagessen"] == "(4WPP S.45) Spaghetti mit Fenchel und Parmesan (2 Pers.)"
    assert pd.isna(plan.loc[0, "Frühstück"])  # leere Mahlzeit bleibt leer
    assert plan.loc[0, "Punkte"] == "10.0 Pkt"
    liste = blaetter["Einkaufsliste"].set_index("Zutat")
    assert liste.loc["trockene Vollkornspaghetti", "Menge"] == 100  # als Zahl
    assert liste.loc["trockene Vollkornspaghetti", "Einheit"] == "g"


def test_export_abbrechen(app, tmp_path):
    app.speichern_als = ""
    app.export_plan_und_einkaufsliste()
    assert app.dialoge.meldungen == []


def test_export_fehler_wird_gemeldet(app, tmp_path):
    app.speichern_als = str(tmp_path / "gibt_es_nicht" / "plan.xlsx")
    app.export_plan_und_einkaufsliste()
    assert app.dialoge.letzte()[0] == "showerror"
