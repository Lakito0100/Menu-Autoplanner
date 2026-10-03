@echo off
cd /d "%~dp0"

:: Python-Befehl ermitteln (py-Launcher oder python)
:: Hinweis: "if errorlevel" statt %ERRORLEVEL%, da %ERRORLEVEL% in Klammer-
::          bloecken schon beim Einlesen ersetzt wird.
set PYTHON=
where py >nul 2>&1
if not errorlevel 1 set PYTHON=py
if not defined PYTHON (
    where python >nul 2>&1
    if not errorlevel 1 set PYTHON=python
)
if not defined PYTHON (
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python installieren: https://www.python.org/downloads/
    pause
    exit /b 1
)

%PYTHON% menu_planer.py
if errorlevel 1 (
    echo.
    echo Der Menueplaner wurde mit einem Fehler beendet.
    echo Fehlen Pakete? Dann einmalig ausfuehren:  %PYTHON% -m pip install -r requirements.txt
    pause
)
