
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import pandas as pd
from tkinter.filedialog import asksaveasfilename
import re
import os
import sys
import json
import math
import shutil
import tempfile

__version__ = "1.1.1"

# Basisverzeichnis: bei .exe = Ordner der EXE, bei .py = Ordner des Skripts
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    # macOS-App-Bundle: Programm liegt in Menueplaner.app/Contents/MacOS –
    # Rezepte.xlsx und session.json gehören neben das .app-Bundle.
    if sys.platform == "darwin" and BASE_DIR.endswith(os.path.join(".app", "Contents", "MacOS")):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _user_data_dir():
    """Benutzerverzeichnis für Programmdaten (Fallback, falls BASE_DIR schreibgeschützt ist)."""
    if sys.platform.startswith("win"):
        basis = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        basis = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        basis = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(basis, "Menueplaner")


def _session_pfad():
    pfad = os.path.join(BASE_DIR, "session.json")
    if os.path.exists(pfad) or os.access(BASE_DIR, os.W_OK):
        return pfad
    return os.path.join(_user_data_dir(), "session.json")


SESSION_FILE = _session_pfad()
REZEPTE_FILE = os.path.join(BASE_DIR, "Rezepte.xlsx")

_einkaufsliste_state = {"vorhanden": [], "zusaetzlich": [], "geloescht": []}

# Selbsttest für die automatischen Tests (CI): MENUEPLANER_SELBSTTEST=1 startet
# die App, probiert die wichtigsten Funktionen aus und beendet sich mit
# Exit-Code 0 (ok) bzw. 1 (Fehler). Protokoll: selbsttest.log im Programmordner.
SELBSTTEST = bool(os.environ.get("MENUEPLANER_SELBSTTEST"))

