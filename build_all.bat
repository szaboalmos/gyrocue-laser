@echo off
setlocal enabledelayedexpansion
title GYROCUE Laser – Build

echo.
echo =========================================================
echo   GYROCUE Laser v6.0  –  Full build  (EXE + Installer)
echo   Gyrocue Kft  ^|  gyrocue.com
echo =========================================================
echo.

REM ── 1. Python ──────────────────────────────────────────────────
echo [1/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not in PATH. Install Python 3 and retry.
    goto :fail
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo        %PYVER%

REM ── 2. PyInstaller ─────────────────────────────────────────────
echo [2/4] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo        Not found – installing...
    python -m pip install --quiet pyinstaller
    if errorlevel 1 ( echo [ERROR] pip install failed. & goto :fail )
)
for /f "tokens=*" %%V in ('python -m PyInstaller --version 2^>^&1') do set PIVER=%%V
echo        PyInstaller %PIVER%

REM ── 3. EXE build ───────────────────────────────────────────────
echo [3/4] Building EXE with PyInstaller...
echo.

if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
if exist "GYROCUELaser.spec" del /q "GYROCUELaser.spec"

python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --icon "Gyrocue_Logok_EPS-05.ico" ^
    --add-data "logo_panel.png;." ^
    --add-data "Gyrocue_Logok_EPS-05.ico;." ^
    --name "GYROCUELaser" ^
    --clean ^
    laser.py

if not exist "dist\GYROCUELaser.exe" (
    echo.
    echo [ERROR] EXE not found after build. See output above.
    goto :fail
)

for %%I in ("dist\GYROCUELaser.exe") do set EXEMB=%%~zI
set /a EXEMB_KB=%EXEMB% / 1024
echo.
echo        OK  –  dist\GYROCUELaser.exe  (%EXEMB_KB% KB^)

REM ── 4. Inno Setup ──────────────────────────────────────────────
echo [4/4] Building installer with Inno Setup...

set "ISCC="
for %%P in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"
    "%ProgramFiles%\Inno Setup 5\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%~P"
)

if "!ISCC!"=="" (
    echo.
    echo [WARN] Inno Setup not found.
    echo.
    echo  Download from: https://jrsoftware.org/isdl.php
    echo  Install, then run this script again.
    echo.
    echo  EXE is ready at:  dist\GYROCUELaser.exe
    echo  (distribute the EXE directly if you skip the installer^)
    echo.
    pause
    exit /b 0
)

echo        Using: !ISCC!
echo.

if exist "Output" rmdir /s /q "Output"
"!ISCC!" installer.iss
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup compilation failed.
    goto :fail
)

REM ── Summary ────────────────────────────────────────────────────
echo.
echo =========================================================
echo   BUILD SUCCESSFUL
echo =========================================================
echo.
echo   EXE       dist\GYROCUELaser.exe
for %%I in ("Output\*.exe") do (
    for %%J in ("%%I") do set INSZMB=%%~zJ
    set /a INSZMB_KB=!INSZMB! / 1024
    echo   Installer Output\%%~nxI  ^(!INSZMB_KB! KB^)
)
echo.
echo   Distribute the Installer EXE to end users.
echo =========================================================
echo.
pause
exit /b 0

:fail
echo.
echo =========================================================
echo   BUILD FAILED
echo =========================================================
echo.
pause
exit /b 1
