import ctypes
import io
import json
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH,
    BOTTOM,
    END,
    HORIZONTAL,
    LEFT,
    RIGHT,
    TOP,
    VERTICAL,
    X,
    Y,
    Canvas,
    Listbox,
    Menu,
    N,
    S,
    E,
    W,
    StringVar,
    Tk,
    Toplevel,
    colorchooser,
    filedialog,
    messagebox,
    ttk,
)

from PIL import Image, ImageDraw, ImageFont, ImageGrab, ImageOps, ImageTk


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
DEFAULT_CAPTURE_DIR = APP_DIR / "screenshots"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
THEMES = {
    "light": {
        "app_bg": "#eef2f6",
        "surface": "#ffffff",
        "surface_alt": "#f8fafc",
        "text": "#172033",
        "muted": "#4b5563",
        "border": "#c6ced8",
        "button": "#f8fafc",
        "button_active": "#e8eef6",
        "accent": "#2563eb",
        "accent_active": "#1d4ed8",
        "preview_bg": "#17191c",
        "editor_bg": "#f4f6f8",
        "canvas_bg": "#202124",
        "list_bg": "#ffffff",
        "list_fg": "#172033",
        "select_bg": "#2563eb",
        "select_fg": "#ffffff",
    },
    "dark": {
        "app_bg": "#111827",
        "surface": "#1f2937",
        "surface_alt": "#273244",
        "text": "#f3f4f6",
        "muted": "#cbd5e1",
        "border": "#475569",
        "button": "#334155",
        "button_active": "#475569",
        "accent": "#3b82f6",
        "accent_active": "#2563eb",
        "preview_bg": "#0b1120",
        "editor_bg": "#111827",
        "canvas_bg": "#0b1120",
        "list_bg": "#111827",
        "list_fg": "#e5e7eb",
        "select_bg": "#3b82f6",
        "select_fg": "#ffffff",
    },
}

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
CF_DIB = 8
GMEM_MOVEABLE = 0x0002

MODIFIER_KEYS = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "alt": MOD_ALT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

VK_CODES = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "printscreen": 0x2C,
    "prtsc": 0x2C,
}

for index in range(1, 25):
    VK_CODES[f"f{index}"] = 0x70 + index - 1
for code in range(ord("A"), ord("Z") + 1):
    VK_CODES[chr(code).lower()] = code
for code in range(ord("0"), ord("9") + 1):
    VK_CODES[chr(code)] = code


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "capture_dir": str(DEFAULT_CAPTURE_DIR),
        "hotkey": "ctrl+shift+s",
        "capture_mode": "full",
        "selection_color": "#00d1ff",
        "editor_color": "#ff3030",
        "theme": "light",
    }


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def normalize_hotkey(hotkey: str) -> str:
    parts = [part.strip().lower() for part in hotkey.replace("-", "+").split("+")]
    parts = [part for part in parts if part]
    if not parts:
        raise ValueError("Raccourci vide.")

    modifiers = []
    key = None
    for part in parts:
        if part in MODIFIER_KEYS:
            if part in {"control"}:
                part = "ctrl"
            if part in {"windows"}:
                part = "win"
            if part not in modifiers:
                modifiers.append(part)
        else:
            if key is not None:
                raise ValueError("Un raccourci doit contenir une seule touche principale.")
            key = part

    if key is None:
        raise ValueError("Ajoutez une touche principale, par exemple ctrl+shift+s.")
    if key not in VK_CODES:
        raise ValueError(f"Touche non reconnue: {key}")

    ordered_modifiers = [name for name in ("ctrl", "shift", "alt", "win") if name in modifiers]
    return "+".join([*ordered_modifiers, key])


def parse_hotkey(hotkey: str) -> tuple[int, int]:
    normalized = normalize_hotkey(hotkey)
    modifiers = 0
    key_name = None
    for part in normalized.split("+"):
        if part in MODIFIER_KEYS:
            modifiers |= MODIFIER_KEYS[part]
        else:
            key_name = part
    return modifiers, VK_CODES[key_name]


def display_hotkey(hotkey: str) -> str:
    names = []
    for part in normalize_hotkey(hotkey).split("+"):
        names.append(part.upper() if len(part) == 1 or part.startswith("f") else part.title())
    return "+".join(names)


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.strip()
    if len(color) != 7 or not color.startswith("#"):
        return 255, 48, 48
    try:
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    except ValueError:
        return 255, 48, 48


def valid_hex_color(color: str, fallback: str) -> str:
    color = color.strip()
    if len(color) == 7 and color.startswith("#"):
        try:
            int(color[1:], 16)
            return color.lower()
        except ValueError:
            pass
    return fallback


def copy_image_to_clipboard(image: Image.Image) -> None:
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    dib_data = output.getvalue()[14:]
    output.close()

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p

    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib_data))
    if not handle:
        raise OSError("Impossible d'allouer la memoire du presse-papiers.")

    locked = kernel32.GlobalLock(handle)
    if not locked:
        kernel32.GlobalFree(handle)
        raise OSError("Impossible de verrouiller la memoire du presse-papiers.")

    ctypes.memmove(locked, dib_data, len(dib_data))
    kernel32.GlobalUnlock(handle)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise OSError("Impossible d'ouvrir le presse-papiers.")

    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_DIB, handle):
            kernel32.GlobalFree(handle)
            raise OSError("Impossible de copier l'image dans le presse-papiers.")
        handle = None
    finally:
        user32.CloseClipboard()


def load_marker_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for font_path in font_paths:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = center[0] - (bbox[0] + bbox[2]) / 2
    y = center[1] - (bbox[1] + bbox[3]) / 2
    draw.text((x, y), text, font=font, fill=fill)


def normalize_theme(theme: str) -> str:
    return theme if theme in THEMES else "light"