def _selbsttest_log(text):
    try:
        with open(os.path.join(BASE_DIR, "selbsttest.log"), "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError:
        pass
    if sys.stderr is not None:  # bei --windowed-Builds unter Windows None
        print(text, file=sys.stderr)

def _fataler_fehler(titel, text):
    if SELBSTTEST:
        _selbsttest_log(f"FEHLER: {titel}: {text}")
        sys.exit(2)
    _tmp = tk.Tk()
    _tmp.withdraw()
    messagebox.showerror(titel, text)
    _tmp.destroy()
    sys.exit(1)

try:
    df = pd.read_excel(REZEPTE_FILE)
except FileNotFoundError:
    _fataler_fehler(
        "Rezeptdatei fehlt",
        f"'{os.path.basename(REZEPTE_FILE)}' wurde nicht gefunden.\n"
        "Bitte 'Rezepte.xlsx' in denselben Ordner wie das Programm legen."
    )
except Exception as e:
    _fataler_fehler("Fehler beim Laden", f"Rezeptdatei konnte nicht geladen werden:\n{e}")

# Bekannte Einheiten (Vergleich ohne Gross-/Kleinschreibung). Alles andere nach
# der Menge gehört zum Zutatnamen, z.B. "1 rote Zwiebel" oder "1 Pak Choi".
EINHEITEN = {
    "g", "gr", "gramm", "kg", "mg", "ml", "cl", "dl", "l", "liter",
    "el", "tl", "msp", "prise", "prisen", "handvoll", "stück", "stk",
    "scheibe", "scheiben", "stange", "stangen", "stängel", "dose", "dosen",
    "blatt", "blätter", "kugel", "kugeln", "bund", "becher", "packung",
    "packungen", "pck", "pkg", "glas", "gläser", "tasse", "tassen",
    "zehe", "zehen", "zweig", "zweige", "würfel", "tropfen", "spritzer",
    "schuss", "cm",
}

_ZAHL = r"\d+(?:[.,]\d+)?(?:/\d+)?"


def _zahl(text):
    text = text.replace(",", ".")
    if "/" in text:
        zaehler, nenner = text.split("/", 1)
        return float(zaehler) / float(nenner) if float(nenner) else float(zaehler)
    return float(text)


def parse_zutat(z):
    """Zerlegt 'Menge Einheit Name'. Ohne Mengenangabe ist menge None."""
    z = " ".join(str(z).split())
    match = re.match(r"^(" + _ZAHL + r")\s*(.*)$", z)
    if not match or not match.group(2):
        return {"menge": None, "einheit": "", "zutat": z, "text": z}
    menge = _zahl(match.group(1))
    rest = match.group(2)
    teile = rest.split(" ", 1)
    if len(teile) == 2 and teile[0].lower() in EINHEITEN:
        einheit, name = teile
    else:
        einheit, name = "", rest
    return {"menge": menge, "einheit": einheit, "zutat": name, "text": z}


def format_menge(menge):
    if menge is None:
        return ""
    menge = round(menge, 2)
    return str(int(menge)) if menge == int(menge) else str(menge)

rezepte_by_kategorie = {}
rezept_infos = {}
label_by_name = {}

def _zahl_aus_zelle(wert, standard):
    if pd.isna(wert):
        return standard
    try:
        zahl = float(str(wert).replace(",", "."))
    except (ValueError, TypeError):
        return standard
    return zahl if math.isfinite(zahl) else standard

def _lade_rezepte_aus_df(source_df):
    rezept_infos.clear()
    rezepte_by_kategorie.clear()
    label_by_name.clear()
    if "Rezeptname" not in source_df.columns:
        return
    for _, row in source_df.iterrows():
        if pd.isna(row["Rezeptname"]) or not str(row["Rezeptname"]).strip():
            continue  # leere Zeile
        rezept = str(row["Rezeptname"]).strip()
        if rezept in label_by_name:
            continue  # doppelter Rezeptname – erster Eintrag gilt
        kategorie = row["Kategorie"] if "Kategorie" in row and pd.notna(row["Kategorie"]) else "Allgemein"
        kategorie = str(kategorie).strip() or "Allgemein"
        punkte = _zahl_aus_zelle(row["Punkte"], 0.0) if "Punkte" in row else 0.0
        portionen = _zahl_aus_zelle(row["Portionen"], 1.0) if "Portionen" in row else 1.0
        if portionen <= 0:
            portionen = 1.0
        zutaten = [parse_zutat(row[col]) for col in row.index
                   if str(col).startswith("Zutat") and pd.notna(row[col]) and str(row[col]).strip()]
        punkte_display = int(punkte) if punkte == int(punkte) else punkte
        rezept_label = f"{rezept} ({punkte_display} Pkt)"
        rezept_infos[rezept_label] = {
            "punkte": punkte,
            "zutaten": zutaten,
            "kategorie": kategorie,
            "rezeptname": rezept,
            "portionen": portionen
        }
        label_by_name[rezept] = rezept_label
        rezepte_by_kategorie.setdefault(kategorie, []).append(rezept_label)

def finde_rezept_label(text, name=None):
    """Liefert das aktuelle Label zu einem (evtl. veralteten) Label oder Rezeptnamen."""
    if text in rezept_infos:
        return text
    if name and name in label_by_name:
        return label_by_name[name]
    if text in label_by_name:
        return label_by_name[text]
    ohne_punkte = re.sub(r"\s*\([^()]*Pkt\)$", "", str(text))
    return label_by_name.get(ohne_punkte, "")

_lade_rezepte_aus_df(df)

tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
mahlzeiten = ["Frühstück", "Mittagessen", "Abendessen"]

def _erzeuge_tk(versuche=3):
    """Unter Windows kann Tk beim Start vereinzelt eigene .tcl-Dateien nicht
    lesen (z.B. während ein Virenscanner sie prüft) – dann kurz neu versuchen."""
    import time
    for versuch in range(versuche):
        try:
            return tk.Tk()
        except tk.TclError:
            if versuch == versuche - 1:
                raise
            time.sleep(0.5)

root = _erzeuge_tk()
root.title(f"Menüplaner v{__version__}")
root.minsize(600, 400)

# ── Anzeige-Zoom (HiDPI / 4K) ─────────────────────────────────────────────────
# Tk skaliert unter Linux nach der DPI, die der X-Server meldet. XWayland meldet
# auch auf 4K-Bildschirmen oft 96 dpi – dann ist alles winzig. Deshalb rechnet
# die App unter X11 mit 96 dpi = 100 % und vergrössert selbst (Ansicht-Menü,
# Strg +/-/0). Unter Windows und macOS ist 100 % die Systemeinstellung.

ZOOM_STUFEN = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
_X11 = root.tk.call("tk", "windowingsystem") == "x11"
_zoom = {"faktor": 1.0, "gespeichert": None}  # gespeichert: None = automatisch
_schrift_basis = {}  # Grundgrösse der benannten Schriften bei 100 %
_stil_basis = {}     # Grundwerte des ttk-Themes bei 100 %

if _X11:
    root.tk.call("tk", "scaling", 96 / 72)

def _xft_dpi():
    """Xft.dpi aus den X-Ressourcen (setzen z.B. GNOME und KDE beim Skalieren)."""
    import subprocess
    if not shutil.which("xrdb"):
        return None
    env = dict(os.environ)
    if getattr(sys, "frozen", False):  # PyInstaller: System-Bibliotheken für xrdb
        if "LD_LIBRARY_PATH_ORIG" in env:
            env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
        else:
            env.pop("LD_LIBRARY_PATH", None)
    try:
        ausgabe = subprocess.run(["xrdb", "-query"], capture_output=True, text=True,
                                 timeout=2, env=env).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    treffer = re.search(r"^Xft\.dpi:\s*([\d.]+)", ausgabe, re.M)
    return float(treffer.group(1)) if treffer else None

def berechne_auto_zoom(x11, env, xft_dpi, hoehe_px, hoehe_mm):
    """Zoomfaktor für den Start, wenn der Benutzer nichts eingestellt hat."""
    if not x11:
        return 1.0  # Windows/macOS skalieren selbst
    def zahl(name):
        try:
            wert = float(env.get(name, ""))
        except ValueError:
            return None
        return wert if math.isfinite(wert) and wert > 0 else None
    faktor = None
    if zahl("GDK_SCALE") or zahl("GDK_DPI_SCALE"):
        faktor = (zahl("GDK_SCALE") or 1.0) * (zahl("GDK_DPI_SCALE") or 1.0)
    elif zahl("QT_SCALE_FACTOR"):
        faktor = zahl("QT_SCALE_FACTOR")
    elif xft_dpi and abs(xft_dpi - 96) > 1:
        faktor = xft_dpi / 96
    elif hoehe_px >= 1200:
        dpi = hoehe_px / (hoehe_mm / 25.4) if hoehe_mm > 0 else 0
        if 110 < dpi < 600:  # glaubwürdige Bildschirmgrösse gemeldet
            faktor = 2.0 if dpi >= 192 else 1.5 if dpi >= 144 else 1.0
        elif hoehe_px >= 2000:  # 4K, aber DPI unbekannt (z.B. XWayland)
            faktor = 2.0
    if faktor is None:
        return 1.0
    return min(max(round(faktor * 4) / 4, 1.0), 3.0)

def auto_zoom():
    return berechne_auto_zoom(_X11, os.environ, _xft_dpi() if _X11 else None,
                              root.winfo_screenheight(), root.winfo_screenmmheight())

def px(wert):
    """Pixelangabe passend zum aktuellen Zoom."""
    return int(round(wert * _zoom["faktor"]))

def setze_zoom(faktor):
    faktor = min(max(float(faktor), 0.5), 4.0)
    _zoom["faktor"] = faktor
    for name in tkfont.names(root):
        schrift = tkfont.nametofont(name, root=root)
        basis = _schrift_basis.setdefault(name, int(schrift.cget("size")) or 10)
        groesse = int(round(abs(basis) * faktor)) or 1
        schrift.configure(size=groesse if basis > 0 else -groesse)  # Punkte bzw. Pixel
    style = ttk.Style(root)
    zeile = tkfont.nametofont("TkDefaultFont", root=root).metrics("linespace")
    style.configure("Treeview", rowheight=zeile + px(6))
    # Pfeile und Breite von Scrollbars/Comboboxen (feste Pixelwerte des Themes)
    for stil, option in (("TCombobox", "arrowsize"), ("TScrollbar", "arrowsize"),
                         ("TScrollbar", "width"), ("TSpinbox", "arrowsize")):
        basis = _stil_basis.setdefault((stil, option), style.lookup(stil, option))
        try:
            style.configure(stil, **{option: px(float(basis))})
        except (ValueError, TypeError):
            pass  # Theme ohne diese Option (z.B. native Windows-/macOS-Themes)

def _lade_zoom_einstellung():
    """Liest nur den gespeicherten Zoom (vor dem Aufbau der Oberfläche)."""
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            zoom = json.load(f).get("einstellungen", {}).get("zoom")
    except Exception:
        return None
    if isinstance(zoom, (int, float)) and not isinstance(zoom, bool) and 0.5 <= zoom <= 4:
        return float(zoom)
    return None

def _start_zoom():
    try:
        umgebung = float(os.environ.get("MENUEPLANER_ZOOM", ""))
        if 0.5 <= umgebung <= 4:
            return umgebung
    except ValueError:
        pass
    _zoom["gespeichert"] = _lade_zoom_einstellung()
    return _zoom["gespeichert"] or auto_zoom()

# Eigene Schriften (statt fest "Arial", das es unter Linux meist nicht gibt)
_standard = tkfont.nametofont("TkDefaultFont", root=root).actual()
SCHRIFT_TITEL = tkfont.Font(root=root, name="MenueTitel", family=_standard["family"],
                            size=int(round(_standard["size"] * 1.4)) or 14, weight="bold")
SCHRIFT_FETT = tkfont.Font(root=root, name="MenueFett", family=_standard["family"],
                           size=_standard["size"] or 10, weight="bold")
setze_zoom(_start_zoom())

# Unter X11 übernimmt sonst jede Textauswahl in einem Eingabefeld die
# PRIMARY-Auswahl des Systems. Das ist hier unnötig und vermeidet Probleme mit
# der Zwischenablage-Brücke von Wayland-Desktops (XWayland).
root.option_add("*exportSelection", False)

canvas = tk.Canvas(root)
scroll_y = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scroll_y.set)

scroll_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
canvas.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# ── Mausrad-Scrolling (Windows, macOS, Linux) ─────────────────────────────────

_scroll_canvases = [canvas]

