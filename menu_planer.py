
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from tkinter.filedialog import asksaveasfilename
import re
import os
import json

SESSION_FILE = "session.json"

df = pd.read_excel("Rezepte.xlsx")

def parse_zutat(z):
    z = str(z).strip()
    match = re.match(r"^(\d+(?:[\.,]\d+)?)\s+(\w+)\s+(.+)", str(z).strip())
    if match:
        menge = float(match.group(1).replace(",", "."))
        einheit = match.group(2)
        name = match.group(3)
        return {"menge": menge, "einheit": einheit, "zutat": name}

    fallback_match = re.match(r"^(\d+(?:[\.,]\d+)?)\s+(.+)", z)
    if fallback_match:
        menge = float(fallback_match.group(1).replace(",", "."))
        name = fallback_match.group(2)
        einheit = ""
        return {"menge": menge, "einheit": einheit, "zutat": name}

    return {"menge": 1, "einheit": "", "zutat": z}

rezepte_by_kategorie = {}
rezept_infos = {}

def _lade_rezepte_aus_df(source_df):
    rezept_infos.clear()
    rezepte_by_kategorie.clear()
    for _, row in source_df.iterrows():
        rezept = row["Rezeptname"]
        kategorie = row["Kategorie"] if "Kategorie" in row and pd.notna(row["Kategorie"]) else "Allgemein"
        punkte = row["Punkte"]
        portionen = row["Portionen"] if "Portionen" in row and pd.notna(row["Portionen"]) else 1
        zutaten = [parse_zutat(row[col]) for col in row.index if col.startswith("Zutat") and pd.notna(row[col])]
        rezept_label = f"{rezept} ({punkte} Pkt)"
        rezept_infos[rezept_label] = {
            "punkte": punkte,
            "zutaten": zutaten,
            "kategorie": kategorie,
            "rezeptname": rezept,
            "portionen": portionen
        }
        rezepte_by_kategorie.setdefault(kategorie, []).append(rezept_label)

_lade_rezepte_aus_df(df)

tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
mahlzeiten = ["Frühstück", "Mittagessen", "Abendessen"]

root = tk.Tk()
root.title("Menüplaner")
root.geometry("750x830")
root.minsize(800, 860)

canvas = tk.Canvas(root)
scroll_y = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scroll_y.set)

scroll_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
canvas.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

auswahl_kat = {}
auswahl_rezept = {}
anzahl_personen = {}
punkte_labels = {}

# ── Dropdown-Logik ────────────────────────────────────────────────────────────

def update_rezept_dropdown_for(key):
    kat_box = auswahl_kat[key]
    rezept_box = auswahl_rezept[key]
    kategorie = kat_box.get()
    aktuelle_auswahl = rezept_box.get()
    neue_liste = rezepte_by_kategorie.get(kategorie, [])
    rezept_box["values"] = neue_liste
    if aktuelle_auswahl in neue_liste:
        rezept_box.set(aktuelle_auswahl)
    elif neue_liste:
        rezept_box.set(neue_liste[0])
    else:
        rezept_box.set("")

def update_rezept_dropdown(event=None):
    for key in auswahl_kat.keys():
        update_rezept_dropdown_for(key)
    update_punkte()

def update_punkte():
    for tag in tage:
        tages_summe = 0
        for mahlzeit in mahlzeiten:
            key = f"{tag}_{mahlzeit}"
            rezept = auswahl_rezept[key].get()
            if rezept in rezept_infos:
                tages_summe += rezept_infos[rezept]["punkte"]
        punkte_labels[tag]["text"] = f"{tages_summe} Pkt"

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
            base = [r for recipes in rezepte_by_kategorie.values() for r in recipes]
        if typed:
            filtered = [r for r in base if typed.lower() in r.lower()]
        else:
            filtered = base
        rezept_combo["values"] = filtered
        update_punkte()

    rezept_combo.bind("<KeyRelease>", filter_recipes)

# ── Einkaufsliste ─────────────────────────────────────────────────────────────

def generate_list():
    zutaten_dict = {}
    for key, box in auswahl_rezept.items():
        rezept = box.get()
        personen = anzahl_personen[key].get()
        if rezept in rezept_infos:
            try:
                personen = float(personen)
            except:
                personen = 1
            portionen = rezept_infos[rezept]["portionen"]
            faktor = personen / portionen if portionen > 0 else 1
            for z in rezept_infos[rezept]["zutaten"]:
                k = (z["zutat"], z["einheit"])
                zutaten_dict[k] = zutaten_dict.get(k, 0) + z["menge"] * faktor
    generate_list.einkaufsliste = pd.DataFrame([
        {"Menge": round(m, 2), "Einheit": e, "Zutat": z} for (z, e), m in zutaten_dict.items()
    ])
    return generate_list.einkaufsliste

