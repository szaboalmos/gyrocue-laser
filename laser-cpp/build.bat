@echo off
setlocal enabledelayedexpansion
title GYROCUE Laser C++ – Build

echo.
echo =========================================================
echo   GYROCUE Laser v6.0 C++  –  Windows Build
echo =========================================================
echo.

REM ── Qt path auto-detect ─────────────────────────────────────────────────────
set "QT_PATH="
for /d %%D in ("%ProgramFiles%\Qt\6.*" "C:\Qt\6.*" "%LOCALAPPDATA%\Qt\6.*") do (
    for /d %%E in ("%%D\msvc2022_64" "%%D\msvc2019_64") do (
        if exist "%%E\bin\qmake.exe" set "QT_PATH=%%E"
    )
)

if "!QT_PATH!"=="" (
    echo [ERROR] Qt6 not found. Install from https://www.qt.io/download
    goto :fail
)
echo [OK] Qt found: !QT_PATH!

REM ── CMake ────────────────────────────────────────────────────────────────────
where cmake >nul 2>&1
if errorlevel 1 (
    echo [ERROR] CMake not found. Install from https://cmake.org/download/
    goto :fail
)

REM ── Copy assets ──────────────────────────────────────────────────────────────
copy /y "..\logo_panel.png" "resources\logo_panel.png" >nul 2>&1
copy /y "..\Gyrocue_Logok_EPS-05.ico" "resources\GYROCUELaser.ico" >nul 2>&1

REM ── Build ────────────────────────────────────────────────────────────────────
if exist "build" rmdir /s /q "build"
mkdir build

cmake -B build -G "Ninja" ^
    -DCMAKE_PREFIX_PATH="!QT_PATH!" ^
    -DCMAKE_BUILD_TYPE=Release

if errorlevel 1 ( echo [ERROR] CMake configure failed. & goto :fail )

cmake --build build --config Release
if errorlevel 1 ( echo [ERROR] Build failed. & goto :fail )

REM ── Deploy Qt ────────────────────────────────────────────────────────────────
echo Deploying Qt dependencies...
"!QT_PATH!\bin\windeployqt.exe" build\GYROCUELaser.exe --no-translations --no-system-d3d-compiler
if errorlevel 1 ( echo [ERROR] windeployqt failed. & goto :fail )

REM ── Installer ────────────────────────────────────────────────────────────────
set "ISCC="
for %%P in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do ( if exist %%P set "ISCC=%%~P" )

if "!ISCC!"=="" (
    echo [WARN] Inno Setup not found – skipping installer.
    echo EXE ready at: build\GYROCUELaser.exe
    goto :done
)

if exist "Output" rmdir /s /q "Output"
"!ISCC!" installer\installer.iss
if errorlevel 1 ( echo [ERROR] Installer build failed. & goto :fail )

:done
echo.
echo =========================================================
echo   BUILD SUCCESSFUL
echo =========================================================
echo.
if exist "Output\GYROCUELaser_Setup_v6.0.exe" (
    echo   Installer: Output\GYROCUELaser_Setup_v6.0.exe
) else (
    echo   EXE: build\GYROCUELaser.exe
)
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
