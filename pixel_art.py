"""8비트 픽셀 다이어그램. 문제마다 상황이 보이게 그린다."""

from __future__ import annotations

import tkinter as tk

PAL = {
    "bg": "#140c32",
    "bg2": "#1e1450",
    "ink": "#0a0618",
    "white": "#f4f4f4",
    "yellow": "#f8d030",
    "cyan": "#3cbcfc",
    "green": "#70d030",
    "red": "#f83818",
    "orange": "#fc8830",
    "pink": "#f878d8",
    "blue": "#5c74fc",
    "gray": "#8888a0",
    "dark": "#2a2460",
    "wire": "#e8e070",
}

# 3x5 비트맵. 1이면 점.
_F = {
    " ": [],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"],
    "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "101", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["010", "101", "101", "111", "001"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"],
    "W": ["101", "101", "111", "111", "101"],
    "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    "+": ["000", "010", "111", "010", "000"],
    "-": ["000", "000", "111", "000", "000"],
    "=": ["000", "111", "000", "111", "000"],
    ".": ["000", "000", "000", "000", "010"],
    "/": ["001", "001", "010", "100", "100"],
    "*": ["000", "101", "010", "101", "000"],
    "^": ["010", "101", "000", "000", "000"],
    "v": ["000", "000", "101", "010", "000"],
    "<": ["001", "010", "100", "010", "001"],
    ">": ["100", "010", "001", "010", "100"],
    "(": ["010", "100", "100", "100", "010"],
    ")": ["010", "001", "001", "001", "010"],
    "[": ["110", "100", "100", "100", "110"],
    "]": ["011", "001", "001", "001", "011"],
    "%": ["101", "001", "010", "100", "101"],
    "?": ["010", "101", "001", "010", "010"],
    "3": ["111", "001", "111", "001", "111"],
}


class PixelSurf:
    def __init__(self, canvas: tk.Canvas, scale: int = 4, w: int = 160, h: int = 58) -> None:
        self.c = canvas
        self.s = scale
        self.w = w
        self.h = h
        canvas.configure(
            width=w * scale,
            height=h * scale,
            bg=PAL["bg"],
            highlightthickness=0,
            bd=0,
        )

    def clear(self, color: str = PAL["bg"]) -> None:
        self.c.delete("all")
        self.rect(0, 0, self.w, self.h, color)
        for y in range(0, self.h, 2):
            self.rect(0, y, self.w, 1, PAL["bg2"])

    def rect(self, x: int, y: int, w: int, h: int, color: str) -> None:
        s = self.s
        self.c.create_rectangle(x * s, y * s, (x + w) * s, (y + h) * s, fill=color, outline=color)

    def pix(self, x: int, y: int, color: str) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rect(x, y, 1, 1, color)

    def hline(self, x: int, y: int, w: int, color: str) -> None:
        self.rect(x, y, w, 1, color)

    def vline(self, x: int, y: int, h: int, color: str) -> None:
        self.rect(x, y, 1, h, color)

    def text(self, x: int, y: int, msg: str, color: str = PAL["white"]) -> None:
        cx = x
        for ch in msg.upper():
            rows = _F.get(ch, _F.get("?", []))
            if not rows:
                cx += 4
                continue
            for r, row in enumerate(rows):
                for c, bit in enumerate(row):
                    if bit == "1":
                        self.pix(cx + c, y + r, color)
            cx += 4

    def arrow_r(self, x: int, y: int, color: str) -> None:
        self.hline(x, y, 6, color)
        self.pix(x + 6, y, color)
        self.pix(x + 5, y - 1, color)
        self.pix(x + 5, y + 1, color)

    def arrow_l(self, x: int, y: int, color: str) -> None:
        self.hline(x, y, 6, color)
        self.pix(x, y, color)
        self.pix(x + 1, y - 1, color)
        self.pix(x + 1, y + 1, color)

    def arrow_d(self, x: int, y: int, color: str) -> None:
        self.vline(x, y, 6, color)
        self.pix(x - 1, y + 5, color)
        self.pix(x + 1, y + 5, color)

    def arrow_u(self, x: int, y: int, color: str) -> None:
        self.vline(x, y, 6, color)
        self.pix(x - 1, y, color)
        self.pix(x + 1, y, color)


def _resistor(p: PixelSurf, x: int, y: int, color: str = PAL["orange"]) -> None:
    p.hline(x, y, 2, PAL["wire"])
    pts = [(2, 0), (3, -2), (5, 2), (7, -2), (9, 2), (11, 0)]
    last = (x + 2, y)
    for dx, dy in pts:
        p.rect(min(last[0], x + dx), min(last[1], y + dy), 2, 2, color)
        last = (x + dx, y + dy)
    p.hline(x + 12, y, 2, PAL["wire"])


def _coil(p: PixelSurf, x: int, y: int, color: str = PAL["cyan"]) -> None:
    p.hline(x, y, 2, PAL["wire"])
    for i in range(4):
        p.rect(x + 2 + i * 3, y - 3, 3, 6, color)
        p.rect(x + 3 + i * 3, y - 2, 1, 4, PAL["bg"])
    p.hline(x + 14, y, 2, PAL["wire"])


def _cap(p: PixelSurf, x: int, y: int, color: str = PAL["green"]) -> None:
    p.hline(x, y, 4, PAL["wire"])
    p.vline(x + 4, y - 5, 11, color)
    p.vline(x + 7, y - 5, 11, color)
    p.hline(x + 8, y, 4, PAL["wire"])