def _on_mousewheel(event):
    widget = event.widget
    if not isinstance(widget, tk.Misc):
        return  # z.B. Combobox-Aufklappliste: scrollt selbst
    if widget.winfo_class() in ("Listbox", "Treeview", "Text"):
        return  # diese Widgets scrollen selbst
    while widget is not None and widget not in _scroll_canvases:
        widget = widget.master
    if widget is None:
        return
    if event.num == 4:
        schritte = -1
    elif event.num == 5:
        schritte = 1
    elif not event.delta:
        return
    elif abs(event.delta) >= 120:
        schritte = -int(event.delta / 120)  # Windows: Vielfache von 120
    elif sys.platform == "darwin":
        schritte = -event.delta  # macOS liefert kleine Deltas (±1, ±2, …)
    else:
        schritte = -1 if event.delta > 0 else 1  # z.B. Touchpads
    if widget.yview() != (0.0, 1.0):
        widget.yview_scroll(schritte, "units")

def _mausrad_scrollt_seite(widget):
    """Comboboxen ändern beim Mausrad standardmässig ihren Wert. Im Wochenplan
    soll das Mausrad stattdessen die Seite scrollen."""
    def handler(event):
        _on_mousewheel(event)
        return "break"
    for sequenz in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        widget.bind(sequenz, handler)

# Tk 8.6 unter X11 meldet das Mausrad als Button-4/5, sonst (und ab Tk 9) als <MouseWheel>
root.bind_all("<MouseWheel>", _on_mousewheel)
root.bind_all("<Button-4>", _on_mousewheel)
root.bind_all("<Button-5>", _on_mousewheel)

def _modal(win):
    """Macht ein Toplevel-Fenster modal. Unter Linux schlägt grab_set fehl,
    solange das Fenster noch nicht sichtbar ist – daher ggf. später erneut."""
    win.transient(root)
    def grab():
        if not win.winfo_exists():
            return
        try:
            win.grab_set()
        except tk.TclError:
            root.after(50, grab)
    grab()
    win.focus_set()

def _fenstergroesse(win, breite, hoehe):
    """Setzt die Fenstergrösse: mindestens so gross wie der Inhalt verlangt
    (Schriften sind je nach System unterschiedlich breit), höchstens Bildschirmgrösse."""
    win.update_idletasks()
    breite = min(max(breite, win.winfo_reqwidth()), win.winfo_screenwidth() - 40)
    hoehe = min(max(hoehe, win.winfo_reqheight()), win.winfo_screenheight() - 120)
    win.geometry(f"{breite}x{hoehe}")

