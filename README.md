# GYROCUE Laser – Build Guide (Windows)

## Files

| File | Purpose |
|------|---------|
| `laser.py` | Source code |
| `build.bat` | EXE only build (PyInstaller) |
| `build_all.bat` | EXE + installer in one step |
| `installer.iss` | Inno Setup installer script |

## One-time setup

1. **Python** must be installed (3.10+) and in PATH
2. **Inno Setup 6** download and install:
   https://jrsoftware.org/isdl.php
   (install to default location: `C:\Program Files (x86)\Inno Setup 6`)

`PyInstaller` is auto-installed on first build.

## Build

Single command:
```
build_all.bat
```

Two outputs are produced:
- `dist\GYROCUELaser.exe` – the runnable program
- `Output\GYROCUELaser_Setup_v6.0.exe` – installer for distribution

## Installer features

- English UI
- Configurable install directory (default: `Program Files\GYROCUELaser`)
- Optional desktop and Start Menu shortcuts (user choice)
- No admin rights required (lowest privilege)
- Removes `%APPDATA%\GYROCUELaser` on uninstall
- Kills running instances before install / uninstall (`taskkill`)
- Automatic upgrade of previous versions (matched by AppId)

## EXE only build (no installer)

```
build.bat
```

This produces only `dist\GYROCUELaser.exe`, no Inno Setup needed.

## Troubleshooting

**"PyInstaller install failed"** → Try manually:
```
python -m pip install --upgrade pyinstaller
```

**"Inno Setup not found"** → Either install it, or if installed elsewhere, edit `build_all.bat` and adjust the `ISCC` path.

**"EXE build failed"** → Check the output, usually an import error. Typical fix:
```
python -m pip install --upgrade pyinstaller
```

**Windows SmartScreen blocks the installer EXE** → Normal for unsigned EXEs. The user can click "More info" → "Run anyway". To avoid this, you'd need a code-signing certificate (~ €100/year).
