# GYROCUE Laser – macOS

Apple Silicon (M1/M2/M3/M4) + macOS 13 (Ventura) or newer.

## Files

| File | Purpose |
|------|---------|
| `laser_mac.py` | Source code (PyObjC / AppKit / Quartz) |
| `build_mac.sh` | Builds `.app` + `.dmg` in one go |

## Run from source (development)

```bash
pip3 install --user pyobjc
python3 laser_mac.py
```

## Build: .app + .dmg

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Outputs:
- `dist/GYROCUELaser.app` – the app
- `dist/GYROCUELaser_v6.0.dmg` – installer for distribution

When the user opens the `.dmg`, they simply drag the icon into the **Applications** folder.

## Required permissions

On first launch macOS will prompt for several permissions. **Both are needed** for full functionality:

### 1. Input Monitoring → for global hotkeys

`System Settings → Privacy & Security → Input Monitoring`

Enable the `GYROCUELaser` entry (or `Terminal` / `Python` if running from source).

Effect: F9/F10/F11/F8/ESC work everywhere. Without this, hotkeys are inactive but the panel UI still works.

### 2. Accessibility → for window management

`System Settings → Privacy & Security → Accessibility`

Many macOS versions request this for overlay windows. If not requested, leave it.

## Permission revoked / not working

If something gets stuck or you reinstall the app:

1. `System Settings → Privacy & Security → Input Monitoring`
2. Remove the old entry (uncheck AND `−` button)
3. Restart the app — it will re-request the permission

## Notarization (for end-user distribution)

The `.dmg` produced by `build_mac.sh` is **not signed**. When other users open it, macOS Gatekeeper will block it:

> "GYROCUELaser cannot be opened because the developer cannot be verified"

The user can bypass it:
- Right-click the `.app` → **Open** → **Open** (again)
- Or: `System Settings → Privacy & Security` → "Open anyway"

For clean distribution (no warnings), you'll need:
1. **Apple Developer Program** subscription (~$99/year)
2. **Developer ID Application** certificate
3. `codesign` to sign the app
4. `notarytool` to submit for Apple notarization
5. `stapler` to attach the ticket

This is a separate process — let me know if you need a script for it.

## Limitations on macOS

| Feature | Status |
|---------|--------|
| Hide system cursor | ✓ `NSCursor.hide()` |
| Click-through window | ✓ `setIgnoresMouseEvents` |
| Always on top (over fullscreen) | ✓ NSScreenSaverWindowLevel |
| Global hotkeys | ✓ `CGEventTap` (needs Input Monitoring) |
| Settings persistence | ✓ `~/Library/Application Support/GYROCUELaser/` |
| Click ripple feedback | not yet |
| Multiple cursor shapes | dot only for now |

## Known issues

- **The cursor sometimes reappears when switching apps.**
  macOS aggressively restores the cursor on app switch. The program updates at 120 fps so it's mostly invisible, but you may see a flicker. F9 twice fixes any stuck state.

- **In some apps' fullscreen mode, the laser may not show.**
  `NSWindowCollectionBehaviorFullScreenAuxiliary` covers most cases, but PowerPoint / Keynote presentation modes can be tricky depending on macOS version.