def _natuerlich(text):
    """Sortierschlüssel, der Zahlen numerisch vergleicht (S.20 vor S.101)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]

_zwischenablage = {"text": None}  # zuletzt von der App kopierter Text

def _in_zwischenablage(widget, text):
    widget.clipboard_clear()
    widget.clipboard_append(text)
    _zwischenablage["text"] = text
    # Unter X11 (Linux) ist der Inhalt nur verfügbar, solange das Programm läuft
    widget.update()

auswahl_kat = {}
auswahl_rezept = {}
anzahl_personen = {}
punkte_labels = {}

# ── Dropdown-Logik ────────────────────────────────────────────────────────────

def update_rezept_dropdown_for(key, auto_auswahl=False):
    """Aktualisiert die Rezeptliste eines Feldes. Nur bei auto_auswahl (Kategorie
    wurde vom Benutzer gewechselt) wird ggf. das erste Rezept vorausgewählt."""
    kat_box = auswahl_kat[key]
    rezept_box = auswahl_rezept[key]
    kategorie = kat_box.get()
    if kategorie not in rezepte_by_kategorie:
        # Keine (oder nicht mehr vorhandene) Kategorie: alle Rezepte zur Auswahl
        if kategorie:
            kat_box.set("")
        rezept_box["values"] = alle_rezepte()
        return
    neue_liste = rezepte_by_kategorie[kategorie]
    rezept_box["values"] = neue_liste
    if auto_auswahl and rezept_box.get() not in neue_liste:
        rezept_box.set(neue_liste[0] if neue_liste else "")

def alle_rezepte():
    return [r for recipes in rezepte_by_kategorie.values() for r in recipes]

def rezept_gewaehlt(key):
    """Rezept aus der Liste gewählt: passende Kategorie mitsetzen."""
    rezept = auswahl_rezept[key].get()
    if rezept in rezept_infos:
        kategorie = rezept_infos[rezept]["kategorie"]
        if auswahl_kat[key].get() != kategorie:
            auswahl_kat[key].set(kategorie)
            auswahl_rezept[key]["values"] = rezepte_by_kategorie.get(kategorie, [])
    update_punkte()

def update_rezept_dropdown(event=None):
    for key in auswahl_kat.keys():
        update_rezept_dropdown_for(key)
    update_punkte()

def update_punkte():
    for tag in tage:
        tages_summe = 0.0
        for mahlzeit in mahlzeiten:
            key = f"{tag}_{mahlzeit}"
            rezept = auswahl_rezept[key].get()
            if rezept in rezept_infos:
                portionen = rezept_infos[rezept]["portionen"]
                faktor = 1.0 / portionen if portionen > 0 else 1.0
                tages_summe += rezept_infos[rezept]["punkte"] * faktor
        punkte_labels[tag]["text"] = f"{round(tages_summe, 1)} Pkt"

def setup_searchable_rezept(key):
    """Macht die Rezept-Combobox durchsuchbar (Freitext-Filter)."""
    rezept_combo = auswahl_rezept[key]
    rezept_combo.configure(state="normal")

    def filter_recipes(event=None):
        typed = rezept_combo.get()
        kat = auswahl_kat[key].get()
        if kat:
            base = rezepte_by_kategorie.get(kat, [])
        else:
            base = alle_rezepte()
        if typed:
            filtered = [r for r in base if typed.lower() in r.lower()]
        else:
            filtered = base
        rezept_combo["values"] = filtered
        update_punkte()

    rezept_combo.bind("<KeyRelease>", filter_recipes)

# ── Einkaufsliste ─────────────────────────────────────────────────────────────

def get_personen(key):
    try:
        personen = float(str(anzahl_personen[key].get()).strip().replace(",", "."))
    except (ValueError, TypeError):
        return 1.0
    if not math.isfinite(personen) or personen < 0:
        return 1.0
    return personen

def generate_list():
    """Liste von (Menge, Einheit, Zutat); Menge ist '' bei Zutaten ohne Mengenangabe."""
    zutaten_dict = {}
    for key, box in auswahl_rezept.items():
        rezept = box.get()
        if rezept in rezept_infos:
            personen = get_personen(key)
            portionen = rezept_infos[rezept]["portionen"]
            faktor = personen / portionen if portionen > 0 else 1
            for z in rezept_infos[rezept]["zutaten"]:
                k = (z["zutat"], z["einheit"])
                bisher = zutaten_dict.get(k)
                if z["menge"] is None:
                    zutaten_dict[k] = bisher
                else:
                    zutaten_dict[k] = (bisher or 0) + z["menge"] * faktor
    return [(format_menge(m), e, z) for (z, e), m in zutaten_dict.items()]

def _status_keys(name):
    eintraege = _einkaufsliste_state.get(name, [])
    return {(str(x[0]), str(x[1])) for x in eintraege if isinstance(x, (list, tuple)) and len(x) == 2}

def zeige_einkaufsliste():
    einkaufsliste = generate_list()

    win = tk.Toplevel(root)
    win.title("Einkaufsliste")
    win.minsize(500, 300)

    # Treeview + Scrollbar
    frame_tree = ttk.Frame(win)
    frame_tree.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    cols = ("Menge", "Einheit", "Zutat", "Status")
    tree = ttk.Treeview(frame_tree, columns=cols, show="headings", height=18)
    tree.heading("Menge", text="Menge")
    tree.heading("Einheit", text="Einheit")
    tree.heading("Zutat", text="Zutat")
    tree.heading("Status", text="Status")
    tree.column("Menge", width=px(60), anchor="e")
    tree.column("Einheit", width=px(70))
    tree.column("Zutat", width=px(300))
    tree.column("Status", width=px(110))

    tree.tag_configure("vorhanden", foreground="#999999")
    tree.tag_configure("zusaetzlich", foreground="#0066cc", background="#eef4fb")

    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="left", fill="y")

    # Gespeicherten Zustand anwenden
    geloescht_keys = _status_keys("geloescht")

    def fuelle_liste(mit_status=True):
        vorhanden_keys = _status_keys("vorhanden") if mit_status else set()
        for menge, einheit, zutat in einkaufsliste:
            key = (zutat, einheit)
            if mit_status and key in geloescht_keys:
                continue
            if key in vorhanden_keys:
                tree.insert("", "end", values=(menge, einheit, zutat, "✓ vorhanden"), tags=("vorhanden",))
            else:
                tree.insert("", "end", values=(menge, einheit, zutat, ""))
        if mit_status:
            for item in _einkaufsliste_state.get("zusaetzlich", []):
                tree.insert("", "end", values=(item["menge"], item["einheit"], item["zutat"], "+ zusätzlich"),
                            tags=("zusaetzlich",))

    fuelle_liste()

    # Manuelle Eingabe
    frame_add = ttk.LabelFrame(win, text="Eintrag hinzufügen")
    frame_add.pack(fill="x", padx=10, pady=5)

    ttk.Label(frame_add, text="Menge:").grid(row=0, column=0, padx=4, pady=4)
    entry_menge = ttk.Entry(frame_add, width=7)
    entry_menge.grid(row=0, column=1, padx=2)

    ttk.Label(frame_add, text="Einheit:").grid(row=0, column=2, padx=4)
    entry_einheit = ttk.Entry(frame_add, width=8)
    entry_einheit.grid(row=0, column=3, padx=2)

    ttk.Label(frame_add, text="Zutat:").grid(row=0, column=4, padx=4)
    entry_zutat = ttk.Entry(frame_add, width=22)
    entry_zutat.grid(row=0, column=5, padx=2)

    def add_item(event=None):
        zutat = entry_zutat.get().strip()
        if not zutat:
            return
        tree.insert("", "end", values=(entry_menge.get().strip(), entry_einheit.get().strip(), zutat, "+ zusätzlich"), tags=("zusaetzlich",))
        entry_menge.delete(0, tk.END)
        entry_einheit.delete(0, tk.END)
        entry_zutat.delete(0, tk.END)

    ttk.Button(frame_add, text="Hinzufügen", command=add_item).grid(row=0, column=6, padx=6)
    entry_zutat.bind("<Return>", add_item)

    # Aktions-Buttons
    frame_btns = ttk.Frame(win)
    frame_btns.pack(fill="x", padx=10, pady=6)

    def toggle_vorhanden():
        for iid in tree.selection():
            tags = tree.item(iid, "tags")
            vals = tree.item(iid, "values")
            if "zusaetzlich" in tags:
                continue
            if "vorhanden" in tags:
                tree.item(iid, values=(vals[0], vals[1], vals[2], ""), tags=())
            else:
                tree.item(iid, values=(vals[0], vals[1], vals[2], "✓ vorhanden"), tags=("vorhanden",))

    def export_excel():
        data = [{"Menge": _als_zahl(tree.item(i, "values")[0]),
                 "Einheit": tree.item(i, "values")[1],
                 "Zutat": tree.item(i, "values")[2],
                 "Status": tree.item(i, "values")[3]}
                for i in tree.get_children()]
        if not data:
            messagebox.showwarning("Leer", "Einkaufsliste ist leer.", parent=win)
            return
        filepath = asksaveasfilename(defaultextension=".xlsx",
                                     filetypes=[("Excel-Dateien", "*.xlsx")],
                                     parent=win)
        if filepath:
            filepath = _mit_xlsx_endung(filepath)
            try:
                pd.DataFrame(data).to_excel(filepath, index=False)
                messagebox.showinfo("Erfolg", "Einkaufsliste exportiert.", parent=win)
            except Exception as e:
                messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{e}", parent=win)

    def copy_text():
        lines = []
        for i in tree.get_children():
            vals = tree.item(i, "values")
            menge, einheit, zutat, status = vals
            line = f"{menge} {einheit} {zutat}".strip()
            if status:
                line += f"  [{status}]"
            lines.append(line)
        _in_zwischenablage(win, "\n".join(lines))
        messagebox.showinfo("Kopiert", "Einkaufsliste in Zwischenablage kopiert.", parent=win)

    def on_close():
        vorhanden = []
        zusaetzlich = []
        for iid in tree.get_children():
            vals = tree.item(iid, "values")
            tags = tree.item(iid, "tags")
            if "vorhanden" in tags:
                vorhanden.append([str(vals[2]), str(vals[1])])
            elif "zusaetzlich" in tags:
                zusaetzlich.append({"menge": str(vals[0]), "einheit": str(vals[1]), "zutat": str(vals[2])})
        _einkaufsliste_state["vorhanden"] = vorhanden
        _einkaufsliste_state["zusaetzlich"] = zusaetzlich
        _einkaufsliste_state["geloescht"] = [list(k) for k in sorted(geloescht_keys)]
        try:
            save_session()
        finally:
            win.destroy()

    def delete_selected():
        for iid in tree.selection():
            if "zusaetzlich" not in tree.item(iid, "tags"):
                vals = tree.item(iid, "values")
                geloescht_keys.add((str(vals[2]), str(vals[1])))
            tree.delete(iid)

    def reset_liste():
        # Ursprüngliche Liste aus dem Wochenplan wiederherstellen
        geloescht_keys.clear()
        tree.delete(*tree.get_children())
        fuelle_liste(mit_status=False)

    win.protocol("WM_DELETE_WINDOW", on_close)

    ttk.Button(frame_btns, text="Als vorhanden markieren", command=toggle_vorhanden).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Eintrag löschen", command=delete_selected).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Als Excel exportieren", command=export_excel).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Als Text kopieren", command=copy_text).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Liste zurücksetzen", command=reset_liste).pack(side="left", padx=4)

    _fenstergroesse(win, px(700), px(600))
    _modal(win)

# ── Wochenplan-Export ─────────────────────────────────────────────────────────

def _mit_xlsx_endung(filepath):
    return filepath if filepath.lower().endswith(".xlsx") else filepath + ".xlsx"

def _als_zahl(text):
    """Mengen als Zahl exportieren, damit Excel damit rechnen kann."""
    try:
        zahl = float(str(text).replace(",", "."))
    except ValueError:
        return text
    if not math.isfinite(zahl):
        return text
    return int(zahl) if zahl == int(zahl) else zahl

def export_plan_und_einkaufsliste():
    einkaufsliste = generate_list()
    filepath = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel-Dateien", "*.xlsx")])
    if not filepath:
        return
    filepath = _mit_xlsx_endung(filepath)
    plan_data = []
    for tag in tage:
        row = {"Tag": tag}
        for mahlzeit in mahlzeiten:
            key = f"{tag}_{mahlzeit}"
            rezept = auswahl_rezept[key].get()
            anzahl = anzahl_personen[key].get()
            rezeptname = rezept_infos.get(rezept, {}).get("rezeptname", "")
            row[mahlzeit] = f"{rezeptname} ({anzahl} Pers.)" if rezeptname else ""
        row["Punkte"] = punkte_labels[tag]["text"]
        plan_data.append(row)
    plan_df = pd.DataFrame(plan_data)

    # Einkaufsliste mit Status aus gespeichertem Zustand aufbauen
    vorhanden_keys = _status_keys("vorhanden")
    geloescht_keys = _status_keys("geloescht")
    el_rows = []
    for menge, einheit, zutat in einkaufsliste:
        key = (zutat, einheit)
        if key in geloescht_keys:
            continue
        status = "✓ vorhanden" if key in vorhanden_keys else ""
        el_rows.append({"Menge": _als_zahl(menge), "Einheit": einheit, "Zutat": zutat, "Status": status})
    for item in _einkaufsliste_state.get("zusaetzlich", []):
        el_rows.append({"Menge": _als_zahl(item["menge"]), "Einheit": item["einheit"], "Zutat": item["zutat"], "Status": "+ zusätzlich"})
    el_df = pd.DataFrame(el_rows) if el_rows else pd.DataFrame(columns=["Menge", "Einheit", "Zutat", "Status"])

    try:
        with pd.ExcelWriter(filepath) as writer:
            plan_df.to_excel(writer, index=False, sheet_name="Wochenplan")
            el_df.to_excel(writer, index=False, sheet_name="Einkaufsliste")
    except Exception as e:
        messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{e}")
        return
    messagebox.showinfo("Erfolg", "Wochenplan und Einkaufsliste exportiert.")

def copy_wochenplan():
    lines = []
    for tag in tage:
        lines.append(f"── {tag} ──")
        tages_punkte = punkte_labels[tag]["text"]
        for mahlzeit in mahlzeiten:
            key = f"{tag}_{mahlzeit}"
            rezept = auswahl_rezept[key].get()
            personen = anzahl_personen[key].get()
            rezeptname = rezept_infos.get(rezept, {}).get("rezeptname", "")
            if rezeptname:
                lines.append(f"  {mahlzeit}: {rezeptname} ({personen} Pers.)")
            else:
                lines.append(f"  {mahlzeit}: –")
        lines.append(f"  Punkte: {tages_punkte}")
        lines.append("")
    text = "\n".join(lines).strip()
    _in_zwischenablage(root, text)
    messagebox.showinfo("Kopiert", "Wochenplan in Zwischenablage kopiert.")

# ── Rezeptverwaltung ──────────────────────────────────────────────────────────

def reload_rezepte(umbenannt=None):
    """Lädt Rezepte neu und behält die Auswahl im Wochenplan (über den Rezeptnamen) bei."""
    global df
    try:
        df = pd.read_excel(REZEPTE_FILE)
    except Exception as e:
        messagebox.showerror("Fehler", f"Rezeptdatei konnte nicht geladen werden:\n{e}")
        return
    vorher = {key: rezept_infos.get(box.get(), {}).get("rezeptname") for key, box in auswahl_rezept.items()}
    _lade_rezepte_aus_df(df)
    kategorien = list(rezepte_by_kategorie.keys())
    for key, kat_box in auswahl_kat.items():
        kat_box["values"] = kategorien
        name = vorher[key]
        if name is None:
            continue
        if umbenannt and name in umbenannt:
            name = umbenannt[name]
        label = label_by_name.get(name, "")
        auswahl_rezept[key].set(label)
        if label:
            kat_box.set(rezept_infos[label]["kategorie"])
    update_rezept_dropdown()

def _schreibe_rezepte(daten):
    """Erst in eine versteckte Temp-Datei schreiben, dann ersetzen: Bei einem
    Absturz oder vollem Datenträger bleibt die alte Rezepte.xlsx erhalten."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(REZEPTE_FILE), prefix=".Rezepte-", suffix=".xlsx")
    os.close(fd)
    try:
        if os.path.exists(REZEPTE_FILE):
            shutil.copymode(REZEPTE_FILE, tmp)  # Dateirechte beibehalten
        daten.to_excel(tmp, index=False)
        os.replace(tmp, REZEPTE_FILE)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

