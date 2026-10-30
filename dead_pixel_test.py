#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dead Pixel Test — desktop edition (Windows / macOS / Linux)

Zero dependencies: uses only Python's standard library (tkinter).
Run it with any Python 3.8+:

    python3 dead_pixel_test.py            # interactive, starts at black
    python3 dead_pixel_test.py --auto 3   # auto-cycle every 3 seconds
    python3 dead_pixel_test.py --pattern red
    python3 dead_pixel_test.py --list     # list patterns and exit
    python3 dead_pixel_test.py --fixer    # stuck-pixel fixer mode

Controls (same as the web version):
    → / ← ........ next / previous pattern      Space ... auto-cycle on/off
    F ............ toggle fullscreen           H ....... hide/show HUD
    1-9 .......... jump to pattern             +/- ..... auto-cycle speed
    Mouse click .. next   Right-click .. back  Wheel ... next/previous
    Esc / Q ...... quit                         X ....... stuck-pixel fixer

WARNING: the fixer and the "inversion" pattern flash rapidly.
Do not use them if you have epilepsy or photosensitivity.
"""
from __future__ import annotations

import argparse
import sys
import time

__version__ = "1.0.0"

# ---------------------------------------------------------------- patterns
# Each pattern: (id, name_en, name_tr, type, color)
# type: solid | gh | gv | grgb | bars | checker | checker1 | gridd | gridl
#       | moving | inversion
PATTERNS: list[tuple[str, str, str, str, str]] = [
    ("black",     "Black",                    "Siyah",                   "solid", "#000000"),
    ("white",     "White",                    "Beyaz",                   "solid", "#FFFFFF"),
    ("red",       "Red",                      "Kırmızı",                 "solid", "#FF0000"),
    ("green",     "Green",                    "Yeşil",                   "solid", "#00FF00"),
    ("blue",      "Blue",                     "Mavi",                    "solid", "#0000FF"),
    ("yellow",    "Yellow",                   "Sarı",                    "solid", "#FFFF00"),
    ("cyan",      "Cyan",                     "Camgöbeği",               "solid", "#00FFFF"),
    ("magenta",   "Magenta",                  "Macenta",                 "solid", "#FF00FF"),
    ("gray50",    "Gray 50%",                 "Gri %50",                 "solid", "#808080"),
    ("gray25",    "Gray 25% (uniformity)",    "Gri %25 (bulutlanma)",   "solid", "#404040"),
    ("gray75",    "Gray 75%",                 "Gri %75",                 "solid", "#BFBFBF"),
    ("orange",    "Orange",                   "Turuncu",                 "solid", "#FF8000"),
    ("gh",        "Gradient →",               "Yatay Gradyan",           "gh",    ""),
    ("gv",        "Gradient ↓",               "Dikey Gradyan",           "gv",    ""),
    ("grgb",      "RGB Gradient",             "RGB Gradyan",             "grgb",  ""),
    ("bars",      "Color Bars",               "Renk Çubukları",          "bars",  ""),
    ("checker",   "Checkerboard",             "Dama Tahtası",            "checker",  ""),
    ("checker1",  "Checker 1px (inversion)",  "Dama 1px (inversiyon)",  "checker1", ""),
    ("gridd",     "Grid (Dark)",              "Izgara (Koyu)",           "gridd", ""),
    ("gridl",     "Grid (Light)",             "Izgara (Açık)",           "gridl", ""),
    ("moving",    "Moving Bar (ghosting)",    "Hareketli Çubuk (gölgelenme)", "moving", ""),
    ("inversion", "Inversion (flashing!)",    "Ters Çevirme (yanıp söner!)",   "inversion", ""),
]

FIX_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF",
              "#000000", "#FFFF00", "#00FFFF", "#FF00FF"]


def pattern_index(pid: str) -> int:
    for i, p in enumerate(PATTERNS):
        if p[0] == pid.lower():
            return i
    raise ValueError(f"unknown pattern: {pid!r} (use --list)")


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def lerp_color(c1: str, c2: str, t: float) -> str:
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return rgb_to_hex(*(round(a[i] + (b[i] - a[i]) * t) for i in range(3)))


# ---------------------------------------------------------------- app
class DeadPixelTest:
    def __init__(self, start: int = 0, auto: float = 0.0, fixer: bool = False,
                 windowed: bool = False):
        try:
            import tkinter as tk
        except ImportError:
            sys.exit(
                "ERROR: tkinter is not installed.\n"
                "  Windows/macOS : reinstall Python from python.org (tkinter is included)\n"
                "  Debian/Ubuntu : sudo apt install python3-tk\n"
                "  Fedora        : sudo dnf install python3-tkinter\n"
                "  Arch          : sudo pacman -S tk\n"
                "Or just use the web version: open index.html in any browser."
            )
        self.tk = tk
        self.root = tk.Tk()
        self.root.title("Dead Pixel Test")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", not windowed)
        if windowed:
            self.root.geometry("1100x700")

        self.canvas = tk.Canvas(self.root, highlightthickness=0, borderwidth=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.hud = tk.Label(
            self.root, font=("Helvetica", 13, "bold"), bg="#0B0E14", fg="#E8EDF7",
            padx=16, pady=7,
        )
        self.hud_visible = True
        self._hud_job = None

        self.idx = start
        self.auto = auto            # seconds, 0 = off
        self._auto_job = None
        self._anim_job = None
        self._t0 = time.time()

        self.fix_on = False
        self._fix_job = None
        self._fix_n = 0

        self._bind()
        self.draw()
        if self.auto > 0:
            self._schedule_auto()
        if fixer:
            self.root.after(100, self.toggle_fixer)
        self.root.mainloop()

    # ------------------------------------------------------------ drawing
    def size(self) -> tuple[int, int]:
        return max(self.canvas.winfo_width(), 2), max(self.canvas.winfo_height(), 2)

    def draw(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        _, _, _, ptype, color = PATTERNS[self.idx]
        w, h = self.size()
        c = self.canvas
        c.delete("all")

        if ptype == "solid":
            c.configure(bg=color)
        elif ptype in ("gh", "grgb"):
            c.configure(bg="black")
            stops = (["#000000", "#FFFFFF"] if ptype == "gh"
                     else ["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF", "#FF0000"])
            seg = 1.0 / (len(stops) - 1)
            for x in range(w):
                t = x / max(w - 1, 1)
                k = min(int(t / seg), len(stops) - 2)
                col = lerp_color(stops[k], stops[k + 1], (t - k * seg) / seg)
                c.create_line(x, 0, x, h, fill=col)
        elif ptype == "gv":
            c.configure(bg="black")
            for y in range(h):
                c.create_line(0, y, w, y, fill=lerp_color("#000000", "#FFFFFF", y / max(h - 1, 1)))
        elif ptype == "bars":
            c.configure(bg="black")
            cols = ["#FFFFFF", "#FFFF00", "#00FFFF", "#00FF00", "#FF00FF", "#FF0000", "#0000FF"]
            bw = w / len(cols)
            for i, col in enumerate(cols):
                c.create_rectangle(i * bw, 0, (i + 1) * bw + 1, h * 0.75, fill=col, outline="")
            for x in range(w):
                c.create_line(x, h * 0.75, x, h, fill=lerp_color("#000000", "#FFFFFF", x / max(w - 1, 1)))
        elif ptype in ("checker", "checker1"):
            self._checker(1 if ptype == "checker1" else max(8, w // 80), invert=False)
        elif ptype in ("gridd", "gridl"):
            bg, fg = ("#000000", "#FFFFFF") if ptype == "gridd" else ("#FFFFFF", "#000000")
            c.configure(bg=bg)
            s = max(16, w // 60)
            for x in range(0, w, s):
                c.create_line(x, 0, x, h, fill=fg)
            for y in range(0, h, s):
                c.create_line(0, y, w, y, fill=fg)
            c.create_line(w // 2, 0, w // 2, h, fill=fg, width=2)
            c.create_line(0, h // 2, w, h // 2, fill=fg, width=2)
        elif ptype == "moving":
            c.configure(bg="black")
            self._t0 = time.time()
            self._draw_moving()
        elif ptype == "inversion":
            self._t0 = time.time()
            self._draw_inversion()
        self._show_hud()

    def _checker(self, s: int, invert: bool):
        w, h = self.size()
        c = self.canvas
        c.configure(bg="#FFFFFF" if invert else "#000000")
        fg = "#000000" if invert else "#FFFFFF"
        for row, y in enumerate(range(0, h, s)):
            for x in range(s if row % 2 else 0, w, 2 * s):
                c.create_rectangle(x, y, x + s, y + s, fill=fg, outline="")

    def _draw_moving(self):
        w, h = self.size()
        bw = max(40, int(w * 0.06))
        x = int(((time.time() - self._t0) * w / 3.5) % (w + bw)) - bw
        self.canvas.delete("all")
        self.canvas.create_rectangle(x, 0, x + bw, h, fill="#FFFFFF", outline="")
        self._anim_job = self.root.after(16, self._draw_moving)

    def _draw_inversion(self):
        self.canvas.delete("all")
        self._checker(2, invert=int((time.time() - self._t0) * 2) % 2 == 1)
        self._anim_job = self.root.after(500, self._draw_inversion)

    # ------------------------------------------------------------ HUD
    def _show_hud(self):
        if not self.hud_visible or self.fix_on:
            return
        pid, en, tr, ptype, color = PATTERNS[self.idx]
        name = tr if _is_tr() else en
        hexpart = f"   {color}" if ptype == "solid" else ""
        auto = f"   ▶ {self.auto:g}s" if self.auto > 0 else ""
        self.hud.config(text=f"{name}{hexpart}    {self.idx + 1}/{len(PATTERNS)}{auto}")
        self.hud.place(relx=0.5, y=14, anchor="n")
        if self._hud_job:
            self.root.after_cancel(self._hud_job)
        self._hud_job = self.root.after(2600, lambda: self.hud.place_forget())

    # ------------------------------------------------------------ flow
    def go(self, i: int):
        self.idx = i % len(PATTERNS)
        self.draw()

    def _schedule_auto(self):
        if self._auto_job:
            self.root.after_cancel(self._auto_job)
        if self.auto > 0:
            self._auto_job = self.root.after(int(self.auto * 1000), self._auto_step)

    def _auto_step(self):
        self.go(self.idx + 1)
        self._schedule_auto()

    def toggle_auto(self):
        self.auto = 0.0 if self.auto > 0 else 3.0
        self._schedule_auto()
        self._show_hud()

    # ------------------------------------------------------------ fixer
    def toggle_fixer(self):
        if self.fix_on:
            self.fix_on = False
            if self._fix_job:
                self.root.after_cancel(self._fix_job)
            self.draw()
            return
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        self.hud.place_forget()
        self.fix_on = True
        self._fix_n = 0
        self._fix_step()

    def _fix_step(self):
        # A flashing box follows the mouse; leave it over the stuck pixel.
        w, h = self.size()
        mx = self.root.winfo_pointerx() - self.root.winfo_rootx()
        my = self.root.winfo_pointery() - self.root.winfo_rooty()
        box = 150
        c = self.canvas
        c.configure(bg="black")
        c.delete("all")
        c.create_rectangle(mx - box // 2, my - box // 2, mx + box // 2, my + box // 2,
                           fill=FIX_COLORS[self._fix_n % len(FIX_COLORS)], outline="")
        self._fix_n += 1
        if self.fix_on:
            self._fix_job = self.root.after(33, self._fix_step)  # ~30 fps

    # ------------------------------------------------------------ input
    def _bind(self):
        r = self.root
        r.bind("<Right>", lambda e: self.go(self.idx + 1))
        r.bind("<Down>", lambda e: self.go(self.idx + 1))
        r.bind("<Left>", lambda e: self.go(self.idx - 1))
        r.bind("<Up>", lambda e: self.go(self.idx - 1))
        r.bind("<space>", lambda e: self.toggle_auto())
        r.bind("<Escape>", lambda e: self.toggle_fixer() if self.fix_on else r.destroy())
        r.bind("q", lambda e: r.destroy())
        r.bind("Q", lambda e: r.destroy())
        r.bind("f", lambda e: r.attributes("-fullscreen", not r.attributes("-fullscreen")))
        r.bind("F", lambda e: r.attributes("-fullscreen", not r.attributes("-fullscreen")))
        r.bind("h", self._toggle_hud)
        r.bind("H", self._toggle_hud)
        r.bind("x", lambda e: self.toggle_fixer())
        r.bind("X", lambda e: self.toggle_fixer())
        r.bind("<plus>", self._speed_up)
        r.bind("<equal>", self._speed_up)
        r.bind("<minus>", self._speed_down)
        for n in range(1, 10):
            r.bind(str(n), lambda e, n=n: self.go(n - 1))
        self.canvas.bind("<Button-1>", lambda e: None if self.fix_on else self.go(self.idx + 1))
        self.canvas.bind("<Button-3>", lambda e: self.go(self.idx - 1))
        self.canvas.bind("<MouseWheel>", self._wheel)          # Windows / macOS
        self.canvas.bind("<Button-4>", lambda e: self.go(self.idx - 1))  # Linux up
        self.canvas.bind("<Button-5>", lambda e: self.go(self.idx + 1))  # Linux down
        self.canvas.bind("<Configure>", lambda e: None if self.fix_on else self.draw())
        r.bind("<Motion>", lambda e: self._show_hud())

    def _wheel(self, e):
        self.go(self.idx + (1 if e.delta < 0 else -1))

    def _toggle_hud(self, _e=None):
        self.hud_visible = not self.hud_visible
        if self.hud_visible:
            self._show_hud()
        else:
            self.hud.place_forget()

    def _speed_up(self, _e=None):
        self.auto = max(0.5, (self.auto or 3.0) - 0.5)
        self._schedule_auto(); self._show_hud()

    def _speed_down(self, _e=None):
        self.auto = min(30.0, (self.auto or 3.0) + 0.5)
        self._schedule_auto(); self._show_hud()


def _is_tr() -> bool:
    import locale
    try:
        return (locale.getlocale()[0] or "").lower().startswith(("tr", "turkish"))
    except Exception:
        return False


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="dead-pixel-test",
        description="Dead / stuck pixel test for any screen (desktop edition).",
    )
    ap.add_argument("--pattern", default="black", help="start pattern id (see --list)")
    ap.add_argument("--auto", type=float, default=0.0, metavar="SEC",
                    help="auto-cycle every SEC seconds (0 = off)")
    ap.add_argument("--fixer", action="store_true",
                    help="start in stuck-pixel fixer mode (FLASHING — epilepsy warning!)")
    ap.add_argument("--windowed", action="store_true", help="don't start fullscreen")
    ap.add_argument("--list", action="store_true", help="list patterns and exit")
    ap.add_argument("--version", action="version", version=f"dead-pixel-test {__version__}")
    args = ap.parse_args(argv)

    if args.list:
        for pid, en, tr, ptype, color in PATTERNS:
            print(f"{pid:<10} {en:<28} {tr:<32} {color}")
        return 0

    try:
        start = pattern_index(args.pattern)
    except ValueError as exc:
        ap.error(str(exc))

    DeadPixelTest(start=start, auto=args.auto, fixer=args.fixer, windowed=args.windowed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
