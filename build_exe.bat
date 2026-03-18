@echo off
echo ============================================
echo   Menueplaner - EXE Build
echo ============================================
echo.

:: Python-Befehl ermitteln (py-Launcher oder python)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py
) else (
    set PYTHON=python
)

:: Abhaengigkeiten installieren
echo Installiere Abhaengigkeiten...
%PYTHON% -m pip install pyinstaller pandas openpyxl

:: EXE bauen
echo Baue Menueplaner.exe ...
%PYTHON% -m PyInstaller --onefile --windowed --name "Menueplaner" ^
    --collect-all pandas ^
    --collect-all openpyxl ^
    menu_planer.py

echo.
echo ============================================
echo Fertig! Die EXE liegt unter: dist\Menueplaner.exe
echo Wichtig: Rezepte.xlsx muss im selben Ordner wie die EXE liegen!
echo ============================================
pause
