"""
gyrocue.com – GYROCUE Laser v6.0 (Windows)

Architecture: cursor and panel run as separate processes.
The v4 cursor base is kept unchanged (it works!), and the panel is
launched as a subprocess that communicates via a JSON file.

Run:   python laser.py
Build: build.bat (single .exe contains both modes)
"""

import sys
import os
import json
import time
import ctypes
import ctypes.wintypes
import atexit
import subprocess

# ── Config location ──────────────────────────────────────────────────────────
def config_dir():
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    d = os.path.join(base, "GYROCUELaser")
    os.makedirs(d, exist_ok=True)
    return d

CONFIG_PATH  = os.path.join(config_dir(), "settings.json")
COMMAND_PATH = os.path.join(config_dir(), "command.json")

DEFAULT_CFG = {"color": "#ff2020", "size": 18, "visible": False, "monitor": 0, "start_mode": "center", "last_pos": None}

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


def get_monitors():
    """Return list of {left, top, right, bottom} dicts for each physical monitor."""
    class RECT(ctypes.Structure):
        _fields_ = [("left",   ctypes.c_long), ("top",    ctypes.c_long),
                    ("right",  ctypes.c_long), ("bottom", ctypes.c_long)]
    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
        ctypes.POINTER(RECT), ctypes.c_double)
    result = []
    def _cb(hMon, hdcMon, lpRect, dwData):
        r = lpRect.contents
        result.append({"left": r.left, "top": r.top,
                       "right": r.right, "bottom": r.bottom})
        return 1
    ctypes.windll.user32.EnumDisplayMonitors(None, None, MonitorEnumProc(_cb), 0)
    return result


