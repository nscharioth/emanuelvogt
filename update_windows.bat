@echo off
REM Git Repository aktualisieren und Datenbank holen

echo ================================================================================
echo ARCHIVE VIEWER - GIT UPDATE
echo ================================================================================
echo.

REM Zum Projekt-Verzeichnis wechseln
cd /d C:\Users\vogt-\Documents\Git\emanuelvogt

echo Aktueller Status:
git status
echo.

echo ================================================================================
echo Hole neueste Version vom Server...
echo ================================================================================

REM Lokale Änderungen sichern (falls vorhanden)
git stash
echo.

REM Neueste Version holen
git pull origin main
echo.

echo ================================================================================
echo UPDATE ABGESCHLOSSEN
echo ================================================================================
echo.

REM Prüfen ob Datenbank vorhanden
if exist "data\archive.db" (
    echo [OK] Datenbank gefunden: data\archive.db
    for %%A in ("data\archive.db") do echo      Groesse: %%~zA Bytes
) else (
    echo [FEHLER] Datenbank NICHT gefunden!
    echo.
    echo Bitte siehe: WINDOWS_DATENBANK_FEHLT.txt
)

echo.
pause
