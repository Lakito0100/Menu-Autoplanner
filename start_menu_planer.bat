@echo off
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON=python
    ) else (
        echo FEHLER: Python wurde nicht gefunden.
        echo Bitte Python installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)
%PYTHON% menu_planer.py
