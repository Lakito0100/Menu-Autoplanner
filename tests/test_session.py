"""Sitzung speichern und wiederherstellen (session.json)."""
import json
import os

import pytest

MO_FR = "Montag_Frühstück"
MO_MI = "Montag_Mittagessen"
SO_AB = "Sonntag_Abendessen"
SPAGHETTI_LABEL = "(4WPP S.45) Spaghetti mit Fenchel und Parmesan (10 Pkt)"


def ordner_schreibgeschuetzt(monkeypatch, ordner):
    """Simuliert einen schreibgeschützten Programmordner (chmod wirkt nicht als root/unter Windows)."""
    echtes_access = os.access

    def access(pfad, modus, **k):
        try:
            if os.path.samefile(pfad, ordner):
                return False
        except OSError:
            pass
        return echtes_access(pfad, modus, **k)

    monkeypatch.setattr(os, "access", access)


def lies_session(app):
    return json.loads((app.verzeichnis / "session.json").read_text(encoding="utf-8"))


def schreibe_session(ordner, inhalt):
    text = inhalt if isinstance(inhalt, str) else json.dumps(inhalt, ensure_ascii=False)
    (ordner / "session.json").write_text(text, encoding="utf-8")


def test_ohne_session_startet_leer(app):
    assert not (app.verzeichnis / "session.json").exists()
    assert app.auswahl_rezept[MO_FR].get() == ""


def test_speichern_und_wiederherstellen(app, starte_app):
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app.setze_personen(MO_MI, 3)
    app.waehle_kategorie(MO_FR, "Suppen")
    app.setze_personen(SO_AB, "2,5")
    app.beenden()
    daten = lies_session(app)
    assert daten[MO_MI] == {"kategorie": "Pasta", "rezept": SPAGHETTI_LABEL,
                            "rezeptname": "(4WPP S.45) Spaghetti mit Fenchel und Parmesan", "personen": "3"}

    neu = starte_app()
    assert neu.auswahl_rezept[MO_MI].get() == SPAGHETTI_LABEL
    assert neu.auswahl_kat[MO_MI].get() == "Pasta"
    assert neu.anzahl_personen[MO_MI].get() == "3"
    assert neu.auswahl_kat[MO_FR].get() == "Suppen"
    assert neu.auswahl_rezept[MO_FR].get() == app.rezepte_by_kategorie["Suppen"][0]
    assert neu.anzahl_personen[SO_AB].get() == "2,5"
    assert neu.punkte_labels["Montag"]["text"] != "0.0 Pkt"


def test_fenster_x_speichert(app):
    app.setze_personen(SO_AB, 7)
    app.root.tk.call(app.root.protocol("WM_DELETE_WINDOW"))
    assert lies_session(app)[SO_AB]["personen"] == "7"


def test_keine_temporaeren_dateien_bleiben_liegen(app):
    app.save_session()
    app.save_session()
    assert sorted(p.name for p in app.verzeichnis.iterdir()) == ["Rezepte.xlsx", "menu_planer.py", "session.json"]


def test_einkaufsliste_status_wird_wiederhergestellt(app_ordner, starte_app):
    schreibe_session(app_ordner, {"einkaufsliste": {
        "vorhanden": [["Fenchelknolle", ""]],
        "geloescht": [["Salz, Pfeffer", ""]],
        "zusaetzlich": [{"menge": "1", "einheit": "", "zutat": "Brot"}],
    }})
    app = starte_app()
    assert app._einkaufsliste_state == {
        "vorhanden": [["Fenchelknolle", ""]],
        "geloescht": [["Salz, Pfeffer", ""]],
        "zusaetzlich": [{"menge": "1", "einheit": "", "zutat": "Brot"}],
    }


