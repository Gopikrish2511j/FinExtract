@echo off
setlocal
title FinExtract Ultimate Launcher

echo ====================================================
echo             FINEXTRACT - AI PLATFORM
echo ====================================================
echo.

echo [1/3] Cleaning up previous sessions...
taskkill /F /IM python.exe /T >nul 2>&1
echo.

echo [2/3] Starting AI Engine...
cd /d "F:\Gopi\Personal Documents\app\backend"

:: Check for virtual environment and launch
if exist venv\Scripts\python.exe (
    start "FinExtract Backend" /min "venv\Scripts\python.exe" app.py
) else (
    echo [ERROR] Virtual environment not found! Attempting global python...
    start "FinExtract Backend" /min python app.py
)

echo.
echo [3/3] Preparing your Dashboard...
echo Waiting 5 seconds for initialization...
timeout /t 5 /nobreak > nul

:: Open in App Mode (Professional look)
set URL=http://localhost:5000
where msedge >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start msedge --app=%URL%
) else (
    start chrome --app=%URL%
)

echo.
echo ====================================================
echo    SUCCESS: FinExtract is now running on your laptop!
echo ====================================================
echo.
echo IF YOU SEE A WHITE SCREEN:
echo 1. Click on the browser window.
echo 2. Press CTRL + F5 on your keyboard.
echo.
timeout /t 10
exit