def _lese_rezepte_zum_bearbeiten():
    # Als object einlesen: pandas >= 3 verweigert sonst z.B. Text in leeren
    # (float-)Zutat-Spalten oder Kommazahlen in Ganzzahl-Spalten.
    return pd.read_excel(REZEPTE_FILE, dtype=object)

def oeffne_rezeptverwaltung():
    win = tk.Toplevel(root)
    win.title("Rezepte verwalten")
    win.minsize(700, 450)

    # Linke Spalte: Rezeptliste
    frame_left = ttk.Frame(win)
    frame_left.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

    ttk.Label(frame_left, text="Rezepte", font=SCHRIFT_FETT).pack(anchor="w")

    frame_lb = ttk.Frame(frame_left)
    frame_lb.pack(fill="both", expand=True)

    listbox = tk.Listbox(frame_lb, width=50, height=32, exportselection=False)
    listbox.pack(side="left", fill="both", expand=True)
    sb_lb = ttk.Scrollbar(frame_lb, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=sb_lb.set)
    sb_lb.pack(side="left", fill="y")

    def refresh_listbox():
        listbox.delete(0, tk.END)
        for label in sorted(rezept_infos.keys(), key=_natuerlich):
            listbox.insert(tk.END, label)

    refresh_listbox()

    # Rechte Spalte: Formular
    frame_right = ttk.Frame(win)
    frame_right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    ttk.Label(frame_right, text="Rezeptdetails", font=SCHRIFT_FETT).grid(
        row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

    lbl_names = ["Rezeptname:", "Kategorie:", "Punkte:", "Portionen:"]
    entries = {}

    for i, lbl in enumerate(lbl_names):
        ttk.Label(frame_right, text=lbl).grid(row=i + 1, column=0, sticky="e", padx=5, pady=3)
        if lbl == "Kategorie:":
            widget = ttk.Combobox(frame_right, values=list(rezepte_by_kategorie.keys()), width=32)
        else:
            widget = ttk.Entry(frame_right, width=34)
        widget.grid(row=i + 1, column=1, sticky="w", pady=3)
        entries[lbl] = widget

    ttk.Label(frame_right, text="Zutaten:", font=SCHRIFT_FETT).grid(
        row=6, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))
    ttk.Label(frame_right, text="Format: Menge Einheit Zutatname  (z.B. '500 g Hackfleisch' oder '2 Eier')",
              wraplength=px(380)).grid(row=7, column=0, columnspan=2, sticky="w", padx=5)

    # Scrollbares Zutaten-Frame
    frame_z_outer = ttk.Frame(frame_right)
    frame_z_outer.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=5, pady=4)
    frame_right.rowconfigure(8, weight=1)

    canvas_z = tk.Canvas(frame_z_outer, height=px(250))
    sb_z = ttk.Scrollbar(frame_z_outer, orient="vertical", command=canvas_z.yview)
    canvas_z.configure(yscrollcommand=sb_z.set)
    canvas_z.pack(side="left", fill="both", expand=True)
    sb_z.pack(side="left", fill="y")

    frame_zutaten = ttk.Frame(canvas_z)
    canvas_z.create_window((0, 0), window=frame_zutaten, anchor="nw")
    frame_zutaten.bind("<Configure>", lambda e: canvas_z.configure(scrollregion=canvas_z.bbox("all")))
    _scroll_canvases.append(canvas_z)
    win.bind("<Destroy>", lambda e: canvas_z in _scroll_canvases and e.widget is win
             and _scroll_canvases.remove(canvas_z))

    zutat_entries = []

    def add_zutat_row(text=""):
        row_frame = ttk.Frame(frame_zutaten)
        row_frame.pack(fill="x", pady=1)
        e = ttk.Entry(row_frame, width=46)
        e.insert(0, text)
        e.pack(side="left")

        def remove_row():
            if e in zutat_entries:
                zutat_entries.remove(e)
            row_frame.destroy()

        ttk.Button(row_frame, text="✕", width=2, command=remove_row).pack(side="left", padx=2)
        zutat_entries.append(e)

    for _ in range(3):
        add_zutat_row()
    # Canvas so breit wie die Zutatenzeilen (inkl. ✕-Button) machen
    frame_zutaten.update_idletasks()
    canvas_z.configure(width=frame_zutaten.winfo_reqwidth())

    ttk.Button(frame_right, text="+ Zutat hinzufügen", command=add_zutat_row).grid(
        row=9, column=0, columnspan=2, pady=4)

    # Name des geladenen Rezepts (für Umbenennen beim Speichern)
    geladen = {"name": None}

    # Rezept in Formular laden
    def load_rezept(event=None):
        sel = listbox.curselection()
        if not sel:
            return
        label = listbox.get(sel[0])
        info = rezept_infos.get(label, {})
        geladen["name"] = info.get("rezeptname")

        entries["Rezeptname:"].delete(0, tk.END)
        entries["Rezeptname:"].insert(0, info.get("rezeptname", ""))
        entries["Kategorie:"].set(info.get("kategorie", ""))
        entries["Punkte:"].delete(0, tk.END)
        entries["Punkte:"].insert(0, format_menge(info.get("punkte", 0.0)))
        entries["Portionen:"].delete(0, tk.END)
        entries["Portionen:"].insert(0, format_menge(info.get("portionen", 1.0)))

        for e in list(zutat_entries):
            e.master.destroy()
        zutat_entries.clear()

        for z in info.get("zutaten", []):
            add_zutat_row(z["text"])  # Originaltext, damit Speichern nichts verändert

        if not zutat_entries:
            add_zutat_row()

    listbox.bind("<<ListboxSelect>>", load_rezept)

    def neu_rezept():
        geladen["name"] = None
        listbox.selection_clear(0, tk.END)
        for lbl in ["Rezeptname:", "Punkte:", "Portionen:"]:
            entries[lbl].delete(0, tk.END)
        entries["Kategorie:"].set("")
        for e in list(zutat_entries):
            e.master.destroy()
        zutat_entries.clear()
        for _ in range(3):
            add_zutat_row()

    def speichern_rezept():
        name = entries["Rezeptname:"].get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Rezeptname darf nicht leer sein.", parent=win)
            return
        kategorie = entries["Kategorie:"].get().strip() or "Allgemein"
        try:
            punkte = float(entries["Punkte:"].get().replace(",", "."))
            if not math.isfinite(punkte):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Fehler", "Punkte müssen eine Zahl sein.", parent=win)
            return
        portionen_text = entries["Portionen:"].get().strip()
        try:
            portionen = float(portionen_text.replace(",", ".")) if portionen_text else 1.0
            if not math.isfinite(portionen) or portionen <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Fehler", "Portionen müssen eine Zahl grösser 0 sein.", parent=win)
            return

        zutaten_liste = [e.get().strip() for e in zutat_entries if e.get().strip()]

        row_data = {"Rezeptname": name, "Kategorie": kategorie,
                    "Punkte": punkte, "Portionen": portionen}
        for i, z in enumerate(zutaten_liste, 1):
            row_data[f"Zutat {i}"] = z

        try:
            existing_df = _lese_rezepte_zum_bearbeiten()
        except FileNotFoundError:
            existing_df = pd.DataFrame()
        except Exception as e:
            # Nicht mit leerer Tabelle überschreiben – sonst gehen alle Rezepte verloren
            messagebox.showerror("Fehler", f"Rezeptdatei konnte nicht gelesen werden:\n{e}", parent=win)
            return

        if "Rezeptname" in existing_df.columns:
            namen = existing_df["Rezeptname"].map(lambda v: str(v).strip() if pd.notna(v) else "")
        else:
            namen = pd.Series([], dtype=object)
        alter_name = geladen["name"]
        if name != alter_name and (namen == name).any():
            frage = (f"Ein Rezept '{name}' existiert bereits.\nSoll es überschrieben werden?")
            if not messagebox.askyesno("Rezept existiert", frage, parent=win):
                return
            if alter_name and (namen == alter_name).any():
                # Umbenennen auf einen bestehenden Namen: altes Rezept entfernen
                behalten = namen != alter_name
                existing_df = existing_df[behalten]
                namen = namen[behalten]
            ziel = name
        elif alter_name and (namen == alter_name).any():
            ziel = alter_name  # geladenes Rezept bearbeiten (ggf. umbenennen)
        else:
            ziel = name

        if (namen == ziel).any():
            idx = existing_df.index[namen == ziel][0]
            for col in [c for c in existing_df.columns if str(c).startswith("Zutat")]:
                existing_df.at[idx, col] = None
            for k, v in row_data.items():
                existing_df.at[idx, k] = v
        else:
            existing_df = pd.concat([existing_df, pd.DataFrame([row_data], dtype=object)], ignore_index=True)

        try:
            _schreibe_rezepte(existing_df)
        except Exception as e:
            messagebox.showerror("Fehler", f"Rezept konnte nicht gespeichert werden:\n{e}", parent=win)
            return
        umbenannt = {alter_name: name} if alter_name and alter_name != name else None
        geladen["name"] = name
        reload_rezepte(umbenannt)
        refresh_listbox()
        entries["Kategorie:"]["values"] = list(rezepte_by_kategorie.keys())
        neues_label = label_by_name.get(name)
        if neues_label in listbox.get(0, tk.END):
            pos = listbox.get(0, tk.END).index(neues_label)
            listbox.selection_set(pos)
            listbox.see(pos)
        messagebox.showinfo("Erfolg", f"Rezept '{name}' gespeichert.", parent=win)

    def loeschen_rezept():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Kein Rezept gewählt", "Bitte zuerst ein Rezept auswählen.", parent=win)
            return
        label = listbox.get(sel[0])
        info = rezept_infos.get(label)
        if info is None:
            messagebox.showwarning("Fehler", "Rezept nicht gefunden.", parent=win)
            return
        name = info["rezeptname"]
        if not messagebox.askyesno("Löschen bestätigen", f"Rezept '{name}' wirklich löschen?", parent=win):
            return
        try:
            existing_df = _lese_rezepte_zum_bearbeiten()
        except Exception as e:
            messagebox.showerror("Fehler", f"Rezeptdatei konnte nicht gelesen werden:\n{e}", parent=win)
            return
        namen = existing_df["Rezeptname"].map(lambda v: str(v).strip() if pd.notna(v) else "")
        existing_df = existing_df[namen != name]
        try:
            _schreibe_rezepte(existing_df)
        except Exception as e:
            messagebox.showerror("Fehler", f"Rezeptdatei konnte nicht gespeichert werden:\n{e}", parent=win)
            return
        reload_rezepte()
        refresh_listbox()
        neu_rezept()
        messagebox.showinfo("Gelöscht", f"Rezept '{name}' wurde gelöscht.", parent=win)

    frame_btns = ttk.Frame(frame_right)
    frame_btns.grid(row=10, column=0, columnspan=2, pady=8)
    ttk.Button(frame_btns, text="Neues Rezept", command=neu_rezept).pack(side="left", padx=6)
    ttk.Button(frame_btns, text="Speichern", command=speichern_rezept).pack(side="left", padx=6)
    ttk.Button(frame_btns, text="Löschen", command=loeschen_rezept).pack(side="left", padx=6)

    _fenstergroesse(win, px(940), px(680))
    _modal(win)