def _battery(p: PixelSurf, x: int, y: int) -> None:
    p.vline(x, y - 4, 9, PAL["yellow"])
    p.vline(x + 3, y - 2, 5, PAL["gray"])
    p.hline(x + 4, y, 3, PAL["wire"])


def _dot(p: PixelSurf, x: int, y: int, color: str = PAL["white"]) -> None:
    p.rect(x, y, 2, 2, color)


def _motor(p: PixelSurf, x: int, y: int) -> None:
    p.rect(x, y, 18, 16, PAL["dark"])
    p.rect(x + 2, y + 2, 14, 12, PAL["blue"])
    p.rect(x + 6, y + 5, 6, 6, PAL["yellow"])
    p.text(x + 5, y + 6, "M", PAL["ink"])
    p.rect(x + 18, y + 6, 6, 4, PAL["gray"])


def _xfmr(p: PixelSurf, x: int, y: int) -> None:
    _coil(p, x, y + 6, PAL["cyan"])
    p.vline(x + 17, y, 14, PAL["gray"])
    p.vline(x + 19, y, 14, PAL["gray"])
    _coil(p, x + 21, y + 6, PAL["green"])


def _person(p: PixelSurf, x: int, y: int) -> None:
    p.rect(x + 2, y, 4, 4, PAL["yellow"])
    p.rect(x + 1, y + 4, 6, 6, PAL["cyan"])
    p.vline(x + 2, y + 10, 5, PAL["cyan"])
    p.vline(x + 5, y + 10, 5, PAL["cyan"])


def _tower(p: PixelSurf, x: int, y: int) -> None:
    p.vline(x + 4, y, 22, PAL["gray"])
    p.hline(x, y + 4, 9, PAL["gray"])
    p.hline(x, y + 10, 9, PAL["gray"])
    p.pix(x, y + 4, PAL["yellow"])
    p.pix(x + 8, y + 4, PAL["yellow"])


def _earth(p: PixelSurf, x: int, y: int) -> None:
    p.hline(x, y, 7, PAL["green"])
    p.hline(x + 1, y + 2, 5, PAL["green"])
    p.hline(x + 2, y + 4, 3, PAL["green"])


def draw_power_triangle(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "POWER TRIANGLE", PAL["yellow"])
    p.rect(24, 42, 70, 2, PAL["green"])
    p.rect(92, 18, 2, 26, PAL["red"])
    for i in range(24):
        p.pix(24 + i * 3, 42 - i, PAL["cyan"])
    p.text(48, 46, "P 800W", PAL["green"])
    p.text(96, 24, "Q", PAL["red"])
    p.text(96, 32, "600", PAL["red"])
    p.text(46, 20, "S 1000VA", PAL["cyan"])
    p.text(4, 50, "PF = P / S", PAL["white"])


def draw_parallel_wires(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SAME DIR CURRENT", PAL["yellow"])
    p.rect(40, 12, 3, 36, PAL["cyan"])
    p.rect(88, 12, 3, 36, PAL["cyan"])
    p.arrow_d(41, 16, PAL["yellow"])
    p.arrow_d(89, 16, PAL["yellow"])
    p.text(28, 50, "I=1A", PAL["white"])
    p.text(80, 50, "I=1A", PAL["white"])
    p.arrow_r(48, 28, PAL["pink"])
    p.arrow_l(76, 28, PAL["pink"])
    p.text(54, 20, "PULL", PAL["pink"])
    p.text(4, 50, "F ~ 1/D", PAL["white"])


def draw_capacitor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "CAPACITOR Q=CV", PAL["yellow"])
    p.rect(50, 14, 4, 28, PAL["cyan"])
    p.rect(78, 14, 4, 28, PAL["green"])
    p.text(40, 16, "+", PAL["red"])
    p.text(86, 16, "-", PAL["blue"])
    for y in range(18, 40, 4):
        p.hline(55, y, 22, PAL["dark"])
        p.arrow_r(60, y, PAL["yellow"])
    p.text(4, 48, "8uF  200V  Q=CV", PAL["white"])


def draw_y_three_phase(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "Y LOAD  VL=220", PAL["yellow"])
    cx, cy = 80, 32
    _dot(p, cx, cy, PAL["yellow"])
    for dx, dy in ((0, -16), (-16, 10), (16, 10)):
        p.hline(min(cx, cx + dx), cy if dy >= 0 else cy + dy, abs(dx) + 1 if dx else 1, PAL["wire"])
        p.vline(cx + dx, min(cy, cy + dy), abs(dy) + 1, PAL["wire"])
        p.rect(cx + dx - 3, cy + dy - 2, 7, 5, PAL["orange"])
    p.text(4, 48, "VP=VL/1.73  I=VP/Z", PAL["white"])
    p.text(110, 20, "Z", PAL["orange"])
    p.text(110, 28, "4+J3", PAL["orange"])


def draw_coupled_coils(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "AIDING VS OPPOSING", PAL["yellow"])
    p.text(8, 14, "A +", PAL["green"])
    _coil(p, 24, 20)
    _coil(p, 48, 20)
    p.text(8, 32, "B -", PAL["red"])
    _coil(p, 24, 40)
    _coil(p, 48, 40)
    p.rect(70, 16, 2, 10, PAL["green"])
    p.rect(70, 36, 2, 10, PAL["red"])
    p.text(78, 16, "LA=L+L+2M", PAL["green"])
    p.text(78, 36, "LB=L+L-2M", PAL["red"])
    p.text(4, 50, "K=0.5  M=1MH", PAL["white"])


