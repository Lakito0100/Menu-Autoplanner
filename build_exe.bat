@echo off
cd /d "%~dp0"
echo ============================================
echo   Menueplaner - EXE Build
echo ============================================
echo.

:: Python-Befehl ermitteln: MENUEPLANER_PYTHON (optional, z.B. in der CI),
:: sonst py-Launcher oder python
set "PYTHON=%MENUEPLANER_PYTHON%"
if not defined PYTHON (
    where py >nul 2>&1
    if not errorlevel 1 set PYTHON=py
)
if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set PYTHON=python
)
if not defined PYTHON (
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python installieren: https://www.python.org/downloads/
    if not defined CI pause
    exit /b 1
)

:: Abhaengigkeiten installieren
echo Installiere Abhaengigkeiten...
%PYTHON% -m pip install --upgrade pyinstaller -r requirements.txt
if errorlevel 1 goto fehler

:: EXE bauen
echo Baue Menueplaner.exe ...
%PYTHON% -m PyInstaller --noconfirm --onefile --windowed --name "Menueplaner" ^
    --collect-all pandas ^
    --collect-all openpyxl ^
    menu_planer.py
if errorlevel 1 goto fehler

:: Rezeptdatenbank neben die EXE legen (eine vorhandene wird nicht ueberschrieben)
if not exist "dist\Rezepte.xlsx" copy "Rezepte.xlsx" "dist\" >nul

echo.
echo ============================================
echo Fertig! Die EXE liegt unter: dist\Menueplaner.exe
echo Wichtig: Rezepte.xlsx muss im selben Ordner wie die EXE liegen (bereits kopiert).
echo ============================================
if not defined CI pause
exit /b 0

:fehler
echo.
echo FEHLER: Der Build ist fehlgeschlagen (siehe Meldungen oben).
if not defined CI pause
exit /b 1
