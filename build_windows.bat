@echo off
REM ============================================================
REM  NEXUS — one-click Windows build
REM  Produces: dist\NEXUS\NEXUS.exe  (the app)
REM            installer_out\NEXUS-Setup-0.4.0.exe (the installer)
REM  Requirements: Python 3.10+ from python.org on PATH.
REM  Optional: Inno Setup 6 (jrsoftware.org) for the installer.
REM ============================================================
setlocal
cd /d "%~dp0"

echo [1/4] Creating build environment...
py -3 -m venv .venv || goto :fail
call .venv\Scripts\activate.bat

echo [2/4] Installing build dependencies...
pip install --quiet --upgrade pip
pip install --quiet PySide6 pyinstaller || goto :fail

echo [3/4] Building NEXUS.exe ...
pyinstaller --noconfirm --clean --windowed --name NEXUS ^
  --icon assets\nexus.ico ^
  --add-data "content;content" ^
  --add-data "assets;assets" ^
  qt_main.py || goto :fail

echo.
echo Built: dist\NEXUS\NEXUS.exe  (double-click to run)
echo.

echo [4/4] Building the installer (needs Inno Setup 6)...
where iscc >nul 2>nul
if %errorlevel%==0 (
  iscc installer.iss || goto :fail
  echo.
  echo Installer ready: installer_out\NEXUS-Setup-0.4.0.exe
) else (
  echo Inno Setup not found. To make the installer:
  echo   1. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
  echo   2. Re-run this script, or run:  iscc installer.iss
  echo Meanwhile, dist\NEXUS\ is fully portable - zip and share it.
)
echo.
echo Done.
pause
exit /b 0

:fail
echo BUILD FAILED - see messages above.
pause
exit /b 1