# ── Session-Persistenz ────────────────────────────────────────────────────────

def save_session():
    data = {}
    for key in auswahl_kat:
        rezept = auswahl_rezept[key].get()
        data[key] = {
            "kategorie": auswahl_kat[key].get(),
            "rezept": rezept,
            "rezeptname": rezept_infos.get(rezept, {}).get("rezeptname", ""),
            "personen": anzahl_personen[key].get()
        }
    data["einkaufsliste"] = _einkaufsliste_state
    if _zoom["gespeichert"] is not None:
        data["einstellungen"] = {"zoom": _zoom["gespeichert"]}
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        # Erst in Temp-Datei schreiben, dann ersetzen: kein kaputtes JSON bei Absturz
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(SESSION_FILE), prefix=".session-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, SESSION_FILE)
        except Exception:
            os.remove(tmp)
            raise
    except Exception:
        pass

def _liste_von_paaren(wert):
    if not isinstance(wert, list):
        return []
    return [[str(x[0]), str(x[1])] for x in wert if isinstance(x, (list, tuple)) and len(x) == 2]

def load_session():
    if not os.path.exists(SESSION_FILE):
        return
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    state = data.get("einkaufsliste")
    if isinstance(state, dict):
        zusaetzlich = state.get("zusaetzlich", [])
        _einkaufsliste_state["vorhanden"] = _liste_von_paaren(state.get("vorhanden"))
        _einkaufsliste_state["geloescht"] = _liste_von_paaren(state.get("geloescht"))
        _einkaufsliste_state["zusaetzlich"] = [
            {"menge": str(x.get("menge", "")), "einheit": str(x.get("einheit", "")), "zutat": str(x["zutat"])}
            for x in (zusaetzlich if isinstance(zusaetzlich, list) else [])
            if isinstance(x, dict) and x.get("zutat")
        ]
    for key, vals in data.items():
        if key not in auswahl_kat or not isinstance(vals, dict):
            continue
        kat = str(vals.get("kategorie", ""))
        rezept = finde_rezept_label(str(vals.get("rezept", "")), str(vals.get("rezeptname") or ""))
        if rezept:
            kat = rezept_infos[rezept]["kategorie"]
        auswahl_kat[key].set(kat if kat in rezepte_by_kategorie else "")
        auswahl_rezept[key].set(rezept)
        update_rezept_dropdown_for(key)
        pers = str(vals.get("personen", "1"))
        anzahl_personen[key].delete(0, tk.END)
        anzahl_personen[key].insert(0, pers)
    update_punkte()

