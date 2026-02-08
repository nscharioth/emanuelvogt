@echo off
REM Datenbank-Diagnose und Reparatur für Windows

echo ================================================================================
echo DATENBANK DIAGNOSE UND REPARATUR
echo ================================================================================
echo.

cd /d C:\Users\vogt-\Documents\Git\emanuelvogt

echo [1] Suche nach Datenbank-Dateien im data\ Ordner:
echo ================================================================================
dir /b data\archive*
echo.

echo [2] Detaillierte Ansicht mit Dateiendungen:
echo ================================================================================
dir data\archive* /a
echo.

echo [3] Pruefe ob korrekte Datenbank existiert:
echo ================================================================================
if exist "data\archive.db" (
    echo [OK] Datei "data\archive.db" gefunden!
    for %%A in ("data\archive.db") do (
        echo      Groesse: %%~zA Bytes
        if %%~zA GTR 100000 (
            echo      Status: Groesse OK ^(sollte ca. 800 KB sein^)
        ) else (
            echo      [WARNUNG] Datei zu klein! Sollte ca. 800 KB sein.
        )
    )
) else (
    echo [FEHLER] Datei "data\archive.db" NICHT gefunden!
    echo.
    echo Suche nach falscher Benennung...
    
    if exist "data\archive" (
        echo.
        echo [GEFUNDEN] Datei "data\archive" ^(ohne .db Endung^)
        echo.
        echo REPARATUR: Fuege .db Endung hinzu...
        ren "data\archive" "archive.db"
        
        if exist "data\archive.db" (
            echo [OK] Erfolgreich umbenannt zu "archive.db"!
            for %%A in ("data\archive.db") do echo      Groesse: %%~zA Bytes
        ) else (
            echo [FEHLER] Umbenennung fehlgeschlagen!
        )
    ) else (
        echo [FEHLER] Keine Datenbank-Datei gefunden!
        echo.
        echo Bitte siehe: WINDOWS_DATENBANK_FEHLT.txt
    )
)

echo.
echo [4] SQLite-Datenbank testen:
echo ================================================================================
if exist "data\archive.db" (
    python -c "import sqlite3; conn = sqlite3.connect('data/archive.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM works'); print(f'Werke in Datenbank: {c.fetchone()[0]}'); conn.close()" 2>nul
    if errorlevel 1 (
        echo [FEHLER] Datenbank beschaedigt oder leer!
    )
) else (
    echo [UEBERSPRUNGEN] Keine Datenbank zum Testen vorhanden.
)

echo.
echo ================================================================================
echo DIAGNOSE ABGESCHLOSSEN
echo ================================================================================
echo.
echo NAECHSTE SCHRITTE:
if exist "data\archive.db" (
    echo 1. Datenbank ist OK - starte Viewer: run_viewer.bat
    echo 2. Oeffne Browser: http://localhost:8000
) else (
    echo 1. Siehe Anleitung: WINDOWS_DATENBANK_FEHLT.txt
    echo 2. Oder fuehre aus: update_windows.bat
)

echo.
pause