def zeige_einkaufsliste():
    einkaufsliste = generate_list()

    win = tk.Toplevel(root)
    win.title("Einkaufsliste")
    win.geometry("560x660")
    win.grab_set()

    # Treeview + Scrollbar
    frame_tree = ttk.Frame(win)
    frame_tree.pack(fill="both", expand=True, padx=10, pady=(10, 0))

    cols = ("Menge", "Einheit", "Zutat")
    tree = ttk.Treeview(frame_tree, columns=cols, show="headings", height=18)
    tree.heading("Menge", text="Menge")
    tree.heading("Einheit", text="Einheit")
    tree.heading("Zutat", text="Zutat")
    tree.column("Menge", width=70, anchor="e")
    tree.column("Einheit", width=80)
    tree.column("Zutat", width=340)

    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="left", fill="y")

    for _, row in einkaufsliste.iterrows():
        tree.insert("", "end", values=(row["Menge"], row["Einheit"], row["Zutat"]))

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

    def add_item():
        zutat = entry_zutat.get().strip()
        if not zutat:
            return
        tree.insert("", "end", values=(entry_menge.get().strip(), entry_einheit.get().strip(), zutat))
        entry_menge.delete(0, tk.END)
        entry_einheit.delete(0, tk.END)
        entry_zutat.delete(0, tk.END)

    ttk.Button(frame_add, text="Hinzufügen", command=add_item).grid(row=0, column=6, padx=6)

    # Aktions-Buttons
    frame_btns = ttk.Frame(win)
    frame_btns.pack(fill="x", padx=10, pady=6)

    def delete_selected():
        for item in tree.selection():
            tree.delete(item)

    def export_excel():
        data = [{"Menge": tree.item(i, "values")[0],
                 "Einheit": tree.item(i, "values")[1],
                 "Zutat": tree.item(i, "values")[2]}
                for i in tree.get_children()]
        if not data:
            messagebox.showwarning("Leer", "Einkaufsliste ist leer.", parent=win)
            return
        filepath = asksaveasfilename(defaultextension=".xlsx",
                                     filetypes=[("Excel-Dateien", "*.xlsx")],
                                     parent=win)
        if filepath:
            pd.DataFrame(data).to_excel(filepath, index=False)
            messagebox.showinfo("Erfolg", "Einkaufsliste exportiert.", parent=win)

    def copy_text():
        lines = []
        for i in tree.get_children():
            menge, einheit, zutat = tree.item(i, "values")
            lines.append(f"{menge} {einheit} {zutat}".strip())
        win.clipboard_clear()
        win.clipboard_append("\n".join(lines))
        messagebox.showinfo("Kopiert", "Einkaufsliste in Zwischenablage kopiert.", parent=win)

    ttk.Button(frame_btns, text="Ausgewählte löschen", command=delete_selected).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Als Excel exportieren", command=export_excel).pack(side="left", padx=4)
    ttk.Button(frame_btns, text="Als Text kopieren", command=copy_text).pack(side="left", padx=4)

# ── Wochenplan-Export ─────────────────────────────────────────────────────────

def export_plan_und_einkaufsliste():
    einkaufsliste = generate_list()
    filepath = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel-Dateien", "*.xlsx")])
    if not filepath:
        return
    plan_data = []
    for tag in tage:
        row = {"Tag": tag}
        for mahlzeit in mahlzeiten:
            key = f"{tag}_{mahlzeit}"
            rezept = auswahl_rezept[key].get()
            anzahl = anzahl_personen[key].get()
            rezeptname = rezept_infos.get(rezept, {}).get("rezeptname", "")
            row[mahlzeit] = f"{rezeptname} ({anzahl} Pers.)"
        row["Punkte"] = punkte_labels[tag]["text"]
        plan_data.append(row)
    plan_df = pd.DataFrame(plan_data)
    with pd.ExcelWriter(filepath) as writer:
        plan_df.to_excel(writer, index=False, sheet_name="Wochenplan")
        einkaufsliste.to_excel(writer, index=False, sheet_name="Einkaufsliste")
    messagebox.showinfo("Erfolg", "Wochenplan und Einkaufsliste exportiert.")