def _auswahl_freigeben():
    """Unter X11 gehören Zwischenablage und Textauswahl dem Programm, das sie
    gesetzt hat. Vor dem Beenden geordnet freigeben, damit andere Programme
    (unter Wayland über die XWayland-Brücke) nicht auf ein verschwundenes
    Programm warten."""
    if not _X11:
        return
    try:
        if root.tk.call("selection", "own", "-selection", "PRIMARY"):
            root.tk.call("selection", "clear", "-selection", "PRIMARY")
        # Tk nennt keinen Besitzer der Zwischenablage. Nur freigeben, wenn sie
        # noch den Text dieser App enthält – sonst würde die Zwischenablage
        # eines anderen Programms gelöscht.
        if _zwischenablage["text"] is not None and root.clipboard_get() == _zwischenablage["text"]:
            root.tk.call("selection", "clear", "-selection", "CLIPBOARD")
    except tk.TclError:
        pass
    try:
        root.update()  # offene Anfragen beantworten und Freigabe senden
    except tk.TclError:
        pass

def beenden():
    save_session()
    _auswahl_freigeben()
    root.destroy()

# ── GUI aufbauen ──────────────────────────────────────────────────────────────

ttk.Label(scroll_frame, text=f"Menüplaner v{__version__}", font=SCHRIFT_TITEL).grid(
    row=0, column=0, columnspan=5, pady=10)

for r, tag in enumerate(tage):
    ttk.Label(scroll_frame, text=tag, font=SCHRIFT_FETT).grid(
        row=1 + r * 5, column=0, sticky="w")
    for j, mahlzeit in enumerate(mahlzeiten):
        key = f"{tag}_{mahlzeit}"
        ttk.Label(scroll_frame, text=mahlzeit).grid(row=2 + r * 5 + j, column=0, sticky="e")
        kat_combo = ttk.Combobox(scroll_frame, values=list(rezepte_by_kategorie.keys()),
                                  state="readonly", width=30)
        kat_combo.grid(row=2 + r * 5 + j, column=1)
        rezept_combo = ttk.Combobox(scroll_frame, values=[], width=60)
        rezept_combo.grid(row=2 + r * 5 + j, column=2)
        entry = ttk.Entry(scroll_frame, width=5)
        entry.insert(0, "1")
        entry.grid(row=2 + r * 5 + j, column=3)
        ttk.Label(scroll_frame, text="Personen").grid(row=2 + r * 5 + j, column=4, sticky="w")
        kat_combo.bind("<<ComboboxSelected>>", lambda e, k=key: (update_rezept_dropdown_for(k, True), update_punkte()))
        for w in (kat_combo, rezept_combo, entry):
            _mausrad_scrollt_seite(w)
        rezept_combo.bind("<<ComboboxSelected>>", lambda e, k=key: rezept_gewaehlt(k))
        auswahl_kat[key] = kat_combo
        auswahl_rezept[key] = rezept_combo
        anzahl_personen[key] = entry
        setup_searchable_rezept(key)
    lbl = ttk.Label(scroll_frame, text="0 Pkt", foreground="blue")
    lbl.grid(row=2 + r * 5 + len(mahlzeiten), column=1, columnspan=3, sticky="w")
    punkte_labels[tag] = lbl

