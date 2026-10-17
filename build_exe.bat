@echo off
title VidDrop - Build EXE
cd /d "%~dp0"
echo ===============================================
echo    VidDrop - building VidDrop.exe
echo    (run setup.bat first if you haven't)
echo ===============================================
echo.
echo [1/3] Installing PyInstaller...
python -m pip install -U pyinstaller
echo.
echo [2/3] Creating icon...
python make_icon.py
echo.
echo [3/3] Building (this takes 1-3 minutes)...
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name VidDrop --icon icon.ico ^
  --collect-all customtkinter ^
  --collect-all imageio_ffmpeg ^
  --collect-all yt_dlp_ejs ^
  --collect-submodules yt_dlp ^
  viddrop.py
echo.
if exist "dist\VidDrop.exe" (
    echo ===== Done! Your program is here: dist\VidDrop.exe =====
    explorer dist
) else (
    echo [!] Build failed - copy the messages above and send them to Claude.
)
pause
