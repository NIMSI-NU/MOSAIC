"""
MOSAIC GUI - Moving Object Segmentation under Adverse Imaging Conditions
Tkinter-based desktop application for the MOSAIC library
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import threading
from importlib.metadata import version
import numpy as np

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import mosaic
    MOSAIC_AVAILABLE = True
except ImportError:
    MOSAIC_AVAILABLE = False


# ─── Theme / Style Constants ──────────────────────────────────────────────────
BG_DARK    = "#0d1117"
BG_PANEL   = "#161b22"
BG_CARD    = "#1c2128"
BG_INPUT   = "#21262d"
BORDER     = "#30363d"
ACCENT     = "#58a6ff"
ACCENT_DIM = "#1f4068"
SUCCESS    = "#3fb950"
WARNING    = "#d29922"
ERROR      = "#f85149"
TEXT_PRI   = "#e6edf3"
TEXT_SEC   = "#8b949e"
TEXT_DIM   = "#484f58"

FONT_MONO  = ("Courier New", 10)
FONT_SM    = ("Segoe UI", 9)
FONT_MD    = ("Segoe UI", 10)
FONT_LG    = ("Segoe UI", 12)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_HEAD  = ("Segoe UI", 11, "bold")


def apply_theme(root):
    """Configure ttk styles for dark theme."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
        background=BG_DARK, foreground=TEXT_PRI,
        fieldbackground=BG_INPUT, bordercolor=BORDER,
        troughcolor=BG_PANEL, selectbackground=ACCENT_DIM,
        selectforeground=TEXT_PRI, font=FONT_MD)

    style.configure("TFrame", background=BG_DARK)
    style.configure("Card.TFrame", background=BG_CARD)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("TLabel", background=BG_DARK, foreground=TEXT_PRI, font=FONT_MD)
    style.configure("Secondary.TLabel", background=BG_DARK, foreground=TEXT_SEC, font=FONT_SM)
    style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_PRI, font=FONT_MD)
    style.configure("CardSec.TLabel", background=BG_CARD, foreground=TEXT_SEC, font=FONT_SM)
    style.configure("Title.TLabel", background=BG_DARK, foreground=TEXT_PRI, font=FONT_TITLE)
    style.configure("Head.TLabel", background=BG_CARD, foreground=TEXT_PRI, font=FONT_HEAD)
    style.configure("Accent.TLabel", background=BG_DARK, foreground=ACCENT, font=FONT_MD)
    style.configure("Success.TLabel", background=BG_DARK, foreground=SUCCESS, font=FONT_SM)
    style.configure("Warning.TLabel", background=BG_DARK, foreground=WARNING, font=FONT_SM)
    style.configure("Error.TLabel",   background=BG_DARK, foreground=ERROR,   font=FONT_SM)

    style.configure("TButton",
        background=BG_CARD, foreground=TEXT_PRI,
        bordercolor=BORDER, relief="flat", padding=(10, 6), font=FONT_MD)
    style.map("TButton",
        background=[("active", BG_INPUT), ("pressed", BORDER)],
        foreground=[("active", TEXT_PRI)])

    style.configure("Accent.TButton",
        background=ACCENT, foreground=BG_DARK,
        bordercolor=ACCENT, relief="flat", padding=(10, 6), font=("Segoe UI", 10, "bold"))
    style.map("Accent.TButton",
        background=[("active", "#79b8ff"), ("pressed", "#388bfd")],
        foreground=[("active", BG_DARK)])

    style.configure("Success.TButton",
        background=SUCCESS, foreground=BG_DARK,
        bordercolor=SUCCESS, relief="flat", padding=(10, 6), font=("Segoe UI", 10, "bold"))
    style.map("Success.TButton",
        background=[("active", "#56d364"), ("pressed", "#2ea043")],
        foreground=[("active", BG_DARK)])

    style.configure("Danger.TButton",
        background=ERROR, foreground=BG_DARK,
        bordercolor=ERROR, relief="flat", padding=(10, 6), font=FONT_MD)
    style.map("Danger.TButton",
        background=[("active", "#ff7b72"), ("pressed", "#da3633")],
        foreground=[("active", BG_DARK)])

    style.configure("TEntry",
        fieldbackground=BG_INPUT, foreground=TEXT_PRI,
        bordercolor=BORDER, insertcolor=ACCENT, relief="flat", padding=(6, 4))
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox",
        fieldbackground=BG_INPUT, foreground=TEXT_PRI,
        background=BG_INPUT, selectbackground=ACCENT_DIM,
        arrowcolor=TEXT_SEC)
    style.map("TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        selectbackground=[("readonly", ACCENT_DIM)])

    style.configure("TCheckbutton",
        background=BG_CARD, foreground=TEXT_PRI, font=FONT_MD,
        indicatorcolor=BG_INPUT, indicatorrelief="flat")
    style.map("TCheckbutton",
        background=[("active", BG_CARD)],
        indicatorcolor=[("selected", ACCENT)])

    style.configure("TNotebook",
        background=BG_PANEL, bordercolor=BORDER, tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab",
        background=BG_PANEL, foreground=TEXT_SEC,
        padding=(14, 8), bordercolor=BORDER, font=FONT_MD)
    style.map("TNotebook.Tab",
        background=[("selected", BG_CARD)],
        foreground=[("selected", TEXT_PRI)])

    style.configure("TScrollbar",
        background=BG_PANEL, troughcolor=BG_DARK,
        bordercolor=BG_DARK, arrowcolor=TEXT_SEC, relief="flat")
    style.map("TScrollbar",
        background=[("active", BORDER)])

    style.configure("Horizontal.TScale",
        background=BG_CARD, troughcolor=BG_INPUT,
        sliderrelief="flat", sliderthickness=14)
    style.map("Horizontal.TScale",
        background=[("active", BG_CARD)])

    style.configure("TProgressbar",
        background=ACCENT, troughcolor=BG_INPUT,
        bordercolor=BG_INPUT, lightcolor=ACCENT, darkcolor=ACCENT)

    style.configure("TSeparator", background=BORDER)


# ─── Reusable Widgets ─────────────────────────────────────────────────────────

class LabeledEntry(ttk.Frame):
    """A label + entry in a row, optionally with a browse button."""
    def __init__(self, parent, label, value="", browse=None, tooltip=None, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.var = tk.StringVar(value=str(value))

        lbl = ttk.Label(self, text=label, style="CardSec.TLabel", width=22, anchor="w")
        lbl.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="w")

        entry = ttk.Entry(self, textvariable=self.var, width=28)
        entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.columnconfigure(1, weight=1)

        if browse:
            btn = ttk.Button(self, text="…", width=3, command=browse)
            btn.grid(row=0, column=2, padx=(2, 8), pady=4)

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(str(val))


class LabeledCheck(ttk.Frame):
    def __init__(self, parent, label, value=False, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.var = tk.BooleanVar(value=value)
        lbl = ttk.Label(self, text=label, style="CardSec.TLabel", width=22, anchor="w")
        lbl.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        chk = ttk.Checkbutton(self, variable=self.var)
        chk.grid(row=0, column=1, padx=4, pady=4, sticky="w")

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(bool(val))


class LabeledCombo(ttk.Frame):
    def __init__(self, parent, label, values, current=0, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self.var = tk.StringVar()
        lbl = ttk.Label(self, text=label, style="CardSec.TLabel", width=22, anchor="w")
        lbl.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        combo = ttk.Combobox(self, textvariable=self.var, values=values,
                             state="readonly", width=26)
        combo.grid(row=0, column=1, padx=(4, 8), pady=4, sticky="ew")
        self.columnconfigure(1, weight=1)
        if values:
            combo.current(min(current, len(values) - 1))

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(str(val))


class SectionHeader(ttk.Frame):
    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        ttk.Label(self, text=text, style="Head.TLabel").pack(
            side="left", padx=10, pady=(12, 4))
        sep = tk.Frame(self, height=1, bg=BORDER)
        sep.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=(12, 4))


class LogPanel(ttk.Frame):
    """Scrollable text log."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.text = tk.Text(self, bg=BG_DARK, fg=TEXT_SEC,
                            font=FONT_MONO, relief="flat",
                            wrap="word", state="disabled",
                            insertbackground=ACCENT, borderwidth=0,
                            highlightthickness=1, highlightbackground=BORDER)
        scroll = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.text.tag_configure("info",    foreground=TEXT_SEC)
        self.text.tag_configure("success", foreground=SUCCESS)
        self.text.tag_configure("warning", foreground=WARNING)
        self.text.tag_configure("error",   foreground=ERROR)
        self.text.tag_configure("accent",  foreground=ACCENT)

    def log(self, msg, level="info"):
        self.text.configure(state="normal")
        self.text.insert("end", msg + "\n", level)
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class ImageViewer(ttk.Frame):
    """Canvas-based image viewer with zoom and pan."""
    def __init__(self, parent, show_click = False, **kwargs):
        super().__init__(parent, style="Card.TFrame", **kwargs)
        self._photo = None
        self._zoom = 1.0
        self._offset = [0, 0]
        self._drag_start = None
        self._img_array = None
        self._frame_idx = 0
        self._frame_stack = None
        self._show_click = show_click
        self.last_click = None
        self.list_clicks = None

        # Top controls
        ctrl = ttk.Frame(self, style="Card.TFrame")
        ctrl.pack(fill="x", padx=8, pady=(8, 4))

        self.frame_label = ttk.Label(ctrl, text="No image loaded",
                                     style="CardSec.TLabel")
        self.frame_label.pack(side="left")

        btn_frame = ttk.Frame(ctrl, style="Card.TFrame")
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="+10 |⟨", width=8,
                   command=lambda: self._nav(10)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="⟨", width=3,
                   command=lambda: self._nav(1)).pack(side="left", padx=2)
        self.frame_num = ttk.Entry(btn_frame, width=8)
        self.frame_num.insert(-1, f'{self._frame_idx}')
        self.frame_num.pack(side="left", padx=2)
        ttk.Button(btn_frame, text="⟩", width=3,
                   command=lambda: self._nav(-1)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="⟩| -10", width=8,
                   command=lambda: self._nav(-10)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Fit", width=4,
                   command=self._fit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="1:1", width=4,
                   command=self._zoom_reset).pack(side="left", padx=2)

        self.frame_num.bind("<Return>", self._on_enter)
        # Canvas
        self.canvas = tk.Canvas(self, bg=BG_DARK, relief="flat",
                                highlightthickness=1, highlightbackground=BORDER)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        self.canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<MouseWheel>",      self._on_scroll)
        self.canvas.bind("<Button-4>",        self._on_scroll)
        self.canvas.bind("<Button-5>",        self._on_scroll)
        self.canvas.bind("<Configure>",       lambda e: self._redraw())

        # Placeholder text
        self.canvas.after(100, self._draw_placeholder)

    def _draw_placeholder(self):
        w = self.canvas.winfo_width() or 400
        h = self.canvas.winfo_height() or 300
        self.canvas.delete("placeholder")
        self.canvas.create_text(w//2, h//2,
            text="No image loaded\nLoad images to preview",
            fill=TEXT_DIM, font=FONT_MD, justify="center", tags="placeholder")

    def load_stack(self, stack: np.ndarray, frame_nums=None):
        """Load a numpy array stack (N, H, W) for display."""
        self._frame_stack = stack
        self._frame_nums = frame_nums
        self._frame_idx = 0
        self._show_frame()

    def _show_frame(self):
        if self._frame_stack is None:
            return
        n = len(self._frame_stack)
        self._frame_idx = max(0, min(self._frame_idx, n - 1))
        frame = self._frame_stack[self._frame_idx]
        # Normalize to uint8
        mn, mx = frame.min(), frame.max()
        if mx > mn:
            norm = ((frame - mn) / (mx - mn) * 255).astype(np.uint8)
        else:
            norm = np.zeros_like(frame, dtype=np.uint8)
        self._img_array = norm
        lbl = f"Frame {self._frame_nums[self._frame_idx] if self._frame_nums is not None else self._frame_idx + 1}  |  {self._frame_idx + 1}/{n}"
        self.frame_label.configure(text=lbl)
        self.canvas.delete("placeholder")
        self._redraw()

    def _redraw(self):
        if self._img_array is None:
            return
        self.canvas.delete("img")
        self.canvas.delete("dot")
        img = Image.fromarray(self._img_array, mode="L")
        w_c = self.canvas.winfo_width()  or 400
        h_c = self.canvas.winfo_height() or 300
        nw = max(1, int(img.width  * self._zoom))
        nh = max(1, int(img.height * self._zoom))
        img = img.resize((nw, nh), Image.NEAREST)
        self._photo = ImageTk.PhotoImage(img)
        x = w_c // 2 + self._offset[0]
        y = h_c // 2 + self._offset[1]
        self.canvas.create_image(x, y, anchor="center",
                                 image=self._photo, tags="img")
        if self._show_click and self.last_click is not None:
            x_dot = int(self._zoom*(self.last_click[0] - self._img_array.shape[1]/2) + x)
            y_dot = int(self._zoom*(self.last_click[1] - self._img_array.shape[0]/2) + y)
            self.canvas.create_oval(x_dot - 3, y_dot - 3, x_dot + 3, y_dot + 3,
                                    fill="white", outline="black", tags="dot")
        

    def _fit(self):
        if self._img_array is None:
            return
        w_c = self.canvas.winfo_width()  or 400
        h_c = self.canvas.winfo_height() or 300
        h, w = self._img_array.shape
        self._zoom = min((w_c - 16) / w, (h_c - 16) / h)
        self._offset = [0, 0]
        self._redraw()

    def _zoom_reset(self):
        self._zoom = 1.0
        self._offset = [0, 0]
        self._redraw()

    def _nav(self, delta):
        if self._frame_stack is None:
            return
        self._frame_idx += delta
        self._show_frame()
        self.frame_num.delete(0, tk.END)
        self.frame_num.insert(-1, f'{self._frame_idx}')

    def _on_drag_start(self, e):
        self._drag_start = (e.x, e.y)

    def _on_drag(self, e):
        if self._drag_start:
            dx = e.x - self._drag_start[0]
            dy = e.y - self._drag_start[1]
            self._offset[0] += dx
            self._offset[1] += dy
            self._drag_start = (e.x, e.y)
            self._redraw()

    def _on_scroll(self, e):
        factor = 1.1
        if e.num == 5 or getattr(e, "delta", 0) < 0:
            factor = 1 / factor
        self._zoom = max(0.05, min(20.0, self._zoom * factor))
        self._redraw()

    def _on_enter(self, event):
        if self._frame_stack is None:
            return
        local_num = int(self.frame_num.get())
        if local_num < self._frame_nums.min():
            local_num = self._frame_nums.min()
        elif local_num > self._frame_nums.max():
            local_num = self._frame_nums.max()
        self._frame_idx = local_num
        self.frame_num.delete(0, tk.END)
        self.frame_num.insert(-1, f'{self._frame_idx}')
        self._show_frame()

    def _draw_dot(self, event):
        self.last_click = (int((event.x - self.canvas.coords("img")[0])/(self._zoom) + 0.5*self._img_array.shape[1]),
                           int((event.y - self.canvas.coords("img")[1])/(self._zoom) + 0.5*self._img_array.shape[0]))
        self.canvas.delete("dot")
        self.canvas.create_oval(event.x-3, event.y-3, event.x+3, event.y+3,
                                fill="white", outline="black", tags="dot")
        if self.list_clicks is None:
            self.list_clicks = np.array([[self._frame_idx, self.last_click[0], self.last_click[1]]])
        else:
            if np.any(self.list_clicks[:,0] == self._frame_idx):
                list_idx = np.nonzero(self.list_clicks[:,0] == self._frame_idx)[0][0]
                self.list_clicks[list_idx] = np.array([[self._frame_idx, self.last_click[0], self.last_click[1]]])
            else:
                list_click_new = np.array([[self._frame_idx, self.last_click[0], self.last_click[1]]])
                self.list_clicks = np.concatenate((self.list_clicks, list_click_new), axis = 0)
                sort_ind = np.argsort(self.list_clicks[:,0])
                self.list_clicks = self.list_clicks[sort_ind]
        
# ─── Tab: Load ────────────────────────────────────────────────────────────────

class LoadTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.configure(style="TFrame")
        self._build()
 
    def _build(self):
        # ── Left: file setup ──
        left = ttk.Frame(self, style="Card.TFrame")
        left.pack(side="left", fill="y", padx=(12, 6), pady=12, ipadx=4)
 
        ttk.Label(left, text="File Setup", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(left).pack(fill="x", padx=10, pady=(0, 8))
 
        # ── Source type selector ──
        src_frame = ttk.Frame(left, style="Card.TFrame")
        src_frame.pack(fill="x", padx=4, pady=(0, 6))
        ttk.Label(src_frame, text="Source Type", style="CardSec.TLabel",
                  width=22, anchor="w").grid(row=0, column=0, padx=(8, 4), pady=4, sticky="w")
        self._src_mode = tk.StringVar(value="folder")
        src_combo = ttk.Combobox(src_frame, textvariable=self._src_mode,
                                 values=["folder", "cine", "cih/cihx"],
                                 state="readonly", width=16)
        src_combo.grid(row=0, column=1, padx=(4, 8), pady=4, sticky="ew")
        src_frame.columnconfigure(1, weight=1)
        src_combo.bind("<<ComboboxSelected>>", lambda e: self._switch_mode())
 
        # ── Mode-specific input panels (stacked, only one shown at a time) ──
        self._mode_container = ttk.Frame(left, style="Card.TFrame")
        self._mode_container.pack(fill="x", padx=4, pady=2)
 
        # --- Folder panel ---
        self._panel_folder = ttk.Frame(self._mode_container, style="Card.TFrame")
        self.img_folder = LabeledEntry(self._panel_folder, "Image Folder",
                                       browse=self._browse_folder)
        self.img_folder.pack(fill="x", pady=2)
        self.ext_entry = LabeledEntry(self._panel_folder, "File Extension", value="*.tif")
        self.ext_entry.pack(fill="x", pady=2)
        self.regex_entry = LabeledEntry(self._panel_folder, "Frame # Regex", value=r"\d+")
        self.regex_entry.pack(fill="x", pady=2)
 
        # --- .cine panel ---
        self._panel_cine = ttk.Frame(self._mode_container, style="Card.TFrame")
        self.cine_file = LabeledEntry(self._panel_cine, ".cine File",
                                      browse=self._browse_cine)
        self.cine_file.pack(fill="x", pady=2)
        ttk.Label(self._panel_cine,
                  text="Frame range below selects frames from the file.\nLeave blank to load all frames.",
                  style="CardSec.TLabel", justify="left").pack(
                  anchor="w", padx=8, pady=(0, 4))
 
        # --- .cih/.cihx panel ---
        self._panel_cih = ttk.Frame(self._mode_container, style="Card.TFrame")
        self.cih_file = LabeledEntry(self._panel_cih, ".cih/.cihx File",
                                     browse=self._browse_cih)
        self.cih_file.pack(fill="x", pady=2)
        ttk.Label(self._panel_cih,
                  text="The paired .mraw file must be in the same\ndirectory with the same base name.",
                  style="CardSec.TLabel", justify="left").pack(
                  anchor="w", padx=8, pady=(0, 4))
 
        # Show the default panel
        self._panel_folder.pack(fill="x")
 
        # ── Shared: Props + Toolpath ──
        self.props_file = LabeledEntry(left, "Props JSON",
            browse=self._browse_props)
        self.props_file.pack(fill="x", padx=4, pady=2)
 
        self.toolpath_file = LabeledEntry(left, "Toolpath File",
            browse=self._browse_toolpath)
        self.toolpath_file.pack(fill="x", padx=4, pady=2)
 
        # ── Shared: Frame range ──
        SectionHeader(left, "Frame Range").pack(fill="x", padx=4, pady=(8, 2))
        ttk.Label(left, text="Leave Start/End blank for binary files to load all frames.",
                  style="CardSec.TLabel", wraplength=280, justify="left").pack(
                  anchor="w", padx=12, pady=(0, 4))
 
        rng_frame = ttk.Frame(left, style="Card.TFrame")
        rng_frame.pack(fill="x", padx=4, pady=2)
        ttk.Label(rng_frame, text="Start", style="CardSec.TLabel", width=10).grid(
            row=0, column=0, padx=(8,4), pady=4)
        self.frame_start = ttk.Entry(rng_frame, width=8)
        self.frame_start.grid(row=0, column=1, padx=4, pady=4)
 
        ttk.Label(rng_frame, text="End", style="CardSec.TLabel", width=10).grid(
            row=0, column=2, padx=(8,4), pady=4)
        self.frame_end = ttk.Entry(rng_frame, width=8)
        self.frame_end.grid(row=0, column=3, padx=(4,8), pady=4)
 
        ttk.Label(rng_frame, text="Step", style="CardSec.TLabel", width=10).grid(
            row=1, column=0, padx=(8,4), pady=4)
        self.frame_step = ttk.Entry(rng_frame, width=8)
        self.frame_step.insert(0, "1")
        self.frame_step.grid(row=1, column=1, padx=4, pady=4)
 
        # ── Buttons ──
        btn_row = ttk.Frame(left, style="Card.TFrame")
        btn_row.pack(fill="x", padx=8, pady=(16, 8))
        ttk.Button(btn_row, text="Load Images",
                   style="Accent.TButton",
                   command=self._load_images).pack(fill="x", pady=3)
        ttk.Button(btn_row, text="Load Configs",
                   command=self._load_configs).pack(fill="x", pady=3)
 
        # Status indicator
        self.status_lbl = ttk.Label(left, text="● Not loaded",
                                    style="Warning.TLabel")
        self.status_lbl.pack(padx=10, pady=4, anchor="w")
 
        # ── Right: preview ──
        right = ttk.Frame(self, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True,
                   padx=(6, 12), pady=12)
 
        ttk.Label(right, text="Preview", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(right).pack(fill="x", padx=10, pady=(0, 6))
 
        self.viewer = ImageViewer(right)
        self.viewer.pack(fill="both", expand=True, padx=4, pady=(0, 4))
 
        # Info bar
        info = ttk.Frame(right, style="Card.TFrame")
        info.pack(fill="x", padx=4, pady=(0, 8))
        self.info_frames = ttk.Label(info, text="Frames: —",
                                     style="CardSec.TLabel")
        self.info_frames.pack(side="left", padx=8)
        self.info_shape = ttk.Label(info, text="Shape: —",
                                    style="CardSec.TLabel")
        self.info_shape.pack(side="left", padx=8)
        self.info_source = ttk.Label(info, text="Source: —",
                                     style="CardSec.TLabel")
        self.info_source.pack(side="left", padx=8)
 
    # ── Mode switching ──────────────────────────────────────────────────────
 
    def _switch_mode(self):
        """Show only the panel relevant to the selected source type."""
        for panel in (self._panel_folder, self._panel_cine, self._panel_cih):
            panel.pack_forget()
        mode = self._src_mode.get()
        if mode == "folder":
            self._panel_folder.pack(fill="x")
        elif mode == "cine":
            self._panel_cine.pack(fill="x")
        else:
            self._panel_cih.pack(fill="x")
 
    # ── Browse helpers ──────────────────────────────────────────────────────
 
    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Image Folder")
        if path:
            self.img_folder.set(path)
 
    def _browse_cine(self):
        path = filedialog.askopenfilename(
            title="Select .cine File",
            filetypes=[("CINE files", "*.cine"), ("All files", "*.*")])
        if path:
            self.cine_file.set(path)
 
    def _browse_cih(self):
        path = filedialog.askopenfilename(
            title="Select .cih or .cihx File",
            filetypes=[("CIH files", "*.cih *.cihx"), ("All files", "*.*")])
        if path:
            self.cih_file.set(path)
 
    def _browse_props(self):
        path = filedialog.askopenfilename(
            title="Select Props JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            self.props_file.set(path)
 
    def _browse_toolpath(self):
        path = filedialog.askopenfilename(
            title="Select Toolpath File",
            filetypes=[("Text/CSV files", "*.txt *.csv"), ("All files", "*.*")])
        if path:
            self.toolpath_file.set(path)
 
    # ── Frame range helpers ─────────────────────────────────────────────────
 
    def _get_frame_range(self, allow_none=False):
        """Return a numpy arange from the Start/End/Step fields.
        If allow_none=True and both Start and End are blank, returns None
        (used by binary loaders that can load all frames automatically)."""
        s = self.frame_start.get().strip()
        e = self.frame_end.get().strip()
        step_str = self.frame_step.get().strip()
        if allow_none and not s and not e:
            return None
        try:
            start = int(s) if s else 0
            end   = int(e) if e else 0
            step  = int(step_str) if step_str else 1
            return np.arange(start, end + 1, step)
        except ValueError:
            messagebox.showerror("Error", "Invalid frame range values.")
            return "error"
 
    # ── Load dispatcher ─────────────────────────────────────────────────────
 
    def _load_images(self):
        if not MOSAIC_AVAILABLE:
            self.app.log("MOSAIC library not found. Cannot load images.", "error")
            return
        mode = self._src_mode.get()
        if mode == "folder":
            self._load_folder()
        elif mode == "cine":
            self._load_cine()
        else:
            self._load_cih()
 
    def _load_folder(self):
        folder = self.img_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid image folder.")
            return
        frames = self._get_frame_range()
        if frames is None or isinstance(frames, str):
            # frames=="error" means invalid input; None means blank — treat as "load all"
            # For folder mode with blank range, default to 0–400
            frames = np.arange(0, 401)
        ext   = self.ext_entry.get()
        regex = self.regex_entry.get()
 
        def _run():
            try:
                self.app.log(f"Loading image folder: {folder}", "accent")
                self.app.log(f"  Frames {frames[0]}–{frames[-1]}, ext={ext}")
                fo, fro = mosaic.core.init_load_images(
                    folder, frames, extension=ext, regex_str=regex)
                self.app.fo  = fo
                self.app.fro = fro
                self.app.log(f"  Loaded {fro.numFramesOpen} frames, shape {fro.frameShape}", "success")
                self.app.root.after(0, lambda: self._on_load_success("folder"))
            except Exception as e:
                self.app.log(f"Error loading images: {e}", "error")
                self.app.root.after(0, lambda: self.status_lbl.configure(
                    text="● Load failed", style="Error.TLabel"))
 
        threading.Thread(target=_run, daemon=True).start()
 
    def _load_cine(self):
        path = self.cine_file.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid .cine file.")
            return
        frames = self._get_frame_range(allow_none=True)
        if frames is None or isinstance(frames, str):
            return
 
        def _run():
            try:
                self.app.log(f"Loading .cine file: {os.path.basename(path)}", "accent")
                if frames is None:
                    self.app.log("  No frame range specified — loading all frames.")
                else:
                    self.app.log(f"  Frames {frames[0]}–{frames[-1]}")
                fo, fro = mosaic.file_io.load_cine_file(path, frames)
                self.app.fo  = fo
                self.app.fro = fro
                self.app.log(f"  Loaded {fro.numFramesOpen} frames, shape {fro.frameShape}", "success")
                self.app.root.after(0, lambda: self._on_load_success("cine"))
            except Exception as e:
                self.app.log(f"Error loading .cine file: {e}", "error")
                self.app.root.after(0, lambda: self.status_lbl.configure(
                    text="● Load failed", style="Error.TLabel"))
 
        threading.Thread(target=_run, daemon=True).start()
 
    def _load_cih(self):
        path = self.cih_file.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid .cih/.cihx file.")
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".cih", ".cihx"):
            messagebox.showerror("Error", "File must be a .cih or .cihx file.")
            return
        # Check the paired .mraw exists
        mraw_path = os.path.splitext(path)[0] + ".mraw"
        if not os.path.isfile(mraw_path):
            messagebox.showerror(
                "Error",
                f"Paired .mraw file not found:\n{mraw_path}\n\n"
                "The .mraw file must be in the same directory with the same base name.")
            return
        frames = self._get_frame_range(allow_none=True)
        if frames is None or isinstance(frames, str):
            return
 
        def _run():
            try:
                self.app.log(f"Loading .cih file: {os.path.basename(path)}", "accent")
                self.app.log(f"  Paired .mraw: {os.path.basename(mraw_path)}")
                if frames is None:
                    self.app.log("  No frame range specified — loading all frames.")
                else:
                    self.app.log(f"  Frames {frames[0]}–{frames[-1]}")
                fo, fro = mosaic.file_io.load_mraw_file(path, frames)
                self.app.fo  = fo
                self.app.fro = fro
                self.app.log(f"  Loaded {fro.numFramesOpen} frames, shape {fro.frameShape}", "success")
                self.app.root.after(0, lambda: self._on_load_success("cih"))
            except Exception as e:
                self.app.log(f"Error loading .cih/.mraw file: {e}", "error")
                self.app.root.after(0, lambda: self.status_lbl.configure(
                    text="● Load failed", style="Error.TLabel"))
 
        threading.Thread(target=_run, daemon=True).start()
 
    # ── Post-load ────────────────────────────────────────────────────────────
 
    def _on_load_success(self, source_type):
        fro = self.app.fro
        self.status_lbl.configure(text="● Images loaded", style="Success.TLabel")
        self.info_frames.configure(text=f"Frames: {fro.numFramesOpen}")
        self.info_shape.configure(text=f"Shape: {fro.frameShape}")
        labels = {"folder": "Image Folder", "cine": ".cine", "cih": ".cih/.mraw"}
        self.info_source.configure(text=f"Source: {labels.get(source_type, source_type)}")
        self.viewer.load_stack(fro.openFrames, fro.openedFrameNums)
        self.viewer._fit()
        self.app.toolpath_tab._reload_img()
 
    def _load_configs(self):
        if not MOSAIC_AVAILABLE:
            self.app.log("MOSAIC library not found.", "error")
            return
        if self.app.fro is None:
            messagebox.showwarning("Warning", "Load images first.")
            return
        props    = self.props_file.get()   or None
        toolpath = self.toolpath_file.get() or None
        if not props and not toolpath:
            messagebox.showwarning("Warning", "No config files specified.")
            return
        try:
            self.app.fro = mosaic.core.load_configs(
                self.app.fro,
                propsJSON=props if props and os.path.isfile(props) else None,
                toolpath=toolpath if toolpath and os.path.isfile(toolpath) else None)
            self.app.log("Configs loaded successfully.", "success")
            self.app.props_tab.sync_from_fro()
        except Exception as e:
            self.app.log(f"Error loading configs: {e}", "error")

class ToolpathTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        toolpath_header = ttk.Frame(self, style="Panel.TFrame")
        toolpath_header.pack(fill="x", padx=12, pady=(10, 4))
        ttk.Label(toolpath_header, text="Toolpath Input Panel",
                  style="Head.TLabel").pack(side="left", padx=(0,12))
        toolpath_frame = ttk.Frame(self, style="Panel.TFrame")
        toolpath_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.click_canvas = ImageViewer(toolpath_frame, True)
        self.click_canvas.pack(fill="both", side="left", expand=True)
        
        matrix_frame = ttk.Frame(toolpath_frame, style="Panel.TFrame")
        matrix_frame.pack(side='left',fill='x')
        self.point_list = ttk.Treeview(matrix_frame, selectmode='none',
                                       show='headings',style='Panel.TFrame')
        self.point_list["columns"] = (1, 2, 3)
        self.point_list.pack(fill='both')
        self.point_list.heading(1, text='Frame #')
        self.point_list.heading(2, text='X')
        self.point_list.heading(3, text='Y')
        self.point_list.column(1, width=100, stretch=False)
        self.point_list.column(2, width=100, stretch=False)
        self.point_list.column(3, width=100, stretch=False)

        button_frame = ttk.Frame(matrix_frame, style="Panel.TFrame")
        button_frame.pack(fill='x')
        ttk.Button(button_frame, text="Set all X = 0",
                   command=lambda: self._set_coord_zero(0)).pack(pady=4)
        ttk.Button(button_frame, text="Set all Y = 0",
                   command=lambda: self._set_coord_zero(1)).pack(pady=4)
        ttk.Button(button_frame, text="Generate Toolpath",
                   command=self._gen_toolpath).pack(pady=4)
        ttk.Button(button_frame, text="Save Toolpath",
                   command=self._save_toolpath).pack(pady=4)

        self.click_canvas.canvas.bind("<ButtonPress-3>", self._update_treeview_click)

    def _reload_img(self):
        if self.app.fro is None:
            messagebox.showwarning("Warning", "Load images first.")
            return
        self.click_canvas.load_stack(self.app.fro.openFrames, self.app.fro.openedFrameNums)
    
    def _update_treeview_click(self, event):
        self.click_canvas._draw_dot(event)
        if self.click_canvas.list_clicks is None:
            return
        self.point_list.delete(*self.point_list.get_children())
        read_points = self.click_canvas.list_clicks.copy()
        read_points[:,0] = self.app.fro.openedFrameNums[read_points[:,0]]
        for i in range(read_points.shape[0]):
            self.point_list.insert("","end", values=(read_points[i,0], read_points[i,1], read_points[i,2]))
    
    def _set_coord_zero(self, coord):
        if self.click_canvas.list_clicks is None:
            return
        self.point_list.delete(*self.point_list.get_children())
        points = self.click_canvas.list_clicks.copy()
        points[:, coord+1] = 0
        self.click_canvas.list_clicks = points.copy()
        points[:, 0] = self.app.fro.openedFrameNums[points[:, 0]]
        for i in range(points.shape[0]):
            self.point_list.insert("","end", values=(points[i,0], points[i,1], points[i,2]))
        
    def _gen_toolpath(self):
        if self.click_canvas.list_clicks is None:
            return
        if not hasattr(self.app.fro, 'procProps'):
            self.app.fro = mosaic.file_io.load_props(self.app.fro, None)
        mod_points = self.click_canvas.list_clicks.copy()
        mod_points[:, 0] = self.app.fro.openedFrameNums[mod_points[:, 0]]
        self.app.fro = mosaic.process.vec_to_toolpath(self.app.fro, mod_points)
        self.app.log("Toolpath generated and saved to current frame object")

    def _save_toolpath(self):
        if self.app.fro.procProps.toolpathArr is None:
            messagebox.showerror("Toolpath Save Error", "There is no toolpath array to save. Please generate one")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv"),
                                                       ("TXT files", "*.txt"),
                                                       ("All files", "*.*")],
                                            title="Save Toolpath File",
                                            initialfile="toolpath")
        if path:
            np.savetxt(path, self.app.fro.procProps.toolpathArr,
                       delimiter=',', header='Frame #, X (Pixel), Y (Pixel)')
            self.app.log(f"Success saving toolpath. File located at {path}", "success")

        
# ─── Tab: Properties ──────────────────────────────────────────────────────────

class PropsTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        # Scrollable canvas
        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(canvas, style="TFrame")
        self.inner_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.inner_id, width=e.width))

        col1 = ttk.Frame(self.inner, style="TFrame")
        col1.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=12)
        col2 = ttk.Frame(self.inner, style="TFrame")
        col2.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)

        # ── Processing Props ──
        proc_card = ttk.Frame(col1, style="Card.TFrame")
        proc_card.pack(fill="x", pady=(0, 8))
        ttk.Label(proc_card, text="Processing Properties", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(proc_card).pack(fill="x", padx=10, pady=(0, 6))

        self.p_isMoving   = LabeledCheck(proc_card, "Is Moving")
        self.p_isMoving.pack(fill="x", padx=4, pady=1)

        self.p_bgType = LabeledCombo(proc_card, "Background Type",
            ["uniform", "mean_all", "mean_excluded"])
        self.p_bgType.pack(fill="x", padx=4, pady=1)

        self.p_bgProp1    = LabeledEntry(proc_card, "BG Prop1")
        self.p_bgProp1.pack(fill="x", padx=4, pady=1)

        self.p_bwCutoff   = LabeledEntry(proc_card, "Butterworth Cutoff")
        self.p_bwCutoff.pack(fill="x", padx=4, pady=1)

        self.p_rescaleLo  = LabeledEntry(proc_card, "Rescale Low")
        self.p_rescaleLo.pack(fill="x", padx=4, pady=1)

        self.p_rescaleHi  = LabeledEntry(proc_card, "Rescale High")
        self.p_rescaleHi.pack(fill="x", padx=4, pady=1)

        self.p_useMedian  = LabeledCheck(proc_card, "Use Median Filter")
        self.p_useMedian.pack(fill="x", padx=4, pady=1)

        self.p_medSize    = LabeledEntry(proc_card, "Median Size")
        self.p_medSize.pack(fill="x", padx=4, pady=1)

        self.p_useAbs     = LabeledCheck(proc_card, "Use Absolute Value")
        self.p_useAbs.pack(fill="x", padx=4, pady=1)

        self.p_invertVal  = LabeledCheck(proc_card, "Invert Values")
        self.p_invertVal.pack(fill="x", padx=4, pady=1)

        self.p_timeFunc   = LabeledCheck(proc_card, "Time Processing")
        self.p_timeFunc.pack(fill="x", padx=4, pady=1)

        self.p_window     = LabeledEntry(proc_card, "Crop Window (x0,y0,w,h)")
        self.p_window.pack(fill="x", padx=4, pady=1)

        # ── Segmentation Props ──
        seg_card = ttk.Frame(col2, style="Card.TFrame")
        seg_card.pack(fill="x", pady=(0, 8))
        ttk.Label(seg_card, text="Segmentation Properties", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(seg_card).pack(fill="x", padx=10, pady=(0, 6))

        self.s_statType   = LabeledCombo(seg_card, "Stationary Img Type",
            ["median", "mean", "none"])
        self.s_statType.pack(fill="x", padx=4, pady=1)

        self.s_excludeImg = LabeledCheck(seg_card, "Exclude Images")
        self.s_excludeImg.pack(fill="x", padx=4, pady=1)

        self.s_excludeSpan= LabeledEntry(seg_card, "Exclude Min Span")
        self.s_excludeSpan.pack(fill="x", padx=4, pady=1)

        self.s_numLevels  = LabeledEntry(seg_card, "Num Otsu Levels")
        self.s_numLevels.pack(fill="x", padx=4, pady=1)

        self.s_numBins    = LabeledEntry(seg_card, "Num Bins", value="25")
        self.s_numBins.pack(fill="x", padx=4, pady=1)

        self.s_maskLo     = LabeledEntry(seg_card, "Init Mask Level (proc)")
        self.s_maskLo.pack(fill="x", padx=4, pady=1)

        self.s_maskHi     = LabeledEntry(seg_card, "Init Mask Level (core)")
        self.s_maskHi.pack(fill="x", padx=4, pady=1)

        self.s_pepper     = LabeledEntry(seg_card, "Remove Pepper Thresh")
        self.s_pepper.pack(fill="x", padx=4, pady=1)

        self.s_fillHoles  = LabeledEntry(seg_card, "Fill Holes Thresh")
        self.s_fillHoles.pack(fill="x", padx=4, pady=1)

        self.s_openRad    = LabeledEntry(seg_card, "Sep. Opening Radius")
        self.s_openRad.pack(fill="x", padx=4, pady=1)

        self.s_overlapT   = LabeledEntry(seg_card, "Overlap Threshold")
        self.s_overlapT.pack(fill="x", padx=4, pady=1)

        self.s_dilRad     = LabeledEntry(seg_card, "Exp. Dilation Radius")
        self.s_dilRad.pack(fill="x", padx=4, pady=1)

        # Buttons row (spans both columns)
        btn_row = ttk.Frame(self.inner, style="TFrame")
        btn_row.pack(fill="x", padx=12, pady=8)
        ttk.Button(btn_row, text="Apply to Session",
                   style="Accent.TButton",
                   command=self._apply_props).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Load from File",
                   command=self._load_from_file).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Save to File",
                   command=self._save_to_file).pack(side="left")

    def sync_from_fro(self):
        """Populate UI fields from fro.procProps / fro.segProps."""
        fro = self.app.fro
        if fro is None or not hasattr(fro, "procProps"):
            return
        p = fro.procProps
        s = fro.segProps
        try:
            self.p_isMoving.set(getattr(p, "isMoving", False))
            self.p_bgType.set(getattr(p, "backgroundType", "uniform"))
            self.p_bgProp1.set(getattr(p, "backgroundProp1", 1))
            self.p_bwCutoff.set(getattr(p, "butterworthCutoff", 0.2))
            ri = getattr(p, "rescaleIntens", [1, 1])
            self.p_rescaleLo.set(ri[0])
            self.p_rescaleHi.set(ri[1])
            self.p_useMedian.set(getattr(p, "useMedian", True))
            self.p_medSize.set(getattr(p, "medianSize", 3))
            self.p_useAbs.set(getattr(p, "useAbs", False))
            self.p_invertVal.set(getattr(p, "invertVal", False))
            self.p_timeFunc.set(getattr(p, "timeFunc", True))
            w = getattr(p, "window", [0, 0, 0, 0])
            self.p_window.set(",".join(str(x) for x in w))

            self.s_statType.set(getattr(s, "stationaryImgType", "median"))
            self.s_excludeImg.set(getattr(s, "excludeImg", False))
            self.s_excludeSpan.set(getattr(s, "excludeMinSpan", 50))
            self.s_numLevels.set(getattr(s, "numLevels", 5))
            self.s_numBins.set(getattr(s, "numBins", 25))
            ml = getattr(s, "initMaskLevels", [3, 3])
            self.s_maskLo.set(ml[0])
            self.s_maskHi.set(ml[1])
            self.s_pepper.set(getattr(s, "remvPepperThresh", 64))
            self.s_fillHoles.set(getattr(s, "fillHolesThresh", 600))
            self.s_openRad.set(getattr(s, "sepOpeningRad", 2))
            self.s_overlapT.set(getattr(s, "overlapThres", 0.1))
            self.s_dilRad.set(getattr(s, "expDilationRad", 5))
        except Exception as e:
            self.app.log(f"Sync warning: {e}", "warning")

    def _collect_props_dict(self):
        try:
            window = [int(x) for x in self.p_window.get().split(",")]
        except Exception:
            window = [0, 0, 0, 0]
        proc = {
            "isMoving":        self.p_isMoving.get(),
            "backgroundType":  self.p_bgType.get(),
            "backgroundProp1": float(self.p_bgProp1.get()),
            "butterworthCutoff": float(self.p_bwCutoff.get()),
            "rescaleIntens":   [float(self.p_rescaleLo.get()),
                                float(self.p_rescaleHi.get())],
            "useMedian":       self.p_useMedian.get(),
            "medianSize":      int(self.p_medSize.get()),
            "useAbs":          self.p_useAbs.get(),
            "invertVal":       self.p_invertVal.get(),
            "timeFunc":        self.p_timeFunc.get(),
            "window":          window,
        }
        seg = {
            "stationaryImgType": self.s_statType.get(),
            "excludeImg":        self.s_excludeImg.get(),
            "excludeMinSpan":    int(self.s_excludeSpan.get()),
            "numLevels":         int(self.s_numLevels.get()),
            "numBins":           int(self.s_numBins.get()),
            "initMaskLevels":    [int(self.s_maskLo.get()),
                                  int(self.s_maskHi.get())],
            "remvPepperThresh":  int(self.s_pepper.get()),
            "fillHolesThresh":   int(self.s_fillHoles.get()),
            "sepOpeningRad":     float(self.s_openRad.get()),
            "overlapThres":      float(self.s_overlapT.get()),
            "expDilationRad":    float(self.s_dilRad.get()),
        }
        return {"processing_props": proc, "segmentation_props": seg}

    def _apply_props(self):
        """Write UI values into fro.procProps / fro.segProps."""
        if not MOSAIC_AVAILABLE:
            return
        fro = self.app.fro
        if fro is None:
            messagebox.showwarning("Warning", "No session loaded.")
            return
        # Write to temp JSON then reload
        os.makedirs("temp", exist_ok=True)
        tmp = os.path.join("temp", "gui_props.json")
        with open(tmp, "w") as f:
            json.dump(self._collect_props_dict(), f, indent=3)
        try:
            self.app.fro = mosaic.file_io.load_props(fro, tmp)
            self.app.log("Properties applied to session.", "success")
        except Exception as e:
            self.app.log(f"Error applying props: {e}", "error")

    def _load_from_file(self):
        path = filedialog.askopenfilename(
            title="Load Props JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path) as f:
                data = json.load(f)
            # Populate UI
            proc = data.get("processing_props", {})
            seg  = data.get("segmentation_props", {})
            if "isMoving"        in proc: self.p_isMoving.set(proc["isMoving"])
            if "backgroundType"  in proc: self.p_bgType.set(proc["backgroundType"])
            if "backgroundProp1" in proc: self.p_bgProp1.set(proc["backgroundProp1"])
            if "butterworthCutoff" in proc: self.p_bwCutoff.set(proc["butterworthCutoff"])
            if "rescaleIntens"   in proc:
                self.p_rescaleLo.set(proc["rescaleIntens"][0])
                self.p_rescaleHi.set(proc["rescaleIntens"][1])
            if "useMedian"  in proc: self.p_useMedian.set(proc["useMedian"])
            if "medianSize" in proc: self.p_medSize.set(proc["medianSize"])
            if "useAbs"     in proc: self.p_useAbs.set(proc["useAbs"])
            if "invertVal"  in proc: self.p_invertVal.set(proc["invertVal"])
            if "timeFunc"   in proc: self.p_timeFunc.set(proc["timeFunc"])
            if "window"     in proc:
                self.p_window.set(",".join(str(x) for x in proc["window"]))

            if "stationaryImgType" in seg: self.s_statType.set(seg["stationaryImgType"])
            if "excludeImg"     in seg: self.s_excludeImg.set(seg["excludeImg"])
            if "excludeMinSpan" in seg: self.s_excludeSpan.set(seg["excludeMinSpan"])
            if "numLevels"      in seg: self.s_numLevels.set(seg["numLevels"])
            if "numBins"        in seg: self.s_numBins.set(seg["numBins"])
            if "initMaskLevels" in seg:
                self.s_maskLo.set(seg["initMaskLevels"][0])
                self.s_maskHi.set(seg["initMaskLevels"][1])
            if "remvPepperThresh" in seg: self.s_pepper.set(seg["remvPepperThresh"])
            if "fillHolesThresh"  in seg: self.s_fillHoles.set(seg["fillHolesThresh"])
            if "sepOpeningRad"    in seg: self.s_openRad.set(seg["sepOpeningRad"])
            if "overlapThres"     in seg: self.s_overlapT.set(seg["overlapThres"])
            if "expDilationRad"   in seg: self.s_dilRad.set(seg["expDilationRad"])
            self.app.log(f"Loaded props from: {path}", "success")
        except Exception as e:
            self.app.log(f"Error reading props file: {e}", "error")

    def _save_to_file(self):
        path = filedialog.asksaveasfilename(
            title="Save Props JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self._collect_props_dict(), f, indent=3)
            self.app.log(f"Props saved to: {path}", "success")
        except Exception as e:
            self.app.log(f"Error saving props: {e}", "error")


# ─── Tab: Run ─────────────────────────────────────────────────────────────────

class RunTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        self._running_full = False
        self._running_proc = False
        self._running_seg = False
        self._seg_stop_request = False
        self._proc_request_stop = False
        self._request_full_stop = False


        left = ttk.Frame(self, style="Card.TFrame")
        left.pack(side="left", fill="y", padx=(12, 6), pady=12, ipadx=4)

        ttk.Label(left, text="Run Pipeline", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(left).pack(fill="x", padx=10, pady=(0, 10))

        # Frame range overrides
        SectionHeader(left, "Frame Ranges (optional)").pack(
            fill="x", padx=4, pady=(4, 2))
        ttk.Label(left, text="Leave blank to use all loaded frames",
                  style="CardSec.TLabel").pack(anchor="w", padx=12, pady=(0, 4))

        rng = ttk.Frame(left, style="Card.TFrame")
        rng.pack(fill="x", padx=4, pady=2)

        for i, (lbl, attr) in enumerate([
                ("Proc Start",  "proc_start"),
                ("Proc End",    "proc_end"),
                ("Seg Start",   "seg_start"),
                ("Seg End",     "seg_end")]):
            ttk.Label(rng, text=lbl, style="CardSec.TLabel", width=12).grid(
                row=i//2, column=(i%2)*2, padx=(8,4), pady=3, sticky="w")
            e = ttk.Entry(rng, width=8)
            e.grid(row=i//2, column=(i%2)*2+1, padx=4, pady=3)
            setattr(self, attr, e)

        SectionHeader(left, "Actions").pack(fill="x", padx=4, pady=(12, 4))
        procButtons = ttk.Frame(left, style="Card.TFrame")
        procButtons.pack(fill="x")
        ttk.Button(procButtons, text="▶  Run Preprocessing",
                   command=self._run_preprocess).pack(
                   fill="x",side='left', padx=8, pady=3)
        ttk.Button(procButtons, text="⏹",
                   command=self._stop_preprocess).pack(
                   side='right', padx=8, pady=3)
        segButtons = ttk.Frame(left, style="Card.TFrame")
        segButtons.pack(fill='x')
        ttk.Button(segButtons, text="▶  Run Segmentation",
                   command=self._run_segment).pack(
                   fill="x", side='left', padx=8, pady=3)
        ttk.Button(segButtons, text="⏹",
                   command=self._stop_segment).pack(
                   side='right', padx=8, pady=3)
        pipeButtons = ttk.Frame(left, style='Card.TFrame')
        pipeButtons.pack(fill='x')
        ttk.Button(pipeButtons, text="▶▶  Run Full Pipeline",
                   style="Accent.TButton",
                   command=self._run_full).pack(
                   fill="x", side='left', padx=8, pady=3)
        ttk.Button(pipeButtons, text="⏹",
                   command=self._full_stop).pack(
                   side='right', padx=8, pady=3)
        ttk.Separator(left).pack(fill="x", padx=10, pady=12)

        SectionHeader(left, "Save Outputs").pack(fill="x", padx=4, pady=(4, 4))

        self.proc_folder = LabeledEntry(left, "Proc Subfolder", value="processedImages")
        self.proc_folder.pack(fill="x", padx=4, pady=2)
        self.seg_folder  = LabeledEntry(left, "Seg Subfolder",  value="segmentedImages")
        self.seg_folder.pack(fill="x", padx=4, pady=2)
        self.save_ext    = LabeledCombo(left, "Save Format",
            [".tif", ".png", ".jpg"], current=0)
        self.save_ext.pack(fill="x", padx=4, pady=2)

        ttk.Button(left, text="💾  Save Processed Images",
                   command=self._save_proc).pack(fill="x", padx=8, pady=3)
        ttk.Button(left, text="💾  Save Segmented Images",
                   command=self._save_seg).pack(fill="x", padx=8, pady=3)

        # ── Right: progress + timing ──
        right = ttk.Frame(self, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True,
                   padx=(6, 12), pady=12)

        ttk.Label(right, text="Status", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 6))
        ttk.Separator(right).pack(fill="x", padx=10, pady=(0, 10))

        # Progress
        prog_frame = ttk.Frame(right, style="Card.TFrame")
        prog_frame.pack(fill="x", padx=10, pady=4)
        ttk.Label(prog_frame, text="Progress", style="CardSec.TLabel").pack(
            anchor="w", pady=(0, 4))
        self.progress = ttk.Progressbar(prog_frame, mode="indeterminate", length=300)
        self.progress.pack(fill="x")

        # Status cards
        stat_frame = ttk.Frame(right, style="Card.TFrame")
        stat_frame.pack(fill="x", padx=10, pady=8)

        for label, attr in [
                ("Images Loaded",    "stat_loaded"),
                ("Frames Processed", "stat_proc"),
                ("Frames Segmented", "stat_seg"),
                ("Avg. Proc Time",   "stat_time")]:
            row = ttk.Frame(stat_frame, style="Card.TFrame")
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=label, style="CardSec.TLabel", width=20,
                      anchor="w").pack(side="left", padx=(8, 4))
            lbl = ttk.Label(row, text="—", style="Card.TLabel")
            lbl.pack(side="left", padx=4)
            setattr(self, attr, lbl)

    def _get_frame_range_override(self, start_w, end_w, fallback):
        s = start_w.get().strip()
        e = end_w.get().strip()
        if s and e:
            try:
                return np.arange(int(s), int(e) + 1)
            except ValueError:
                pass
        return fallback

    def _update_stats(self):
        fro = self.app.fro
        if fro is None:
            return
        loaded = getattr(fro, "numFramesOpen", "—")
        proc   = getattr(fro, "numFramesProc", "—")
        seg    = getattr(fro, "numFramesSeg",  "—")
        t      = getattr(fro, "timeMeasured",  None)
        self.stat_loaded.configure(text=str(loaded))
        self.stat_proc.configure(text=str(proc))
        self.stat_seg.configure(text=str(seg))
        self.stat_time.configure(text=f"{t*1000:.2f} ms/frame" if t else "—")

    def _run_preprocess(self):
        if not MOSAIC_AVAILABLE:
            self.app.log("MOSAIC not available.", "error"); return
        if self.app.fro is None:
            messagebox.showwarning("Warning", "Load images first."); return
        frames = self._get_frame_range_override(
            self.proc_start, self.proc_end,
            getattr(self.app.fro, "openedFrameNums", None))
        if frames is None:
            messagebox.showerror("Error", "No frames to process."); return

        def _run():
            try:
                self.app.root.after(0, self.progress.start)
                self.app.log("Starting preprocessing…", "accent")
                self._running_proc = True
                idx = 0

                while not self._proc_request_stop:
                    self.app.fro, _ = mosaic.gui_backend.gui_run_processing(self.app.fro,
                                                                         frames,
                                                                         idx)
                    self.app.log(f"Processing Frame {frames[idx]}", "accent")
                    idx += 1
                    if idx >= len(frames):
                        self._proc_request_stop = True

                self._running_proc = False
                self.app.log(f"Preprocessing done. {self.app.fro.numFramesProc} frames.", "success")
                self.app.root.after(0, self._on_proc_done)
            except Exception as e:
                self.app.log(f"Preprocessing error: {e}", "error")
                self.app.root.after(0, self.progress.stop)

        threading.Thread(target=_run, daemon=True).start()

    def _on_proc_done(self):
        self.progress.stop()
        self._update_stats()
        self.app.results_tab.show_proc()
        self._request_full_stop = False
        self._proc_request_stop = False

    def _stop_preprocess(self):
        if self._running_proc:
            self._proc_request_stop = True
            self.app.log(f"Attempting to stop the preprocessor...", "accent")

    def _run_segment(self):
        if not MOSAIC_AVAILABLE:
            self.app.log("MOSAIC not available.", "error"); return
        if self.app.fro is None or not hasattr(self.app.fro, "procFrames"):
            messagebox.showwarning("Warning", "Run preprocessing first."); return
        frames = self._get_frame_range_override(
            self.seg_start, self.seg_end,
            getattr(self.app.fro, "procFrameNums", None))

        def _run():
            try:
                self.app.root.after(0, self.progress.start)
                self.app.log("Starting segmentation…", "accent")
                self._running_seg = True
                idx = 0

                while not self._seg_stop_request:
                    self.app.log(f"Segmenting Frame {frames[idx]}", "accent")
                    self.app.fro = mosaic.gui_backend.gui_run_segmentation(self.app.fro,
                                                                           frames,
                                                                           idx)
                    idx += 1
                    if idx >= len(frames):
                        self._seg_stop_request = True

                self._running_seg = False
                self.app.log(f"Segmentation done. {self.app.fro.numFramesSeg} frames.", "success")
                self.app.root.after(0, self._on_seg_done)
            except Exception as e:
                self.app.log(f"Segmentation error: {e}", "error")
                self.app.root.after(0, self.progress.stop)

        threading.Thread(target=_run, daemon=True).start()

    def _on_seg_done(self):
        self.progress.stop()
        self._update_stats()
        self.app.results_tab.show_seg()
        self._seg_stop_request = False
        self._request_full_stop = False

    def _stop_segment(self):
        if self._running_seg:
            self._seg_stop_request = True
            self.app.log(f"Attempting to stop the segmentation...", "accent")

    def _run_full(self):
        if not MOSAIC_AVAILABLE:
            self.app.log("MOSAIC not available.", "error"); return
        if self.app.fro is None:
            messagebox.showwarning("Warning", "Load images first."); return

        def _run():
            try:
                self.app.root.after(0, self.progress.start)
                fro = self.app.fro
                frames = getattr(fro, "openedFrameNums", None)
                self.app.log("Running full pipeline…", "accent")
                self._running_all = True
                idx = 0
                self.app
                while not self._request_full_stop and idx < len(frames):
                    self.app.fro, _ = mosaic.gui_backend.gui_run_processing(self.app.fro, 
                                                                         frames, idx)
                    self.app.log(f"Processing Frame {frames[idx]}", "accent")
                    idx += 1
                
                self.app.log("  Preprocessing complete.", "success")
                idx = 0
                frames = getattr(self.app.fro, "procFrameNums", None)
                while not self._request_full_stop and idx < len(frames):
                    self.app.fro = mosaic.gui_backend.gui_run_segmentation(self.app.fro, 
                                                                          frames, 
                                                                          idx)
                    self.app.log(f"Segmenting Frame {frames[idx]}")
                    idx += 1
                
                self._running_all = False
                self.app.log("  Segmentation complete.", "success")
                self.app.log("Full pipeline done.", "success")
                self.app.root.after(0, self._on_full_done)
            except Exception as e:
                self.app.log(f"Pipeline error: {e}", "error")
                self.app.root.after(0, self.progress.stop)

        threading.Thread(target=_run, daemon=True).start()

    def _on_full_done(self):
        self.progress.stop()
        self._update_stats()
        self.app.results_tab.show_seg()
    
    def _full_stop(self):
        if self._running_all:
            self._request_full_stop = True
            self.app.log("Attempting to stop the full pipeline...", "accent")

    def _save_proc(self):
        if not MOSAIC_AVAILABLE: return
        fro = self.app.fro
        if fro is None or not hasattr(fro, "procFrames"):
            messagebox.showwarning("Warning", "No processed images to save."); return
        try:
            mosaic.core.save_proc_img(fro,
                folderTitle=self.proc_folder.get(),
                fileType=self.save_ext.get())
            self.app.log(f"Processed images saved to …/{self.proc_folder.get()}", "success")
        except Exception as e:
            self.app.log(f"Save error: {e}", "error")

    def _save_seg(self):
        if not MOSAIC_AVAILABLE: return
        fro = self.app.fro
        if fro is None or not hasattr(fro, "segFrames"):
            messagebox.showwarning("Warning", "No segmented images to save."); return
        try:
            mosaic.core.save_seg_img(fro,
                folderTitle=self.seg_folder.get(),
                fileType=self.save_ext.get())
            self.app.log(f"Segmented images saved to …/{self.seg_folder.get()}", "success")
        except Exception as e:
            self.app.log(f"Save error: {e}", "error")


# ─── Tab: Results ─────────────────────────────────────────────────────────────

class ResultsTab(ttk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.configure(style="TFrame")
        self._build()

    def _build(self):
        # View selector
        ctrl = ttk.Frame(self, style="Card.TFrame")
        ctrl.pack(fill="x", padx=12, pady=(12, 0))
        ttk.Label(ctrl, text="Display:", style="Card.TLabel").pack(
            side="left", padx=(10, 6), pady=8)
        self.view_mode = tk.StringVar(value="processed")
        for text, val in [("Raw", "raw"), ("Processed", "processed"), ("Segmented", "segmented")]:
            ttk.Radiobutton(ctrl, text=text, variable=self.view_mode,
                            value=val, command=self._refresh).pack(
                            side="left", padx=6, pady=8)

        # Viewers - side by side
        viewer_frame = ttk.Frame(self, style="TFrame")
        viewer_frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        left = ttk.Frame(viewer_frame, style="Card.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))
        ttk.Label(left, text="Primary View", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 4))
        self.viewer_main = ImageViewer(left)
        self.viewer_main.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        right = ttk.Frame(viewer_frame, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True, padx=(4, 0))
        ttk.Label(right, text="Overlay View", style="Head.TLabel").pack(
            anchor="w", padx=10, pady=(10, 4))
        self.viewer_overlay = ImageViewer(right)
        self.viewer_overlay.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    def show_proc(self):
        self.view_mode.set("processed")
        self._refresh()

    def show_seg(self):
        self.view_mode.set("segmented")
        self._refresh()

    def _refresh(self):
        fro = self.app.fro
        if fro is None:
            return
        mode = self.view_mode.get()
        if mode == "raw" and hasattr(fro, "openFrames"):
            self.viewer_main.load_stack(fro.openFrames, fro.openedFrameNums)
        elif mode == "processed" and hasattr(fro, "procFrames"):
            self.viewer_main.load_stack(fro.procFrames, fro.procFrameNums)
        elif mode == "segmented" and hasattr(fro, "segFrames"):
            self.viewer_main.load_stack(fro.segFrames, fro.segFrameNums)

        # Overlay: if seg exists, show it alongside
        if hasattr(fro, "segFrames"):
            self.viewer_overlay.load_stack(fro.segFrames, fro.segFrameNums)
        elif hasattr(fro, "procFrames"):
            self.viewer_overlay.load_stack(fro.procFrames, fro.procFrameNums)

        self.viewer_main._fit()
        self.viewer_overlay._fit()


# ─── Main Application ─────────────────────────────────────────────────────────

class MosaicApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MOSAIC  —  Moving Object Segmentation under Adverse Imaging Conditions")
        self.root.geometry("1200x780")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        self.fo  = None
        self.fro = None

        apply_theme(self.root)
        self._build_layout()
        self._check_deps()

    def _build_layout(self):
        # ── Header bar ──
        header = tk.Frame(self.root, bg=BG_PANEL, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo_PIL = Image.open('MOSAIC logo.png').resize([50, 40])
        logo = ImageTk.PhotoImage(logo_PIL)
        logo_label = tk.Label(header, image=logo)
        logo_label.image = logo
        logo_label.pack(side="left", padx=6, pady=1)
        tk.Label(header, text="MOSAIC", bg=BG_PANEL,
                 fg=ACCENT, font=("Courier New", 16, "bold")).pack(
                 side="left", padx=(0, 6), pady=12)
        tk.Label(header, text="Moving Object Segmentation under Adverse Imaging Conditions",
                 bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Segoe UI", 9)).pack(side="left", pady=12)

        # Version badge
        mosaic_version = version('mosaic')
        badge = tk.Label(header, text=f" v{mosaic_version} ", bg=ACCENT_DIM,
                         fg=ACCENT, font=("Courier New", 9))
        badge.pack(side="right", padx=18, pady=16)

        # Separator
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # ── Notebook (main content) ──

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, side="top")

        self.load_tab    = LoadTab(self.notebook, self)
        self.props_tab   = PropsTab(self.notebook, self)
        self.run_tab     = RunTab(self.notebook, self)
        self.results_tab = ResultsTab(self.notebook, self)

        # ── Console tab ──
        console_tab = ttk.Frame(self.notebook, style="TFrame")
        console_header = ttk.Frame(console_tab, style="Panel.TFrame")
        console_header.pack(fill="x", padx=12, pady=(10, 4))
        ttk.Label(console_header, text="Console Output",
                  style="Head.TLabel").pack(side="left", padx=(0, 12))
        ttk.Button(console_header, text="Clear",
                   command=lambda: self.log_panel.clear()).pack(side="right")
        self.log_panel = LogPanel(console_tab, style="Panel.TFrame")
        self.log_panel.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        #Toolpath Tab
        self.toolpath_tab  = ToolpathTab(self.notebook, self)


        self.notebook.add(self.load_tab,    text="  Load  ")
        self.notebook.add(self.toolpath_tab,     text="  Toolpath   ")
        self.notebook.add(self.props_tab,   text="  Properties  ")
        self.notebook.add(self.run_tab,     text="  Run  ")
        self.notebook.add(self.results_tab, text="  Results  ")
        self.notebook.add(console_tab,      text="  Console  ")

    def _check_deps(self):
        if not PIL_AVAILABLE:
            self.log("WARNING: Pillow not installed. Image display disabled.", "warning")
        if not MOSAIC_AVAILABLE:
            self.log("WARNING: MOSAIC library not found. Install with: pip install -e .", "warning")
        else:
            self.log("MOSAIC ready. Load an image folder to begin.", "accent")

    def log(self, msg: str, level: str = "info"):
        """Thread-safe log to the console panel."""
        self.root.after(0, lambda: self.log_panel.log(msg, level))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MosaicApp()
    app.run()