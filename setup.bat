@echo off
title VidDrop - Setup
echo ===============================================
echo    VidDrop - installing requirements (one time)
echo ===============================================
echo.
where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python is not installed. Get it from python.org
    echo     and tick "Add python.exe to PATH" during install.
    pause
    exit /b 1
)
echo [1/2] Installing Python libraries...
python -m pip install --upgrade pip
python -m pip install -U -r "%~dp0requirements.txt"
echo.
echo [2/2] Installing Deno (needed by yt-dlp for YouTube)...
where deno >nul 2>nul
if errorlevel 1 (
    winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements
) else (
    echo Deno already installed.
)
echo.
echo ===== Done! Start the app with run.bat =====
pause