def apply_app_style(style: ttk.Style, theme: str) -> None:
    palette = THEMES[normalize_theme(theme)]
    style.configure(".", font=("Segoe UI", 10), background=palette["app_bg"], foreground=palette["text"])
    style.configure("TFrame", background=palette["app_bg"])
    style.configure("Surface.TFrame", background=palette["surface"], relief="flat")
    style.configure("TLabel", background=palette["surface"], foreground=palette["text"])
    style.configure("Title.TLabel", background=palette["surface"], foreground=palette["text"], font=("Segoe UI", 12, "bold"))
    style.configure("Status.TLabel", background=palette["surface"], foreground=palette["muted"])
    style.configure("TButton", padding=(10, 6), background=palette["button"], foreground=palette["text"])
    style.map("TButton", background=[("active", palette["button_active"])], foreground=[("active", palette["text"])])
    style.configure("Tool.TButton", padding=(8, 5), background=palette["button"], foreground=palette["text"])
    style.map("Tool.TButton", background=[("active", palette["button_active"])], foreground=[("active", palette["text"])])
    style.configure("Accent.TButton", padding=(12, 7), background=palette["accent"], foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", palette["accent_active"])], foreground=[("active", "#ffffff")])
    style.configure("TRadiobutton", background=palette["surface"], foreground=palette["text"])
    style.map("TRadiobutton", background=[("active", palette["surface"])], foreground=[("active", palette["text"])])
    style.configure("TEntry", padding=5, fieldbackground=palette["surface_alt"], foreground=palette["text"])
    style.configure("TSpinbox", arrowsize=12, fieldbackground=palette["surface_alt"], foreground=palette["text"])


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", ctypes.c_ulong),
        ("pt", ctypes.c_long * 2),
    ]


class HotkeyListener:
    def __init__(self, callback):
        self.callback = callback
        self.thread = None
        self.thread_id = None
        self.command_queue = queue.Queue()
        self.running = threading.Event()
        self.current_hotkey = None
        self.user32 = ctypes.windll.user32

    def start(self, hotkey: str) -> None:
        if self.thread and self.thread.is_alive():
            self.set_hotkey(hotkey)
            return
        self.current_hotkey = hotkey
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.running.wait(timeout=3)

    def set_hotkey(self, hotkey: str) -> None:
        self.current_hotkey = hotkey
        self.command_queue.put(("set_hotkey", hotkey))
        if self.thread_id:
            self.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def stop(self) -> None:
        self.command_queue.put(("stop", None))
        if self.thread_id:
            self.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def _register(self, hotkey: str) -> bool:
        modifiers, vk = parse_hotkey(hotkey)
        self.user32.UnregisterHotKey(None, 1)
        return bool(self.user32.RegisterHotKey(None, 1, modifiers, vk))

    def _run(self) -> None:
        self.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        registered = False
        try:
            registered = self._register(self.current_hotkey)
            self.running.set()
            if not registered:
                self.callback("hotkey_error")
                return

            while True:
                msg = MSG()
                result = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                while not self.command_queue.empty():
                    command, value = self.command_queue.get_nowait()
                    if command == "stop":
                        return
                    if command == "set_hotkey":
                        if not self._register(value):
                            self.callback("hotkey_error")
                if result == 0:
                    continue
                if msg.message == WM_HOTKEY:
                    self.callback("capture")
        finally:
            if registered:
                self.user32.UnregisterHotKey(None, 1)


@dataclass
class EditorState:
    image: Image.Image
    path: Path
    display_image: ImageTk.PhotoImage | None = None
    scale: float = 1.0
    mode: str = "draw"
    crop_start: tuple[int, int] | None = None
    crop_rect: int | None = None
    last_draw_point: tuple[int, int] | None = None


