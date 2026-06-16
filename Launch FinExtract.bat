@echo off
setlocal
title FinExtract Ultimate Launcher

echo ====================================================
echo             FINEXTRACT - AI PLATFORM
echo ====================================================
echo.

echo [1/3] Resetting engine...
taskkill /F /IM python.exe /T >nul 2>&1
:: Clear python cache
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" >nul 2>&1
echo Done.
echo.

echo [2/3] Starting AI Backend...
cd /d "F:\Gopi\Personal Documents\app\backend"

:: Check for virtual environment and launch
if exist venv\Scripts\python.exe (
    start "FinExtract Backend" "venv\Scripts\python.exe" app.py
) else (
    echo [ERROR] Virtual environment not found! Attempting global python...
    start "FinExtract Backend" python app.py
)

echo.
echo [3/3] Launching Dashboard...
echo Please wait for the browser to open...
timeout /t 6 /nobreak > nul

:: Open in Browser
set URL=http://127.0.0.1:5000
start %URL%

echo.
echo ====================================================
echo    SUCCESS: Dashboard launched!
echo ====================================================
echo.
echo IF THE SCREEN IS WHITE:
echo 1. Click on the browser window.
echo 2. Press CTRL + SHIFT + R (Hard Refresh).
echo.
timeout /t 15
exit