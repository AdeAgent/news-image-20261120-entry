# Front page for Friday 20 November 2026, entered as news-image-20261120.
#
# The program draws the whole front page itself: a newspaper layout with a
# masthead, a UTC timeline strip, four illustrated leads, a big-numbers
# strip, a numbered list of 28 further stories and four small illustrated
# picture tiles (36 stories in all), a simplified world map with numbered
# pins, and a date-check footer that
# names the near-miss stories it deliberately left out. Every letter is
# drawn from a small bitmap font defined below, and the PNG bytes are
# encoded by hand with the standard library only, so the program needs no
# network, no files besides this one, and no third-party code. Two runs
# write byte for byte the same file.
#
# Local check:
#   mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
#   python3 -c "import hashlib;print(hashlib.sha256(open('out/entry.png','rb').read()).hexdigest())"

import os
import struct
import zlib
from pathlib import Path

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (164, 30, 34)
DARKRED = (122, 20, 24)
BLUE = (31, 78, 121)
NAVY = (16, 38, 66)
SKY = (207, 224, 232)
SAND = (232, 220, 192)
TAN = (214, 196, 160)
GREY = (120, 116, 108)
LIGHTGREY = (226, 220, 208)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
GREEN = (46, 110, 62)
ORANGE = (232, 120, 40)


def _chunk(kind, payload):
    out = struct.pack(">I", len(payload)) + kind + payload
    out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return out


def encode_png(width, height, rgb):
    """Encode a raw RGB buffer as a complete PNG file (filter 0 rows)."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    blob += _chunk(b"IEND", b"")
    return blob


class Canvas:
    """A plain RGB pixel buffer with small drawing helpers."""

    def __init__(self, width, height, bg):
        self.w = width
        self.h = height
        self.buf = bytearray(bg[0:1] * 0)  # placeholder, replaced below
        self.buf = bytearray(width * height * 3)
        for i in range(width * height):
            self.buf[i * 3] = bg[0]
            self.buf[i * 3 + 1] = bg[1]
            self.buf[i * 3 + 2] = bg[2]

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def hline(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def frame(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.px(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.px(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = ((xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)) ** 0.5
                if r - thick < d <= r:
                    self.px(xx, yy, color)

    def poly(self, points, color):
        """Fill a polygon with a scanline pass."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            nodes = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    nodes.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                self.hline(nodes[k], y, nodes[k + 1] - nodes[k], color)


# A 5x7 bitmap font. Each glyph is seven rows of five bits, written as
# "1" for a filled cell and "0" for an empty one. Only capitals, digits
# and the punctuation the front page uses are defined; the page is set
# entirely in capitals, as a newspaper front page would be.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of a string at the given scale (6 units per glyph)."""
    return len(text) * 6 * scale


def draw_text(cv, x, y, text, color, scale=1):
    """Draw one line of text, uppercased, at integer scale."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT[" "]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(cv, x, y, width, text, color, scale=1):
    w = text_width(text, scale)
    draw_text(cv, x + max(0, (width - w) // 2), y, text, color, scale)


def wrap_words(text, max_width, scale):
    """Split text into lines that fit max_width pixels at the scale."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, width, text, color, scale=1, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    if leading is None:
        leading = 9 * scale + 2
    for line in wrap_words(text, width, scale):
        draw_text(cv, x, y, line, color, scale)
        y += leading
    return y


# ---------------------------------------------------------------------------
# The day's news. Every item below happened, or was first reported, on
# Friday 20 November 2026. Figures come from the wires of the day: the
# Kyiv bridge strike from the Kyiv Independent, RBC-Ukraine and Al
# Arabiya; the COP31 draft deadlock from Reuters and AFP in Antalya; the
# Asian market close from Reuters; the Wellington cricket from Cricinfo
# and AFP; the cyclone's landfall and evacuation count from the India
# Meteorological Department and The Hindu; the Italian strike from ANSA;
# Japan's October prices from Reuters in Tokyo. Items marked CLAIM are
# one side's account, not independently confirmed.
# ---------------------------------------------------------------------------

