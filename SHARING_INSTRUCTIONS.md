# Windows-User Setup Anleitung (Komplette Schrittfolge)

Diese Anleitung beschreibt, wie ein Windows-User das Emanuel Vogt Digital Archive auf seinem Computer einrichtet und nutzt.

---

## 📦 Schritt 1: Benötigte Dateien erhalten

Der Windows-User benötigt folgende Dateien/Ordner:

### Essenzielle Dateien:
```
emanuelvogt/
├── app/
│   ├── backend.py
│   ├── index.html
│   ├── musicxml_player.html
│   └── static/
│       ├── app.js
│       └── style.css
├── data/
│   ├── archive.db           ← WICHTIG: Datenbank mit allen Metadaten
│   └── manual/              ← MusicXML-Dateien (optional, für Notenvorschau)
│       ├── werk_9.musicxml
│       ├── werk_12d.musicxml
│       ├── werk_461.musicxml
│       └── werk_1872.musicxml
├── archive/
│   └── files/               ← ~28GB PDFs (kann auch später hinzugefügt werden)
│       ├── Psalmen/
│       └── Werke/           ← WICHTIG: Muss "Werke" heißen, nicht "Werke - außer Psalmen"
├── requirements.txt
└── run_viewer.bat           ← Windows-Startskript
```

### Transfer-Methoden:
- **USB-Stick/externe SSD** (empfohlen für 28GB archive/)
- **Cloud-Link** (Dropbox, Google Drive)
- **Git Repository** + separate Übertragung der großen Dateien

---

## 🔧 Schritt 2: Python Installation prüfen

1. **Kommandozeile öffnen:**
   - `Windows-Taste` drücken
   - "cmd" tippen
   - Enter drücken

2. **Python-Version prüfen:**
   ```batch
   python --version
   ```
   
   **Erwartetes Ergebnis:** `Python 3.9.x` oder höher

