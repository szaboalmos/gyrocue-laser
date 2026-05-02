#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  GYROCUE Laser - macOS build (.app + .dmg)
#  Apple Silicon + macOS 13+
#
#  Run: ./build_mac.sh
# ─────────────────────────────────────────────────────────────────

set -e  # stop on errors

APP_NAME="GYROCUELaser"
APP_VERSION="6.0"
BUNDLE_ID="com.gyrocue.laser"

echo ""
echo "====================================================="
echo "  GYROCUE Laser - macOS Build"
echo "====================================================="
echo ""

# ── 1. Check Python ───────────────────────────────────────────
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed!"
    echo "        brew install python  or  https://www.python.org/downloads/"
    exit 1
fi
PY_VER=$(python3 --version)
echo "   $PY_VER OK"

# ── 2. Dependencies ───────────────────────────────────────────
echo "[2/5] Checking dependencies..."

python3 -c "import objc" 2>/dev/null || {
    echo "   Installing PyObjC..."
    pip3 install --user pyobjc
}

python3 -c "import PySide6" 2>/dev/null || {
    echo "   Installing PySide6..."
    pip3 install --user PySide6
}

python3 -c "import PyInstaller" 2>/dev/null || {
    echo "   Installing PyInstaller..."
    pip3 install --user pyinstaller
}

echo "   OK"

# ── 3. .app build ─────────────────────────────────────────────
echo "[3/5] Building .app bundle..."

rm -rf build dist *.spec

python3 -m PyInstaller \
    --name "$APP_NAME" \
    --windowed \
    --onedir \
    --osx-bundle-identifier "$BUNDLE_ID" \
    --noconfirm \
    --clean \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtCore" \
    --add-data "logo_panel.png:." \
    --add-data "Gyrocue_Logok_EPS-05.icns:." \
    laser_mac.py

if [ ! -d "dist/$APP_NAME.app" ]; then
    echo "[ERROR] .app build failed!"
    exit 1
fi
echo "   OK: dist/$APP_NAME.app"

# ── 4. Info.plist tweaks ──────────────────────────────────────
echo "[4/5] Configuring Info.plist..."

PLIST="dist/$APP_NAME.app/Contents/Info.plist"

# Permission usage descriptions
/usr/libexec/PlistBuddy -c "Add :NSAppleEventsUsageDescription string 'GYROCUE Laser uses this to track the mouse cursor.'" "$PLIST" 2>/dev/null || true

/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string 13.0" "$PLIST" 2>/dev/null || \
    /usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 13.0" "$PLIST"

# Retina support
/usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST" 2>/dev/null || true

# Hide from Dock (uncomment to make it a background-only app)
# /usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$PLIST" 2>/dev/null || true

echo "   OK"

# ── 5. DMG build ──────────────────────────────────────────────
echo "[5/5] Building DMG installer..."

DMG_NAME="${APP_NAME}_v${APP_VERSION}.dmg"
DMG_TMP="dist/dmg_tmp"

rm -rf "$DMG_TMP" "dist/$DMG_NAME"
mkdir -p "$DMG_TMP"

# Copy the .app
cp -R "dist/$APP_NAME.app" "$DMG_TMP/"

# Symlink to /Applications for drag-to-install UX
ln -s /Applications "$DMG_TMP/Applications"

# Create the DMG
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_TMP" \
    -ov \
    -format UDZO \
    "dist/$DMG_NAME"

rm -rf "$DMG_TMP"

if [ ! -f "dist/$DMG_NAME" ]; then
    echo "[ERROR] DMG build failed!"
    exit 1
fi

DMG_SIZE=$(du -h "dist/$DMG_NAME" | cut -f1)

echo ""
echo "====================================================="
echo "  DONE!"
echo "====================================================="
echo ""
echo "  .app  -> dist/$APP_NAME.app"
echo "  .dmg  -> dist/$DMG_NAME  ($DMG_SIZE)"
echo ""
echo "====================================================="
echo ""
echo "Tip: Share the DMG. The user double-clicks it and drags"
echo "     the icon to the Applications folder."
echo ""
