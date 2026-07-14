# KI Datei-Umbenenner Pro (Archivar-Edition)

Ein intelligentes Python/Tkinter-Werkzeug zur automatisierten Benennung von Dokumenten (PDFs und Bildern) mittels lokaler KI (LM Studio) und OCR (Tesseract).

## Features
- **Archivarin-Persona:** Das lokale Modell analysiert den Text gezielt nach Betreffzeilen und Relevanz, um dateisystemfreundliche Namen zu erzeugen.
- **In-Context Learning (Gedächtnis):** Erfolgreiche Umbenennungen werden in einer Historie (`history.json`) gespeichert und dienen der KI bei der nächsten Analyse als Stil-Vorlage.
- **Auto-Scaling Preview:** Dokumente (PDFs und Bilder) werden automatisch perfekt eingepasst und in maximal möglicher Größe im Vorschaufenster dargestellt.
- **Live-Vorschau:** Manuelle Änderungen an Name, Datum oder Typ im Eingabefeld aktualisieren sofort die Dateinamens-Vorschau.
- **KDE Plasma Integration:** Erkennt das aktive System-Theme (Dark/Light) unter Debian automatisch und passt das Design der App an.

## Voraussetzungen (Debian 13)
Installiere die benötigten System-Pakete über dein Terminal:

```bash
sudo apt update
sudo apt install python3-pip tesseract-ocr tesseract-ocr-deu libmupdf-dev python3-full