# Emanuel Vogt Archiv - Dokumentation

Dieses Verzeichnis enthält alle technischen Reports und Dokumentation zum Projekt.

## Projektstruktur

### Hauptdokumentation
- **README.md** - Projekt-Übersicht und Anleitungen
- **DATABASE_SCHEMA.md** - Datenbankstruktur und Schema
- **SHARING_INSTRUCTIONS.md** - Anleitung zum Teilen des Archivs

### Entwicklungs-Phasen

#### Initiale Setup-Phasen
- **ARCHIVE_ASSESSMENT_PLAN.md** - Ursprünglicher Plan für Archiv-Assessment
- **STRATEGY_PIVOT.md** - Strategiewechsel während der Entwicklung
- **PROGRESS_REPORT.md** - Fortschritts-Übersicht

#### Phase 2: Katalog-Konsolidierung
- **PHASE2_COMPLETE.md** - Zusammenführung verschiedener Excel-Kataloge

#### Phase 3: Quality Assessment
- **PHASE3_INSTRUCTIONS.md** - Anleitung für Quality Assessment
- **PHASE3_REPORT.md** - Ergebnisse des Quality Assessments

#### Phase 4: PDF-Analyse
- **PHASE4_REPORT.md** - PDF-Struktur und Qualitätsanalyse

#### Phase 5: Datenbank-Setup
- **PHASE5_SUMMARY.md** - SQLite-Datenbank Initialisierung

#### Phase 7: Web-Viewer
- **PHASE7_REPORT.md** - Erste Version des Web-Viewers

#### Phase 8: MusicXML Player
- **PHASE8_MUSICXML_PLAYER.md** - Interaktiver MusicXML-Player mit Tone.js

#### Phase 9: Windows Kompatibilität
- **PHASE9_COMPLETION_REPORT.md** - Fixes für Windows-Pfade und Batch-Scripts
- **WINDOWS_COMPATIBILITY_FIX.md** - Technische Details der Windows-Anpassungen

#### Phase 10: Erweiterte Features

##### Phase 10a: MusicXML Instruments (Deferred)
- **PHASE10A_MUSICXML_INSTRUMENTS_NOTES.md** - Instrument-spezifische Synthesizer-Settings
- **PHASE10_MUSICXML_INSTRUMENTS_REPORT.md** - Analyse und Erkenntnisse
- **Status**: Vertagt - Tone.js Envelope-Effekte zu subtil bei kurzen Noten

##### Phase 10b: PDF Rotation System
- **PHASE10_PDF_ROTATION.md** - Persistentes PDF-Rotationssystem
- **Status**: ✅ Abgeschlossen - Backend PyPDF2 + Frontend CSS Hybrid

## Technologie-Stack

- **Backend**: Python, FastAPI, SQLite, PyPDF2
- **Frontend**: HTML, CSS, JavaScript, Tone.js
- **PDF Processing**: PyPDF2, pdf.js
- **Audio**: Tone.js, MusicXML.js

## Aktuelle Features

### Viewer
- ✅ Werk-Suche (Titel, Nummer)
- ✅ Filter nach Gattung
- ✅ Filter nach Besetzung
- ✅ PDF-Anzeige im Browser
- ✅ PDF-Rotation (persistent, zentral)

### MusicXML Player
- ✅ Interaktive Notendarstellung
- ✅ Audio-Playback mit Tone.js
- ✅ Play/Pause/Stop Controls
- ✅ Note-Highlighting während Playback
- ✅ Transponierung
- ✅ Tempo-Anpassung

### Plattform-Support
- ✅ macOS (native)
- ✅ Windows (run_viewer.bat)
- ✅ Linux (should work)

## Scripts

Siehe `../scripts/` für:
- Katalog-Konsolidierung
- Quality Assessment
- Datenbank-Initialisierung
- PDF-Analyse (Rotation, Landscape-Detection)
- Windows-Kompatibilität Fixes

## Daten

Siehe `../data/` für:
- CSV-Kataloge (GEMA, Psalmen, Werke, Hauptseite)
- `archive.db` - SQLite-Datenbank
- Quality Assessment Reports
- PDF-Analysen (Landscape, Rotation)

## Nächste Schritte

- [ ] Windows-Testing Phase 10b
- [ ] Batch-Rotation für bekannte Landscape-PDFs
- [ ] Performance-Optimierung (Caching)
- [ ] User-Dokumentation
- [ ] Phase 10a revisited (Soundfonts statt Tone.js Envelopes)