# ── Rezeptverwaltung ──────────────────────────────────────────────────────────

def reload_rezepte():
    global df
    df = pd.read_excel("Rezepte.xlsx")
    _lade_rezepte_aus_df(df)
    kategorien = list(rezepte_by_kategorie.keys())
    for kat_box in auswahl_kat.values():
        kat_box["values"] = kategorien
    update_rezept_dropdown()

def oeffne_rezeptverwaltung():
    win = tk.Toplevel(root)
    win.title("Rezepte verwalten")
    win.geometry("940x680")
    win.grab_set()

    # Linke Spalte: Rezeptliste
    frame_left = ttk.Frame(win)
    frame_left.pack(side="left", fill="y", padx=(10, 0), pady=10)

    ttk.Label(frame_left, text="Rezepte", font=("Arial", 10, "bold")).pack(anchor="w")

    frame_lb = ttk.Frame(frame_left)
    frame_lb.pack(fill="y", expand=True)

    listbox = tk.Listbox(frame_lb, width=32, height=32, exportselection=False)
    listbox.pack(side="left", fill="y", expand=True)
    sb_lb = ttk.Scrollbar(frame_lb, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=sb_lb.set)
    sb_lb.pack(side="left", fill="y")

    def refresh_listbox():
        listbox.delete(0, tk.END)
        for label in sorted(rezept_infos.keys()):
            listbox.insert(tk.END, label)

    refresh_listbox()

    # Rechte Spalte: Formular
    frame_right = ttk.Frame(win)
    frame_right.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    ttk.Label(frame_right, text="Rezeptdetails", font=("Arial", 10, "bold")).grid(
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

    ttk.Label(frame_right, text="Zutaten:", font=("Arial", 9, "bold")).grid(
        row=6, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 0))
    ttk.Label(frame_right, text="Format: Menge Einheit Zutatname  (z.B. '500 g Hackfleisch' oder '2 Eier')").grid(
        row=7, column=0, columnspan=2, sticky="w", padx=5)

    # Scrollbares Zutaten-Frame
    frame_z_outer = ttk.Frame(frame_right)
    frame_z_outer.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=5, pady=4)
    frame_right.rowconfigure(8, weight=1)

    canvas_z = tk.Canvas(frame_z_outer, height=250)
    sb_z = ttk.Scrollbar(frame_z_outer, orient="vertical", command=canvas_z.yview)
    canvas_z.configure(yscrollcommand=sb_z.set)
    canvas_z.pack(side="left", fill="both", expand=True)
    sb_z.pack(side="left", fill="y")

    frame_zutaten = ttk.Frame(canvas_z)
    canvas_z.create_window((0, 0), window=frame_zutaten, anchor="nw")
    frame_zutaten.bind("<Configure>", lambda e: canvas_z.configure(scrollregion=canvas_z.bbox("all")))

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

    ttk.Button(frame_right, text="+ Zutat hinzufügen", command=add_zutat_row).grid(
        row=9, column=0, columnspan=2, pady=4)

    # Rezept in Formular laden
    def load_rezept(event=None):
        sel = listbox.curselection()
        if not sel:
            return
        label = listbox.get(sel[0])
        info = rezept_infos.get(label, {})

        entries["Rezeptname:"].delete(0, tk.END)
        entries["Rezeptname:"].insert(0, info.get("rezeptname", ""))
        entries["Kategorie:"].set(info.get("kategorie", ""))
        entries["Punkte:"].delete(0, tk.END)
        entries["Punkte:"].insert(0, str(info.get("punkte", "")))
        entries["Portionen:"].delete(0, tk.END)
        entries["Portionen:"].insert(0, str(info.get("portionen", "")))

        for e in list(zutat_entries):
            e.master.destroy()
        zutat_entries.clear()

        for z in info.get("zutaten", []):
            m = z["menge"]
            m_str = str(int(m)) if m == int(m) else str(m)
            line = f"{m_str} {z['einheit']} {z['zutat']}".strip()
            add_zutat_row(line)

        if not zutat_entries:
            add_zutat_row()

    listbox.bind("<<ListboxSelect>>", load_rezept)

    def neu_rezept():
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
        except ValueError:
            messagebox.showwarning("Fehler", "Punkte müssen eine Zahl sein.", parent=win)
            return
        try:
            portionen = float(entries["Portionen:"].get().replace(",", "."))
        except ValueError:
            portionen = 1.0

        zutaten_liste = [e.get().strip() for e in zutat_entries if e.get().strip()]

        row_data = {"Rezeptname": name, "Kategorie": kategorie,
                    "Punkte": punkte, "Portionen": portionen}
        for i, z in enumerate(zutaten_liste, 1):
            row_data[f"Zutat {i}"] = z

        try:
            existing_df = pd.read_excel("Rezepte.xlsx")
        except Exception:
            existing_df = pd.DataFrame()

        if "Rezeptname" in existing_df.columns and name in existing_df["Rezeptname"].values:
            idx = existing_df.index[existing_df["Rezeptname"] == name][0]
            for col in [c for c in existing_df.columns if c.startswith("Zutat")]:
                existing_df.at[idx, col] = None
            for k, v in row_data.items():
                existing_df.at[idx, k] = v
        else:
            existing_df = pd.concat([existing_df, pd.DataFrame([row_data])], ignore_index=True)

        existing_df.to_excel("Rezepte.xlsx", index=False)
        reload_rezepte()
        refresh_listbox()
        entries["Kategorie:"]["values"] = list(rezepte_by_kategorie.keys())
        messagebox.showinfo("Erfolg", f"Rezept '{name}' gespeichert.", parent=win)

    def loeschen_rezept():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Kein Rezept gewählt", "Bitte zuerst ein Rezept auswählen.", parent=win)
            return
        label = listbox.get(sel[0])
        name = rezept_infos[label]["rezeptname"]
        if not messagebox.askyesno("Löschen bestätigen", f"Rezept '{name}' wirklich löschen?", parent=win):
            return
        existing_df = pd.read_excel("Rezepte.xlsx")
        existing_df = existing_df[existing_df["Rezeptname"] != name]
        existing_df.to_excel("Rezepte.xlsx", index=False)
        reload_rezepte()
        refresh_listbox()
        neu_rezept()
        messagebox.showinfo("Gelöscht", f"Rezept '{name}' wurde gelöscht.", parent=win)

    frame_btns = ttk.Frame(frame_right)
    frame_btns.grid(row=10, column=0, columnspan=2, pady=8)
    ttk.Button(frame_btns, text="Neues Rezept", command=neu_rezept).pack(side="left", padx=6)
    ttk.Button(frame_btns, text="Speichern", command=speichern_rezept).pack(side="left", padx=6)
    ttk.Button(frame_btns, text="Löschen", command=loeschen_rezept).pack(side="left", padx=6)

