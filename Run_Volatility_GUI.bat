@echo off
title VolForensics Studio - Memory Forensics UI
color 0B
echo =====================================================================
echo           VolForensics Studio - Volatility 2 & 3 Modern UI
echo =====================================================================
echo.
cd /d "%~dp0"

echo [*] Starting VolForensics Studio...
python run_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] An error occurred. Retrying with py launcher...
    py -3 run_gui.py
)
pause
