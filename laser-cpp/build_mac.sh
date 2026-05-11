#!/bin/bash
set -e

APP_NAME="GYROCUELaser"
APP_VERSION="6.0"

echo ""
echo "====================================================="
echo "  GYROCUE Laser v6.0 C++ – macOS Build"
echo "====================================================="
echo ""

# ── Qt path ──────────────────────────────────────────────────────────────────
QT_PATH=""
for candidate in \
    "$(brew --prefix qt 2>/dev/null)" \
    "/opt/homebrew/opt/qt" \
    "/usr/local/opt/qt" \
    "$HOME/Qt/6.*/macos"
do
    if [ -f "$candidate/bin/qmake" ]; then
        QT_PATH="$candidate"
        break
    fi
done

if [ -z "$QT_PATH" ]; then
    echo "[ERROR] Qt6 not found."
    echo "        brew install qt"
    exit 1
fi
echo "[OK] Qt: $QT_PATH"

# ── Copy assets ──────────────────────────────────────────────────────────────
cp -f ../logo_panel.png resources/logo_panel.png 2>/dev/null || true

# ── Build ─────────────────────────────────────────────────────────────────────
rm -rf build
mkdir build

cmake -B build \
    -DCMAKE_PREFIX_PATH="$QT_PATH" \
    -DCMAKE_BUILD_TYPE=Release

cmake --build build

# ── Deploy ────────────────────────────────────────────────────────────────────
"$QT_PATH/bin/macdeployqt" "build/$APP_NAME.app" -dmg

DMG="build/${APP_NAME}_v${APP_VERSION}.dmg"
mv "build/${APP_NAME}.dmg" "$DMG" 2>/dev/null || true

echo ""
echo "====================================================="
echo "  DONE: $DMG"
echo "====================================================="
