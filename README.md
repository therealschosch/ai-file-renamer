# KI Datei-Umbenenner Pro (Archivar-Edition)

Ein intelligentes Python/Tkinter-Werkzeug zur automatisierten Benennung von Dokumenten (PDFs und Bildern) mittels lokaler KI (LM Studio) und OCR (Tesseract).

## Features
- **Archivarin-Persona:** Das lokale Modell analysiert den Text gezielt nach Betreffzeilen und Relevanz, um dateisystemfreundliche Namen zu erzeugen.
- **In-Context Learning (Gedächtnis):** Erfolgreiche Umbenennungen werden in einer Historie (`history.json`) gespeichert und dienen der KI bei der nächsten Analyse als Stil-Vorlage.
- **Auto-Scaling Preview:** Dokumente (PDFs und Bilder) werden automatisch perfekt eingepasst und in maximal möglicher Größe im Vorschaufenster dargestellt.
- **Live-Vorschau:** Manuelle Änderungen an Name, Datum oder Typ im Eingabefeld aktualisieren sofort die Dateinamens-Vorschau.
- **KDE Plasma Integration:** Erkennt das aktive System-Theme (Dark/Light) unter Debian automatisch und passt das Design der App an.

---

## 1. LM Studio & Llama Setup

Damit das Skript mit der KI kommunizieren kann, muss im Hintergrund ein lokaler Server mit einem passenden Sprachmodell (LLM) laufen.

### Schritt A: LM Studio installieren (Debian)
1. Gehe auf [lmstudio.ai](https://lmstudio.ai) und lade die Version für **Linux (AppImage)** herunter.
2. Öffne dein Terminal im Download-Ordner und mache das AppImage ausführbar:
```bash
chmod +x LM_Studio-*.AppImage
```
3. Starte LM Studio:
```bash
./LM_Studio-*.AppImage
```

### Schritt B: Llama-Modell herunterladen
Für dieses Projekt wird ein Modell empfohlen, das gut Deutsch spricht und ressourcenschonend läuft.
1. Öffne LM Studio und klicke links auf das **Lupen-Symbol (Suche)**.
2. Suche nach `Llama 3.1 8B Instruct` (oder alternativ `Llama 3 8B Instruct`).
3. Wähle eine **GGUF-Version** aus (ideal ist die Quantisierung **Q4_K_M** oder **Q5_K_M** – diese bieten die beste Balance aus Geschwindigkeit und Genauigkeit).
4. Klicke rechts auf **Download**.

### Schritt C: Lokalen Server starten
1. Klicke in LM Studio in der linken Menüleiste auf das **Server-Symbol** (zwei geschwungene Pfeile / Stecker-Symbol).
2. Wähle ganz oben im Dropdown-Menü dein frisch heruntergeladenes Llama-Modell aus (es wird nun in den Arbeitsspeicher geladen).
3. Stelle sicher, dass unter *Server Settings* der Port auf `1234` steht.
4. Klicke auf den grünen Button **Start Server**.
5. Sobald dort `Server listening on port 1234` steht, ist die KI einsatzbereit!

---

## 2. System-Voraussetzungen (Debian 13)
Installiere die benötigten System-Pakete über dein Terminal:
```bash
sudo apt update
sudo apt install python3-pip tesseract-ocr tesseract-ocr-deu libmupdf-dev python3-full
```

---

## 3. Installation & Setup des Skripts
1. Navigiere in deinen Projektordner:
```bash
cd ~/filerenamer
```
2. Erstelle und aktiviere die virtuelle Python-Umgebung:
```bash
python3 -m venv filerenamer_env
source filerenamer_env/bin/activate
```
3. Aktualisiere Pip und installiere die Python-Abhängigkeiten:
```bash
pip install --upgrade pip
pip install sv-ttk openai pymupdf pytesseract Pillow
```

---

## 4. Nutzung
1. Vergewissere dich, dass der **LM Studio Server** läuft (siehe Schritt 1).
2. Stelle sicher, dass deine virtuelle Python-Umgebung im Terminal aktiv ist (erkennbar am `(filerenamer_env)` vor der Eingabezeile):
```bash
source filerenamer_env/bin/activate
```
3. Starte das Programm:
```bash
python ki-file-renamer_v22.py
```
