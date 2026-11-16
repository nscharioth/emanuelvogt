# Phase 12: WordPress-Plugin „EmanuelVogt Werkverzeichnis“

**Ziel:** Ein Admin-Bereich in WordPress, in dem der Betreiber die 2.300+ Werke
direkt bearbeiten kann – ohne Umweg über Python-Skripte oder den
Mediathek-Trick mit der Kurzbeschreibung.

## Was das Plugin macht

| Bereich | Inhalt |
|---|---|
| **Werkverzeichnis → Alle Werke** | Liste aller Werke aus `archive.db` mit Suche (Werknummer, Titel, Gattung, Besetzung, Kommentar), Ansichten (Mit Neusatz / Mit Aufnahme / Mit Kommentar / Ohne Dateien), Sortierung nach Nr. (natürlich: 1, 2, 9c, 14, 14a … P-1, P-2) oder Titel, 50 Werke pro Seite. |
| **Werk bearbeiten** | ID und Werknummer (fest), Titel, Originalscans (Ansicht mit Links, je Scan „ausblenden“ für die Website), bis zu zwei **Neusatz-PDFs** (mit Hinweis „Notensatz mit Capella 10 erstellt.“ unter der Anzeige) und bis zu zwei **Aufnahmen (MP3)** per Mediathek-Auswahl, **Kommentar** (Freitext, erscheint im Werk-Dialog). |
| **Werkverzeichnis → Werkzeuge** | Status der Datenbank, Download der aktuellen `archive.db`, Schema-Migration, erneute Übernahme von Mediathek-Zuordnungen, Liste der Sicherungskopien. |
| **REST-API `evogt/v1`** | Alle Endpunkte (`works`, `work/{id}`, `genres`, `instrumentations`, `pdf-rotation`, `recordings`) wurden aus dem Child-Theme ins Plugin verschoben. Das Theme enthält nur noch Darstellung. |

## Wo die Daten liegen

- Alle Werkdaten bleiben in der SQLite-Datei
  `wp-content/uploads/archive/data/archive.db` (wie bisher die PDF-Rotationen).
- Neue Spalten in `works`: `comment`, `transcription_attachment_id`,
  `transcription2_attachment_id`, `audio_attachment_id`, `audio2_attachment_id`,
  `updated_at`. Ausgeblendete Originale: `files.is_public = 0`. Die beiden `*_attachment_id` zeigen auf
  Einträge der WordPress-Mediathek der Live-Seite (Anhang-IDs sind also
  seitenspezifisch).
- Das Plugin legt die Spalten beim Aktivieren automatisch an und erstellt
  vorher eine Kopie `archive.db.bak-<Datum>-schema` im selben Ordner. Wird
  später eine neue `archive.db` hochgeladen, wird sie beim nächsten
  Admin-Aufruf automatisch nachmigriert. Nach einem Plugin-Update per Upload geschieht
  das beim ersten Seitenaufruf, weil dabei keine Aktivierung läuft.
- Der Ordner `uploads/archive/data/` erhält eine `.htaccess`, die den
  Direktzugriff auf `.db`-Dateien und Sicherungen sperrt (Apache; bei nginx
  bitte eine entsprechende `location`-Regel ergänzen).

## Installation / Update auf dem Server

Die Reihenfolge ist wichtig, weil das **alte** Theme dieselben PHP-Funktionen
definiert wie das Plugin:

1. Vorher: die auf dem Server liegende `functions.php` des Child-Themes
   herunterladen und mit dem Repository vergleichen. Falls dort zusätzlicher
   Code liegt (z. B. eine Route `evogt/v1/musicxml/list`), diesen in
   `wp-plugin/evogt-works-admin/includes/rest.php` übernehmen.
2. Plugin-ZIP unter *Plugins → Installieren → Plugin hochladen* hochladen,
   **noch nicht aktivieren**.
3. Theme-ZIP unter *Design → Themes → Hochladen* hochladen und
   „Aktuelles durch hochgeladenes ersetzen“ wählen. (Die Suche auf der
   Startseite ist jetzt bis Schritt 4 kurz ohne Funktion.)
4. Plugin aktivieren. Dabei laufen Sicherung, Schema-Migration und die
   einmalige Übernahme der per Kurzbeschreibung verknüpften PDFs/MP3s.
   Ergebnis unter *Werkverzeichnis → Werkzeuge* prüfen.
5. Startseite neu laden (Assets Version 1.7.2), ein Werk mit Neusatz/Aufnahme
   öffnen, im Admin ein Werk bearbeiten.

ZIPs bauen:

```bash
cd wp-plugin && zip -r ../evogt-works-admin-1.1.0.zip evogt-works-admin -x '*.DS_Store'
cd wp-theme  && zip -r ../astra-child-1.7.2.zip astra-child -x '*.DS_Store'
```

## Datenbank zurück ins Repository holen

Die Server-Kopie ist die maßgebliche Datenbank (Rotationen, Kommentare,
Verknüpfungen). Um `data/archive.db` im Repository aktuell zu halten:

1. *Werkverzeichnis → Werkzeuge → „Datenbank sichern“* – lädt einen
   konsistenten Schnappschuss herunter.
2. Datei als `data/archive.db` ablegen und committen.

Für eine lokale Kopie ohne Server (z. B. nach einem neuen Import) sorgt
`python3 scripts/27_add_work_media_columns.py` für dieselben Spalten.

## Alte Mediathek-Zuordnung

Die frühere Zuordnung „Kurzbeschreibung = Dateiname des Originals“ ist
abgeschaltet. Bereits so verknüpfte Dateien wurden bei der Aktivierung in die
neuen Felder übernommen. „Medien erneut übernehmen“ unter *Werkzeuge* füllt nur
leere Felder und überschreibt nie manuell gesetzte Dateien.

## Dateien

```
wp-plugin/evogt-works-admin/
├── evogt-works-admin.php          Plugin-Header, Konstanten, Aktivierung
├── uninstall.php
├── includes/db.php                SQLite-Verbindung, Status, Sicherungen
├── includes/schema.php            Schema-Migration
├── includes/media-migration.php   Übernahme der Mediathek-Zuordnungen
├── includes/works-repo.php        Datenzugriff (Liste, Werk, Dateien, Speichern)
├── includes/rest.php              REST-API evogt/v1
├── includes/class-evogt-works-list-table.php
├── includes/admin.php             Menü, Hinweise, Liste
├── includes/admin-edit.php        Bearbeiten-Formular + Speichern
├── includes/admin-tools.php       Werkzeuge
└── assets/admin.js, admin.css
```
