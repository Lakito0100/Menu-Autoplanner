"""Zerlegen von Zutaten und kleine Hilfsfunktionen."""
import pytest


@pytest.mark.parametrize("text, menge, einheit, zutat", [
    ("500 g Hackfleisch", 500, "g", "Hackfleisch"),
    ("1,5 l Gemüsebrühe", 1.5, "l", "Gemüsebrühe"),
    ("1.5 l Gemüsebrühe", 1.5, "l", "Gemüsebrühe"),
    ("2 Eier", 2, "", "Eier"),
    ("1 Pak Choi", 1, "", "Pak Choi"),                 # früher: Einheit "Pak"
    ("1 rote Zwiebel", 1, "", "rote Zwiebel"),         # früher: Einheit "rote"
    ("1 Rindersteak (ca. 180 g)", 1, "", "Rindersteak (ca. 180 g)"),
    ("3 EL zarte Haferflocken", 3, "EL", "zarte Haferflocken"),
    ("1 TL Senf", 1, "TL", "Senf"),
    ("1 Msp Zimt", 1, "Msp", "Zimt"),
    ("1 Stück Ingwer (ca. 1 cm pro Stück)", 1, "Stück", "Ingwer (ca. 1 cm pro Stück)"),
    ("2 Scheiben Brot", 2, "Scheiben", "Brot"),
    ("1 Handvoll Rucola", 1, "Handvoll", "Rucola"),
    ("0.5 Dose Thunfisch im eigenen Saft", 0.5, "Dose", "Thunfisch im eigenen Saft"),
    ("200g Mehl", 200, "g", "Mehl"),                   # ohne Leerzeichen
    ("1/2 TL Zimt", 0.5, "TL", "Zimt"),                # Bruch
    ("3/4 l Milch", 0.75, "l", "Milch"),
    ("  2   EL    Öl  ", 2, "EL", "Öl"),               # überzählige Leerzeichen
    ("100 ML Sahne", 100, "ML", "Sahne"),              # Einheit unabhängig von Gross/Klein
])
def test_zutat_mit_menge(app, text, menge, einheit, zutat):
    z = app.parse_zutat(text)
    assert z["menge"] == pytest.approx(menge)
    assert z["einheit"] == einheit
    assert z["zutat"] == zutat


@pytest.mark.parametrize("text", ["Salz, Pfeffer", "Pfeffer", "3", "etwas Petersilie", ""])
def test_zutat_ohne_menge(app, text):
    z = app.parse_zutat(text)
    assert z["menge"] is None
    assert z["einheit"] == ""
    assert z["zutat"] == text.strip()


def test_originaltext_bleibt_erhalten(app):
    assert app.parse_zutat("1,5 l Gemüsebrühe")["text"] == "1,5 l Gemüsebrühe"
    assert app.parse_zutat("Salz, Pfeffer")["text"] == "Salz, Pfeffer"


def test_bruch_mit_null_im_nenner_stuerzt_nicht_ab(app):
    assert app.parse_zutat("1/0 TL Salz")["menge"] == 1


def test_zahl_als_zelle(app):
    assert app.parse_zutat(5)["menge"] is None  # nur Zahl, kein Name
    assert app.parse_zutat(5)["zutat"] == "5"


@pytest.mark.parametrize("menge, text", [
    (None, ""), (3, "3"), (3.0, "3"), (0.5, "0.5"), (1 / 3, "0.33"), (149.999, "150"), (0, "0"),
])
def test_format_menge(app, menge, text):
    assert app.format_menge(menge) == text


@pytest.mark.parametrize("text, erwartet", [
    ("150", 150), ("0.5", 0.5), ("1,5", 1.5), ("", ""), ("abc", "abc"), ("inf", "inf"),
])
def test_als_zahl(app, text, erwartet):
    assert app._als_zahl(text) == erwartet
    assert type(app._als_zahl(text)) is type(erwartet)


@pytest.mark.parametrize("pfad, erwartet", [
    ("plan", "plan.xlsx"), ("plan.xlsx", "plan.xlsx"), ("PLAN.XLSX", "PLAN.XLSX"), ("plan.xls", "plan.xls.xlsx"),
])
def test_xlsx_endung(app, pfad, erwartet):
    assert app._mit_xlsx_endung(pfad) == erwartet


def test_natuerliche_sortierung(app):
    labels = ["(4WPP S.101) B", "(4WPP S.20) A", "(4WPP S.9) C", "apfel"]
    assert sorted(labels, key=app._natuerlich) == ["(4WPP S.9) C", "(4WPP S.20) A", "(4WPP S.101) B", "apfel"]
