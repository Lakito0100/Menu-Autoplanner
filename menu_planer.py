
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from tkinter.filedialog import asksaveasfilename
import re
import os

df = pd.read_excel("Rezepte.xlsx")

def parse_zutat(z):
    z = str(z).strip()
    match = re.match(r"^(\d+(?:[\.,]\d+)?)\s+(\w+)\s+(.+)", str(z).strip())
    if match:
        menge = float(match.group(1).replace(",", "."))
        einheit = match.group(2)
        name = match.group(3)
        return {"menge": menge, "einheit": einheit, "zutat": name}

        #print(f"[WARNUNG] Ungültiges Format für Zutat: {z} \n Bitte korrekter Format verwenden: [Menge] [Einheit] [Zutat] \n")
    fallback_match = re.match(r"^(\d+(?:[\.,]\d+)?)\s+(.+)", z)
    if fallback_match:
        menge = float(fallback_match.group(1).replace(",", "."))
        name = fallback_match.group(2)
        einheit = ""
        return {"menge": menge, "einheit": einheit, "zutat": name}
    
    # Völlig unlesbar → Standardwert
    return {"menge": 1, "einheit": "", "zutat": z}

rezepte_by_kategorie = {}
rezept_infos = {}

for _, row in df.iterrows():
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

tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
mahlzeiten = ["Frühstück", "Mittagessen", "Abendessen"]

root = tk.Tk()
root.title("Menüplaner")

# Dynamisches Fenster (nicht fixiert)
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

def update_rezept_dropdown_for(key):
    kat_box = auswahl_kat[key]
    rezept_box = auswahl_rezept[key]
    kategorie = kat_box.get()
    aktuelle_auswahl = rezept_box.get()
    rezept_box["values"] = rezepte_by_kategorie.get(kategorie, [])
    if aktuelle_auswahl in rezept_box["values"]:
        rezept_box.set(aktuelle_auswahl)
    elif rezept_box["values"]:
        rezept_box.current(0)

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

def beenden():
    root.destroy()
    os._exit(0)

ttk.Label(scroll_frame, text="Menüplaner", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=5, pady=10)

for r, tag in enumerate(tage):
    ttk.Label(scroll_frame, text=tag, font=("Arial", 10, "bold")).grid(row=1 + r*5, column=0, sticky="w")
    for j, mahlzeit in enumerate(mahlzeiten):
        key = f"{tag}_{mahlzeit}"
        ttk.Label(scroll_frame, text=mahlzeit).grid(row=2 + r*5 + j, column=0, sticky="e")
        kat_combo = ttk.Combobox(scroll_frame, values=list(rezepte_by_kategorie.keys()), state="readonly", width=30)
        kat_combo.grid(row=2 + r*5 + j, column=1)
        rezept_combo = ttk.Combobox(scroll_frame, values=[], state="readonly", width=60)
        rezept_combo.grid(row=2 + r*5 + j, column=2)
        entry = ttk.Entry(scroll_frame, width=5)
        entry.insert(0, "1")
        entry.grid(row=2 + r*5 + j, column=3)
        ttk.Label(scroll_frame, text="Personen").grid(row=2 + r*5 + j, column=4, sticky="w")
        kat_combo.bind("<<ComboboxSelected>>", lambda e, k=key: update_rezept_dropdown_for(k))
        rezept_combo.bind("<<ComboboxSelected>>", lambda e: update_punkte())
        auswahl_kat[key] = kat_combo
        auswahl_rezept[key] = rezept_combo
        anzahl_personen[key] = entry
    lbl = ttk.Label(scroll_frame, text="0 Pkt", foreground="blue")
    lbl.grid(row=2 + r*5 + len(mahlzeiten), column=1, columnspan=3, sticky="w")
    punkte_labels[tag] = lbl

ttk.Button(scroll_frame, text="Einkaufsliste + Wochenplan exportieren", command=export_plan_und_einkaufsliste).grid(row=1000, column=0, columnspan=5, pady=10)
ttk.Button(scroll_frame, text="Beenden", command=beenden).grid(row=1001, column=0, columnspan=5, pady=10)

update_rezept_dropdown()
root.mainloop()