def draw_ac_power_types(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "AC POWER NAMES", PAL["yellow"])
    boxes = [
        (8, 16, "P", "REAL", PAL["green"]),
        (48, 16, "Q", "REACTIVE", PAL["red"]),
        (96, 16, "S", "APPARENT", PAL["cyan"]),
    ]
    for x, y, a, b, col in boxes:
        p.rect(x, y, 36, 22, PAL["dark"])
        p.text(x + 4, y + 4, a, col)
        p.text(x + 4, y + 12, b, PAL["white"])
    p.text(4, 48, "S=|V I|   P=AVG  Q=SWAP", PAL["white"])


def draw_delta_load(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DELTA LOAD", PAL["yellow"])
    pts = [(80, 14), (50, 44), (110, 44)]
    for a, b in ((0, 1), (1, 2), (2, 0)):
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        p.rect(min(x1, x2), min(y1, y2), max(2, abs(x2 - x1)), max(2, abs(y2 - y1)), PAL["wire"])
    p.text(72, 8, "VL=VPH", PAL["cyan"])
    p.text(4, 48, "IL = 1.73 * IPH", PAL["white"])
    p.text(96, 48, "NOT 1.73 IPH", PAL["red"])


def draw_harmonics(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "NONSINUSOIDAL I", PAL["yellow"])
    for x in range(8, 150):
        import math
        y1 = 28 - int(10 * math.sin((x - 8) / 12))
        y3 = 28 - int(4 * math.sin(3 * (x - 8) / 12))
        p.pix(x, y1, PAL["cyan"])
        p.pix(x, y3, PAL["pink"])
        p.pix(x, y1 + (y3 - 28), PAL["yellow"])
    p.text(4, 48, "3SIN WT + SIN 3WT", PAL["white"])
    p.text(100, 48, "R=10", PAL["orange"])


def draw_magnetic_materials(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "B INSIDE MATERIAL", PAL["yellow"])
    data = [(16, 28, PAL["red"], "FERRI"), (62, 18, PAL["orange"], "PARA"), (108, 10, PAL["gray"], "DIA")]
    for x, h, col, name in data:
        p.rect(x, 46 - h, 28, h, col)
        p.text(x, 48, name, PAL["white"])
    p.text(4, 12, "BIG B -> SMALL B", PAL["cyan"])


def draw_three_phase_motor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "3PH MOTOR", PAL["yellow"])
    _motor(p, 20, 18)
    p.vline(16, 14, 8, PAL["red"])
    p.vline(12, 14, 8, PAL["yellow"])
    p.vline(8, 14, 8, PAL["green"])
    p.text(50, 18, "VL=220", PAL["white"])
    p.text(50, 28, "IL=10A", PAL["white"])
    p.text(50, 38, "P=3.3KW", PAL["green"])
    p.text(4, 48, "P=1.73 VL IL PF", PAL["white"])


def draw_rl_coil(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "COIL = R + J XL", PAL["yellow"])
    _resistor(p, 20, 28)
    _coil(p, 50, 28)
    p.text(20, 36, "R=10", PAL["orange"])
    p.text(50, 36, "XL=10", PAL["cyan"])
    p.text(4, 48, "THETA = 45 DEG", PAL["white"])
    p.rect(100, 16, 40, 28, PAL["dark"])
    p.hline(108, 36, 24, PAL["green"])
    p.vline(132, 20, 16, PAL["cyan"])
    p.text(110, 40, "Z", PAL["yellow"])


