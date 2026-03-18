@echo off
echo ============================================
echo   Menueплaner - EXE Build
echo ============================================
echo.

:: PyInstaller installieren falls noetig
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller wird installiert...
    pip install pyinstaller
)

:: EXE bauen
echo Baue menu_planer.exe ...
pyinstaller --onefile --windowed --name "Menueplaner" menu_planer.py

echo.
echo ============================================
echo Fertig! Die EXE liegt unter: dist\Menueплaner.exe
echo Wichtig: Rezepte.xlsx muss im selben Ordner wie die EXE liegen!
echo ============================================
pause
