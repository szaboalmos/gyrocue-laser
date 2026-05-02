"""
gyrocue.com – GYROCUE Laser v6.0 (macOS)
Apple Silicon + macOS 13+ (Ventura, Sonoma, Sequoia)

Architecture:
  - Cursor process : PyObjC overlay (NSWindow) + CGEventTap hotkeys
  - Panel process  : PySide6 UI (subprocess, same JSON command protocol as Windows)

Permissions:
  System Settings -> Privacy & Security ->
    - Accessibility    <- enable Python / the .app
    - Input Monitoring <- enable Python / the .app

Run:   python3 laser_mac.py
Build: ./build_mac.sh
"""

import os
import sys
import json
import subprocess
import atexit

# ── Config ────────────────────────────────────────────────────────────────────
def config_dir():
    d = os.path.expanduser("~/Library/Application Support/GYROCUELaser")
    os.makedirs(d, exist_ok=True)
    return d

CONFIG_PATH  = os.path.join(config_dir(), "settings.json")
COMMAND_PATH = os.path.join(config_dir(), "command.json")

DEFAULT_CFG = {
    "color": "#ff2020", "size": 18, "visible": False,
    "start_mode": "center", "last_pos": None,
}

def load_cfg():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_CFG, **json.load(f)}
    except Exception:
        return dict(DEFAULT_CFG)

def save_cfg(c):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

PRESETS = ["#ff2020","#ff8800","#ffee00","#00e676",
           "#2979ff","#e040fb","#ffffff","#00e5ff"]