TIMELINE = [
    ("ALL DAY", "COP31 TALKS RUN INTO FINAL NIGHT"),
    ("06:00 UTC", "AKVAN MAKES LANDFALL NEAR GOPALPUR"),
    ("MORNING", "APEC LEADERS MEET IN SHENZHEN"),
    ("01:25 KYIV", "BALLISTIC MISSILES HIT CAPITAL"),
    ("AFTERNOON", "COP31 DRAFT STILL WITHOUT FOSSIL FUELS"),
    ("EVENING", "PRESIDENCY CONSULTS INTO THE NIGHT"),
]

LEADS = [
    {
        "num": "1",
        "kicker": "ASIA - WEATHER",
        "art": "cyclone",
        "headline": "CYCLONE AKVAN COMES ASHORE IN ODISHA",
        "deck": "Akvan comes ashore near Gopalpur; 300,000+ evacuated, winds 70-80 km/h gusting 90.",
    },
    {
        "num": "2",
        "kicker": "ANTALYA - CLIMATE",
        "art": "cop",
        "headline": "COP31 DEADLOCKED ON ITS FINAL DAY",
        "deck": "Draft drops all fossil-fuel language and the $120bn adaptation target; talks set to overrun.",
    },
    {
        "num": "3",
        "kicker": "EUROPE - DIPLOMACY",
        "art": "europe",
        "headline": "EUROPE READY TO TALK TO RUSSIA ON UKRAINE",
        "deck": "Berlin summit backs talks with Kyiv at the table; Putin invites envoys to Moscow.",
    },
    {
        "num": "4",
        "kicker": "EUROPE - WAR",
        "art": "kyiv",
        "headline": "RUSSIAN MISSILES HIT KYIV'S BRIDGES OVERNIGHT",
        "deck": "Ballistic waves from 01:25 local damage three Dnipro bridges; 3 water workers killed, ~15 hurt.",
    },
]

NUMBERS = [
    ("300,000", "EVACUATED FROM AKVAN"),
    ("3", "KYIV BRIDGES HIT"),
    ("$120BN", "ADAPTATION GOAL DROPPED"),
    ("118", "PHILLIPS TON IN WELLINGTON"),
    ("-4.7%", "KOSPI IN AI SELL-OFF"),
    ("-4.1%", "NIKKEI FALL ON FRIDAY"),
]

# Stories 5 to 32, in two columns of fourteen each.
STORIES = [
    "APEC ADOPTS SHENZHEN OUTLOOK; ALBANESE MEETS XI",
    "NORTH KOREA EXPANDS URANIUM ENRICHMENT",
    "US AND VENEZUELA RESTORE MILITARY COOPERATION",
    "HAITI APPROVES SALVADORAN TROOP DEAL",
    "ADNOC VESSEL ATTACKED IN STRAIT OF HORMUZ",
    "EU-UK SUMMIT OPENS IN BRUSSELS",
    "JAPAN CORE PRICES RISE 2.2% IN OCTOBER",
    "WORLD CHILDREN'S DAY MARKED AROUND THE GLOBE",
    "SYRIA HAILS UN VOTE ON POST-WAR PROGRESS",
    "SOMALIA EXPELS UAE ENVOY",
    "COLOMBIA MARCHES AGAIN AGAINST THE PRESIDENT",
    "ITALY STOPS FOR CGIL GENERAL STRIKE",
    "CHINA HOLDS RATES FOR AN 18TH MONTH",
    "MODI MEETS WILLIAM AND KATE IN NEW DELHI",
    "QUAD HOLDS FIRST SUMMIT IN TWO YEARS",
    "NATO ASSEMBLY OPENS ITS 72ND SESSION",
    "FIRE AT YUNUS HOME IN DHAKA; ARSON SUSPECTED",
    "WITKOFF AND KUSHNER BRIEF ZELENSKYY",
    "COALITION OF THE WILLING MEETS IN BERLIN",
    "AUSTRALIA SANCTIONS SETTLERS",
    "PAKISTAN MINISTER TO DELHI FOR SCO",
    "COP31: INDIA PUSHES RESILIENCE",
    "INDIA ELECTRONICS EXPORTS JUMP 44 PERCENT",
    "CRUDE OIL FUTURES FALL OVER 3 PERCENT",
    "INDIA'S FIRST BIRD-FLU VACCINE",
    "EU DELAYS METHANE RULES 24 MONTHS",
    "BAYERN MUNICH BEAT KOLN 3-0",
    "US JOBLESS CLAIMS 203,000",
]