@pytest.mark.parametrize("inhalt", [
    "{kein json",
    "",
    "[1, 2, 3]",
    "null",
    {"Montag_Frühstück": "kein dict", "Montag_Mittagessen": [1, 2]},
    {"Montag_Frühstück": {"kategorie": 5, "rezept": None, "rezeptname": [1], "personen": 3}},
    {"einkaufsliste": "kaputt"},
    {"einkaufsliste": {"vorhanden": [1, "ab", [1, 2, 3], None], "geloescht": {"a": 1},
                       "zusaetzlich": ["x", {"menge": 1}, None, {"zutat": "Brot", "menge": 2}]}},
    {"Unbekannter_Schlüssel": {"rezept": "x"}},
], ids=["kaputt", "leer", "liste", "null", "falsche_typen", "falsche_werte", "liste_kaputt",
        "liste_falsche_typen", "unbekannt"])
def test_beschaedigte_session_verhindert_start_nicht(app_ordner, starte_app, inhalt):
    schreibe_session(app_ordner, inhalt)
    app = starte_app()
    state = app._einkaufsliste_state
    assert all(isinstance(x, list) and len(x) == 2 for x in state["vorhanden"] + state["geloescht"])
    assert all(isinstance(x, dict) and x["zutat"] for x in state["zusaetzlich"])
    # Die App bleibt bedienbar
    app.waehle_rezept(MO_MI, "Spaghetti mit Fenchel")
    app.oeffne_einkaufsliste()
    app.beenden()
    assert isinstance(lies_session(app), dict)


def test_session_aus_version_1_1_0(app_ordner, starte_app):
    """Alte Sessions haben kein 'rezeptname' und kein 'geloescht'."""
    schreibe_session(app_ordner, {
        MO_MI: {"kategorie": "Pasta", "rezept": SPAGHETTI_LABEL, "personen": "2"},
        "einkaufsliste": {"vorhanden": [["Fenchelknolle", ""]], "zusaetzlich": []},
    })
    app = starte_app()
    assert app.auswahl_rezept[MO_MI].get() == SPAGHETTI_LABEL
    assert app._einkaufsliste_state["geloescht"] == []


def test_veraltetes_label_wird_ueber_namen_gefunden(app_ordner, starte_app):
    """Punkte wurden extern in Excel geändert -> Label in der Session ist veraltet."""
    schreibe_session(app_ordner, {
        MO_MI: {"kategorie": "Pasta", "rezept": "(4WPP S.45) Spaghetti mit Fenchel und Parmesan (99 Pkt)",
                "personen": "1"},
        MO_FR: {"kategorie": "Pasta", "rezept": "Gelöschtes Rezept (3 Pkt)", "personen": "1"},
    })
    app = starte_app()
    assert app.auswahl_rezept[MO_MI].get() == SPAGHETTI_LABEL
    # Unbekanntes Rezept wird geleert statt durch ein anderes ersetzt
    assert app.auswahl_rezept[MO_FR].get() == ""
    assert app.auswahl_kat[MO_FR].get() == "Pasta"


def test_unbekannte_kategorie_wird_ignoriert(app_ordner, starte_app):
    schreibe_session(app_ordner, {MO_FR: {"kategorie": "Gibt es nicht", "rezept": "", "personen": "1"}})
    app = starte_app()
    assert app.auswahl_kat[MO_FR].get() == ""


def test_session_im_benutzerordner_wenn_programmordner_schreibgeschuetzt(app_ordner, starte_app,
                                                                         monkeypatch, tmp_path):
    heim = tmp_path / "heim"
    for var in ("HOME", "USERPROFILE", "APPDATA", "XDG_CONFIG_HOME"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(heim))
    monkeypatch.setenv("USERPROFILE", str(heim))
    monkeypatch.setenv("APPDATA", str(heim / "AppData"))
    ordner_schreibgeschuetzt(monkeypatch, app_ordner)
    app = starte_app()
    assert str(app.SESSION_FILE).startswith(str(heim))
    assert os.path.basename(os.path.dirname(app.SESSION_FILE)) == "Menueplaner"
    app.beenden()
    assert os.path.exists(app.SESSION_FILE)
    assert not (app_ordner / "session.json").exists()


def test_bestehende_session_im_programmordner_wird_weiter_benutzt(app_ordner, starte_app, monkeypatch):
    schreibe_session(app_ordner, {})
    ordner_schreibgeschuetzt(monkeypatch, app_ordner)
    app = starte_app()
    assert os.path.samefile(app.SESSION_FILE, app_ordner / "session.json")