ttk.Button(scroll_frame, text="Einkaufsliste anzeigen",
           command=zeige_einkaufsliste).grid(row=1000, column=0, columnspan=5, pady=(10, 2))
ttk.Button(scroll_frame, text="Einkaufsliste + Wochenplan exportieren",
           command=export_plan_und_einkaufsliste).grid(row=1001, column=0, columnspan=5, pady=2)
ttk.Button(scroll_frame, text="Wochenplan als Text kopieren",
           command=copy_wochenplan).grid(row=1002, column=0, columnspan=5, pady=2)
ttk.Button(scroll_frame, text="Rezepte verwalten",
           command=oeffne_rezeptverwaltung).grid(row=1003, column=0, columnspan=5, pady=2)
ttk.Button(scroll_frame, text="Beenden",
           command=beenden).grid(row=1004, column=0, columnspan=5, pady=(2, 10))

update_rezept_dropdown()
load_session()

# Auch beim Schliessen über das Fenster-X (bzw. Cmd+Q unter macOS) speichern
root.protocol("WM_DELETE_WINDOW", beenden)
if sys.platform == "darwin":
    root.createcommand("::tk::mac::Quit", beenden)

def _hauptfenster_anpassen():
    """Fenstergrösse an Inhalt und Bildschirm anpassen (Schriftbreiten
    unterscheiden sich zwischen Windows, macOS und Linux und je nach Zoom)."""
    root.update_idletasks()
    _fenstergroesse(root, scroll_frame.winfo_reqwidth() + scroll_y.winfo_reqwidth() + 4,
                    scroll_frame.winfo_reqheight() + 4)

# ── Ansicht-Menü (Zoom) ───────────────────────────────────────────────────────

_zoom_var = tk.DoubleVar(root, value=_zoom["faktor"])

def zoom_einstellen(faktor, speichern=True):
    """Zoom ändern; faktor=None bedeutet automatisch."""
    _zoom["gespeichert"] = None if faktor is None else min(max(float(faktor), 0.5), 4.0)
    setze_zoom(auto_zoom() if faktor is None else _zoom["gespeichert"])
    _zoom_var.set(_zoom["faktor"])
    _hauptfenster_anpassen()
    if speichern:
        save_session()

def zoom_schritt(richtung):
    aktuell = _zoom["faktor"]
    if richtung > 0:
        groesser = [z for z in ZOOM_STUFEN if z > aktuell + 0.01]
        ziel = groesser[0] if groesser else ZOOM_STUFEN[-1]
    else:
        kleiner = [z for z in ZOOM_STUFEN if z < aktuell - 0.01]
        ziel = kleiner[-1] if kleiner else ZOOM_STUFEN[0]
    zoom_einstellen(ziel)

_menuleiste = tk.Menu(root, tearoff=False)
_ansicht = tk.Menu(_menuleiste, tearoff=False)
_menuleiste.add_cascade(label="Ansicht", menu=_ansicht)
_taste = "Cmd" if sys.platform == "darwin" else "Strg"
_ansicht.add_command(label="Grösser", accelerator=f"{_taste}++", command=lambda: zoom_schritt(1))
_ansicht.add_command(label="Kleiner", accelerator=f"{_taste}+-", command=lambda: zoom_schritt(-1))
_ansicht.add_command(label="Automatisch", accelerator=f"{_taste}+0", command=lambda: zoom_einstellen(None))
_ansicht.add_separator()
for _stufe in ZOOM_STUFEN:
    _ansicht.add_radiobutton(label=f"{int(_stufe * 100)} %", variable=_zoom_var, value=_stufe,
                             command=lambda s=_stufe: zoom_einstellen(s))
root.config(menu=_menuleiste)

_modifikator = "Command" if sys.platform == "darwin" else "Control"
for _sequenz, _richtung in (("plus", 1), ("equal", 1), ("KP_Add", 1), ("minus", -1), ("KP_Subtract", -1)):
    root.bind(f"<{_modifikator}-{_sequenz}>", lambda e, r=_richtung: zoom_schritt(r))
for _sequenz in ("0", "KP_0"):
    root.bind(f"<{_modifikator}-{_sequenz}>", lambda e: zoom_einstellen(None))

_hauptfenster_anpassen()

# ── Selbsttest ────────────────────────────────────────────────────────────────

_selbsttest_fehler = []

def _selbsttest():
    import traceback
    global asksaveasfilename
    try:
        # Dialoge dürfen im Selbsttest nicht blockieren
        messagebox.showinfo = lambda *a, **k: None
        messagebox.showwarning = lambda *a, **k: _selbsttest_fehler.append(("Warnung",) + a)
        messagebox.showerror = lambda *a, **k: _selbsttest_fehler.append(("Fehler",) + a)
        export_datei = os.path.join(tempfile.mkdtemp(), "selbsttest.xlsx")
        asksaveasfilename = lambda **k: export_datei

        if not rezept_infos:
            raise RuntimeError("keine Rezepte geladen")
        key = f"{tage[0]}_{mahlzeiten[0]}"
        label = next((l for l, info in rezept_infos.items() if info["zutaten"]), None)
        if label is None:
            raise RuntimeError("kein Rezept mit Zutaten gefunden")
        auswahl_rezept[key].set(label)
        rezept_gewaehlt(key)
        if not generate_list():
            raise RuntimeError("Einkaufsliste ist leer")
        for fenster_oeffnen in (zeige_einkaufsliste, oeffne_rezeptverwaltung):
            fenster_oeffnen()
            root.update()
            for w in root.winfo_children():
                if isinstance(w, tk.Toplevel):
                    w.destroy()
        start_zoom = _zoom["faktor"]
        setze_zoom(2.0)
        root.update()
        setze_zoom(start_zoom)
        export_plan_und_einkaufsliste()
        blaetter = pd.read_excel(export_datei, sheet_name=None)
        if set(blaetter) != {"Wochenplan", "Einkaufsliste"}:
            raise RuntimeError(f"Export unvollständig: {list(blaetter)}")
        copy_wochenplan()
    except Exception:
        _selbsttest_fehler.append(traceback.format_exc())
    for f in _selbsttest_fehler:
        _selbsttest_log(f"FEHLER: {f}")
    _selbsttest_log("SELBSTTEST " + ("FEHLGESCHLAGEN" if _selbsttest_fehler else "OK")
                    + f" ({len(rezept_infos)} Rezepte, Python {sys.version.split()[0]},"
                    f" Tk {tk.TkVersion}, pandas {pd.__version__}, Zoom {_zoom['faktor']:g})")
    root.destroy()

if SELBSTTEST:
    root.report_callback_exception = lambda typ, wert, tb: _selbsttest_fehler.append(f"{typ.__name__}: {wert}")
    root.after(60000, lambda: (_selbsttest_log("FEHLER: Zeitüberschreitung"), os._exit(3)))
    root.after(300, _selbsttest)

root.mainloop()

if SELBSTTEST:
    sys.exit(1 if _selbsttest_fehler else 0)