# ═════════════════════════════════════════════════════════════════════════════
# CURSOR PROCESS (--cursor mode, the default)
# ═════════════════════════════════════════════════════════════════════════════
def run_cursor():
    import tkinter as tk

    try:    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except Exception: pass

    user32 = ctypes.windll.user32

    GWL_EXSTYLE       = -20
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_LAYERED     = 0x00080000
    IMAGE_CURSOR      = 2
    SPI_SETCURSORS    = 0x0057
    OCR_IDS = [32512,32513,32514,32515,32642,32643,32644,
               32645,32646,32648,32649,32650,32651]

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def get_cursor_pos():
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def create_invisible_cursor():
        w = h = 32
        bpr = (w + 7) // 8
        sz = bpr * h
        and_mask = (ctypes.c_ubyte * sz)(*([0xFF] * sz))
        xor_mask = (ctypes.c_ubyte * sz)(*([0x00] * sz))
        user32.CreateCursor.restype = ctypes.c_void_p
        user32.CreateCursor.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_void_p,
        ]
        return user32.CreateCursor(
            None, 0, 0, w, h,
            ctypes.cast(and_mask, ctypes.c_void_p),
            ctypes.cast(xor_mask, ctypes.c_void_p),
        )

    def hide_system_cursor():
        hc = create_invisible_cursor()
        if not hc: return False
        user32.CopyImage.restype  = ctypes.c_void_p
        user32.CopyImage.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                      ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        user32.SetSystemCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        for cid in OCR_IDS:
            cp = user32.CopyImage(hc, IMAGE_CURSOR, 0, 0, 0)
            if cp: user32.SetSystemCursor(cp, cid)
        user32.DestroyCursor(hc)
        return True

    def restore_system_cursors():
        user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)

    atexit.register(restore_system_cursors)

    def make_click_through(hwnd):
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                              style | WS_EX_TRANSPARENT | WS_EX_LAYERED)

    def darker(h, a=80):
        r=max(0,int(h[1:3],16)-a); g=max(0,int(h[3:5],16)-a); b=max(0,int(h[5:7],16)-a)
        return f"#{r:02x}{g:02x}{b:02x}"

    def lighter(h, a=100):
        r=min(255,int(h[1:3],16)+a); g=min(255,int(h[3:5],16)+a); b=min(255,int(h[5:7],16)+a)
        return f"#{r:02x}{g:02x}{b:02x}"

    cfg = load_cfg()
    monitors = get_monitors()  # list of {left,top,right,bottom}, 0-based
    state = {
        "color":      cfg["color"],
        "size":       int(cfg["size"]),
        "visible":    False,          # hold-to-show: always starts hidden
        "cidx":       PRESETS.index(cfg["color"]) if cfg["color"] in PRESETS else 0,
        "start_mode": cfg.get("start_mode", "center"),  # "center" or "last"
        "monitor": int(cfg.get("monitor", 0)),  # 0=all, 1..N=specific monitor
    }

    # ── Window (V4 STYLE, THIS WORKS) ────────────────────────────────────────
    WIN_SIZE = 100
    root = tk.Tk()
    root.withdraw()

    cur = tk.Toplevel(root)
    cur.overrideredirect(True)
    cur.attributes("-topmost", True)
    cur.attributes("-transparentcolor", "black")
    cur.config(bg="black")
    cur.geometry(f"{WIN_SIZE}x{WIN_SIZE}+0+0")

    canvas = tk.Canvas(cur, bg="black", highlightthickness=0,
                       width=WIN_SIZE, height=WIN_SIZE)
    canvas.pack()

    def cursor_on_selected_monitor_xy(x, y):
        mon_idx = state["monitor"]
        if mon_idx == 0 or not monitors:
            return True
        idx = mon_idx - 1
        if idx >= len(monitors):
            return True
        m = monitors[idx]
        return m["left"] <= x < m["right"] and m["top"] <= y < m["bottom"]

    def cursor_on_selected_monitor():
        x, y = get_cursor_pos()
        return cursor_on_selected_monitor_xy(x, y)

    def draw_dot():
        canvas.delete("all")
        if not state["visible"]: return
        if not cursor_on_selected_monitor(): return
        cx = cy = WIN_SIZE // 2
        r  = state["size"] // 2
        col = state["color"]
        canvas.create_oval(cx-r-3, cy-r-3, cx+r+3, cy+r+3,
                           fill="", outline=darker(col, 120), width=2)
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                           fill=col, outline=darker(col, 60), width=1)
        inner = max(1, r // 4)
        canvas.create_oval(cx-inner, cy-inner, cx+inner, cy+inner,
                           fill=lighter(col, 120), outline="")

    draw_dot()

    def setup_ct():
        hwnd = user32.GetParent(cur.winfo_id())
        if hwnd == 0:
            hwnd = cur.winfo_id()
        make_click_through(hwnd)

    cur.after(150, setup_ct)

    _follow_state = {"prev_on_mon": True}

    def follow_mouse():
        x, y = get_cursor_pos()
        half = WIN_SIZE // 2
        cur.geometry(f"{WIN_SIZE}x{WIN_SIZE}+{x-half}+{y-half}")
        on_mon = cursor_on_selected_monitor_xy(x, y)
        if on_mon != _follow_state["prev_on_mon"]:
            _follow_state["prev_on_mon"] = on_mon
            draw_dot()
        root.after(8, follow_mouse)

    root.after(200, follow_mouse)

    # ── Hotkeys ──────────────────────────────────────────────────────────────
    VK = {"F18": 0x81}
    _hk_prev = {k: False for k in VK}

    def on_close():
        try: restore_system_cursors()
        except: pass
        try: root.destroy()
        except: pass
        os._exit(0)

    _saved_pos        = [None]  # cursor position saved on F18 press (to restore on release)
    _lp = cfg.get("last_pos")
    _last_laser_pos   = [tuple(_lp) if _lp else None]  # persisted across restarts
    _center_next_press = [True]  # True at startup → first press always centers

    def get_screen_center():
        """Center of the selected monitor, or primary screen if 'All'."""
        mon_idx = state["monitor"]
        if mon_idx > 0 and mon_idx <= len(monitors):
            m = monitors[mon_idx - 1]
            return (m["left"] + m["right"]) // 2, (m["top"] + m["bottom"]) // 2
        # Primary monitor
        return user32.GetSystemMetrics(0) // 2, user32.GetSystemMetrics(1) // 2

    def hotkey_tick():
        vk = VK["F18"]
        now = bool(user32.GetAsyncKeyState(vk) & 0x8000)
        if now != _hk_prev["F18"]:
            state["visible"] = now
            if now:
                _saved_pos[0] = get_cursor_pos()
                if _center_next_press[0]:
                    cx, cy = get_screen_center()
                    user32.SetCursorPos(cx, cy)
                    _center_next_press[0] = False
                elif state["start_mode"] == "center":
                    cx, cy = get_screen_center()
                    user32.SetCursorPos(cx, cy)
                elif state["start_mode"] == "last" and _last_laser_pos[0]:
                    user32.SetCursorPos(_last_laser_pos[0][0], _last_laser_pos[0][1])
                hide_system_cursor()
            else:
                # Only save laser pos in "last" mode (prevent center sessions polluting it)
                if state["start_mode"] == "last":
                    _last_laser_pos[0] = get_cursor_pos()
                    sync_cfg()  # persist across restarts
                # Move cursor back WHILE still invisible, then restore visibility
                # This prevents the cursor from visibly jumping
                if _saved_pos[0]:
                    user32.SetCursorPos(_saved_pos[0][0], _saved_pos[0][1])
                    _saved_pos[0] = None
                restore_system_cursors()
            draw_dot()
        _hk_prev["F18"] = now
        root.after(40, hotkey_tick)

    def sync_cfg():
        cfg["color"]      = state["color"]
        cfg["size"]       = state["size"]
        cfg["monitor"]    = state["monitor"]
        cfg["start_mode"] = state["start_mode"]
        cfg["last_pos"]   = list(_last_laser_pos[0]) if _last_laser_pos[0] else None
        # visible not saved: it's transient (F18 hold-to-show)
        save_cfg(cfg)

    root.after(400, hotkey_tick)

    # ── Watch panel commands ─────────────────────────────────────────────────
    def watch_commands():
        try:
            if os.path.exists(COMMAND_PATH):
                with open(COMMAND_PATH, "r", encoding="utf-8") as f:
                    cmd = json.load(f)
                os.remove(COMMAND_PATH)

                if "color" in cmd:
                    state["color"] = cmd["color"]
                    if cmd["color"] in PRESETS:
                        state["cidx"] = PRESETS.index(cmd["color"])
                if "size" in cmd:
                    state["size"] = int(cmd["size"])
                if "monitor" in cmd:
                    state["monitor"] = int(cmd["monitor"])
                    # Force boundary re-evaluation on next follow_mouse tick
                    _follow_state["prev_on_mon"] = not cursor_on_selected_monitor()
                if "start_mode" in cmd:
                    state["start_mode"] = cmd["start_mode"]
                    sync_cfg()
                if cmd.get("center_next"):
                    _center_next_press[0] = True
                if cmd.get("quit"):
                    on_close()
                    return

                sync_cfg()
                draw_dot()
        except Exception:
            pass
        root.after(150, watch_commands)

    root.after(500, watch_commands)

    # ── Startup ──────────────────────────────────────────────────────────────
    print("=" * 50)
    print("GYROCUE Laser v6.0 (cursor process)")
    print("=" * 50)
    print(f"Config: {CONFIG_PATH}")
    print("F18=hold to show laser")

    panel_proc = start_panel()

    def watch_panel():
        if panel_proc and panel_proc.poll() is not None:
            pass  # panel closed; the cursor keeps running
        root.after(1000, watch_panel)
    root.after(2000, watch_panel)

    root.mainloop()


def start_panel():
    """Launch the panel as a separate process."""
    try:
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--panel"]
        else:
            cmd = [sys.executable, os.path.abspath(__file__), "--panel"]
        return subprocess.Popen(cmd, creationflags=0x08000000)  # CREATE_NO_WINDOW
    except Exception as e:
        print(f"Failed to start panel: {e}")
        return None


# ═════════════════════════════════════════════════════════════════════════════
# PANEL PROCESS (--panel mode)  –  PySide6 UI
# ═════════════════════════════════════════════════════════════════════════════
def run_panel():
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QSlider, QPushButton, QLineEdit, QFrame,
        QRadioButton, QButtonGroup, QColorDialog, QSizePolicy,
    )
    from PySide6.QtGui import (
        QColor, QPainter, QBrush, QPen, QFont, QPixmap, QIcon,
        QFontDatabase,
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QObject

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    cfg      = load_cfg()
    monitors = get_monitors()

    # ── Palette ───────────────────────────────────────────────────────────────
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
        "monitor":    int(cfg.get("monitor", 0)),
        "start_mode": cfg.get("start_mode", "center"),
    }

    def send_command(cmd):
        try:
            with open(COMMAND_PATH, "w", encoding="utf-8") as f:
                json.dump(cmd, f)
        except Exception:
            pass

    # ── App & stylesheet ──────────────────────────────────────────────────────
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    SS = f"""
        QWidget {{ background: {BG}; color: {FG}; font-family: 'Segoe UI'; font-size: 9pt; }}
        QLineEdit {{
            background: {EL}; color: {FG}; border: none; border-radius: 3px;
            padding: 4px 6px; font-family: Consolas; font-size: 9pt;
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

    # ── Main window ───────────────────────────────────────────────────────────
    win = QWidget()
    win.setWindowTitle("GYROCUE Laser")
    win.setFixedWidth(320)
    win.setWindowFlags(win.windowFlags() & ~Qt.WindowMaximizeButtonHint)

    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    ico_path  = os.path.join(base_path, "Gyrocue_Logok_EPS-05.ico")
    if os.path.exists(ico_path):
        win.setWindowIcon(QIcon(ico_path))

    root_layout = QVBoxLayout(win)
    root_layout.setContentsMargins(0, 0, 0, 0)
    root_layout.setSpacing(0)

    # ── Helper: horizontal divider ────────────────────────────────────────────
    def make_div():
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {DIV}; border: none;")
        return line

    # ── Helper: section label ─────────────────────────────────────────────────
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

    # Color dot (custom painted)
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

    # Preset swatches
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

    # ── MONITOR ───────────────────────────────────────────────────────────────
    root_layout.addWidget(make_sec("Monitor"))

    mon_group = QButtonGroup(win)
    mon_group.setExclusive(True)

    def add_mon_rb(text, val):
        rb = QRadioButton(text)
        rb.setStyleSheet(f"QRadioButton {{ background: {BG}; padding: 2px 22px; }}")
        rb.setChecked(state["monitor"] == val)
        mon_group.addButton(rb, val)
        root_layout.addWidget(rb)

    add_mon_rb("All monitors", 0)
    for i, m in enumerate(monitors):
        label = (f"Monitor {i + 1}  "
                 f"({m['right'] - m['left']}×{m['bottom'] - m['top']}  "
                 f"@ {m['left']},{m['top']})")
        add_mon_rb(label, i + 1)

    def on_monitor_change(btn_id):
        state["monitor"] = btn_id
        send_command({"monitor": btn_id})

    mon_group.idClicked.connect(on_monitor_change)

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
            new_mon = int(new_cfg.get("monitor", 0))
            if new_mon != state["monitor"]:
                state["monitor"] = new_mon
                btn = mon_group.button(new_mon)
                if btn:
                    btn.setChecked(True)
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
        try:
            if os.path.exists(COMMAND_PATH):
                os.remove(COMMAND_PATH)
        except: pass
        run_cursor()