class ImageEditor(Toplevel):
    def __init__(self, master, image_path: Path, on_saved, initial_color: str = "#ff3030", theme: str = "light"):
        super().__init__(master)
        self.title(f"Edition - {image_path.name}")
        self.geometry("1060x760")
        self.minsize(720, 560)
        self.on_saved = on_saved
        self.state = EditorState(Image.open(image_path).convert("RGB"), image_path)
        self.brush_size = StringVar(value="6")
        self.marker_number = StringVar(value="1")
        self.icon_size = StringVar(value="6")
        self.tool_color = StringVar(value=valid_hex_color(initial_color, "#ff3030"))
        self.status = StringVar(value="Selectionnez un outil, puis agissez directement sur l'image.")
        self.theme = normalize_theme(theme)
        self.palette = THEMES[self.theme]
        self.icons = self.build_icons()

        self.configure(background=self.palette["editor_bg"])
        toolbar = ttk.Frame(self, padding=(10, 8), style="Surface.TFrame")
        toolbar.pack(side=TOP, fill=X)
        for column in range(8):
            toolbar.columnconfigure(column, weight=0)
        toolbar.columnconfigure(7, weight=1)

        ttk.Label(toolbar, text="Outils", style="Title.TLabel").grid(row=0, column=0, sticky=W, padx=(0, 10))
        self.icon_button(toolbar, "Dessin", "draw", lambda: self.set_mode("draw")).grid(row=0, column=1, padx=2, pady=2)
        self.icon_button(toolbar, "Cadre", "frame", lambda: self.set_mode("frame")).grid(row=0, column=2, padx=2, pady=2)
        self.icon_button(toolbar, "Recadrer", "crop", lambda: self.set_mode("crop")).grid(row=0, column=3, padx=2, pady=2)
        ttk.Label(toolbar, text="Trait").grid(row=0, column=4, sticky=E, padx=(12, 4))
        ttk.Spinbox(toolbar, from_=1, to=50, width=4, textvariable=self.brush_size).grid(row=0, column=5, padx=2, pady=2)
        self.editor_color_preview = Canvas(
            toolbar,
            width=28,
            height=22,
            background=self.palette["surface"],
            highlightthickness=1,
            highlightbackground=self.palette["border"],
        )
        self.editor_color_preview.grid(row=0, column=6, padx=(12, 4), pady=2)
        self.editor_color_preview.bind("<Button-1>", lambda _event: self.choose_tool_color())
        self.icon_button(toolbar, "Couleur", "color", self.choose_tool_color).grid(row=0, column=7, sticky=W, padx=2, pady=2)

        ttk.Label(toolbar, text="Actions", style="Title.TLabel").grid(row=1, column=0, sticky=W, padx=(0, 10), pady=(6, 0))
        self.icon_button(toolbar, "Gauche", "rotate_left", lambda: self.transform("rotate_left")).grid(row=1, column=1, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Droite", "rotate_right", lambda: self.transform("rotate_right")).grid(row=1, column=2, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Miroir", "flip", lambda: self.transform("flip")).grid(row=1, column=3, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Gris", "gray", lambda: self.transform("gray")).grid(row=1, column=4, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Copier", "copy", self.copy_current_image).grid(row=1, column=5, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Copie", "save_copy", self.save_copy).grid(row=1, column=6, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Sauver", "save", self.save, style="Accent.TButton").grid(row=1, column=7, sticky=W, padx=2, pady=(6, 2))

        ttk.Label(toolbar, text="Logos", style="Title.TLabel").grid(row=2, column=0, sticky=W, padx=(0, 10), pady=(6, 0))
        self.icon_button(toolbar, "Numero", "number", lambda: self.set_mode("number")).grid(row=2, column=1, padx=2, pady=(6, 2))
        ttk.Label(toolbar, text="N").grid(row=2, column=2, sticky=E, padx=(4, 2), pady=(6, 2))
        ttk.Spinbox(toolbar, from_=1, to=999, width=5, textvariable=self.marker_number).grid(row=2, column=3, sticky=W, padx=2, pady=(6, 2))
        ttk.Label(toolbar, text="Taille logo").grid(row=2, column=4, sticky=E, padx=(8, 2), pady=(6, 2))
        ttk.Spinbox(toolbar, from_=1, to=50, width=4, textvariable=self.icon_size).grid(row=2, column=5, sticky=W, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Warning", "warning", lambda: self.set_mode("warning")).grid(row=3, column=1, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Interdit", "forbidden", lambda: self.set_mode("forbidden")).grid(row=3, column=2, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Info", "info", lambda: self.set_mode("info")).grid(row=3, column=3, padx=2, pady=(6, 2))
        self.icon_button(toolbar, "Valide", "check", lambda: self.set_mode("check")).grid(row=3, column=4, padx=2, pady=(6, 2))

        self.canvas = Canvas(self, background=self.palette["canvas_bg"], highlightthickness=0)
        self.canvas.pack(side=TOP, fill=BOTH, expand=True)
        ttk.Label(self, textvariable=self.status, anchor=W, padding=(10, 5)).pack(side=BOTTOM, fill=X)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Configure>", lambda _event: self.render())
        self.update_color_preview()
        self.render()

    def icon_button(self, parent, text: str, icon_name: str, command, style: str = "Tool.TButton") -> ttk.Button:
        return ttk.Button(
            parent,
            text=text,
            image=self.icons[icon_name],
            compound=LEFT,
            command=command,
            style=style,
        )

    def build_icons(self) -> dict[str, ImageTk.PhotoImage]:
        return {name: ImageTk.PhotoImage(self.draw_toolbar_icon(name)) for name in (
            "draw",
            "frame",
            "crop",
            "color",
            "rotate_left",
            "rotate_right",
            "flip",
            "gray",
            "copy",
            "save_copy",
            "save",
            "number",
            "warning",
            "forbidden",
            "info",
            "check",
        )}

    def draw_toolbar_icon(self, name: str) -> Image.Image:
        image = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        blue = (37, 99, 235, 255)
        slate = (71, 85, 105, 255)
        red = (220, 38, 38, 255)
        amber = (245, 158, 11, 255)
        green = (22, 163, 74, 255)

        if name == "draw":
            draw.line((5, 18, 16, 7), fill=blue, width=4)
            draw.polygon(((14, 5), (19, 10), (16, 7)), fill=slate)
        elif name == "frame":
            draw.rectangle((5, 5, 19, 19), outline=blue, width=3)
        elif name == "crop":
            draw.line((7, 3, 7, 17, 21, 17), fill=slate, width=3)
            draw.line((3, 7, 17, 7, 17, 21), fill=blue, width=3)
        elif name == "color":
            draw.ellipse((4, 4, 20, 20), fill=(255, 255, 255, 255), outline=slate, width=2)
            draw.pieslice((5, 5, 19, 19), 20, 140, fill=red)
            draw.pieslice((5, 5, 19, 19), 140, 260, fill=blue)
            draw.pieslice((5, 5, 19, 19), 260, 20, fill=green)
        elif name in {"rotate_left", "rotate_right"}:
            if name == "rotate_left":
                draw.arc((5, 5, 19, 19), 40, 320, fill=blue, width=3)
                draw.polygon(((4, 8), (10, 5), (9, 12)), fill=blue)
            else:
                draw.arc((5, 5, 19, 19), 220, 140, fill=blue, width=3)
                draw.polygon(((20, 8), (14, 5), (15, 12)), fill=blue)
        elif name == "flip":
            draw.polygon(((5, 5), (11, 12), (5, 19)), outline=blue, fill=None)
            draw.polygon(((19, 5), (13, 12), (19, 19)), outline=blue, fill=None)
            draw.line((12, 4, 12, 20), fill=slate, width=2)
        elif name == "gray":
            draw.rectangle((5, 5, 19, 19), fill=(226, 232, 240, 255), outline=slate, width=2)
            draw.rectangle((12, 5, 19, 19), fill=(71, 85, 105, 255))
        elif name == "copy":
            draw.rectangle((7, 5, 17, 15), outline=slate, width=2)
            draw.rectangle((4, 9, 14, 19), outline=blue, width=2)
        elif name in {"save", "save_copy"}:
            draw.rectangle((5, 4, 19, 20), fill=blue, outline=(30, 64, 175, 255), width=1)
            draw.rectangle((8, 5, 16, 10), fill=(219, 234, 254, 255))
            draw.rectangle((8, 15, 16, 20), fill=(255, 255, 255, 255))
            if name == "save_copy":
                draw.rectangle((2, 7, 8, 17), outline=slate, width=1)
        elif name == "number":
            font = load_marker_font(11)
            draw.ellipse((3, 3, 21, 21), fill=blue, outline=(255, 255, 255, 255), width=2)
            draw_centered_text(draw, (12, 12), "1", font, (255, 255, 255))
        elif name == "warning":
            draw.polygon(((12, 3), (3, 21), (21, 21)), fill=amber, outline=(120, 53, 15, 255))
            draw_centered_text(draw, (12, 15), "!", load_marker_font(15), (30, 41, 59))
        elif name == "forbidden":
            draw.ellipse((4, 4, 20, 20), outline=red, width=4)
            draw.line((7, 17, 17, 7), fill=red, width=4)
        elif name == "info":
            draw.ellipse((4, 4, 20, 20), fill=blue, outline=(255, 255, 255, 255), width=2)
            draw_centered_text(draw, (12, 12), "i", load_marker_font(15), (255, 255, 255))
        elif name == "check":
            draw.ellipse((4, 4, 20, 20), fill=green, outline=(255, 255, 255, 255), width=2)
            draw.line((7, 12, 11, 16, 18, 8), fill=(255, 255, 255, 255), width=3)

        return image

    def set_mode(self, mode: str) -> None:
        self.state.mode = mode
        labels = {
            "crop": "Recadrage actif: tirez un rectangle sur l'image.",
            "draw": "Dessin actif: maintenez le clic pour tracer.",
            "frame": "Cadre actif: tirez un rectangle sur l'image.",
            "number": "Numero actif: cliquez pour placer le marqueur. Le numero avance automatiquement.",
            "warning": "Warning actif: cliquez pour placer le pictogramme.",
            "forbidden": "Interdit actif: cliquez pour placer le pictogramme.",
            "info": "Info actif: cliquez pour placer le pictogramme.",
            "check": "Valide actif: cliquez pour placer le pictogramme.",
        }
        self.canvas.configure(cursor="crosshair" if mode != "draw" else "arrow")
        self.status.set(labels.get(mode, "Mode dessin"))

    def choose_tool_color(self) -> None:
        _rgb, color = colorchooser.askcolor(color=self.tool_color.get(), title="Couleur de l'outil")
        if color:
            self.tool_color.set(color.lower())
            self.update_color_preview()

    def update_color_preview(self) -> None:
        self.editor_color_preview.delete("all")
        self.editor_color_preview.create_rectangle(2, 2, 26, 20, fill=self.tool_color.get(), outline=self.tool_color.get())

    def transform(self, action: str) -> None:
        if action == "rotate_left":
            self.state.image = self.state.image.rotate(90, expand=True)
        elif action == "rotate_right":
            self.state.image = self.state.image.rotate(-90, expand=True)
        elif action == "flip":
            self.state.image = ImageOps.mirror(self.state.image)
        elif action == "gray":
            self.state.image = ImageOps.grayscale(self.state.image).convert("RGB")
        self.render()

    def canvas_to_image(self, x: int, y: int) -> tuple[int, int]:
        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        image_width, image_height = self.state.image.size
        displayed_width = image_width * self.state.scale
        displayed_height = image_height * self.state.scale
        offset_x = (canvas_width - displayed_width) / 2
        offset_y = (canvas_height - displayed_height) / 2
        image_x = int((x - offset_x) / self.state.scale)
        image_y = int((y - offset_y) / self.state.scale)
        image_x = max(0, min(image_width - 1, image_x))
        image_y = max(0, min(image_height - 1, image_y))
        return image_x, image_y

    def image_to_canvas(self, x: int, y: int) -> tuple[int, int]:
        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        image_width, image_height = self.state.image.size
        displayed_width = image_width * self.state.scale
        displayed_height = image_height * self.state.scale
        offset_x = (canvas_width - displayed_width) / 2
        offset_y = (canvas_height - displayed_height) / 2
        return int(offset_x + x * self.state.scale), int(offset_y + y * self.state.scale)

    def on_press(self, event) -> None:
        point = self.canvas_to_image(event.x, event.y)
        if self.state.mode in {"crop", "frame"}:
            self.state.crop_start = point
            if self.state.crop_rect:
                self.canvas.delete(self.state.crop_rect)
                self.state.crop_rect = None
        elif self.state.mode in {"number", "warning", "forbidden", "info", "check"}:
            self.place_marker(point)
        else:
            self.state.last_draw_point = point

    def marker_size(self) -> int:
        try:
            value = int(self.icon_size.get() or 1)
        except ValueError:
            value = 6
        return max(28, min(180, value * 6))

    def next_marker_number(self) -> str:
        value = self.marker_number.get().strip() or "1"
        try:
            number = max(1, int(value))
        except ValueError:
            number = 1
        self.marker_number.set(str(number + 1))
        return str(number)

    def place_marker(self, center: tuple[int, int]) -> None:
        mode = self.state.mode
        size = self.marker_size()
        color = hex_to_rgb(self.tool_color.get())
        if mode == "number":
            marker = self.create_number_marker(size, color, self.next_marker_number())
        elif mode == "warning":
            marker = self.create_warning_marker(size)
        elif mode == "forbidden":
            marker = self.create_forbidden_marker(size)
        elif mode == "info":
            marker = self.create_info_marker(size)
        elif mode == "check":
            marker = self.create_check_marker(size)
        else:
            return
        self.paste_marker(marker, center)
        self.status.set("Logo ajoute")
        self.render()

    def marker_canvas(self, size: int, scale: int = 4) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
        canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
        return canvas, ImageDraw.Draw(canvas), scale

    def finish_marker(self, marker: Image.Image, size: int) -> Image.Image:
        return marker.resize((size, size), Image.Resampling.LANCZOS)

    def paste_marker(self, marker: Image.Image, center: tuple[int, int]) -> None:
        x = center[0] - marker.width // 2
        y = center[1] - marker.height // 2
        image_width, image_height = self.state.image.size
        left = max(0, x)
        top = max(0, y)
        right = min(image_width, x + marker.width)
        bottom = min(image_height, y + marker.height)
        if right <= left or bottom <= top:
            return
        marker_crop = marker.crop((left - x, top - y, right - x, bottom - y))
        self.state.image.paste(marker_crop, (left, top), marker_crop)

    def create_number_marker(self, size: int, color: tuple[int, int, int], number: str) -> Image.Image:
        marker, draw, scale = self.marker_canvas(size)
        s = size * scale
        pad = max(3 * scale, int(s * 0.06))
        shadow = int(s * 0.04)
        outline_width = max(3 * scale, int(s * 0.08))
        draw.ellipse((pad + shadow, pad + shadow, s - pad + shadow, s - pad + shadow), fill=(0, 0, 0, 70))
        draw.ellipse((pad, pad, s - pad, s - pad), fill=(*color, 255), outline=(255, 255, 255, 255), width=outline_width)
        font_size = int(s * (0.48 if len(number) <= 2 else 0.38))
        font = load_marker_font(max(12, font_size))
        draw_centered_text(draw, (s // 2, s // 2), number, font, (255, 255, 255))
        return self.finish_marker(marker, size)

    def create_warning_marker(self, size: int) -> Image.Image:
        marker, draw, scale = self.marker_canvas(size)
        s = size * scale
        pad = int(s * 0.09)
        outline_width = max(3 * scale, int(s * 0.055))
        points = [(s // 2, pad), (s - pad, s - pad), (pad, s - pad)]
        shadow = int(s * 0.035)
        shadow_points = [(x + shadow, y + shadow) for x, y in points]
        draw.polygon(shadow_points, fill=(0, 0, 0, 70))
        draw.polygon(points, fill=(245, 158, 11, 255))
        draw.line([points[0], points[1], points[2], points[0]], fill=(120, 53, 15, 255), width=outline_width, joint="curve")
        font = load_marker_font(int(s * 0.62))
        draw_centered_text(draw, (s // 2, int(s * 0.63)), "!", font, (30, 41, 59))
        return self.finish_marker(marker, size)

    def create_forbidden_marker(self, size: int) -> Image.Image:
        marker, draw, scale = self.marker_canvas(size)
        s = size * scale
        pad = int(s * 0.12)
        width = max(5 * scale, int(s * 0.13))
        box = (pad, pad, s - pad, s - pad)
        shadow = int(s * 0.035)
        draw.ellipse((pad + shadow, pad + shadow, s - pad + shadow, s - pad + shadow), outline=(0, 0, 0, 80), width=width)
        draw.ellipse(box, fill=(255, 255, 255, 230), outline=(220, 38, 38, 255), width=width)
        offset = int(s * 0.29)
        draw.line((s // 2 - offset, s // 2 + offset, s // 2 + offset, s // 2 - offset), fill=(220, 38, 38, 255), width=width)
        return self.finish_marker(marker, size)

    def create_info_marker(self, size: int) -> Image.Image:
        marker, draw, scale = self.marker_canvas(size)
        s = size * scale
        pad = int(s * 0.08)
        outline_width = max(3 * scale, int(s * 0.055))
        shadow = int(s * 0.04)
        draw.ellipse((pad + shadow, pad + shadow, s - pad + shadow, s - pad + shadow), fill=(0, 0, 0, 70))
        draw.ellipse((pad, pad, s - pad, s - pad), fill=(37, 99, 235, 255), outline=(255, 255, 255, 255), width=outline_width)
        font = load_marker_font(int(s * 0.64))
        draw_centered_text(draw, (s // 2, int(s * 0.53)), "i", font, (255, 255, 255))
        return self.finish_marker(marker, size)

    def create_check_marker(self, size: int) -> Image.Image:
        marker, draw, scale = self.marker_canvas(size)
        s = size * scale
        pad = int(s * 0.08)
        outline_width = max(3 * scale, int(s * 0.055))
        shadow = int(s * 0.04)
        draw.ellipse((pad + shadow, pad + shadow, s - pad + shadow, s - pad + shadow), fill=(0, 0, 0, 70))
        draw.ellipse((pad, pad, s - pad, s - pad), fill=(22, 163, 74, 255), outline=(255, 255, 255, 255), width=outline_width)
        width = max(5 * scale, int(s * 0.1))
        points = [
            (int(s * 0.28), int(s * 0.52)),
            (int(s * 0.43), int(s * 0.67)),
            (int(s * 0.73), int(s * 0.35)),
        ]
        draw.line(points, fill=(255, 255, 255, 255), width=width, joint="curve")
        return self.finish_marker(marker, size)

    def on_drag(self, event) -> None:
        point = self.canvas_to_image(event.x, event.y)
        if self.state.mode in {"crop", "frame"} and self.state.crop_start:
            if self.state.crop_rect:
                self.canvas.delete(self.state.crop_rect)
            x1, y1 = self.image_to_canvas(*self.state.crop_start)
            x2, y2 = self.image_to_canvas(*point)
            self.state.crop_rect = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline=self.tool_color.get(),
                width=2,
            )
        elif self.state.mode == "draw" and self.state.last_draw_point:
            draw = ImageDraw.Draw(self.state.image)
            size = max(1, int(self.brush_size.get() or 1))
            draw.line([self.state.last_draw_point, point], fill=hex_to_rgb(self.tool_color.get()), width=size)
            self.state.last_draw_point = point
            self.render()

    def on_release(self, event) -> None:
        if self.state.mode in {"crop", "frame"} and self.state.crop_start:
            end = self.canvas_to_image(event.x, event.y)
            x_values = sorted((self.state.crop_start[0], end[0]))
            y_values = sorted((self.state.crop_start[1], end[1]))
            if x_values[1] - x_values[0] > 10 and y_values[1] - y_values[0] > 10:
                if self.state.mode == "crop":
                    self.state.image = self.state.image.crop((x_values[0], y_values[0], x_values[1], y_values[1]))
                    self.status.set("Image recadree")
                else:
                    draw = ImageDraw.Draw(self.state.image)
                    size = max(1, int(self.brush_size.get() or 1))
                    draw.rectangle(
                        (x_values[0], y_values[0], x_values[1], y_values[1]),
                        outline=hex_to_rgb(self.tool_color.get()),
                        width=size,
                    )
                    self.status.set("Cadre ajoute")
            self.state.crop_start = None
            self.state.crop_rect = None
            self.render()
        self.state.last_draw_point = None

    def render(self) -> None:
        if not self.canvas.winfo_exists():
            return
        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        image_width, image_height = self.state.image.size
        self.state.scale = min(canvas_width / image_width, canvas_height / image_height, 1.0)
        display_size = (max(1, int(image_width * self.state.scale)), max(1, int(image_height * self.state.scale)))
        preview = self.state.image.resize(display_size, Image.Resampling.LANCZOS)
        self.state.display_image = ImageTk.PhotoImage(preview)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.state.display_image)

    def save(self) -> None:
        self.state.image.save(self.state.path)
        self.status.set(f"Sauvegarde: {self.state.path.name}")
        self.on_saved(self.state.path)

    def save_copy(self) -> None:
        stem = self.state.path.stem
        target = self.state.path.with_name(f"{stem}_edit_{datetime.now():%Y%m%d_%H%M%S}.png")
        self.state.image.save(target)
        self.status.set(f"Copie sauvegardee: {target.name}")
        self.on_saved(target)

    def copy_current_image(self) -> None:
        try:
            copy_image_to_clipboard(self.state.image)
        except OSError as error:
            messagebox.showerror("Copie impossible", str(error))
            return
        self.status.set("Image copiee dans le presse-papiers")


class AreaSelector(Toplevel):
    def __init__(self, master, on_selected, on_cancelled, rectangle_color: str):
        super().__init__(master)
        self.on_selected = on_selected
        self.on_cancelled = on_cancelled
        self.rectangle_color = valid_hex_color(rectangle_color, "#00d1ff")
        self.start = None
        self.rect = None

        left = ctypes.windll.user32.GetSystemMetrics(76)
        top = ctypes.windll.user32.GetSystemMetrics(77)
        width = ctypes.windll.user32.GetSystemMetrics(78)
        height = ctypes.windll.user32.GetSystemMetrics(79)
        self.geometry(f"{width}x{height}+{left}+{top}")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.32)

        self.canvas = Canvas(self, cursor="crosshair", background="black", highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=True)
        self.canvas.create_text(
            width // 2,
            36,
            fill="white",
            text="Selectionnez une zone avec la souris. Echap pour annuler.",
            font=("Segoe UI", 14),
        )
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda _event: self.cancel())
        self.focus_force()
        self.grab_set()

    def on_press(self, event) -> None:
        self.start = (event.x_root, event.y_root)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline=self.rectangle_color,
            width=3,
        )

    def on_drag(self, event) -> None:
        if not self.start or not self.rect:
            return
        start_x = self.start[0] - self.winfo_rootx()
        start_y = self.start[1] - self.winfo_rooty()
        self.canvas.coords(self.rect, start_x, start_y, event.x, event.y)

    def on_release(self, event) -> None:
        if not self.start:
            self.cancel()
            return
        x_values = sorted((self.start[0], event.x_root))
        y_values = sorted((self.start[1], event.y_root))
        self.grab_release()
        self.destroy()
        if x_values[1] - x_values[0] < 10 or y_values[1] - y_values[0] < 10:
            self.on_cancelled()
            return
        self.on_selected((x_values[0], y_values[0], x_values[1], y_values[1]))

    def cancel(self) -> None:
        self.grab_release()
        self.destroy()
        self.on_cancelled()


class ScreenshotManager:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Gestionnaire de screenshots")
        self.root.geometry("1100x720")
        self.root.minsize(880, 560)
        self.config = load_config()
        self.capture_dir = Path(self.config["capture_dir"])
        self.hotkey_var = StringVar(value=normalize_hotkey(self.config["hotkey"]))
        capture_mode = self.config.get("capture_mode", "full")
        if capture_mode not in {"full", "area"}:
            capture_mode = "full"
        self.capture_mode_var = StringVar(value=capture_mode)
        self.selection_color_var = StringVar(value=valid_hex_color(self.config.get("selection_color", ""), "#00d1ff"))
        self.editor_color_var = StringVar(value=valid_hex_color(self.config.get("editor_color", ""), "#ff3030"))
        self.theme_var = StringVar(value=normalize_theme(self.config.get("theme", "light")))
        self.folder_var = StringVar(value=str(self.capture_dir))
        self.status_var = StringVar(value="")
        self.preview_image = None
        self.history_paths: list[Path] = []
        self.hotkey_listener = HotkeyListener(self.handle_hotkey_event)

        self.build_ui()
        self.ensure_capture_dir()
        self.refresh_history()
        self.start_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_ui(self) -> None:
        palette = THEMES[self.theme_var.get()]
        apply_app_style(ttk.Style(self.root), self.theme_var.get())
        self.root.configure(background=palette["app_bg"])
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        settings = ttk.Frame(self.root, padding=(14, 12), style="Surface.TFrame")
        settings.grid(row=0, column=0, columnspan=2, sticky=E + W, padx=12, pady=(12, 6))
        settings.columnconfigure(1, weight=1)

        ttk.Label(settings, text="Dossier").grid(row=0, column=0, sticky=W, padx=(0, 8))
        ttk.Entry(settings, textvariable=self.folder_var).grid(row=0, column=1, sticky=E + W)
        ttk.Button(settings, text="Choisir", command=self.choose_folder).grid(row=0, column=2, padx=8)
        ttk.Button(settings, text="Ouvrir", command=self.open_folder).grid(row=0, column=3)

        ttk.Label(settings, text="Raccourci").grid(row=1, column=0, sticky=W, padx=(0, 8), pady=(10, 0))
        ttk.Entry(settings, textvariable=self.hotkey_var, width=24).grid(row=1, column=1, sticky=W, pady=(10, 0))
        ttk.Button(settings, text="Appliquer", command=self.apply_settings).grid(row=1, column=2, padx=8, pady=(10, 0))
        ttk.Button(settings, text="Capture mode choisi", style="Accent.TButton", command=self.take_screenshot).grid(
            row=1,
            column=3,
            pady=(10, 0),
        )

        mode_frame = ttk.Frame(settings, style="Surface.TFrame")
        mode_frame.grid(row=2, column=1, sticky=W, pady=(8, 0))
        ttk.Radiobutton(mode_frame, text="Ecran complet", variable=self.capture_mode_var, value="full").pack(side=LEFT)
        ttk.Radiobutton(mode_frame, text="Zone", variable=self.capture_mode_var, value="area").pack(side=LEFT, padx=(12, 0))
        ttk.Button(settings, text="Tout l'ecran", command=self.take_full_screenshot).grid(row=2, column=2, padx=8, pady=(8, 0))
        ttk.Button(settings, text="Selection zone", command=self.start_area_screenshot).grid(row=2, column=3, pady=(8, 0))
        self.theme_button = ttk.Button(settings, text=self.theme_button_text(), command=self.toggle_theme)
        self.theme_button.grid(row=3, column=0, sticky=W, pady=(10, 0), padx=(0, 8))

        color_frame = ttk.Frame(settings, style="Surface.TFrame")
        color_frame.grid(row=3, column=1, columnspan=3, sticky=W, pady=(10, 0))
        ttk.Label(color_frame, text="Rectangle zone").pack(side=LEFT)
        self.selection_color_preview = Canvas(
            color_frame,
            width=28,
            height=22,
            background=palette["surface"],
            highlightthickness=1,
            highlightbackground=palette["border"],
        )
        self.selection_color_preview.pack(side=LEFT, padx=(8, 4))
        self.selection_color_preview.bind("<Button-1>", lambda _event: self.choose_selection_color())
        ttk.Button(color_frame, text="Couleur", command=self.choose_selection_color).pack(side=LEFT, padx=(0, 18))
        ttk.Label(color_frame, text="Edition").pack(side=LEFT)
        self.default_editor_color_preview = Canvas(
            color_frame,
            width=28,
            height=22,
            background=palette["surface"],
            highlightthickness=1,
            highlightbackground=palette["border"],
        )
        self.default_editor_color_preview.pack(side=LEFT, padx=(8, 4))
        self.default_editor_color_preview.bind("<Button-1>", lambda _event: self.choose_editor_color())
        ttk.Button(color_frame, text="Couleur", command=self.choose_editor_color).pack(side=LEFT)

        left_panel = ttk.Frame(self.root, padding=(12, 10), style="Surface.TFrame")
        left_panel.grid(row=1, column=0, sticky=N + S + W, padx=(12, 6), pady=6)
        left_panel.rowconfigure(1, weight=1)

        ttk.Label(left_panel, text="Historique", style="Title.TLabel").grid(row=0, column=0, sticky=W, pady=(0, 8))
        list_frame = ttk.Frame(left_panel, style="Surface.TFrame")
        list_frame.grid(row=1, column=0, sticky=N + S + E + W)
        self.history_list = Listbox(
            list_frame,
            width=36,
            exportselection=False,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=palette["border"],
            background=palette["list_bg"],
            foreground=palette["list_fg"],
            selectbackground=palette["select_bg"],
            selectforeground=palette["select_fg"],
            activestyle="none",
        )
        self.history_list.pack(side=LEFT, fill=Y)
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.history_list.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.history_list.configure(yscrollcommand=scrollbar.set)
        self.history_list.bind("<<ListboxSelect>>", lambda _event: self.show_selected())
        self.history_list.bind("<Double-Button-1>", lambda _event: self.edit_selected())

        ttk.Button(left_panel, text="Rafraichir", command=self.refresh_history).grid(row=2, column=0, sticky=E + W, pady=(10, 0))
        ttk.Button(left_panel, text="Copier l'image", command=self.copy_selected_image).grid(row=3, column=0, sticky=E + W, pady=(6, 0))
        ttk.Button(left_panel, text="Modifier l'image", command=self.edit_selected).grid(row=4, column=0, sticky=E + W, pady=(6, 0))
        ttk.Button(left_panel, text="Supprimer", command=self.delete_selected_image).grid(row=5, column=0, sticky=E + W, pady=(6, 0))

        preview_panel = ttk.Frame(self.root, padding=(12, 10), style="Surface.TFrame")
        preview_panel.grid(row=1, column=1, sticky=N + S + E + W, padx=(6, 12), pady=6)
        preview_panel.rowconfigure(0, weight=1)
        preview_panel.columnconfigure(0, weight=1)
        self.preview_canvas = Canvas(preview_panel, background=palette["preview_bg"], highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky=N + S + E + W)
        self.preview_canvas.bind("<Configure>", lambda _event: self.show_selected())

        status = ttk.Label(self.root, textvariable=self.status_var, anchor=W, padding=(14, 7), style="Status.TLabel")
        status.grid(row=2, column=0, columnspan=2, sticky=E + W, padx=12, pady=(6, 12))

        menu = Menu(self.root)
        file_menu = Menu(menu, tearoff=False)
        file_menu.add_command(label="Capture mode choisi", command=self.take_screenshot)
        file_menu.add_command(label="Tout l'ecran", command=self.take_full_screenshot)
        file_menu.add_command(label="Selection zone", command=self.start_area_screenshot)
        file_menu.add_command(label="Copier l'image selectionnee", command=self.copy_selected_image)
        file_menu.add_command(label="Supprimer l'image selectionnee", command=self.delete_selected_image)
        file_menu.add_command(label="Rafraichir", command=self.refresh_history)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.close)
        menu.add_cascade(label="Fichier", menu=file_menu)
        self.root.config(menu=menu)
        self.update_main_color_previews()

    def ensure_capture_dir(self) -> None:
        self.capture_dir = Path(self.folder_var.get()).expanduser()
        self.capture_dir.mkdir(parents=True, exist_ok=True)

    def apply_settings(self) -> None:
        try:
            normalized_hotkey = normalize_hotkey(self.hotkey_var.get())
            self.hotkey_var.set(normalized_hotkey)
            self.ensure_capture_dir()
        except (OSError, ValueError) as error:
            messagebox.showerror("Configuration invalide", str(error))
            return

        self.config["capture_dir"] = str(self.capture_dir)
        self.config["hotkey"] = normalized_hotkey
        self.config["capture_mode"] = self.capture_mode_var.get()
        self.config["selection_color"] = self.selection_color_var.get()
        self.config["editor_color"] = self.editor_color_var.get()
        self.config["theme"] = self.theme_var.get()
        save_config(self.config)
        self.hotkey_listener.set_hotkey(normalized_hotkey)
        self.refresh_history()
        self.status_var.set(f"Configuration sauvegardee. Raccourci actif: {display_hotkey(normalized_hotkey)}")

    def theme_button_text(self) -> str:
        return "Theme clair" if self.theme_var.get() == "dark" else "Theme sombre"

    def toggle_theme(self) -> None:
        self.theme_var.set("dark" if self.theme_var.get() == "light" else "light")
        self.config["theme"] = self.theme_var.get()
        save_config(self.config)
        self.apply_theme()
        self.status_var.set("Theme sombre active." if self.theme_var.get() == "dark" else "Theme clair active.")

    def apply_theme(self) -> None:
        theme = self.theme_var.get()
        palette = THEMES[theme]
        apply_app_style(ttk.Style(self.root), theme)
        self.root.configure(background=palette["app_bg"])
        self.theme_button.configure(text=self.theme_button_text())
        self.history_list.configure(
            background=palette["list_bg"],
            foreground=palette["list_fg"],
            highlightbackground=palette["border"],
            selectbackground=palette["select_bg"],
            selectforeground=palette["select_fg"],
        )
        self.preview_canvas.configure(background=palette["preview_bg"])
        for preview in (self.selection_color_preview, self.default_editor_color_preview):
            preview.configure(background=palette["surface"], highlightbackground=palette["border"])
        self.update_main_color_previews()

    def choose_selection_color(self) -> None:
        _rgb, color = colorchooser.askcolor(color=self.selection_color_var.get(), title="Couleur du rectangle de zone")
        if color:
            self.selection_color_var.set(color.lower())
            self.update_main_color_previews()
            self.apply_settings()

    def choose_editor_color(self) -> None:
        _rgb, color = colorchooser.askcolor(color=self.editor_color_var.get(), title="Couleur par defaut de l'edition")
        if color:
            self.editor_color_var.set(color.lower())
            self.update_main_color_previews()
            self.apply_settings()

    def update_main_color_previews(self) -> None:
        for preview, color_var in (
            (self.selection_color_preview, self.selection_color_var),
            (self.default_editor_color_preview, self.editor_color_var),
        ):
            preview.delete("all")
            preview.create_rectangle(2, 2, 26, 20, fill=color_var.get(), outline=color_var.get())

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self.capture_dir if self.capture_dir.exists() else APP_DIR))
        if selected:
            self.folder_var.set(selected)
            self.apply_settings()

    def open_folder(self) -> None:
        self.ensure_capture_dir()
        ctypes.windll.shell32.ShellExecuteW(None, "open", str(self.capture_dir), None, None, 1)

    def start_hotkey(self) -> None:
        try:
            self.hotkey_listener.start(self.hotkey_var.get())
            self.status_var.set(f"Pret. Raccourci actif: {display_hotkey(self.hotkey_var.get())}")
        except ValueError as error:
            self.status_var.set(str(error))

    def handle_hotkey_event(self, event: str) -> None:
        if event == "capture":
            self.root.after(0, self.take_screenshot)
        elif event == "hotkey_error":
            self.root.after(
                0,
                lambda: messagebox.showwarning(
                    "Raccourci indisponible",
                    "Le raccourci global n'a pas pu etre enregistre. Essayez une autre combinaison.",
                ),
            )

    def take_screenshot(self) -> None:
        if self.capture_mode_var.get() == "area":
            self.start_area_screenshot()
        else:
            self.take_full_screenshot()

    def take_full_screenshot(self) -> None:
        try:
            self.ensure_capture_dir()
            image = ImageGrab.grab(all_screens=True)
            target = self.save_capture(image, "screenshot_full")
        except Exception as error:
            messagebox.showerror("Capture impossible", str(error))
            return
        self.status_var.set(f"Capture sauvegardee: {target.name}")
        self.refresh_history(select_path=target)

    def start_area_screenshot(self) -> None:
        self.ensure_capture_dir()
        self.status_var.set("Selectionnez une zone a capturer.")
        self.root.withdraw()
        self.root.after(
            180,
            lambda: AreaSelector(
                self.root,
                self.finish_area_screenshot,
                self.cancel_area_screenshot,
                self.selection_color_var.get(),
            ),
        )

    def finish_area_screenshot(self, bbox: tuple[int, int, int, int]) -> None:
        try:
            virtual_left = ctypes.windll.user32.GetSystemMetrics(76)
            virtual_top = ctypes.windll.user32.GetSystemMetrics(77)
            image = ImageGrab.grab(all_screens=True)
            crop_box = (
                bbox[0] - virtual_left,
                bbox[1] - virtual_top,
                bbox[2] - virtual_left,
                bbox[3] - virtual_top,
            )
            target = self.save_capture(image.crop(crop_box), "screenshot_zone")
        except Exception as error:
            self.root.deiconify()
            self.root.lift()
            messagebox.showerror("Capture impossible", str(error))
            return
        self.root.deiconify()
        self.root.lift()
        self.status_var.set(f"Zone sauvegardee: {target.name}")
        self.refresh_history(select_path=target)

    def cancel_area_screenshot(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.status_var.set("Capture de zone annulee.")

    def save_capture(self, image: Image.Image, prefix: str) -> Path:
        target = self.capture_dir / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.png"
        image.save(target)
        return target

    def refresh_history(self, select_path: Path | None = None) -> None:
        self.ensure_capture_dir()
        self.history_paths = sorted(
            [path for path in self.capture_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        self.history_list.delete(0, END)
        for path in self.history_paths:
            modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.history_list.insert(END, f"{modified}  {path.name}")

        if self.history_paths:
            index = 0
            if select_path:
                try:
                    index = self.history_paths.index(select_path)
                except ValueError:
                    index = 0
            self.history_list.selection_clear(0, END)
            self.history_list.selection_set(index)
            self.history_list.activate(index)
            self.show_selected()
        else:
            self.preview_canvas.delete("all")
            self.status_var.set("Aucune image dans le dossier.")

    def selected_path(self) -> Path | None:
        selection = self.history_list.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self.history_paths):
            return None
        return self.history_paths[index]

    def show_selected(self) -> None:
        path = self.selected_path()
        self.preview_canvas.delete("all")
        if not path or not path.exists():
            return
        try:
            image = Image.open(path).convert("RGB")
        except OSError as error:
            self.status_var.set(str(error))
            return

        canvas_width = max(self.preview_canvas.winfo_width(), 1)
        canvas_height = max(self.preview_canvas.winfo_height(), 1)
        scale = min(canvas_width / image.width, canvas_height / image.height, 1.0)
        size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        image.thumbnail(size, Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(image)
        self.preview_canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.preview_image)
        self.status_var.set(f"Selection: {path.name}")

    def edit_selected(self) -> None:
        path = self.selected_path()
        if not path:
            messagebox.showinfo("Edition", "Selectionnez une image dans l'historique.")
            return
        ImageEditor(self.root, path, self.after_edit_saved, self.editor_color_var.get(), self.theme_var.get())

    def copy_selected_image(self) -> None:
        path = self.selected_path()
        if not path:
            messagebox.showinfo("Copie", "Selectionnez une image dans l'historique.")
            return
        try:
            image = Image.open(path).convert("RGB")
            copy_image_to_clipboard(image)
        except (OSError, ValueError) as error:
            messagebox.showerror("Copie impossible", str(error))
            return
        self.status_var.set(f"Image copiee dans le presse-papiers: {path.name}")

    def delete_selected_image(self) -> None:
        path = self.selected_path()
        if not path:
            messagebox.showinfo("Suppression", "Selectionnez une image dans l'historique.")
            return
        if not path.exists():
            self.refresh_history()
            self.status_var.set("Image introuvable, historique rafraichi.")
            return

        confirmed = messagebox.askyesno(
            "Supprimer l'image",
            f"Supprimer definitivement cette image ?\n\n{path.name}",
        )
        if not confirmed:
            return

        try:
            path.unlink()
        except OSError as error:
            messagebox.showerror("Suppression impossible", str(error))
            return

        self.preview_image = None
        self.preview_canvas.delete("all")
        self.refresh_history()
        self.status_var.set(f"Image supprimee: {path.name}")

    def after_edit_saved(self, path: Path) -> None:
        self.refresh_history(select_path=path)

    def close(self) -> None:
        self.hotkey_listener.stop()
        self.root.destroy()


def main() -> None:
    root = Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    apply_app_style(style, normalize_theme(load_config().get("theme", "light")))
    ScreenshotManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