# ═════════════════════════════════════════════════════════════════════════════
# CURSOR PROCESS  (PyObjC overlay)
# ═════════════════════════════════════════════════════════════════════════════
def run_cursor():
    import objc
    from AppKit import (
        NSApplication, NSApp, NSWindow, NSView, NSColor, NSBezierPath,
        NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
        NSScreenSaverWindowLevel,
        NSCursor, NSEvent,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorStationary,
        NSWindowCollectionBehaviorIgnoresCycle,
        NSWindowCollectionBehaviorFullScreenAuxiliary,
    )
    from Foundation import (
        NSObject, NSMakeRect, NSMakePoint, NSTimer,
        NSRunLoop, NSDefaultRunLoopMode,
    )
    from Quartz import (
        CGEventTapCreate, CGEventTapEnable,
        kCGEventTapOptionListenOnly,
        kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventKeyDown,
        CGEventGetIntegerValueField, kCGKeyboardEventKeycode,
        CFRunLoopAddSource, CFRunLoopGetMain,
        CFMachPortCreateRunLoopSource, kCFRunLoopCommonModes,
        CGEventGetLocation,
    )

    cfg  = load_cfg()
    state = {
        "color":      cfg["color"],
        "size":       int(cfg["size"]),
        "visible":    False,
        "start_mode": cfg.get("start_mode", "center"),
        "last_pos":   cfg.get("last_pos"),
    }
    _g = {"window": None, "view": None}
    _center_next = [True]

    # ── Color helpers ─────────────────────────────────────────────────────────
    def hex_to_nscolor(h, alpha=1.0):
        r = int(h[1:3], 16) / 255.0
        g = int(h[3:5], 16) / 255.0
        b = int(h[5:7], 16) / 255.0
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, alpha)

    def darker(h, amt=80):
        r = max(0, int(h[1:3], 16) - amt)
        g = max(0, int(h[3:5], 16) - amt)
        b = max(0, int(h[5:7], 16) - amt)
        return f"#{r:02x}{g:02x}{b:02x}"

    def lighter(h, amt=100):
        r = min(255, int(h[1:3], 16) + amt)
        g = min(255, int(h[3:5], 16) + amt)
        b = min(255, int(h[5:7], 16) + amt)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── Overlay view ──────────────────────────────────────────────────────────
    class LaserView(NSView):
        def drawRect_(self, rect):
            if not state["visible"]:
                return
            bounds = self.bounds()
            cx = bounds.size.width  / 2.0
            cy = bounds.size.height / 2.0
            r  = state["size"] / 2.0
            col = state["color"]

            glow = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cx-r-3, cy-r-3, 2*(r+3), 2*(r+3)))
            glow.setLineWidth_(2)
            hex_to_nscolor(darker(col, 120)).setStroke()
            glow.stroke()

            dot = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cx-r, cy-r, 2*r, 2*r))
            hex_to_nscolor(col).setFill()
            dot.fill()
            hex_to_nscolor(darker(col, 60)).setStroke()
            dot.setLineWidth_(1)
            dot.stroke()

            inner = max(1, r / 4)
            ip = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(cx-inner, cy-inner, 2*inner, 2*inner))
            hex_to_nscolor(lighter(col, 120)).setFill()
            ip.fill()

    # ── Create laser window ───────────────────────────────────────────────────
    WIN_SIZE = 100
    rect = NSMakeRect(0, 0, WIN_SIZE, WIN_SIZE)
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False)
    window.setOpaque_(False)
    window.setBackgroundColor_(NSColor.clearColor())
    window.setLevel_(NSScreenSaverWindowLevel)
    window.setIgnoresMouseEvents_(True)
    window.setHasShadow_(False)
    window.setCollectionBehavior_(
        NSWindowCollectionBehaviorCanJoinAllSpaces |
        NSWindowCollectionBehaviorStationary       |
        NSWindowCollectionBehaviorIgnoresCycle     |
        NSWindowCollectionBehaviorFullScreenAuxiliary
    )
    view = LaserView.alloc().initWithFrame_(rect)
    window.setContentView_(view)
    window.orderFrontRegardless()
    _g["window"] = window
    _g["view"]   = view

    def redraw():
        if _g["view"]:
            _g["view"].setNeedsDisplay_(True)

    # ── Cursor helpers ────────────────────────────────────────────────────────
    def get_screen_center():
        from AppKit import NSScreen
        screen = NSScreen.mainScreen()
        f = screen.frame()
        return f.origin.x + f.size.width / 2, f.origin.y + f.size.height / 2

    def get_mouse_pos():
        loc = NSEvent.mouseLocation()
        return loc.x, loc.y

    def move_mouse(x, y):
        from Quartz import CGWarpMouseCursorPosition, CGPoint
        CGWarpMouseCursorPosition((x, y))

    def sync_cfg():
        cfg["color"]      = state["color"]
        cfg["size"]       = state["size"]
        cfg["start_mode"] = state["start_mode"]
        cfg["last_pos"]   = list(state["last_pos"]) if state["last_pos"] else None
        save_cfg(cfg)

    # ── F18 hold-to-show state ────────────────────────────────────────────────
    _saved_pos = [None]
    _f18_down  = [False]

    def on_f18_press():
        _saved_pos[0] = get_mouse_pos()
        state["visible"] = True
        if _center_next[0]:
            cx, cy = get_screen_center()
            move_mouse(cx, cy)
            _center_next[0] = False
        elif state["start_mode"] == "center":
            cx, cy = get_screen_center()
            move_mouse(cx, cy)
        elif state["start_mode"] == "last" and state["last_pos"]:
            move_mouse(state["last_pos"][0], state["last_pos"][1])
        NSCursor.hide()
        redraw()

    def on_f18_release():
        if state["start_mode"] == "last":
            state["last_pos"] = get_mouse_pos()
            sync_cfg()
        state["visible"] = False
        if _saved_pos[0]:
            move_mouse(_saved_pos[0][0], _saved_pos[0][1])
            _saved_pos[0] = None
        NSCursor.unhide()
        redraw()

    def quit_app():
        try: NSCursor.unhide()
        except: pass
        save_cfg(cfg)
        NSApp.terminate_(None)

    atexit.register(lambda: NSCursor.unhide())

    # ── CGEventTap hotkeys ────────────────────────────────────────────────────
    KC_F18 = 79  # macOS keycode for F18

    def event_tap_callback(proxy, event_type, event, refcon):
        if event_type == kCGEventKeyDown:
            kc = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            if kc == KC_F18 and not _f18_down[0]:
                _f18_down[0] = True
                on_f18_press()
        return event

    # We also need key-up — use kCGEventKeyUp
    from Quartz import kCGEventKeyUp
    def event_tap_callback_full(proxy, event_type, event, refcon):
        kc = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
        if event_type == kCGEventKeyDown and kc == KC_F18 and not _f18_down[0]:
            _f18_down[0] = True
            on_f18_press()
        elif event_type == kCGEventKeyUp and kc == KC_F18 and _f18_down[0]:
            _f18_down[0] = False
            on_f18_release()
        return event

    mask = (1 << kCGEventKeyDown) | (1 << kCGEventKeyUp)
    tap = CGEventTapCreate(
        kCGSessionEventTap, kCGHeadInsertEventTap,
        kCGEventTapOptionListenOnly, mask,
        event_tap_callback_full, None)
    if tap:
        src = CFMachPortCreateRunLoopSource(None, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetMain(), src, kCFRunLoopCommonModes)
        CGEventTapEnable(tap, True)
    else:
        print("[WARNING] F18 hotkey unavailable — enable Input Monitoring in System Settings.")

    # ── Mouse follow timer ────────────────────────────────────────────────────
    class MouseTracker(NSObject):
        def followMouse_(self, timer):
            win = _g["window"]
            if win is None:
                return
            loc = NSEvent.mouseLocation()
            sz = win.frame().size
            win.setFrameOrigin_(NSMakePoint(
                loc.x - sz.width / 2.0,
                loc.y - sz.height / 2.0))

    tracker = MouseTracker.alloc().init()
    follow_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        1.0 / 120.0, tracker, "followMouse:", None, True)
    NSRunLoop.currentRunLoop().addTimer_forMode_(follow_timer, NSDefaultRunLoopMode)

    # ── Command watcher ───────────────────────────────────────────────────────
    class CommandWatcher(NSObject):
        def checkCommands_(self, timer):
            try:
                if not os.path.exists(COMMAND_PATH):
                    return
                with open(COMMAND_PATH, "r", encoding="utf-8") as f:
                    cmd = json.load(f)
                os.remove(COMMAND_PATH)

                if "color" in cmd:
                    state["color"] = cmd["color"]
                if "size" in cmd:
                    state["size"] = int(cmd["size"])
                if "start_mode" in cmd:
                    state["start_mode"] = cmd["start_mode"]
                if cmd.get("center_next"):
                    _center_next[0] = True
                if cmd.get("quit"):
                    quit_app()
                    return

                sync_cfg()
                redraw()
            except Exception:
                pass

    watcher = CommandWatcher.alloc().init()
    watch_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        0.15, watcher, "checkCommands:", None, True)
    NSRunLoop.currentRunLoop().addTimer_forMode_(watch_timer, NSDefaultRunLoopMode)

    # ── Launch panel subprocess ───────────────────────────────────────────────
    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--panel"]
        else:
            cmd = [sys.executable, os.path.abspath(__file__), "--panel"]
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"Failed to start panel: {e}")

    print("=" * 50)
    print("GYROCUE Laser v6.0 (macOS cursor process)")
    print("=" * 50)
    print(f"Config: {CONFIG_PATH}")
    print("F18 = hold to show laser")

    NSApp.activateIgnoringOtherApps_(True)
    NSApp.run()


