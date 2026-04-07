# WordPress Migration Plan: Emanuel Vogt Archive

Dieses Dokument fasst den Plan zusammen, um die lokal funktionierende Archiv-Anwendung nahtlos in eine öffentliche WordPress-Instanz zu integrieren.

## 1. Theme & Child-Theme Implementierung (Astra)

Wir verwenden das "Astra" Theme als schlanke Basis. Um Änderungen zukunftssicher vorzunehmen, erstellen wir ein **Astra Child-Theme**.

### Instruktionen zum Child-Theme:
1. **Ordner erstellen:** Im WordPress-Verzeichnis `wp-content/themes/` den Ordner `astra-child` anlegen.
2. **`style.css` erstellen:** Eine Datei `style.css` im Child-Theme anlegen mit diesem Header:
   ```css
   /*
   Theme Name: Astra Child für Emanuel Vogt Archive
   Template: astra
   */
   ```
   *Hier fügen wir alle unsere bestehenden Styles (`app/static/style.css`) ein.*
3. **`functions.php` erstellen:** Im Child-Theme wird die Datei `functions.php` angelegt, die WordPress anweist, unsere eigenen Skripte sowie die Styles des Parent-Themes zu laden:
   ```php
   <?php
   add_action( 'wp_enqueue_scripts', 'evogt_enqueue_styles' );
   function evogt_enqueue_styles() {
       wp_enqueue_style( 'parent-style', get_template_directory_uri() . '/style.css' );
       wp_enqueue_script( 'evogt-app-js', get_stylesheet_directory_uri() . '/assets/js/app.js', array(), '1.0', true );
   }
   ```
4. **JavaScript:** Die Datei `app/static/app.js` kopieren wir nach `wp-content/themes/astra-child/assets/js/app.js`.

---

## 2. Startseite & Integration des Archivs

Da das Archiv direkt **die Startseite** sein soll:
1. Erstellen wir im Child-Theme eine Datei `front-page.php`. WordPress nutzt diese Datei automatisch als Vorlage für die Startseite.
2. In `front-page.php` binden wir das statische HTML unserer bestehenden App (aus `app/index.html`) ein.
3. Im WordPress-Admin unter *Einstellungen -> Lesen* muss "Eine statische Seite" als Startseite gewählt werden.

---

## 3. Backend-Strategie & PDF Rotation

Da sich herausgestellt hat, dass **nicht alle PDF-Rotationen vorab feststehen** und dynamisch nach und nach entdeckt werden:

### Die Datenbank (`archive.db`)
- Wird in einen sicheren Ordner abgelegt (z.B. `/wp-content/uploads/archive/data/archive.db`). 
- Wir portieren die leichten Such- und Filterfunktionen (die FastAPI aktuell macht) in kleine PHP-Funktionen in der `functions.php`, z.B.:
  - `GET /wp-json/evogt/v1/works`
  - `GET /wp-json/evogt/v1/work/{id}`

### PDF-Darstellung & Dynamische Rotation
Die PDFs liegen bereit auf `/home/www/public/wp-content/uploads/archive/flat/`.
Da wir Python (`PyPDF2`) auf dem Standard-Hosting in PHP nicht On-the-fly nutzen können, empfehlen sich zwei Lösungswege:

**Lösung (CSS-Rotation nativ):** 
1. Wenn ein Admin ein PDF dreht, speichert die PHP-API die Drehung in der Datenbank.
2. Wenn das PDF geladen wird, gibt die API den Rotationswert an das JavaScript (`app.js`) weiter.
3. Wir verändern den PDF-Viewer, sodass er das PDF im Iframe oder über eine kleine JavaScript-Bibliothek wie `pdf.js` nativ rotiert anzeigt. Dies erfordert keine Server-Rechenleistung und ist in PHP leicht umzusetzen.

---

## 4. Content-Seiten (Impressum, Datenschutz, Über)

Im WordPress-Adminbereich werden drei reguläre Seiten erstellt:

