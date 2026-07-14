import os
import re
import json
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from pathlib import Path
from datetime import datetime
import sv_ttk 

import pytesseract
from PIL import Image, ImageTk
import pymupdf
from openai import OpenAI

# Konfiguration
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
ERLAUBTE_FORMATE = {'.pdf', '.png', '.jpg', '.jpeg'}
CONFIG_FILE = "dokumenten_typen.json"
SETTINGS_FILE = "app_settings.json"
HISTORY_FILE = "history.json"

class FileRenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KI Datei-Umbenenner Pro (Full Edition)")
        self.root.geometry("1100x800")
        
        self.ordner_pfad = None
        self.zoom_faktor = 0.5
        
        self.apply_kde_theme()
        self.lade_typen()
        self.lade_einstellungen()
        
        self.aktuelle_dateien = []
        self.ausgewaehlte_datei = None
        self.original_image = None
        
        self.setup_ui()
        
        if self.ordner_pfad:
            self.liste_aktualisieren()

    # --- Persistenz & Config ---
    def lade_einstellungen(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pfad = Path(data.get("last_dir", ""))
                    if pfad.exists() and pfad.is_dir(): self.ordner_pfad = pfad
            except: pass

    def speichere_einstellungen(self):
        if self.ordner_pfad:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_dir": str(self.ordner_pfad)}, f, indent=4)

    def lade_typen(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: self.doc_types = json.load(f)
            except: self.doc_types = self.standard_typen()
        else: self.doc_types = self.standard_typen(); self.speichere_typen()

    def speichere_typen(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(self.doc_types, f, indent=4)

    def standard_typen(self):
        return {"Rechnung": "RE_", "Kontoauszug": "KA_", "Deutsche Bank": "DB_", "Comdirect": "Comdirect_", "Flatex": "Flatex_"}

    # --- UI Setup ---
    def setup_ui(self):
        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)
        ttk.Button(top_frame, text="Ordner wählen", command=self.ordner_waehlen).pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(top_frame, text="Status: Bereit", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="Hilfe", command=self.oeffne_hilfe).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Typen verwalten", command=self.oeffne_typen_manager).pack(side=tk.RIGHT, padx=5)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Links: Liste
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        sort_frame = ttk.Frame(left_frame)
        sort_frame.pack(fill=tk.X)
        ttk.Button(sort_frame, text="A-Z", command=lambda: self.sortiere("name", False)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(sort_frame, text="Z-A", command=lambda: self.sortiere("name", True)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(sort_frame, text="Datum ↑", command=lambda: self.sortiere("date", False)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(sort_frame, text="Datum ↓", command=lambda: self.sortiere("date", True)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.tree = ttk.Treeview(left_frame, columns=("Name", "Datum"), show="headings")
        self.tree.heading("Name", text="Name"); self.tree.heading("Datum", text="Datum")
        self.tree.column("Name", width=150); self.tree.column("Datum", width=80)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.datei_ausgewaehlt)

        # Mitte: Eingabefelder
        mid_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(mid_frame, weight=1)
        self.var_datum = tk.StringVar(); self.var_name = tk.StringVar(); self.var_vorschau = tk.StringVar(); self.var_typ = tk.StringVar()
        
        # Verbindung der Variablen zur Live-Vorschau
        self.var_datum.trace_add("write", self.update_vorschau_label)
        self.var_name.trace_add("write", self.update_vorschau_label)
        self.var_typ.trace_add("write", self.update_vorschau_label)
        
        ttk.Label(mid_frame, text="Datum (YYYY-MM-DD):").pack(anchor=tk.W)
        self.ent_datum = ttk.Entry(mid_frame, textvariable=self.var_datum, font=("Arial", 11)); self.ent_datum.pack(fill=tk.X, pady=5)
        
        ttk.Label(mid_frame, text="Typ (Auswahl):").pack(anchor=tk.W)
        self.combo_typ = ttk.Combobox(mid_frame, textvariable=self.var_typ, font=("Arial", 11), state="readonly")
        self.combo_typ.pack(fill=tk.X, pady=5)
        
        ttk.Label(mid_frame, text="Name (ohne Prefix):").pack(anchor=tk.W)
        self.ent_name = ttk.Entry(mid_frame, textvariable=self.var_name, font=("Arial", 11)); self.ent_name.pack(fill=tk.X, pady=5)
        
        ttk.Label(mid_frame, text="Vorschau:").pack(anchor=tk.W, pady=(10,0))
        ttk.Entry(mid_frame, textvariable=self.var_vorschau, font=("Arial", 11, "bold"), state="readonly").pack(fill=tk.X, pady=5)
        
        self.btn_umbenennen = ttk.Button(mid_frame, text="Datei umbenennen", command=self.datei_umbenennen, state=tk.DISABLED)
        self.btn_umbenennen.pack(pady=20)

        # Rechts: Preview & Zoom
        right_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(right_frame, weight=2)
        zoom_frame = ttk.Frame(right_frame)
        zoom_frame.pack(fill=tk.X)
        ttk.Button(zoom_frame, text="Zoom +", width=8, command=lambda: self.aendere_zoom(0.1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom -", width=8, command=lambda: self.aendere_zoom(-0.1)).pack(side=tk.LEFT, padx=2)
        
        self.canvas = tk.Canvas(right_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)

    # --- Logik ---
    def ki_analyse_prozess(self):
        text = self.extrahiere_text(self.ausgewaehlte_datei)
        typen_str = ", ".join(self.doc_types.keys())
        
        # History laden
        history_text = ""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try: 
                    h_data = json.load(f)
                    history_text = "\nFrühere erfolgreiche Benennungen (Dein Stil):\n" + "\n".join([f"- {h['name']}" for h in h_data[-3:]])
                except: pass

        prompt = (
            f"Du bist eine professionelle Archivarin. Analysiere das Dokument für ein Verzeichnissystem.\n"
            f"1. Extrahiere Datum (YYYY-MM-DD).\n"
            f"2. Wähle Typ aus ({typen_str}). Wenn unklar: 'Unbekannt'.\n"
            f"3. Extrahiere Betreff/Inhalt als kurzen Dateinamen (nur Buchstaben/Zahlen/Unterstriche).\n"
            f"4. Konfidenz: 'high' wenn sicher, 'low' wenn raten nötig.\n"
            f"{history_text}\n"
            f"Antworte NUR als JSON: {{\"datum\": \"YYYY-MM-DD\", \"typ\": \"...\", \"name\": \"...\", \"confidence\": \"high/low\"}}\n"
            f"Text: {text[:2000]}"
        )
        
        try:
            res = client.chat.completions.create(model="local-model", messages=[{"role": "user", "content": prompt}], temperature=0.0, timeout=60)
            raw = res.choices[0].message.content
            clean = re.sub(r'```json|```', '', raw).strip()
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            
            if match:
                data = json.loads(match.group(0))
                self.root.after(0, lambda: self.ui_update(data.get("datum"), data.get("typ"), data.get("name"), data.get("confidence")))
            else: self.root.after(0, lambda: self.ui_update(None, "Unbekannt", "Unbekannt", "low"))
        except: self.root.after(0, lambda: self.ui_update(None, "Unbekannt", "Unbekannt", "low"))
        finally: self.root.after(0, lambda: self.lbl_status.config(text="Bereit", foreground="blue"))

    def ui_update(self, d, t, n, conf="high"):
        d_str = str(d).strip() if d else ""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', d_str):
            d_str = datetime.fromtimestamp(self.ausgewaehlte_datei.stat().st_mtime).strftime('%Y-%m-%d')
        
        self.var_datum.set(d_str)
        self.update_combo_values()
        self.var_typ.set(t if t in self.doc_types else "Unbekannt")
        self.var_name.set(n if n and str(n).strip() else "Dokument")
        
        farbe = "lightyellow" if conf == "low" else "white"
        self.ent_datum.config(background=farbe); self.ent_name.config(background=farbe)
        self.btn_umbenennen.config(state=tk.NORMAL)
        self.update_vorschau_label()

    def speichere_erfolgreiche_benennung(self, name):
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try: history = json.load(f)
                except: history = []
        history.append({"name": name, "date": str(datetime.now())})
        with open(HISTORY_FILE, "w") as f: json.dump(history[-20:], f)

    def update_combo_values(self):
        werte = list(self.doc_types.keys())
        if "Unbekannt" not in werte: werte.append("Unbekannt")
        self.combo_typ['values'] = werte

    def update_vorschau_label(self, *args):
        if not self.ausgewaehlte_datei: return
        d = self.var_datum.get().strip(); typ = self.var_typ.get().strip(); name = self.var_name.get().strip()
        prefix = self.doc_types.get(typ, "")
        clean_name = re.sub(r'[^\w]', '_', name)
        vorschau = f"{d}_{prefix}{clean_name}" + self.ausgewaehlte_datei.suffix
        self.var_vorschau.set(vorschau)

    def datei_umbenennen(self):
        neuer_pfad = self.ausgewaehlte_datei.parent / self.var_vorschau.get()
        try:
            os.rename(self.ausgewaehlte_datei, neuer_pfad)
            self.speichere_erfolgreiche_benennung(self.var_name.get())
            self.liste_aktualisieren(); messagebox.showinfo("Erfolg", "Umbenannt!")
        except Exception as e: messagebox.showerror("Fehler", str(e))

    def ordner_waehlen(self):
        ordner = filedialog.askdirectory()
        if ordner: self.ordner_pfad = Path(ordner); self.speichere_einstellungen(); self.liste_aktualisieren()

    def liste_aktualisieren(self):
        if not self.ordner_pfad: return
        self.aktuelle_dateien = [f for f in self.ordner_pfad.iterdir() if f.suffix.lower() in ERLAUBTE_FORMATE]
        self.aktualisiere_treeview_ohne_scan()

    def aktualisiere_treeview_ohne_scan(self):
        self.tree.delete(*self.tree.get_children())
        for f in self.aktuelle_dateien:
            datum_str = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
            self.tree.insert("", tk.END, values=(f.name, datum_str))

    def datei_ausgewaehlt(self, event):
        sel = self.tree.selection()
        if not sel: return
        self.var_typ.set("Unbekannt")
        item = self.tree.item(sel[0])
        self.ausgewaehlte_datei = next((f for f in self.aktuelle_dateien if f.name == item['values'][0]), None)
        self.original_image = self.lade_bild(self.ausgewaehlte_datei)
        
        self.canvas.update()
        canvas_w, canvas_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        img_w, img_h = self.original_image.size
        self.zoom_faktor = min(canvas_w / img_w, canvas_h / img_h) * 0.95
        
        self.update_preview()
        self.lbl_status.config(text="Analysiere...", foreground="orange")
        threading.Thread(target=self.ki_analyse_prozess, daemon=True).start()

    # --- Hilfsmethoden ---
    def sortiere(self, modus, reverse):
        if modus == "name": self.aktuelle_dateien.sort(key=lambda x: x.name.lower(), reverse=reverse)
        else: self.aktuelle_dateien.sort(key=lambda x: x.stat().st_mtime, reverse=reverse)
        self.aktualisiere_treeview_ohne_scan()

    def on_mousewheel(self, event):
        delta = 0.1 if (event.num == 4 or event.delta > 0) else -0.1
        self.aendere_zoom(delta)

    def aendere_zoom(self, delta):
        self.zoom_faktor = max(0.1, min(2.0, self.zoom_faktor + delta))
        self.update_preview()

    def update_preview(self):
        if not self.original_image: return
        w, h = self.original_image.size
        img_resized = self.original_image.resize((int(w * self.zoom_faktor), int(h * self.zoom_faktor)), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all"); self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def lade_bild(self, datei):
        if datei.suffix.lower() == '.pdf':
            doc = pymupdf.open(datei); pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples); doc.close(); return img
        return Image.open(datei)

    def extrahiere_text(self, datei):
        try:
            if datei.suffix.lower() == '.pdf':
                with pymupdf.open(datei) as doc:
                    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
                    return pytesseract.image_to_string(Image.frombytes("RGB", [pix.width, pix.height], pix.samples), lang='deu')
            return pytesseract.image_to_string(Image.open(datei), lang='deu')
        except: return ""

    def oeffne_typen_manager(self):
        w = tk.Toplevel(self.root); w.title("Typen verwalten"); tree = ttk.Treeview(w, columns=("Typ", "Prefix"), show="headings")
        tree.heading("Typ", text="Typ"); tree.heading("Prefix", text="Prefix"); tree.pack(fill=tk.BOTH, expand=True)
        def lade_tree():
            tree.delete(*tree.get_children())
            for t, p in self.doc_types.items(): tree.insert("", tk.END, values=(t, p))
        lade_tree()
        ttk.Button(w, text="Schließen", command=w.destroy).pack(fill=tk.X)

    def oeffne_hilfe(self):
        w = tk.Toplevel(self.root)
        w.title("Hilfe & Anleitung")
        w.geometry("650x550")
        txt = scrolledtext.ScrolledText(w, wrap=tk.WORD, padx=20, pady=20, bg="#fcfcfc")
        txt.pack(fill=tk.BOTH, expand=True)
        txt.tag_config('h1', font=('Arial', 14, 'bold'), foreground='#2c3e50', spacing1=10)
        txt.tag_config('code', font=('Courier New', 10), background='#e0e0e0', lmargin1=10, lmargin2=10)
        txt.insert(tk.END, "Verwendung\n", 'h1')
        txt.insert(tk.END, "1. Ordner wählen\n2. Datei anklicken\n3. KI analysiert (Archivarin-Modus)\n4. Änderungen können manuell angepasst werden.\n5. Live-Vorschau zeigt den Dateinamen.\n")
        txt.insert(tk.END, "\nInstallation (Debian 13)\n", 'h1')
        txt.insert(tk.END, "sudo apt install python3-pip tesseract-ocr tesseract-ocr-deu libmupdf-dev\n", 'code')
        txt.config(state=tk.DISABLED)

    def apply_kde_theme(self):
        try:
            res = subprocess.run(["kreadconfig6", "--group", "General", "--key", "ColorScheme"], capture_output=True, text=True)
            sv_ttk.set_theme("dark" if "Dark" in res.stdout else "light")
        except: sv_ttk.set_theme("dark")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerGUI(root)
    root.mainloop()