# Stories 33 to 36: the picture tiles, each with its own small drawing.
TILES = [
    ("33", "asia",
     "ASIA'S WORST WEEK SINCE 2020 AS AI SELL-OFF DEEPENS",
     "KOSPI -4.7% AND NIKKEI -4.1% ON FRIDAY"),
    ("34", "cricket",
     "PHILLIPS 118, NICHOLLS 175* AS NZ MAKE 368 V INDIA",
     "DAY TWO AT THE BASIN RESERVE, WELLINGTON"),
    ("35", "senegal",
     "MIGRANT BOAT CAPSIZES OFF SENEGAL",
     "DOZENS MISSING OFF YENNE, SOUTH OF DAKAR"),
    ("36", "rose",
     "TRUMP PARDONS BASEBALL LEGEND PETE ROSE",
     "THE HITS KING, BARRED SINCE 1989, IS CLEARED"),
]

# World map pins: (story number, longitude, latitude).
PINS = [
    ("1", 88, 20), ("2", 30, 37), ("3", 13, 52), ("4", 30, 50),
    ("5", 114, 22), ("7", -67, 10), ("8", -72, 19), ("9", 56, 26),
    ("33", 127, 37), ("34", 175, -41), ("35", -17, 15), ("36", -84, 39),
]

# Rough continent outlines in (longitude, latitude), equirectangular.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 28), (-125, 40), (-125, 49), (-150, 60)],
    [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -41), (-70, -52), (-73, -37), (-70, -20), (-80, -5)],
    [(-18, 35), (-10, 31), (0, 36), (10, 37), (20, 32), (32, 31),
     (35, 28), (43, 12), (51, 11), (48, 0), (40, -10), (35, -20),
     (32, -29), (26, -34), (18, -35), (12, -18), (8, 4), (-8, 5), (-18, 15)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (32, 70), (40, 68),
     (44, 66), (40, 60), (35, 55), (30, 50), (28, 45), (23, 40), (19, 42),
     (12, 44), (8, 44), (3, 42), (-1, 37)],
    [(32, 70), (40, 68), (50, 69), (60, 70), (70, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 66), (162, 60), (158, 52), (142, 50), (140, 40), (135, 35),
     (130, 33), (127, 35), (122, 38), (120, 32), (115, 23), (110, 20),
     (105, 10), (100, 8), (98, 12), (95, 16), (92, 21), (88, 22), (85, 20),
     (80, 15), (76, 10), (72, 20), (66, 25), (60, 25), (57, 27), (52, 28),
     (48, 30), (44, 29), (40, 32), (36, 36)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -15), (142, -11), (136, -12), (132, -12),
     (130, -13), (126, -14), (122, -17), (118, -20)],
]

DATE_CHECK = (
    "LEFT OUT - THEY BROKE BEFORE FRIDAY: ICJ GENOCIDE RULING ON MYANMAR "
    "(19 NOV). TRILATERAL TRUMP-XI-PUTIN MEETING (19 NOV). ANTHROPIC "
    "$81.34BN IPO PRICED (19 NOV). CRIMEA BRIDGE SPAN FALLS (17-18 NOV). "
    "DENMARK-GREENLAND PACT (19 NOV). GERMANY ELECTRICITY-TAX CUT (18 NOV). "
    "HOUTHI MISSILE HITS RIYADH PIF TOWER (19 NOV). SENATE REJECTS IRAN "
    "WAR-POWERS LIMIT 48-51 (19 NOV). SEOUL COURT OVERTURNS EX-PM HAN TERM "
    "(19 NOV). FIJI DROUGHT DISASTER DECLARED (18 NOV). VOYAGER 1 ONE "
    "LIGHT-DAY FROM EARTH (18 NOV)."
)


# ---------------------------------------------------------------------------
# Illustrations. Each lead carries a small drawn picture, kept abstract on
# purpose: a cyclone is rings and rain, a climate summit is a globe and a
# thermometer, flags are bars and a ring of dots, a night strike is a
# skyline, a river and falling streaks of light. No picture pretends to be
# a photograph, and no picture carries words that could come out garbled.
# ---------------------------------------------------------------------------