3. **Falls Python nicht installiert ist:**
   - Download von [python.org](https://www.python.org/downloads/)
   - Bei Installation: ✅ **"Add Python to PATH"** aktivieren!

---

## 📁 Schritt 3: Verzeichnisstruktur korrigieren (KRITISCH!)

⚠️ **WICHTIG:** Der Ordner muss umbenannt werden für Windows-Kompatibilität.

1. **Datei-Explorer öffnen** und zum Projekt-Ordner navigieren
2. **In den Ordner gehen:** `archive\files\`
3. **Ordner umbenennen:**
   - **ALT:** `Werke - außer Psalmen`
   - **NEU:** `Werke` (ohne " - außer Psalmen")

4. **Ergebnis überprüfen:**
   ```
   archive\files\Werke\
                 └── Frühe Werke - ab 1943\
                 └── Werke 1 bis 20\
                 └── Werke 21 bis 40\
                 └── ...
   ```

---

## 🐍 Schritt 4: Python-Umgebung einrichten

1. **Kommandozeile im Projekt-Ordner öffnen:**
   - Im Datei-Explorer zum Projekt-Ordner navigieren (`emanuelvogt`)
   - In die Adressleiste klicken
   - `cmd` tippen und Enter drücken

2. **Virtuelle Umgebung erstellen:**
   ```batch
   python -m venv venv
   ```
   
   ⏱️ *Dauert ca. 30 Sekunden*

3. **Virtuelle Umgebung aktivieren:**
   ```batch
   venv\Scripts\activate
   ```
   
   **Erwartetes Ergebnis:** `(venv)` erscheint vor dem Prompt:
   ```
   (venv) C:\Users\Name\emanuelvogt>
   ```

4. **Abhängigkeiten installieren:**
   ```batch
   pip install -r requirements.txt
   ```
   
   ⏱️ *Dauert ca. 1-2 Minuten*
   
   **Erwartete Pakete:**
   - fastapi
   - uvicorn
   - python-multipart
   - openpyxl

---

## 🚀 Schritt 5: Datenbank-Pfade aktualisieren

**Nur notwendig, wenn die Umbenennung in Schritt 3 noch nicht gemacht wurde!**

Falls Sie das Skript verwenden möchten:

```batch
python scripts\11_fix_directory_names.py
```

Eingabe: `yes` und Enter

---

## ▶️ Schritt 6: Archive starten

### Methode A: Doppelklick (einfachste Variante)
1. Im Datei-Explorer zu `emanuelvogt\` navigieren
2. Doppelklick auf `run_viewer.bat`
3. Ein Kommandozeilenfenster öffnet sich

### Methode B: Über Kommandozeile
```batch
run_viewer.bat
```

**Erwartete Ausgabe:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

⚠️ **WICHTIG:** Das Kommandozeilenfenster **nicht schließen** während der Nutzung!

---

## 🌐 Schritt 7: Archive im Browser öffnen

1. **Browser öffnen** (Chrome, Firefox, Edge)
2. **URL eingeben:** `http://localhost:8000`
3. **Enter drücken**

**Sie sollten nun sehen:**
- Suchfeld für Werksuche
- Filter für Besetzung
- Liste der digitalisierten Werke

---

## 🎵 Schritt 8: MusicXML-Player testen (optional)

1. **Nach einem Werk mit MusicXML suchen:**
   - Werk **9**, **12d**, **461** oder **1872** in die Suche eingeben

2. **Werk öffnen** (auf Werkzeile klicken)

3. **Hinweis beachten:**
   - "🎵 **Dieses Werk hat eine MusicXML-Datei**"
   - Link "**Noten ansehen und abspielen**" klicken

4. **Player testen:**
   - ▶️ **Abspielen** - Startet die Wiedergabe
   - ⏸️ **Pause** - Pausiert
   - ⏹️ **Stoppen** - Stoppt und setzt zurück
   - **Tempo-Regler** - Anpassen der Geschwindigkeit (40-200 BPM)

---

## 🛑 Schritt 9: Archive beenden

1. **Zurück zum Kommandozeilenfenster**
2. **Drücken:** `Strg + C`
3. **Bestätigung:** `Strg + C` erneut oder `Y` + Enter

**Erwartete Ausgabe:**
```
INFO:     Shutting down
INFO:     Finished server process
```

---

## ❓ Häufige Probleme und Lösungen

### Problem 1: "python ist kein Befehl"
**Lösung:**
- Python neu installieren mit "Add to PATH" aktiviert
- Oder vollständigen Pfad nutzen: `C:\Python39\python.exe`

### Problem 2: "Port 8000 bereits belegt"
**Lösung:**
```batch
netstat -ano | findstr :8000
taskkill /PID <PID-Nummer> /F
```

### Problem 3: "Module 'fastapi' not found"
**Lösung:**
- Virtuelle Umgebung aktivieren: `venv\Scripts\activate`
- Erneut installieren: `pip install -r requirements.txt`

### Problem 4: Keine PDFs sichtbar
**Überprüfen:**
- Existiert `archive\files\Werke\`? (ohne " - außer Psalmen")
- Existiert `data\archive.db`?

### Problem 5: MusicXML-Player zeigt keine Noten
**Überprüfen:**
- Existiert `data\manual\werk_9.musicxml`?
- Browser-Konsole öffnen (F12) und nach Fehlern suchen

---

## 📊 Was kann das Archive?

### Funktionen:
- ✅ **2.323 Werke** durchsuchbar
- ✅ **Volltext-Werksuche** nach Werknummer
- ✅ **Filter nach Besetzung** (232 verschiedene Instrumentationen)
- ✅ **PDF-Vorschau** direkt im Browser
- ✅ **MusicXML-Player** für interaktive Notenansicht mit Audio
- ✅ **Metadaten** zu jedem Werk (Titel, Jahr, Dateianzahl, etc.)

### Statistiken:
- 2.323 Werke katalogisiert
- 2.829 Dateien verknüpft
- 96,0% Vollständigkeit
- 4 MusicXML-Beispieldateien

---

## 💾 Backup-Empfehlung

Die wichtigste Datei ist: **`data/archive.db`**

**Backup erstellen:**
```batch
copy data\archive.db data\archive_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```

Dies erstellt eine Kopie mit Datum, z.B. `archive_backup_20260207.db`

---

## 🔄 Updates erhalten

Falls neue Versionen verfügbar sind:

1. **Neue Dateien erhalten** (nur geänderte Dateien)
2. **Virtuelle Umgebung aktivieren:**
   ```batch
   venv\Scripts\activate
   ```
3. **Neue Abhängigkeiten installieren:**
   ```batch
   pip install -r requirements.txt --upgrade
   ```
4. **Archive neu starten**

---

## 📞 Support

Bei Problemen bitte folgende Informationen bereitstellen:
- Windows-Version (z.B. Windows 10, Windows 11)
- Python-Version (`python --version`)
- Fehlermeldung (kompletter Text)
- Screenshot des Problems

---

**Viel Erfolg beim Einrichten! 🎵**