# ── Session-Persistenz ────────────────────────────────────────────────────────

def save_session():
    data = {}
    for key in auswahl_kat:
        data[key] = {
            "kategorie": auswahl_kat[key].get(),
            "rezept": auswahl_rezept[key].get(),
            "personen": anzahl_personen[key].get()
        }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return
    for key, vals in data.items():
        if key not in auswahl_kat:
            continue
        kat = vals.get("kategorie", "")
        if kat in rezepte_by_kategorie:
            auswahl_kat[key].set(kat)
        update_rezept_dropdown_for(key)
        rezept = vals.get("rezept", "")
        if rezept in rezept_infos:
            auswahl_rezept[key].set(rezept)
        pers = vals.get("personen", "1")
        anzahl_personen[key].delete(0, tk.END)
        anzahl_personen[key].insert(0, pers)
    update_punkte()

def beenden():
    save_session()
    root.destroy()
    os._exit(0)

# ── GUI aufbauen ──────────────────────────────────────────────────────────────

ttk.Label(scroll_frame, text="Menüplaner", font=("Arial", 14, "bold")).grid(
    row=0, column=0, columnspan=5, pady=10)

for r, tag in enumerate(tage):
    ttk.Label(scroll_frame, text=tag, font=("Arial", 10, "bold")).grid(
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
        kat_combo.bind("<<ComboboxSelected>>", lambda e, k=key: (update_rezept_dropdown_for(k), update_punkte()))
        rezept_combo.bind("<<ComboboxSelected>>", lambda e: update_punkte())
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
ttk.Button(scroll_frame, text="Rezepte verwalten",
           command=oeffne_rezeptverwaltung).grid(row=1002, column=0, columnspan=5, pady=2)
ttk.Button(scroll_frame, text="Beenden",
           command=beenden).grid(row=1003, column=0, columnspan=5, pady=(2, 10))

update_rezept_dropdown()
load_session()
root.mainloop()
