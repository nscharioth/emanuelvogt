#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Diagnose und Reparatur für Windows
Prüft ob archive.db korrekt benannt ist und funktioniert
"""

import os
import sys
from pathlib import Path
import sqlite3

def main():
    print("=" * 80)
    print("DATENBANK DIAGNOSE UND REPARATUR")
    print("=" * 80)
    print()
    
    # Bestimme Projekt-Verzeichnis
    if os.path.exists('data'):
        base_dir = Path.cwd()
    elif os.path.exists('../data'):
        base_dir = Path.cwd().parent
    else:
        print("FEHLER: Nicht im Projekt-Verzeichnis!")
        print("Bitte ausführen aus: C:\\Users\\vogt-\\Documents\\Git\\emanuelvogt")
        sys.exit(1)
    
    data_dir = base_dir / "data"
    print(f"Projekt-Verzeichnis: {base_dir}")
    print(f"Daten-Verzeichnis: {data_dir}")
    print()
    
    # Schritt 1: Suche alle Dateien mit "archive" im Namen
    print("[1] Suche nach Datenbank-Dateien...")
    print("-" * 80)
    
    archive_files = list(data_dir.glob("archive*"))
    if archive_files:
        print(f"Gefundene Dateien: {len(archive_files)}")
        for f in archive_files:
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"  - {f.name}")
            print(f"    Größe: {size_mb:.2f} MB ({f.stat().st_size:,} Bytes)")
            print(f"    Vollständiger Pfad: {f}")
    else:
        print("KEINE Dateien gefunden!")
    print()
    
    # Schritt 2: Prüfe korrekte Datei
    print("[2] Prüfe korrekte Benennung...")
    print("-" * 80)
    
    correct_db = data_dir / "archive.db"
    wrong_db = data_dir / "archive"
    
    needs_fix = False
    
    if correct_db.exists():
        size_mb = correct_db.stat().st_size / 1024 / 1024
        print(f"✅ Korrekt: '{correct_db.name}' existiert")
        print(f"   Größe: {size_mb:.2f} MB")
        
        if size_mb < 0.1:
            print(f"   ⚠️  WARNUNG: Datei zu klein! Sollte ca. 0.85 MB sein.")
            needs_fix = True
    else:
        print(f"❌ Fehlt: '{correct_db.name}' nicht gefunden")
        needs_fix = True
    
    if wrong_db.exists() and not correct_db.exists():
        size_mb = wrong_db.stat().st_size / 1024 / 1024
        print(f"❌ Falsch benannt: '{wrong_db.name}' gefunden (ohne .db)")
        print(f"   Größe: {size_mb:.2f} MB")
        print()
        print("   → Diese Datei muss umbenannt werden!")
        needs_fix = True
    print()
    
    # Schritt 3: Reparatur wenn nötig
    if needs_fix and wrong_db.exists() and not correct_db.exists():
        print("[3] REPARATUR DURCHFÜHREN")
        print("-" * 80)
        
        response = input(f"Umbenennen: '{wrong_db.name}' → '{correct_db.name}' ? (ja/nein): ").strip().lower()
        
        if response in ['ja', 'j', 'yes', 'y']:
            try:
                wrong_db.rename(correct_db)
                print(f"✅ Erfolgreich umbenannt zu '{correct_db.name}'!")
            except Exception as e:
                print(f"❌ Fehler beim Umbenennen: {e}")
                sys.exit(1)
        else:
            print("Abgebrochen.")
            sys.exit(1)
        print()
    
    # Schritt 4: Datenbank-Integrität testen
    print("[4] Teste Datenbank-Integrität...")
    print("-" * 80)
    
    if correct_db.exists():
        try:
            conn = sqlite3.connect(correct_db)
            c = conn.cursor()
            
            # Prüfe Tabellen
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            print(f"Gefundene Tabellen: {', '.join(tables)}")
            
            if 'works' in tables:
                c.execute("SELECT COUNT(*) FROM works")
                work_count = c.fetchone()[0]
                print(f"✅ Anzahl Werke: {work_count:,}")
            else:
                print("❌ FEHLER: Tabelle 'works' nicht gefunden!")
                conn.close()
                sys.exit(1)
            
            if 'files' in tables:
                c.execute("SELECT COUNT(*) FROM files")
                file_count = c.fetchone()[0]
                print(f"✅ Anzahl Dateien: {file_count:,}")
            else:
                print("❌ FEHLER: Tabelle 'files' nicht gefunden!")
                conn.close()
                sys.exit(1)
            
            conn.close()
            print()
            print("✅ DATENBANK IST OK!")
            
        except sqlite3.Error as e:
            print(f"❌ FEHLER beim Zugriff auf Datenbank: {e}")
            print()
            print("Mögliche Ursachen:")
            print("- Datei ist beschädigt")
            print("- Datei ist keine SQLite-Datenbank")
            print("- Datei ist leer")
            print()
            print("Lösung: Siehe WINDOWS_DATENBANK_FEHLT.txt")
            sys.exit(1)
    else:
        print("⚠️  Keine Datenbank zum Testen vorhanden.")
        print("Siehe: WINDOWS_DATENBANK_FEHLT.txt")
        sys.exit(1)
    
    # Zusammenfassung
    print()
    print("=" * 80)
    print("DIAGNOSE ABGESCHLOSSEN")
    print("=" * 80)
    print()
    print("✅ Datenbank ist korrekt konfiguriert!")
    print()
    print("Nächste Schritte:")
    print("1. Starte Viewer: run_viewer.bat")
    print("2. Öffne Browser: http://localhost:8000")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAbgebrochen.")
        sys.exit(0)