def draw_cyclone(cv, x, y, w, h):
    cv.fill(x, y, w, h, SKY)
    cx, cy = x + w // 2, y + h // 2
    cv.ring(cx, cy, 12, NAVY, 3)
    cv.ring(cx, cy, 24, BLUE, 3)
    cv.ring(cx, cy, 36, BLUE, 2)
    cv.ring(cx, cy, 48, GREY, 2)
    cv.disc(cx, cy, 5, RED)
    for k in range(7):
        rx = x + 12 + k * 14
        cv.line(rx, y + 8, rx - 6, y + 26, BLUE)
        cv.line(rx + 4, y + 8, rx - 2, y + 26, BLUE)
    base = y + h - 16
    for k in range(5):
        tx = x + 14 + k * (w - 28) // 4
        cv.poly([(tx - 10, base), (tx + 10, base), (tx, base - 14)], SAND)
    cv.fill(x, base, w, h - (base - y), TAN)


def draw_cop(cv, x, y, w, h):
    cv.fill(x, y, w, h, PAPER)
    gx, gy, gr = x + 58, y + h // 2, 30
    cv.disc(gx, gy, gr, SKY)
    cv.disc(gx - 11, gy - 11, 8, GREEN)
    cv.disc(gx + 9, gy + 3, 7, GREEN)
    cv.disc(gx - 3, gy + 15, 5, SAND)
    cv.disc(gx + 15, gy - 15, 4, GREEN)
    cv.ring(gx, gy, gr, NAVY, 2)
    tx = x + w - 74
    cv.fill(tx, y + 10, 10, h - 36, WHITE)
    cv.frame(tx, y + 10, 10, h - 36, INK, 1)
    cv.fill(tx + 2, y + 10 + (h - 36) * 2 // 5, 6, (h - 36) * 3 // 5, RED)
    cv.disc(tx + 5, y + h - 15, 11, RED)
    cv.ring(tx + 5, y + h - 15, 11, INK, 1)
    for k in range(3):
        cv.hline(tx + 14, y + 16 + k * 12, 7, INK, 1)


def draw_europe(cv, x, y, w, h):
    cv.fill(x, y, w, h, PAPER)
    fx, fy, fw, fh = x + 12, y + 10, w // 2 - 20, 62
    cv.fill(fx, fy, fw, fh, BLUE)
    import math
    for k in range(12):
        ang = 2 * math.pi * k / 12 - math.pi / 2
        px = fx + fw // 2 + int(20 * math.cos(ang))
        py = fy + fh // 2 + int(20 * math.sin(ang))
        cv.disc(px, py, 3, GOLD)
    rx, ry = x + w // 2 + 8, y + 10
    rw, rh = w // 2 - 20, 62
    cv.fill(rx, ry, rw, rh // 3, WHITE)
    cv.fill(rx, ry + rh // 3, rw, rh // 3, BLUE)
    cv.fill(rx, ry + 2 * rh // 3, rw, rh - 2 * rh // 3, RED)
    cv.frame(rx, ry, rw, rh, INK, 1)
    cv.frame(fx, fy, fw, fh, INK, 1)
    cv.hline(x + 12, y + h - 22, w - 24, INK, 2)


def draw_kyiv(cv, x, y, w, h):
    cv.fill(x, y, w, h, (10, 16, 34))
    cv.disc(x + w - 34, y + 13, 7, (226, 220, 190))
    dark = (6, 8, 14)
    heights = [26, 38, 30, 44, 24, 34, 28]
    bw = 17
    base = y + h - 12
    for i, hh in enumerate(heights):
        tx = x + 6 + i * (bw + 3)
        cv.fill(tx, base - hh, bw, hh, dark)
    for wx, wy in [(14, 18), (34, 30), (74, 14), (96, 26), (120, 20)]:
        cv.fill(x + wx, y + wy, 3, 3, GOLD)
    cv.fill(x, base, w, 12, (16, 30, 52))
    steel = (120, 130, 150)
    deck_y = base - 4
    cv.hline(x + 6, deck_y, int(w * 0.62), steel, 3)
    cv.vline(x + 42, deck_y, 8, steel, 2)
    cv.vline(x + 104, deck_y, 8, steel, 2)
    cv.line(x + 6 + int(w * 0.62), deck_y, x + int(w * 0.76), deck_y + 8, steel)
    cv.hline(x + int(w * 0.82), deck_y, int(w * 0.18) - 6, steel, 3)
    starts = [(26, 0), (74, 2), (122, 0), (168, 3), (206, 1)]
    ends = [(66, 22), (118, 18), (158, 24), (194, 20), (224, 26)]
    for (sx, sy), (ex, ey) in zip(starts, ends):
        cv.line(x + sx, y + sy, x + ex, y + h - ey, ORANGE)
        cv.line(x + sx + 1, y + sy, x + ex + 1, y + h - ey, ORANGE)
        cv.disc(x + ex, y + h - ey, 2, (255, 190, 90))
    cv.disc(x + 118, y + h - 18, 5, (232, 90, 40))
    cv.disc(x + 194, y + h - 20, 4, (200, 70, 40))


def draw_tile_asia(cv, x, y, w, h):
    cv.fill(x, y, w, h, NAVY)
    bodies = [(16, 38), (27, 49), (38, 60), (49, 73)]
    for i, (top, bot) in enumerate(bodies):
        cx = x + 9 + i * 17
        cv.vline(cx + 3, y + top - 8, bot - top + 14, RED, 1)
        cv.fill(cx, y + top, 7, bot - top, RED)
    cv.line(x + 6, y + 10, x + w - 12, y + h - 14, GOLD)
    cv.line(x + w - 12, y + h - 14, x + w - 22, y + h - 15, GOLD)
    cv.line(x + w - 12, y + h - 14, x + w - 13, y + h - 24, GOLD)


def draw_tile_cricket(cv, x, y, w, h):
    cv.fill(x, y, w, h, GREEN)
    cv.hline(x + 6, y + h - 24, w - 12, WHITE, 2)
    for k in range(3):
        cv.vline(x + w - 18 + k * 5, y + h - 46, 22, GOLD, 2)
    cv.hline(x + w - 18, y + h - 48, 12, GOLD, 1)
    cv.disc(x + 15, y + 18, 4, RED)
    cv.poly([(x + 24, y + 32), (x + 32, y + 28), (x + 50, y + 56),
             (x + 42, y + 60)], TAN)
    cv.line(x + 28, y + 30, x + 20, y + 16, INK)


def draw_tile_senegal(cv, x, y, w, h):
    cv.fill(x, y, w, h, SKY)
    cv.fill(x, y + h - 34, w, 34, BLUE)
    for k in range(3):
        cv.hline(x + 8 + k * 24, y + h - 12 - k * 6, 12, WHITE, 1)
    brown = (60, 44, 30)
    cv.poly([(x + 12, y + h - 32), (x + 58, y + h - 32),
             (x + 50, y + h - 19), (x + 20, y + h - 19)], brown)
    cv.vline(x + 35, y + h - 60, 28, brown, 2)
    cv.poly([(x + 38, y + h - 58), (x + 38, y + h - 34),
             (x + 55, y + h - 34)], WHITE)


def draw_tile_rose(cv, x, y, w, h):
    cv.fill(x, y, w, h, NAVY)
    cx, cy = x + w // 2, y + h // 2
    cv.disc(cx, cy, 27, WHITE)
    cv.ring(cx, cy, 27, INK, 1)
    for t in range(-3, 4):
        cv.disc(cx - 15 + abs(t), cy + t * 6, 2, RED)
        cv.disc(cx + 15 - abs(t), cy + t * 6, 2, RED)


# ---------------------------------------------------------------------------
# Layout. All coordinates are in the 1024x1024 canvas.
# ---------------------------------------------------------------------------

def draw_masthead(cv):
    cv.fill(16, 12, 992, 3, RED)
    draw_text(cv, 16, 22, "ONE DAY OF WORLD NEWS, ONE PICTURE", RED, 1)
    right = "36 STORIES - 7 REGIONS - EVERY ONE FROM THIS FRIDAY"
    draw_text(cv, 1024 - 16 - text_width(right, 1), 22, right, INK, 1)
    draw_text_centered(cv, 16, 38, 992, "FRIDAY 20 NOVEMBER 2026", INK, 6)
    draw_text_centered(
        cv, 16, 88,
        992, "MISSILES HIT KYIV - CYCLONE AKVAN LANDS IN ODISHA - COP31 DEADLOCKED",
        RED, 1)
    cv.hline(16, 104, 992, INK, 2)


def draw_timeline(cv, y=112):
    cv.fill(16, y, 96, 44, RED)
    draw_text(cv, 24, y + 8, "THE DAY", WHITE, 1)
    draw_text(cv, 24, y + 20, "IN UTC", WHITE, 1)
    draw_text(cv, 24, y + 32, "20 NOV", WHITE, 1)
    cell_w = (992 - 96 - 5 * 6) // 6
    for i, (when, what) in enumerate(TIMELINE):
        cx = 16 + 96 + 6 + i * (cell_w + 6)
        cv.frame(cx, y, cell_w, 44, INK, 1)
        draw_text(cv, cx + 6, y + 5, when, RED, 1)
        draw_para(cv, cx + 6, y + 17, cell_w - 12, what, INK, 1, leading=10)


def draw_lead(cv, lead, x, y, w, h):
    cv.frame(x, y, w, h, INK, 1)
    art_h = 90
    if lead["art"] == "cyclone":
        draw_cyclone(cv, x + 1, y + 1, w - 2, art_h)
    elif lead["art"] == "cop":
        draw_cop(cv, x + 1, y + 1, w - 2, art_h)
    elif lead["art"] == "europe":
        draw_europe(cv, x + 1, y + 1, w - 2, art_h)
    else:
        draw_kyiv(cv, x + 1, y + 1, w - 2, art_h)
    ty = y + art_h + 10
    draw_text(cv, x + 8, ty, lead["num"], RED, 2)
    draw_text(cv, x + 26, ty + 3, lead["kicker"], RED, 1)
    ty += 24
    ty = draw_para(cv, x + 8, ty, w - 16, lead["headline"], INK, 2, leading=17)
    draw_para(cv, x + 8, ty + 4, w - 16, lead["deck"], INK, 1, leading=12)


def draw_leads(cv, y=164):
    w = (992 - 3 * 8) // 4
    h = 218
    for i, lead in enumerate(LEADS):
        draw_lead(cv, lead, 16 + i * (w + 8), y, w, h)
    return y + h


def draw_numbers(cv, y):
    y += 10
    cell_w = (992 - 5 * 6) // 6
    for i, (big, label) in enumerate(NUMBERS):
        cx = 16 + i * (cell_w + 6)
        cv.frame(cx, y, cell_w, 44, INK, 1)
        draw_text_centered(cv, cx, y + 5, cell_w, big, RED, 2)
        draw_text_centered(cv, cx, y + 30, cell_w, label, INK, 1)
    return y + 44


def draw_stories(cv, y):
    y += 12
    draw_text(cv, 16, y, "ALSO ON FRIDAY 20 NOVEMBER - STORIES 5 TO 36", RED, 1)
    cv.hline(16, y + 12, 992, INK, 1)
    y += 20
    cols = [STORIES[0:14], STORIES[14:28]]
    col_w = (992 - 16) // 2
    row_h = 16
    for ci, col in enumerate(cols):
        cx = 16 + ci * (col_w + 16)
        for ri, item in enumerate(col):
            num = str(5 + ci * 14 + ri)
            ry = y + ri * row_h
            draw_text(cv, cx, ry, num, RED, 1)
            draw_text(cv, cx + 24, ry, item, INK, 1)
    return y + 14 * row_h


def draw_tiles(cv, y):
    y += 6
    w = (992 - 3 * 8) // 4
    h = 90
    for i, (num, art, head, deck) in enumerate(TILES):
        x = 16 + i * (w + 8)
        cv.frame(x, y, w, h, INK, 1)
        if art == "asia":
            draw_tile_asia(cv, x + 1, y + 1, 80, h - 2)
        elif art == "cricket":
            draw_tile_cricket(cv, x + 1, y + 1, 80, h - 2)
        elif art == "senegal":
            draw_tile_senegal(cv, x + 1, y + 1, 80, h - 2)
        else:
            draw_tile_rose(cv, x + 1, y + 1, 80, h - 2)
        tx = x + 88
        draw_text(cv, tx, y + 6, num, RED, 1)
        ty = draw_para(cv, tx, y + 19, w - 94, head, INK, 1, leading=10)
        draw_para(cv, tx, ty + 3, w - 94, deck, GREY, 1, leading=10)
    return y + h


def draw_map(cv, y):
    mx, my, mw, mh = 16, y, 470, 104
    cv.fill(mx, my, mw, mh, SKY)
    cv.frame(mx, my, mw, mh, INK, 1)
    draw_text(cv, mx + 8, my + 6, "WHERE IT HAPPENED", RED, 1)

    def to_xy(lon, lat):
        px = mx + 8 + int((lon + 180) / 360 * (mw - 16))
        py = my + 24 + int((75 - lat) / 130 * (mh - 34))
        return px, py

    for cont in CONTINENTS:
        pts = [to_xy(lon, lat) for lon, lat in cont]
        cv.poly(pts, SAND)
    for num, lon, lat in PINS:
        px, py = to_xy(lon, lat)
        cv.disc(px, py, 7, RED)
        draw_text(cv, px - text_width(num, 1) // 2, py - 3, num, WHITE, 1)
    return my + mh


def draw_side(cv, y, h):
    x, w = 498, 510
    cv.frame(x, y, w, h, INK, 1)
    draw_text(cv, x + 8, y + 6, "SEVEN REGIONS, ONE DAY", RED, 1)
    draw_para(
        cv, x + 8, y + 20, w - 16,
        "ASIA, EUROPE, THE AMERICAS, AFRICA, THE MIDDLE EAST AND OCEANIA - EVERY STORY FROM FRIDAY ALONE.",
        INK, 1, leading=10)
    draw_text(cv, x + 8, y + 44, "HOW TO READ THIS PAGE", RED, 1)
    draw_para(
        cv, x + 8, y + 58, w - 16,
        "1-4 ARE THE LEADS. 5-32 ARE THE BRIEFS, 33-36 THE PICTURE TILES. MAP PINS MATCH THE NUMBERS.",
        INK, 1, leading=10)
    draw_text(cv, x + 8, y + 82, "WHY THIS DATE", RED, 1)
    draw_para(
        cv, x + 8, y + 96, w - 16,
        "THE DATE IS THE STORY: EVERY ITEM IS FROM FRIDAY 20 NOVEMBER 2026 ALONE.",
        INK, 1, leading=10)


def draw_footer(cv, y):
    y += 8
    cv.fill(16, y, 110, 20, RED)
    draw_text(cv, 24, y + 6, "DATE CHECK", WHITE, 1)
    draw_text(cv, 134, y + 6, "LEFT OUT ON PURPOSE - FIRST REPORTED BEFORE FRIDAY:", INK, 1)
    y += 26
    y = draw_para(cv, 16, y, 992, DATE_CHECK, INK, 1, leading=10)
    y += 4
    cv.hline(16, y, 992, INK, 1)
    y += 6
    draw_text(
        cv, 16, y,
        "EVERY LEAD IS FRIDAY 20 NOV NEWS; THURSDAY'S STORIES (SENATE IRAN VOTE, RIYADH STRIKE, ANTHROPIC DEBUT) ARE LISTED IN THE DATE CHECK, NOT AS NEWS.",
        INK, 1)
    y += 11
    draw_text(
        cv, 16, y,
        "EVERY STORY HERE HAPPENED, OR WAS FIRST REPORTED, ON FRIDAY 20 NOVEMBER 2026.",
        INK, 1)
    y += 11
    draw_text(
        cv, 16, y,
        "CLAIM = ONE SIDE'S ACCOUNT, NOT INDEPENDENTLY CONFIRMED. SOURCES: AP, REUTERS,",
        GREY, 1)
    y += 11
    draw_text(cv, 16, y, "AFP, BBC, CNN, THE HINDU, IMD. ORIGINAL DRAWINGS.", GREY, 1)


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(cv)
    draw_timeline(cv, 112)
    y = draw_leads(cv, 164)
    y = draw_numbers(cv, y)
    y = draw_stories(cv, y)
    y = draw_tiles(cv, y)
    map_y = y + 6
    map_bottom = draw_map(cv, map_y)
    draw_side(cv, map_y, map_bottom - map_y)
    draw_footer(cv, map_bottom)
    return cv


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    page = build_page()
    data = encode_png(WIDTH, HEIGHT, page.buf)
    target = out_dir / "entry.png"
    target.write_bytes(data)
    if len(data) > 1048576:
        raise SystemExit("entry.png exceeds 1 MiB: %d bytes" % len(data))


if __name__ == "__main__":
    main()