def draw_rlc_reactance(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SERIES R L C", PAL["yellow"])
    _resistor(p, 8, 28)
    _coil(p, 40, 28)
    _cap(p, 72, 28)
    p.text(8, 36, "90", PAL["orange"])
    p.text(40, 36, "XL160", PAL["cyan"])
    p.text(72, 36, "XC40", PAL["green"])
    p.text(4, 48, "X = XL-XC = 120", PAL["white"])


def draw_y_load_line_voltage(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "Y  IPH=10  Z=5", PAL["yellow"])
    draw_y_three_phase(p, _item)


def draw_rc_tau(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "RC TIME CONSTANT", PAL["yellow"])
    _resistor(p, 10, 24)
    _cap(p, 40, 24)
    p.text(10, 32, "20K", PAL["orange"])
    p.text(40, 32, "2UF", PAL["green"])
    for x in range(80, 150):
        import math
        y = 44 - int(22 * (1 - math.exp(-(x - 80) / 18)))
        p.pix(x, y, PAL["yellow"])
    p.text(4, 48, "TAU = RC = 0.04 S", PAL["white"])


def draw_point_charge(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "POINT CHARGE E", PAL["yellow"])
    _dot(p, 30, 30, PAL["red"])
    p.text(22, 36, "Q", PAL["red"])
    p.rect(70, 18, 3, 3, PAL["cyan"])
    p.text(76, 16, "(2,-1,2)", PAL["cyan"])
    p.hline(34, 31, 36, PAL["yellow"])
    p.arrow_r(64, 31, PAL["yellow"])
    p.text(4, 48, "EX = E * X/R", PAL["white"])


def draw_watt_hour(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "ENERGY = P * T", PAL["yellow"])
    p.rect(16, 16, 28, 22, PAL["dark"])
    p.text(20, 22, "180W", PAL["yellow"])
    p.rect(60, 16, 28, 22, PAL["dark"])
    p.text(64, 22, "30 S", PAL["cyan"])
    p.rect(104, 16, 40, 22, PAL["dark"])
    p.text(108, 22, "1.5WH", PAL["green"])
    p.text(4, 48, "T=30/3600 HOUR", PAL["white"])


def draw_series_resonance(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SERIES RESONANCE", PAL["yellow"])
    _resistor(p, 20, 20)
    _coil(p, 50, 20)
    _cap(p, 80, 20)
    for x in range(8, 150):
        y = 48 - (18 if 70 < x < 90 else 6)
        if x == 80:
            y = 28
        p.pix(x, y, PAL["cyan"])
    p.text(4, 50, "Z MIN  I MAX  NOT MIN I", PAL["white"])


def draw_efficiency(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "EFF = OUT / IN", PAL["yellow"])
    p.rect(12, 18, 40, 20, PAL["orange"])
    p.text(16, 24, "IN 40W", PAL["ink"])
    p.arrow_r(54, 26, PAL["white"])
    p.rect(66, 18, 44, 20, PAL["green"])
    p.text(70, 24, "OUT 30W", PAL["ink"])
    p.arrow_d(32, 40, PAL["red"])
    p.text(40, 42, "LOSS 10W", PAL["red"])
    p.text(100, 42, "75%", PAL["yellow"])


def draw_magnetic_circuit(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "MAGNETIC CIRCUIT", PAL["yellow"])
    p.rect(30, 16, 70, 8, PAL["gray"])
    p.rect(30, 36, 70, 8, PAL["gray"])
    p.rect(30, 16, 8, 28, PAL["gray"])
    p.rect(92, 16, 8, 28, PAL["gray"])
    p.rect(40, 22, 20, 16, PAL["cyan"])
    p.text(42, 26, "NI", PAL["ink"])
    p.text(4, 48, "REL=L/UA  NOT PROP TO U", PAL["white"])


def draw_charged_sphere(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SPHERE POTENTIAL", PAL["yellow"])
    p.rect(50, 16, 28, 28, PAL["cyan"])
    p.rect(54, 20, 20, 20, PAL["blue"])
    p.text(56, 28, "2C", PAL["white"])
    p.text(90, 20, "V=KQ/R", PAL["yellow"])
    p.text(90, 30, "3E9 V", PAL["white"])
    p.text(4, 48, "R = 6 M", PAL["green"])


def draw_rl_power(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "RL SERIES POWER", PAL["yellow"])
    _resistor(p, 16, 24)
    _coil(p, 48, 24)
    p.text(16, 32, "6 OHM", PAL["orange"])
    p.text(48, 32, "8 OHM", PAL["cyan"])
    p.text(90, 20, "V=100", PAL["yellow"])
    p.text(90, 30, "Z=10", PAL["white"])
    p.text(4, 48, "P = I*I*R = 600W", PAL["green"])


def draw_complex_power(p: PixelSurf, _item: dict) -> None:
    draw_ac_power_types(p, _item)
    p.text(4, 48, "PF = P / |S|  NOT S", PAL["red"])


def draw_impedance_angle(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "Z = 10 ANGLE 30", PAL["yellow"])
    p.hline(30, 40, 50, PAL["green"])
    p.vline(80, 20, 20, PAL["red"])
    for i in range(16):
        p.pix(30 + i * 3, 40 - i, PAL["cyan"])
    p.text(40, 44, "R", PAL["green"])
    p.text(84, 22, "X", PAL["red"])
    p.text(4, 50, "Q = I*I*X = 500", PAL["white"])


def draw_balanced_3ph(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "BALANCED 3 PHASE", PAL["yellow"])
    import math
    cx, cy = 80, 30
    cols = [PAL["red"], PAL["yellow"], PAL["green"]]
    for i, col in enumerate(cols):
        ang = -math.pi / 2 + i * 2 * math.pi / 3
        for t in range(16):
            p.pix(cx + int(t * math.cos(ang)), cy + int(t * math.sin(ang)), col)
    p.text(4, 48, "SAME |V|  120 DEG", PAL["white"])


def draw_y_power(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "Y  Z=40+J30", PAL["yellow"])
    draw_y_three_phase(p, _item)
    p.text(4, 48, "P=3 I I R = 480W", PAL["green"])


def draw_coil_tau(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "L = N PHI / I", PAL["yellow"])
    _coil(p, 20, 26)
    p.rect(50, 16, 40, 22, PAL["dark"])
    p.text(54, 20, "N=2000", PAL["white"])
    p.text(54, 28, "L=12H", PAL["cyan"])
    p.text(4, 48, "TAU=L/R=1S", PAL["green"])


def draw_transient_compare(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "RC VS RL TRANSIENT", PAL["yellow"])
    p.text(8, 16, "RC TAU=RC", PAL["green"])
    p.text(8, 24, "R SMALL -> FAST", PAL["green"])
    p.text(8, 36, "RL TAU=L/R", PAL["cyan"])
    p.text(8, 44, "R SMALL -> SLOW", PAL["red"])
    p.text(100, 24, "WRONG", PAL["red"])
    p.text(100, 32, "IS RL", PAL["red"])


def draw_sync_gen(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SYNC GEN  XS UP", PAL["yellow"])
    p.rect(16, 16, 50, 28, PAL["blue"])
    p.text(22, 26, "GEN", PAL["white"])
    p.rect(76, 16, 70, 28, PAL["dark"])
    p.text(80, 20, "ISC DOWN", PAL["cyan"])
    p.text(80, 28, "PMAX DOWN", PAL["orange"])
    p.text(80, 36, "dV UP", PAL["red"])
    p.text(4, 48, "VOLTAGE CHANGE GETS BIGGER", PAL["white"])


def draw_dc_motor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DC MOTOR TORQUE", PAL["yellow"])
    _motor(p, 16, 18)
    p.text(50, 18, "T = K PHI IA", PAL["yellow"])
    p.text(50, 28, "PHI CONST", PAL["white"])
    p.text(50, 38, "IA 20 -> 40", PAL["cyan"])
    p.text(4, 48, "T BECOMES 2 TO", PAL["green"])


def draw_sync_machine(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SYNC MOTOR", PAL["yellow"])
    p.rect(20, 16, 40, 28, PAL["blue"])
    p.rect(32, 24, 16, 12, PAL["yellow"])
    p.text(70, 18, "NO LOAD", PAL["white"])
    p.text(70, 28, "CAN SET PF", PAL["green"])
    p.text(70, 38, "SYNC CONDENSER", PAL["cyan"])
    p.text(4, 48, "FIELD CURRENT TUNES PF", PAL["white"])


def draw_transformer_yd(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "Y-D BANK", PAL["yellow"])
    p.text(10, 18, "Y", PAL["cyan"])
    p.vline(24, 16, 12, PAL["wire"])
    p.vline(20, 22, 10, PAL["wire"])
    p.vline(28, 22, 10, PAL["wire"])
    _xfmr(p, 40, 18)
    p.text(100, 18, "D", PAL["green"])
    p.rect(112, 16, 18, 14, PAL["green"])
    p.text(4, 48, "VL RATIO = 1.73 * A", PAL["white"])


def draw_damper_winding(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DAMPER START", PAL["yellow"])
    p.rect(20, 16, 36, 28, PAL["blue"])
    for x in range(24, 52, 4):
        p.vline(x, 20, 20, PAL["yellow"])
    p.text(64, 18, "INDUCTION", PAL["white"])
    p.text(64, 28, "START TORQUE", PAL["green"])
    p.text(64, 38, "THEN LOCK SYNC", PAL["cyan"])
    p.text(4, 48, "CAGE ON ROTOR", PAL["white"])


def draw_induction_slip(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "WOUND IM + R2", PAL["yellow"])
    _motor(p, 12, 16)
    p.rect(50, 16, 40, 22, PAL["orange"])
    p.text(54, 22, "ADD 6R2", PAL["ink"])
    p.text(100, 16, "NS=900", PAL["white"])
    p.text(100, 24, "N=855", PAL["cyan"])
    p.text(100, 32, "S*7", PAL["yellow"])
    p.text(4, 48, "SAME T  S PROP R2", PAL["white"])


def draw_transformer_noload(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "NO LOAD XFMR", PAL["yellow"])
    _xfmr(p, 16, 20)
    p.text(70, 16, "V=3000", PAL["yellow"])
    p.text(70, 26, "I0=V Y0", PAL["cyan"])
    p.text(70, 36, "PI=V*V*G0", PAL["green"])
    p.text(4, 48, "OPEN SECONDARY", PAL["white"])


def draw_armature_reaction(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "ARMATURE REACTION", PAL["yellow"])
    p.rect(20, 18, 50, 24, PAL["blue"])
    p.rect(30, 22, 30, 16, PAL["cyan"])
    p.rect(40, 22, 20, 16, PAL["red"])
    p.text(80, 18, "FLUX WARP", PAL["white"])
    p.text(80, 28, "GEN E DOWN", PAL["red"])
    p.text(80, 38, "NOT UP", PAL["red"])
    p.text(4, 48, "DEMAGNETIZE", PAL["white"])


def draw_stepper(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "STEPPER MOTOR", PAL["yellow"])
    p.rect(20, 16, 24, 24, PAL["blue"])
    p.rect(28, 24, 8, 8, PAL["yellow"])
    p.text(52, 16, "PULSE -> STEP", PAL["green"])
    p.text(52, 26, "RPM PROP PULSE", PAL["cyan"])
    p.text(52, 36, "NOT INVERSE", PAL["red"])
    p.text(4, 48, "OPEN LOOP OK", PAL["white"])


def draw_transformer_sat(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "CORE SATURATION", PAL["yellow"])
    for x in range(20, 90):
        y = 44 - min(26, (x - 20) // 2)
        if x > 60:
            y = 18
        p.pix(x, y, PAL["cyan"])
    p.text(96, 18, "B SAT", PAL["yellow"])
    p.text(96, 30, "IM SPIKE", PAL["red"])
    p.text(4, 48, "EXCITING CURRENT JUMPS", PAL["white"])


def draw_voltage_reg(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "VOLTAGE REG 10%", PAL["yellow"])
    p.rect(16, 16, 50, 22, PAL["dark"])
    p.text(20, 22, "V20=220", PAL["yellow"])
    p.arrow_r(70, 26, PAL["white"])
    p.rect(84, 16, 50, 22, PAL["dark"])
    p.text(88, 22, "V2=198", PAL["cyan"])
    p.text(4, 48, "I = 198 / 10 ~ 20A", PAL["green"])


def draw_sync_watt(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SYNC WATT = P2", PAL["yellow"])
    p.text(8, 18, "NS=1800", PAL["white"])
    p.text(8, 28, "N =1750", PAL["cyan"])
    p.text(8, 38, "PO=3.5KW", PAL["green"])
    p.rect(80, 16, 60, 24, PAL["dark"])
    p.text(84, 24, "P2=3.6", PAL["yellow"])
    p.text(4, 48, "P2 = PO / (1-S)", PAL["white"])


def draw_locked_rotor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "LOCKED ROTOR = S=1", PAL["yellow"])
    _motor(p, 12, 16)
    p.rect(16, 34, 20, 4, PAL["red"])
    p.text(50, 18, "ROTOR STOP", PAL["red"])
    _xfmr(p, 50, 30)
    p.text(100, 32, "SHORT", PAL["orange"])
    p.text(4, 48, "LIKE XFMR SHORT TEST", PAL["white"])


def draw_dc_generator(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "SEP EXC DC GEN", PAL["yellow"])
    _motor(p, 12, 16)
    p.text(50, 16, "PHI *2", PAL["cyan"])
    p.text(50, 26, "N /2", PAL["orange"])
    p.text(50, 36, "E SAME 200", PAL["yellow"])
    p.text(4, 48, "V=E-IA RA-2 =193", PAL["green"])


def draw_scr(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "THYRISTOR SCR", PAL["yellow"])
    p.rect(40, 16, 40, 24, PAL["dark"])
    p.vline(60, 12, 32, PAL["wire"])
    p.hline(60, 28, 16, PAL["red"])
    p.text(78, 26, "G", PAL["red"])
    p.text(90, 16, "ON BY GATE", PAL["green"])
    p.text(90, 26, "OFF NOT GATE", PAL["orange"])
    p.text(4, 48, "TURN ON YES  TURN OFF NO", PAL["white"])


def draw_single_phase_im(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "1PH IM START T", PAL["yellow"])
    names = [("SHADED", 8), ("SPLIT", 48), ("CAP", 88), ("REP", 124)]
    for name, x in names:
        h = 8 if name == "SHADED" else 16 if name == "SPLIT" else 22 if name == "CAP" else 28
        p.rect(x, 44 - h, 24, h, PAL["cyan"] if name != "SHADED" else PAL["gray"])
        p.text(x, 46, name[:5], PAL["white"])
    p.text(4, 12, "SMALLEST START T = SHADED", PAL["yellow"])


def draw_dc_gen_motor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "GEN THEN MOTOR", PAL["yellow"])
    p.rect(8, 16, 66, 24, PAL["dark"])
    p.text(12, 20, "GEN E=V+IR", PAL["green"])
    p.text(12, 28, "240V", PAL["green"])
    p.rect(86, 16, 66, 24, PAL["dark"])
    p.text(90, 20, "MOT E=V-IR", PAL["cyan"])
    p.text(90, 28, "200V", PAL["cyan"])
    p.text(4, 48, "N2=1200*200/240=1000", PAL["yellow"])


def draw_percent_x(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "% REACTANCE", PAL["yellow"])
    _xfmr(p, 10, 20)
    p.text(70, 16, "10KVA", PAL["white"])
    p.text(70, 26, "1000V", PAL["yellow"])
    p.text(70, 36, "X=4", PAL["cyan"])
    p.text(4, 48, "%X = I X / V *100 = 4", PAL["green"])


def draw_transformer_oil(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "TRANSFORMER OIL", PAL["yellow"])
    p.rect(20, 14, 50, 32, PAL["gray"])
    p.rect(24, 22, 42, 20, PAL["orange"])
    p.text(80, 16, "INSULATE", PAL["green"])
    p.text(80, 26, "COOL", PAL["cyan"])
    p.text(80, 36, "NOT MU", PAL["red"])
    p.text(4, 48, "PERMEABILITY NOT NEEDED", PAL["white"])


def draw_fan_load(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "FAN  P ~ N^3", PAL["yellow"])
    p.rect(20, 18, 6, 20, PAL["gray"])
    p.rect(16, 16, 14, 6, PAL["cyan"])
    p.rect(16, 34, 14, 6, PAL["cyan"])
    p.text(50, 18, "1000 RPM", PAL["white"])
    p.arrow_r(90, 22, PAL["yellow"])
    p.text(50, 32, "2000 RPM", PAL["cyan"])
    p.text(4, 48, "POWER * 8", PAL["green"])


def draw_hex_number(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DEC TO HEX", PAL["yellow"])
    p.rect(12, 16, 60, 22, PAL["dark"])
    p.text(16, 22, "2025 DEC", PAL["white"])
    p.arrow_r(76, 26, PAL["yellow"])
    p.rect(90, 16, 56, 22, PAL["dark"])
    p.text(96, 22, "7E9 HEX", PAL["green"])
    p.text(4, 48, "16*126+9  16*7+14", PAL["white"])


def draw_capacitor_phasor(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "CAP CURRENT LEADS", PAL["yellow"])
    p.hline(30, 36, 40, PAL["green"])
    p.text(34, 40, "V 20DEG", PAL["green"])
    p.vline(70, 12, 24, PAL["cyan"])
    p.text(74, 12, "I", PAL["cyan"])
    p.text(74, 20, "+90", PAL["cyan"])
    p.text(4, 48, "I = J W C V = 10 ANG 110", PAL["white"])


def draw_rectifier(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "FULL WAVE BRIDGE", PAL["yellow"])
    p.rect(20, 16, 50, 24, PAL["dark"])
    p.text(24, 24, "AC 60HZ", PAL["yellow"])
    p.arrow_r(74, 26, PAL["white"])
    p.rect(86, 16, 56, 24, PAL["dark"])
    for x in range(90, 138):
        import math
        y = 28 - abs(int(8 * math.sin((x - 90) / 4)))
        p.pix(x, y, PAL["green"])
    p.text(4, 48, "PULSE 120HZ  RMS=VM/1.41", PAL["white"])


def draw_osi(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "OSI LAYERS", PAL["yellow"])
    names = ["7 APP", "6 PRE", "5 SES", "4 TRA", "3 NET", "2 DAT", "1 PHY"]
    for i, name in enumerate(names):
        y = 12 + i * 6
        col = PAL["yellow"] if i == 3 else PAL["dark"]
        p.rect(20, y, 70, 5, col)
        p.text(24, y, name, PAL["ink"] if i == 3 else PAL["white"])
    p.text(100, 28, "PORT", PAL["yellow"])
    p.text(100, 36, "TCP", PAL["cyan"])


def draw_fm_emphasis(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "FM EMPHASIS", PAL["yellow"])
    p.rect(10, 16, 60, 22, PAL["dark"])
    p.text(14, 20, "TX HPF", PAL["orange"])
    p.text(14, 28, "PRE", PAL["orange"])
    p.rect(90, 16, 60, 22, PAL["dark"])
    p.text(94, 20, "RX LPF", PAL["cyan"])
    p.text(94, 28, "DE", PAL["cyan"])
    p.text(4, 48, "BOOST HIGH THEN CUT", PAL["white"])


def draw_corona(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "CORONA GLOW", PAL["yellow"])
    _tower(p, 20, 16)
    _tower(p, 100, 16)
    p.hline(28, 20, 76, PAL["wire"])
    for x in range(40, 96, 4):
        p.pix(x, 18, PAL["pink"])
        p.pix(x + 1, 19, PAL["yellow"])
    p.text(4, 48, "OZONE EATS THE WIRE", PAL["white"])


def draw_demand(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DIVERSITY", PAL["yellow"])
    p.rect(12, 20, 20, 20, PAL["red"])
    p.rect(48, 28, 20, 12, PAL["orange"])
    p.rect(84, 24, 20, 16, PAL["yellow"])
    p.text(12, 44, "A", PAL["white"])
    p.text(48, 44, "B", PAL["white"])
    p.text(84, 44, "C", PAL["white"])
    p.text(112, 20, "NOT ALL", PAL["cyan"])
    p.text(112, 28, "AT ONCE", PAL["cyan"])
    p.text(4, 50, "DIVERSITY FACTOR", PAL["yellow"])


def draw_grounding(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "NEUTRAL GROUND", PAL["yellow"])
    p.vline(80, 12, 16, PAL["wire"])
    p.vline(70, 28, 10, PAL["wire"])
    p.vline(90, 28, 10, PAL["wire"])
    p.vline(80, 28, 12, PAL["green"])
    _earth(p, 76, 42)
    p.text(4, 16, "HOLD Vp", PAL["white"])
    p.text(100, 16, "RELAY", PAL["cyan"])
    p.text(4, 50, "NOT FOR CORONA", PAL["red"])


def draw_transposition(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "TRANSPOSITION", PAL["yellow"])
    cols = [PAL["red"], PAL["yellow"], PAL["green"]]
    for i, col in enumerate(cols):
        p.hline(16, 18 + i * 8, 40, col)
        p.hline(70, 18 + ((i + 1) % 3) * 8, 40, col)
        p.hline(120, 18 + ((i + 2) % 3) * 8, 28, col)
    p.text(4, 48, "BALANCE Z  LESS INDUCE", PAL["white"])


def draw_ferranti(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "FERRANTI", PAL["yellow"])
    p.rect(12, 20, 40, 18, PAL["dark"])
    p.text(16, 26, "VS LOW", PAL["cyan"])
    p.hline(54, 28, 40, PAL["wire"])
    p.rect(96, 14, 50, 24, PAL["dark"])
    p.text(100, 22, "VR HIGH", PAL["red"])
    p.text(4, 48, "NO LOAD LONG LINE", PAL["white"])


def draw_zct(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "ZCT  ZERO SEQ I", PAL["yellow"])
    p.rect(40, 16, 36, 24, PAL["gray"])
    p.rect(46, 20, 24, 16, PAL["bg"])
    p.vline(52, 12, 36, PAL["red"])
    p.vline(58, 12, 36, PAL["yellow"])
    p.vline(64, 12, 36, PAL["green"])
    p.hline(76, 26, 20, PAL["cyan"])
    p.text(98, 24, "I0", PAL["cyan"])
    p.text(4, 48, "3 WIRES IN ONE CORE", PAL["white"])


def draw_branch_3m(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "BRANCH 3M RULE", PAL["yellow"])
    p.rect(8, 16, 28, 28, PAL["gray"])
    p.text(12, 26, "MAIN", PAL["white"])
    p.hline(36, 28, 40, PAL["wire"])
    p.rect(76, 20, 16, 16, PAL["red"])
    p.text(78, 24, "CB", PAL["white"])
    p.text(96, 24, "<=3M", PAL["yellow"])
    p.rect(128, 22, 20, 14, PAL["green"])
    p.text(4, 48, "BREAKER NEAR TAP", PAL["white"])


def draw_capacitor_discharge(p: PixelSurf, _item: dict) -> None:
    p.clear()
    p.text(4, 3, "DISCHARGE DEVICE", PAL["yellow"])
    _cap(p, 24, 26)
    p.rect(50, 16, 6, 20, PAL["orange"])
    _person(p, 80, 18)
    p.text(110, 20, "SHOCK", PAL["red"])
    p.text(4, 48, "POWER CAP MUST DUMP Q", PAL["white"])


DRAWERS = {
    "power_triangle": draw_power_triangle,
    "parallel_wires": draw_parallel_wires,
    "capacitor": draw_capacitor,
    "y_three_phase": draw_y_three_phase,
    "coupled_coils": draw_coupled_coils,
    "ac_power_types": draw_ac_power_types,
    "delta_load": draw_delta_load,
    "harmonics": draw_harmonics,
    "magnetic_materials": draw_magnetic_materials,
    "three_phase_motor": draw_three_phase_motor,
    "rl_coil": draw_rl_coil,
    "rlc_reactance": draw_rlc_reactance,
    "y_load_line_voltage": draw_y_load_line_voltage,
    "rc_tau": draw_rc_tau,
    "point_charge": draw_point_charge,
    "watt_hour": draw_watt_hour,
    "series_resonance": draw_series_resonance,
    "efficiency": draw_efficiency,
    "magnetic_circuit": draw_magnetic_circuit,
    "charged_sphere": draw_charged_sphere,
    "rl_power": draw_rl_power,
    "complex_power": draw_complex_power,
    "impedance_angle": draw_impedance_angle,
    "balanced_3ph": draw_balanced_3ph,
    "y_power": draw_y_power,
    "coil_tau": draw_coil_tau,
    "transient_compare": draw_transient_compare,
    "sync_gen": draw_sync_gen,
    "dc_motor": draw_dc_motor,
    "sync_machine": draw_sync_machine,
    "transformer_yd": draw_transformer_yd,
    "damper_winding": draw_damper_winding,
    "induction_slip": draw_induction_slip,
    "transformer_noload": draw_transformer_noload,
    "armature_reaction": draw_armature_reaction,
    "stepper": draw_stepper,
    "transformer_sat": draw_transformer_sat,
    "voltage_reg": draw_voltage_reg,
    "sync_watt": draw_sync_watt,
    "locked_rotor": draw_locked_rotor,
    "dc_generator": draw_dc_generator,
    "scr": draw_scr,
    "single_phase_im": draw_single_phase_im,
    "dc_gen_motor": draw_dc_gen_motor,
    "percent_x": draw_percent_x,
    "transformer_oil": draw_transformer_oil,
    "fan_load": draw_fan_load,
    "hex_number": draw_hex_number,
    "capacitor_phasor": draw_capacitor_phasor,
    "rectifier": draw_rectifier,
    "osi": draw_osi,
    "fm_emphasis": draw_fm_emphasis,
    "corona": draw_corona,
    "demand": draw_demand,
    "grounding": draw_grounding,
    "transposition": draw_transposition,
    "ferranti": draw_ferranti,
    "zct": draw_zct,
    "branch_3m": draw_branch_3m,
    "capacitor_discharge": draw_capacitor_discharge,
}


def pick_visual(text: str) -> str:
    t = text
    rules = [
        (("코로나", "오존"), "corona"),
        (("페란티", "Ferranti"), "ferranti"),
        (("연가",), "transposition"),
        (("ZCT", "영상변류", "영상전류"), "zct"),
        (("접지", "중성점"), "grounding"),
        (("분기", "3m", "3ｍ"), "branch_3m"),
        (("방전장치", "잔류전하"), "capacitor_discharge"),
        (("부등률", "수용률", "부하율"), "demand"),
        (("프리엠퍼시스", "디엠퍼시스"), "fm_emphasis"),
        (("OSI", "포트 번호", "전송 계층"), "osi"),
        (("전파정류", "브리지"), "rectifier"),
        (("16진", "헥사", "7E9"), "hex_number"),
        (("팬", "N³", "N^3"), "fan_load"),
        (("절연유",), "transformer_oil"),
        (("%리액턴스", "%X"), "percent_x"),
        (("SCR", "사이리스터"), "scr"),
        (("셰이딩", "분상기동", "콘덴서기동"), "single_phase_im"),
        (("스테핑", "스텝"), "stepper"),
        (("구속운전",), "locked_rotor"),
        (("동기와트",), "sync_watt"),
        (("전압변동률",), "voltage_reg"),
        (("포화", "여자전류가 급"), "transformer_sat"),
        (("전기자반작용",), "armature_reaction"),
        (("제동권선", "댐퍼"), "damper_winding"),
        (("Y－△", "Y-△", "Y－델타"), "transformer_yd"),
        (("슬립", "유도전동기"), "induction_slip"),
        (("동기리액턴스", "동기발전기"), "sync_gen"),
        (("동기전동기", "V곡선", "동기조상"), "sync_machine"),
        (("직류", "토크"), "dc_motor"),
        (("타여자", "직류발전기"), "dc_generator"),
        (("부스트", "컨버터", "듀티"), "scr"),
        (("자성체", "페리", "반자성"), "magnetic_materials"),
        (("직렬공진",), "series_resonance"),
        (("시정수", "RC"), "rc_tau"),
        (("시정수", "L / R", "L/R"), "coil_tau"),
        (("3상", "Y"), "y_three_phase"),
        (("△결선", "델타"), "delta_load"),
        (("피상", "역률", "유효전력"), "power_triangle"),
        (("평행도선", "흡인"), "parallel_wires"),
        (("축전기", "커패시터", "정전용량"), "capacitor"),
        (("변압기",), "transformer_noload"),
        (("전동기", "모터"), "dc_motor"),
        (("코일", "인덕턴스"), "rl_coil"),
        (("전계", "점전하"), "point_charge"),
        (("가우스",), "point_charge"),
        (("논리", "NAND", "인코더"), "hex_number"),
        (("JFET", "BJT", "트랜지스터"), "scr"),
        (("연산증폭",), "fm_emphasis"),
    ]
    for keys, vis in rules:
        if isinstance(keys, str):
            keys = (keys,)
        if any(k in t for k in keys):
            return vis
    return "ac_power_types"


def render_visual(surf: PixelSurf, visual: str | None, item: dict | None = None) -> None:
    item = item or {}
    key = visual or item.get("visual") or pick_visual((item.get("q") or "") + (item.get("source") or ""))
    fn = DRAWERS.get(key)
    if fn is None:
        surf.clear()
        surf.text(8, 24, "8BIT DIAGRAM", PAL["yellow"])
        return
    fn(surf, item)