### 1. Impressum
- **Anbieter:** Johannes Vogt-Krause
- **Adresse:** Am Teeberg 16, 29581 Gerdau, Deutschland
- *(Ggf. müssen Email oder Telefonnummer noch ergänzt werden).*

### 2. Datenschutzerklärung
- Standard-Datenschutzerklärung für einfache Websites. Fokus:
  - Erklärung zum berechtigten Interesse (Logfiles des Hosters).
  - Einbindung von Cookies / LocalStorage (sofern wir das für PDF-Ansichten nutzen sollten).

### 3. Über Emanuel Vogt
- Basis: [Wikipedia-Artikel](https://de.wikipedia.org/wiki/Emanuel_Vogt_(Komponist))
- **Inhaltliche Zusammenfassung:** 
  - *Emanuel Vogt (\* 1925 in Augsburg; † 2007) war ein deutscher Kirchenmusiker, Komponist und Kantor.*
  - Beschreibung seines Werdegangs (Rothenburg ob der Tauber, St. Matthäus München, Windsbacher Knabenchor).
  - Listung von ausgewählten Werken ("Kommet, ihr Hirten", Orgelbuch).

---

## Nächste Schritte zur Implementierung
1. [x] **DB Pfade anpassen:** Ein lokales Skript laufen lassen, das die Dateipfade in der `archive.db` so umschreibt, dass sie direkt auf den Server-Ordner `wp-content/uploads/archive/flat/` matchen.
2. [x] **PHP API schreiben:** Die 4 Endpunkte aus `backend.py` in PHP übersetzen und zur `functions.php` hinzufügen.
3. [x] **Child-Theme packen:** Das gesamte Child-Theme-Verzeichnis (inkl. CSS/JS und `front-page.php`) als `.zip` zusammenstellen, damit Sie es im WordPress hochladen können.
4. [x] **Theme hochladen & Design verifizieren:** Thema über WP Admin installieren und letzte Anpassungen (z.b. Z-Index von Modals und Schriften) überprüfen.
5. [x] **Zusätzliche Seiten anlegen:** Impressum, Datenschutzerklärung und Über-Seite (Inhalte liegen in `docs/WP_PAGES_CONTENT.md` bereit).

---

## Finale Bugfixes & Anpassungen (Archiv Migration abgeschlossen)

Folgende spezifische Probleme wurden während der Live-Installation gelöst:

1. **Astra Header & Titel-Sichtbarkeit:** Der Titel "Emanuel Vogt - Digitales Werkverzeichnis" wurde nativer in den WordPress Action-Hook (`astra_site_identity`) injiziert, um zu garantieren, dass er nicht zerschossen wird und sowohl auf der Startseite als auch auf Unterseiten exakt integriert ist.
2. **MusicXML Player (REST-API & 500 Fehler):** Der anfängliche 500-Fehler im Notenplayer wurde korrigiert (verursacht durch eine fehlende PHP Variable). Die PHP-Logik durchsucht nun stabil das Verzeichnis `wp-content/uploads/archive/musicxml/` via Regex und `scandir` nach Notenblättern.
3. **Javascript-Kollision ("addEventListener" Bug):** Das Skript `app.js` wird streng nur noch auf der Hauptseite eingebunden, sodass der Fehler auf Unterseiten mit dem nicht existierenden Suchfeld vermieden wird.
4. **Dropdown-Boxen auf Mac Safari/Chrome (White-on-White Bug):** MacOS Chrome überschrieb Optionen in Auswahllisten standardmäßig fehlerhaft, wenn man den Hintergrund anpasste. Gelöst durch Rückgriff auf die native macOS Benutzeroberfläche gepaart mit dem Befehl `color-scheme: dark !important;`. Das erzwingt verlässliche native dunkle Optionen.
5. **Footer:** Der gesamte Standard-"Powered by Astra"-Footer ist systematisch per CSS entfernt (`display: none;`), um das Archiv-Design abzurunden.
6. **Typografie & Farben:** Spezifische Farben (Goldgelb) bei Unterseiten-Überschriften (`.entry-title`) und Menü-Hover-Effekten wurden sichergestellt.