# ═════════════════════════════════════════════════════════════════════════════
# PANEL PROCESS  (PySide6 UI — same as Windows)
# ═════════════════════════════════════════════════════════════════════════════
def run_panel():
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QSlider, QPushButton, QLineEdit, QFrame,
        QRadioButton, QButtonGroup, QColorDialog, QSizePolicy,
    )
    from PySide6.QtGui import (
        QColor, QPainter, QBrush, QPen, QPixmap, QIcon,
    )
    from PySide6.QtCore import Qt, QTimer, Signal

    cfg = load_cfg()

    BG   = "#f0f0f0"
    HDR  = "#ffffff"
    EL   = "#e0e0e0"
    EL2  = "#d0d0d0"
    DIV  = "#cccccc"
    FG   = "#1a1a1a"
    FG2  = "#555555"
    ACC  = "#ff2020"
    ACCD = "#cc1a1a"

    state = {
        "color":      cfg["color"],
        "size":       int(cfg["size"]),
        "start_mode": cfg.get("start_mode", "center"),
    }

    def send_command(cmd):
        try:
            with open(COMMAND_PATH, "w", encoding="utf-8") as f:
                json.dump(cmd, f)
        except Exception:
            pass

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    SS = f"""
        QWidget {{ background: {BG}; color: {FG}; font-family: 'Helvetica Neue', 'Segoe UI'; font-size: 9pt; }}
        QLineEdit {{
            background: {EL}; color: {FG}; border: none; border-radius: 3px;
            padding: 4px 6px; font-family: Menlo, Consolas; font-size: 9pt;
        }}
        QSlider::groove:horizontal {{
            height: 4px; background: {EL}; border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px; height: 14px; margin: -5px 0;
            background: {ACC}; border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{ background: {ACC}; border-radius: 2px; }}
        QRadioButton {{ spacing: 8px; }}
        QRadioButton::indicator {{ width: 14px; height: 14px; }}
        QPushButton {{ border: none; border-radius: 3px; padding: 7px 14px; }}
        QPushButton:focus {{ outline: none; }}
    """
    app.setStyleSheet(SS)

    win = QWidget()
    win.setWindowTitle("GYROCUE Laser")
    win.setFixedWidth(320)
    win.setWindowFlags(win.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    ico_path  = os.path.join(base_path, "Gyrocue_Logok_EPS-05.icns")
    if os.path.exists(ico_path):
        win.setWindowIcon(QIcon(ico_path))

    root_layout = QVBoxLayout(win)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    def make_div():
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {DIV}; border: none;")
        return line

    def make_sec(text):
        row = QWidget()
        row.setStyleSheet(f"background: {BG};")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(16, 14, 16, 6)
        rl.setSpacing(8)
        bar = QFrame()
        bar.setFixedSize(2, 12)
        bar.setStyleSheet(f"background: {ACC}; border: none;")
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f"color: {FG2}; font-size: 7pt; font-weight: bold;")
        rl.addWidget(bar)
        rl.addWidget(lbl)
        rl.addStretch()
        return row

    # ── HEADER ────────────────────────────────────────────────────────────────
    hdr = QWidget()
    hdr.setStyleSheet(f"background: {HDR};")
    hdr_l = QHBoxLayout(hdr)
    hdr_l.setContentsMargins(12, 7, 12, 7)
    hdr_l.setSpacing(10)

    logo_path = os.path.join(base_path, "logo_panel.png")
    if os.path.exists(logo_path):
        logo_lbl = QLabel()
        pix = QPixmap(logo_path)
        logo_lbl.setPixmap(pix)
        logo_lbl.setStyleSheet(f"background: {HDR};")
        hdr_l.addWidget(logo_lbl)
    else:
        dot = QLabel("⬤")
        dot.setStyleSheet(f"color: {ACC}; font-size: 12pt; background: {HDR};")
        hdr_l.addWidget(dot)

    vf = QVBoxLayout()
    vf.setSpacing(1)
    title_lbl = QLabel("GYROCUE Laser")
    title_lbl.setStyleSheet(f"color: {FG}; font-size: 11pt; font-weight: bold; background: {HDR};")
    sub_lbl = QLabel("gyrocue.com")
    sub_lbl.setStyleSheet(f"color: {FG2}; font-size: 7pt; background: {HDR};")
    vf.addWidget(title_lbl)
    vf.addWidget(sub_lbl)
    hdr_l.addLayout(vf)
    hdr_l.addStretch()

    ver_lbl = QLabel("v6.0")
    ver_lbl.setStyleSheet(f"color: {FG2}; font-size: 7pt; background: {HDR};")
    ver_lbl.setAlignment(Qt.AlignTop | Qt.AlignRight)
    hdr_l.addWidget(ver_lbl)

    root_layout.addWidget(hdr)
    root_layout.addWidget(make_div())

    # ── COLOR ─────────────────────────────────────────────────────────────────
    root_layout.addWidget(make_sec("Color"))

    class ColorDot(QWidget):
        clicked = Signal()
        def __init__(self, color):
            super().__init__()
            self._color = QColor(color)
            self.setFixedSize(34, 34)
            self.setCursor(Qt.PointingHandCursor)
        def set_color(self, hex_str):
            self._color = QColor(hex_str)
            self.update()
        def paintEvent(self, _):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(self._color))
            p.drawEllipse(2, 2, 30, 30)
        def mousePressEvent(self, _):
            self.clicked.emit()

    crow_w = QWidget()
    crow_w.setStyleSheet(f"background: {BG};")
    crow_l = QHBoxLayout(crow_w)
    crow_l.setContentsMargins(16, 0, 16, 8)
    crow_l.setSpacing(10)

    color_dot = ColorDot(state["color"])
    crow_l.addWidget(color_dot)

    hex_edit = QLineEdit(state["color"])
    hex_edit.setFixedWidth(90)
    crow_l.addWidget(hex_edit)

    pick_btn = QPushButton("🎨")
    pick_btn.setStyleSheet(
        f"QPushButton {{ background: {EL}; color: {FG2}; padding: 6px 10px; }}"
        f"QPushButton:hover {{ background: {EL2}; }}"
    )
    pick_btn.setCursor(Qt.PointingHandCursor)
    crow_l.addWidget(pick_btn)
    crow_l.addStretch()
    root_layout.addWidget(crow_w)

    class Swatch(QWidget):
        clicked = Signal(str)
        def __init__(self, hex_color):
            super().__init__()
            self._color = QColor(hex_color)
            self._hex   = hex_color
            self._hover = False
            self.setFixedSize(26, 26)
            self.setCursor(Qt.PointingHandCursor)
        def paintEvent(self, _):
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor("#cccccc"), 2) if self._hover else Qt.NoPen)
            p.setBrush(QBrush(self._color))
            p.drawEllipse(2, 2, 22, 22)
        def enterEvent(self, _):  self._hover = True;  self.update()
        def leaveEvent(self, _):  self._hover = False; self.update()
        def mousePressEvent(self, _): self.clicked.emit(self._hex)

    prow_w = QWidget()
    prow_w.setStyleSheet(f"background: {BG};")
    prow_l = QHBoxLayout(prow_w)
    prow_l.setContentsMargins(16, 0, 16, 12)
    prow_l.setSpacing(6)
    for hc in PRESETS:
        sw = Swatch(hc)
        prow_l.addWidget(sw)
        sw.clicked.connect(lambda h=hc: apply_color(h))
    prow_l.addStretch()
    root_layout.addWidget(prow_w)

    def apply_color(h):
        if not QColor(h).isValid():
            return
        state["color"] = h
        color_dot.set_color(h)
        hex_edit.setText(h)
        send_command({"color": h})

    hex_edit.returnPressed.connect(lambda: apply_color(hex_edit.text()))
    color_dot.clicked.connect(lambda: pick_color_dialog())
    pick_btn.clicked.connect(lambda: pick_color_dialog())

    def pick_color_dialog():
        c = QColorDialog.getColor(QColor(state["color"]), win, "Laser color")
        if c.isValid():
            apply_color(c.name())

    root_layout.addWidget(make_div())

    # ── SIZE ──────────────────────────────────────────────────────────────────
    root_layout.addWidget(make_sec("Dot Size"))

    srow_w = QWidget()
    srow_w.setStyleSheet(f"background: {BG};")
    srow_l = QHBoxLayout(srow_w)
    srow_l.setContentsMargins(16, 0, 16, 14)
    srow_l.setSpacing(10)

    size_slider = QSlider(Qt.Horizontal)
    size_slider.setRange(6, 60)
    size_slider.setValue(state["size"])
    srow_l.addWidget(size_slider)

    size_lbl = QLabel(f"{state['size']} px")
    size_lbl.setFixedWidth(46)
    size_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    size_lbl.setStyleSheet(f"color: {ACC}; font-weight: bold; background: {BG};")
    srow_l.addWidget(size_lbl)

    def on_size(v):
        state["size"] = v
        size_lbl.setText(f"{v} px")
        send_command({"size": v})

    size_slider.valueChanged.connect(on_size)
    root_layout.addWidget(srow_w)
    root_layout.addWidget(make_div())

    # ── START POSITION ────────────────────────────────────────────────────────
    root_layout.addWidget(make_sec("Start Position"))

    seg_w = QWidget()
    seg_w.setStyleSheet(f"background: {EL}; border-radius: 3px;")
    seg_l = QHBoxLayout(seg_w)
    seg_l.setContentsMargins(2, 2, 2, 2)
    seg_l.setSpacing(2)

    btn_ctr = QPushButton("Screen center")
    btn_ctr.setCursor(Qt.PointingHandCursor)
    btn_lst = QPushButton("Last position")
    btn_lst.setCursor(Qt.PointingHandCursor)
    for b in (btn_ctr, btn_lst):
        b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    seg_l.addWidget(btn_ctr)
    seg_l.addWidget(btn_lst)

    seg_wrap = QWidget()
    seg_wrap.setStyleSheet(f"background: {BG};")
    sw_l = QHBoxLayout(seg_wrap)
    sw_l.setContentsMargins(16, 0, 16, 6)
    sw_l.addWidget(seg_w)
    root_layout.addWidget(seg_wrap)

    def update_seg():
        if state["start_mode"] == "center":
            btn_ctr.setStyleSheet(f"QPushButton {{ background: {ACC}; color: white; padding: 8px 10px; }}"
                                  f"QPushButton:hover {{ background: {ACCD}; }}")
            btn_lst.setStyleSheet(f"QPushButton {{ background: {EL2}; color: {FG2}; padding: 8px 10px; }}"
                                  f"QPushButton:hover {{ background: {EL}; }}")
        else:
            btn_ctr.setStyleSheet(f"QPushButton {{ background: {EL2}; color: {FG2}; padding: 8px 10px; }}"
                                  f"QPushButton:hover {{ background: {EL}; }}")
            btn_lst.setStyleSheet(f"QPushButton {{ background: {ACC}; color: white; padding: 8px 10px; }}"
                                  f"QPushButton:hover {{ background: {ACCD}; }}")

    def set_center():
        state["start_mode"] = "center"
        update_seg()
        send_command({"start_mode": "center"})

    def set_last():
        state["start_mode"] = "last"
        update_seg()
        send_command({"start_mode": "last"})

    btn_ctr.clicked.connect(set_center)
    btn_lst.clicked.connect(set_last)
    update_seg()

    cnext_btn = QPushButton("Center")
    cnext_btn.setCursor(Qt.PointingHandCursor)
    cnext_btn.setStyleSheet(
        f"QPushButton {{ background: {ACC}; color: white; padding: 8px 16px; text-align: left; }}"
        f"QPushButton:hover {{ background: {ACCD}; }}"
    )
    cnext_btn.clicked.connect(lambda: send_command({"center_next": True}))

    cnext_wrap = QWidget()
    cnext_wrap.setStyleSheet(f"background: {BG};")
    cw_l = QHBoxLayout(cnext_wrap)
    cw_l.setContentsMargins(16, 0, 16, 12)
    cw_l.addWidget(cnext_btn)
    root_layout.addWidget(cnext_wrap)

    root_layout.addWidget(make_div())

    # ── FOOTER ────────────────────────────────────────────────────────────────
    foot_w = QWidget()
    foot_w.setStyleSheet(f"background: {BG};")
    foot_l = QHBoxLayout(foot_w)
    foot_l.setContentsMargins(16, 10, 16, 10)

    info_lbl = QLabel("ⓘ  Cursor runs in a separate overlay.")
    info_lbl.setStyleSheet(f"color: {FG2}; font-size: 8pt; background: {BG};")
    foot_l.addWidget(info_lbl)
    foot_l.addStretch()

    quit_btn = QPushButton("✕  Quit")
    quit_btn.setCursor(Qt.PointingHandCursor)
    quit_btn.setStyleSheet(
        f"QPushButton {{ background: {ACC}; color: white; font-weight: bold; padding: 7px 16px; }}"
        f"QPushButton:hover {{ background: {ACCD}; }}"
    )
    foot_l.addWidget(quit_btn)
    root_layout.addWidget(foot_w)

    def on_close():
        send_command({"quit": True})
        app.quit()
        os._exit(0)

    quit_btn.clicked.connect(on_close)
    win.keyPressEvent = lambda e: on_close() if e.key() == Qt.Key_Escape else None

    # ── Sync from cfg ─────────────────────────────────────────────────────────
    def sync_from_cfg():
        try:
            new_cfg = load_cfg()
            if new_cfg["color"] != state["color"]:
                apply_color(new_cfg["color"])
            if int(new_cfg["size"]) != state["size"]:
                state["size"] = int(new_cfg["size"])
                size_slider.setValue(state["size"])
            new_sm = new_cfg.get("start_mode", "center")
            if new_sm != state["start_mode"]:
                state["start_mode"] = new_sm
                update_seg()
        except Exception:
            pass

    sync_timer = QTimer()
    sync_timer.timeout.connect(sync_from_cfg)
    sync_timer.start(500)

    win.show()
    win.adjustSize()
    win.move(120, 80)
    sys.exit(app.exec())


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if "--panel" in sys.argv:
        run_panel()
    else:
        import objc
        from AppKit import NSApplication
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(1)  # accessory — no dock icon for cursor process
        try:
            if os.path.exists(COMMAND_PATH):
                os.remove(COMMAND_PATH)
        except Exception:
            pass
        run_cursor()
