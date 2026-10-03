"""Selbsttest der App (als eigener Prozess) und Prüfungen der Projektdateien."""
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import REPO


def starte_selbsttest(ordner):
    env = dict(os.environ, MENUEPLANER_SELBSTTEST="1")
    return subprocess.run([sys.executable, str(ordner / "menu_planer.py")], env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=120)


def test_selbsttest_erfolgreich(app_ordner):
    ergebnis = starte_selbsttest(app_ordner)
    log = (app_ordner / "selbsttest.log").read_text(encoding="utf-8")
    assert ergebnis.returncode == 0, log
    assert "SELBSTTEST OK" in log
    assert not (app_ordner / "session.json").exists()  # Selbsttest verändert nichts


def test_selbsttest_ohne_rezeptdatei_schlaegt_fehl(app_ordner):
    (app_ordner / "Rezepte.xlsx").unlink()
    ergebnis = starte_selbsttest(app_ordner)
    assert ergebnis.returncode == 2
    assert "Rezeptdatei fehlt" in (app_ordner / "selbsttest.log").read_text(encoding="utf-8")


def test_selbsttest_aus_anderem_arbeitsverzeichnis(app_ordner, tmp_path, monkeypatch):
    """Rezepte.xlsx wird neben dem Programm gesucht, nicht im aktuellen Ordner."""
    anderswo = tmp_path / "anderswo"
    anderswo.mkdir()
    monkeypatch.chdir(anderswo)
    assert starte_selbsttest(app_ordner).returncode == 0


# ── Projektdateien ────────────────────────────────────────────────────────────

def lies(name):
    return (REPO / name).read_text(encoding="utf-8")


def test_version_im_readme_aktuell():
    version = re.search(r'__version__ = "([^"]+)"', lies("menu_planer.py")).group(1)
    readme = lies("README.md")
    assert f"Version-{version}-" in readme, "Versions-Badge im README aktualisieren"
    assert f"**v{version}**" in readme, "Versionsverlauf im README ergänzen"


def test_requirements():
    req = lies("requirements.txt")
    assert re.search(r"^pandas>=", req, re.M)
    # pandas >= 2.2 verweigert openpyxl < 3.1 – dann startet die App nicht
    assert re.search(r"^openpyxl>=3\.1", req, re.M)


@pytest.mark.parametrize("skript", ["start_menu_planer.bat", "build_exe.bat"])
def test_batch_dateien(skript):
    text = lies(skript)
    assert 'cd /d "%~dp0"' in text, "Skript soll aus seinem eigenen Ordner laufen"
    code = "\n".join(z for z in text.splitlines() if not z.strip().startswith("::"))
    # %ERRORLEVEL% wird in ( )-Blöcken schon beim Einlesen ersetzt -> "if errorlevel" verwenden
    assert "%ERRORLEVEL%" not in code.upper()
    assert code.count("(") == code.count(")")


@pytest.mark.parametrize("skript", ["start_menu_planer.sh", "build_linux.sh", "build_mac.sh"])
def test_shell_skripte(skript):
    roh = (REPO / skript).read_bytes()
    assert roh.startswith(b"#!/usr/bin/env bash\n")
    assert b"\r\n" not in roh, "Shell-Skripte brauchen LF-Zeilenenden"
    if shutil.which("bash") and sys.platform != "win32":
        subprocess.run(["bash", "-n", str(REPO / skript)], check=True)
        assert os.access(REPO / skript, os.X_OK), f"chmod +x {skript}"


def test_build_skripte_kopieren_rezepte_und_nutzen_requirements():
    for skript in ("build_linux.sh", "build_mac.sh", "build_exe.bat"):
        text = lies(skript)
        assert "Rezepte.xlsx" in text and "dist" in text, skript
        assert "requirements.txt" in text, skript


def test_gitattributes_zeilenenden():
    text = lies(".gitattributes")
    assert "*.bat text eol=crlf" in text
    assert "*.sh text eol=lf" in text


def test_app_quelltext_ohne_syntaxfehler_fuer_python_3_8():
    import ast
    baum = ast.parse(lies("menu_planer.py"), feature_version=(3, 8))
    assert baum is not None
