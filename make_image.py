"""Render a deterministic 1024x1024 editorial news poster (19 November 2026)."""

import os

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
MARGIN = 44

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

BG = (10, 16, 28)
DOT = (26, 36, 56)
PANEL = (17, 26, 44)
EDGE = (36, 50, 80)
WHITE = (245, 248, 252)
GREY = (150, 162, 180)
MUTED = (108, 120, 140)
GOLD = (228, 186, 76)
RED = (222, 66, 66)
BLUE = (72, 118, 210)

MIDDOT = " · "
_FONTS = {}


# ---------------------------------------------------------------- typography

def F(size, bold=False):
    """Cached font factory."""
    key = (int(size), bool(bold))
    font = _FONTS.get(key)
    if font is None:
        font = ImageFont.truetype(FONT_BOLD if key[1] else FONT_REGULAR, key[0])
        _FONTS[key] = font
    return font


def tw(draw, text, size, bold=False):
    """Rendered width of text."""
    return float(draw.textlength(text, font=F(size, bold)))


def fit(draw, text, size, bold, maxw, minsize=8):
    """Shrink a font size until the single line fits maxw."""
    s = int(size)
    while s > minsize and tw(draw, text, s, bold) > maxw:
        s -= 1
    return s


def tracked(draw, text, x, y, size, bold, color, gap=1):
    """Draw text with a fixed extra gap between characters."""
    cx = float(x)
    font = F(size, bold)
    for ch in text:
        draw.text((int(round(cx)), int(y)), ch, font=font, fill=color)
        cx += tw(draw, ch, size, bold) + gap
    return cx - gap


def wrap(draw, text, size, bold, maxw):
    """Balanced word wrap: dynamic programming over break points."""
    words = text.split()
    if not words:
        return []
    sp = tw(draw, " ", size, bold)
    widths = [tw(draw, w, size, bold) for w in words]
    n = len(words)
    inf = float("inf")
    best = [inf] * (n + 1)
    nxt = [n] * (n + 1)
    best[n] = 0.0
    penalty = 0.02 * maxw * maxw
    for i in range(n - 1, -1, -1):
        total = -sp
        for j in range(i + 1, n + 1):
            total += widths[j - 1] + sp
            if total > maxw and j > i + 1:
                break
            slack = maxw - total
            cost = slack * slack + penalty
            if best[j] + cost < best[i] - 1e-12:
                best[i] = best[j] + cost
                nxt[i] = j
    lines = []
    i = 0
    while i < n:
        j = nxt[i]
        if j <= i:
            j = i + 1
        lines.append(" ".join(words[i:j]))
        i = j
    return lines


def draw_wrapped(draw, text, x, y, size, bold, color, maxw, leading, maxlines=None):
    """Wrap text and draw its lines at x/y with a fixed leading."""
    s = int(size)
    lines = wrap(draw, text, s, bold, maxw)
    if maxlines is not None:
        while len(lines) > maxlines and s > 8:
            s -= 1
            lines = wrap(draw, text, s, bold, maxw)
    for k, line in enumerate(lines):
        draw.text((int(x), int(y + k * leading)), line, font=F(s, bold), fill=color)
    return s, lines


def panel(draw, box):
    draw.rounded_rectangle(box, radius=10, fill=PANEL, outline=EDGE, width=1)


# ------------------------------------------------------------------ flags

FLAG_W = 66
FLAG_H = 42

_STAR_10 = (
    (0.0, -1.0), (0.2245, -0.3090), (0.9511, -0.3090), (0.3633, 0.1180),
    (0.5878, 0.8090), (0.0, 0.3820), (-0.5878, 0.8090), (-0.3633, 0.1180),
    (-0.9511, -0.3090), (-0.2245, -0.3090),
)


def star(draw, cx, cy, r, color):
    pts = [(cx + ux * r, cy + uy * r) for ux, uy in _STAR_10]
    draw.polygon(pts, fill=color)


def flag_us(draw, x, y):
    draw.rectangle([x, y, x + FLAG_W - 1, y + FLAG_H - 1], fill=WHITE)
    for i in range(0, 13, 2):
        y0 = y + (i * FLAG_H) // 13
        y1 = y + ((i + 1) * FLAG_H) // 13 - 1
        draw.rectangle([x, y0, x + FLAG_W - 1, y1], fill=(192, 72, 72))
    cw = 27
    chh = 22
    draw.rectangle([x, y, x + cw - 1, y + chh - 1], fill=(59, 78, 140))
    for row in range(3):
        for col in range(3):
            if (row + col) % 2 == 0:
                sx = x + 4 + col * 8
                sy = y + 4 + row * 6
                draw.ellipse([sx, sy, sx + 1, sy + 1], fill=WHITE)


def flag_cn(draw, x, y):
    draw.rectangle([x, y, x + FLAG_W - 1, y + FLAG_H - 1], fill=(196, 58, 58))
    star(draw, x + 13, y + 12, 8, GOLD)
    for sx, sy in ((25, 4), (30, 10), (30, 18), (25, 24)):
        star(draw, x + sx, y + sy, 3, GOLD)


def flag_ru(draw, x, y):
    h3 = FLAG_H // 3
    draw.rectangle([x, y, x + FLAG_W - 1, y + h3 - 1], fill=WHITE)
    draw.rectangle([x, y + h3, x + FLAG_W - 1, y + 2 * h3 - 1], fill=(72, 118, 210))
    draw.rectangle([x, y + 2 * h3, x + FLAG_W - 1, y + FLAG_H - 1], fill=(222, 66, 66))


# -------------------------------------------------------------- pictograms

def pict_chart(draw, x, y, color=RED):
    pts = [(x, y + 4), (x + 7, y + 11), (x + 15, y + 8),
           (x + 23, y + 19), (x + 30, y + 26)]
    draw.line(pts, fill=color, width=3, joint="curve")


def pict_thermometer(draw, x, y, color=GOLD):
    draw.rounded_rectangle([x + 12, y + 1, x + 18, y + 20], radius=3,
                           outline=color, width=2)
    draw.ellipse([x + 9, y + 17, x + 21, y + 29], fill=color)


def pict_arrow(draw, x, y, color=BLUE):
    draw.line([(x + 1, y + 26), (x + 20, y + 7)], fill=color, width=3)
    draw.polygon([(x + 24, y + 3), (x + 13, y + 6), (x + 21, y + 14)], fill=color)


_DIRS8 = (
    (0.0, -1.0), (0.7071, -0.7071), (1.0, 0.0), (0.7071, 0.7071),
    (0.0, 1.0), (-0.7071, 0.7071), (-1.0, 0.0), (-0.7071, -0.7071),
)


def starburst(draw, cx, cy, r, color):
    """Central disc plus eight tapered spikes."""
    for dx, dy in _DIRS8:
        px, py = -dy, dx
        tip = (cx + dx * r * 2.0, cy + dy * r * 2.0)
        b1 = (cx + dx * r * 0.55 + px * 4.0, cy + dy * r * 0.55 + py * 4.0)
        b2 = (cx + dx * r * 0.55 - px * 4.0, cy + dy * r * 0.55 - py * 4.0)
        draw.polygon([tip, b1, b2], fill=color)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color)


def scales(draw, cx, beam_y, color):
    """Scales of justice, kept inside x 800-950 and y 250-420."""
    left = cx - 51
    right = cx + 51
    draw.line([(left, beam_y), (right, beam_y)], fill=color, width=2)
    draw.line([(cx, beam_y - 8), (cx, beam_y + 64)], fill=color, width=2)
    draw.ellipse([cx - 4, beam_y - 12, cx + 4, beam_y - 4], outline=color, width=2)
    draw.rounded_rectangle([cx - 26, beam_y + 64, cx + 26, beam_y + 74],
                           radius=4, outline=color, width=2)
    for px in (left, right):
        draw.line([(px, beam_y), (px, beam_y + 14)], fill=color, width=2)
        draw.polygon(
            [(px - 22, beam_y + 14), (px + 22, beam_y + 14),
             (px + 14, beam_y + 24), (px - 14, beam_y + 24)],
            outline=color,
        )


# ------------------------------------------------------------------- page

def pair(draw, first, second, x, y):
    draw.text((x, y), first, font=F(15), fill=GREY)
    x2 = x + tw(draw, first, 15) + tw(draw, MIDDOT, 15)
    draw.text((int(round(x2)), y), second, font=F(15), fill=GREY)


def main():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # Faint dot grid.
    for gy in range(16, SIZE, 32):
        for gx in range(16, SIZE, 32):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=DOT)

    # 1. Masthead.
    ms = fit(draw, "THE WORLD TODAY", 62, True, 660)
    draw.text((MARGIN, 30), "THE WORLD TODAY", font=F(ms, True), fill=WHITE)

    r1 = "ONE DAY, ONE PICTURE"
    r2 = "EDITION 19.11.26"
    draw.text((int(round(980 - tw(draw, r1, 15, True))), 38), r1,
              font=F(15, True), fill=GOLD)
    draw.text((int(round(980 - tw(draw, r2, 15, False))), 60), r2,
              font=F(15, False), fill=MUTED)

    # 2. Dateline.
    draw.text((MARGIN, 100), "THURSDAY 19 NOVEMBER 2026",
              font=F(26, True), fill=GOLD)
    draw.rectangle([MARGIN, 132, 980, 133], fill=GOLD)

    # 3. Lead panel.
    panel(draw, (44, 146, 980, 470))
    flag_us(draw, 68, 168)
    flag_cn(draw, 144, 168)
    flag_ru(draw, 220, 168)

    tracked(draw, "THE HAGUE · WORLD COURT", 68, 226, 15, True, GOLD, 1)

    headline = "MYANMAR COMMITTED GENOCIDE, RULES UN COURT"
    hs = fit(draw, headline, 44, True, 620)
    draw.text((68, 248), headline, font=F(hs, True), fill=WHITE)

    lead = (
        "Judges at the International Court of Justice found Myanmar's security "
        "forces acted with genocidal intent against the Rohingya, the first such "
        "ruling against a state in the court's history."
    )
    lead_size = 15
    for size in (18, 17, 16, 15):
        if len(wrap(draw, lead, size, False, 610)) <= 3:
            lead_size = size
            break
    draw_wrapped(draw, lead, 68, 318, lead_size, False, GREY, 610, 27)

    draw.text((68, 424), "LANDMARK JUDGMENT · THE GAMBIA V. MYANMAR",
              font=F(13, True), fill=MUTED)

    scales(draw, 875, 288, GOLD)

    # 4. Second panel.
    panel(draw, (44, 484, 980, 626))
    starburst(draw, 102, 555, 12, RED)

    headline2 = "IRAN WAR ESCALATES AS US STRIKES AGAIN"
    hs2 = fit(draw, headline2, 34, True, 828)
    draw.text((128, 508), headline2, font=F(hs2, True), fill=WHITE)

    draw_wrapped(
        draw,
        "New US retaliatory strikes hit Iranian bases as Tehran threatens the "
        "Strait of Hormuz; Trump says he sees no rush and points to next year.",
        128, 552, 18, False, GREY, 800, 24, 2,
    )

    # 5. Brief row.
    briefs = (
        (44, pict_chart, "NVIDIA FIZZLES",
         "Earnings beat estimates, yet the stock slipped 1.6% to $148.55 and "
         "the S&P closed mixed."),
        (356, pict_thermometer, "INFLATION AT FOUR-YEAR HIGH",
         "Wholesale prices rose at their fastest pace in four years, hardening "
         "the Fed's hawkish tone."),
        (668, pict_arrow, "ANTHROPIC'S STRONG DEBUT",
         "The AI lab opened sharply higher in its first session, the year's "
         "biggest technology listing."),
    )
    for px, icon, title, body in briefs:
        panel(draw, (px, 640, px + 296, 800))
        icon(draw, px + 18, 662)
        ts = fit(draw, title, 20, True, 220)
        draw.text((px + 54, 662), title, font=F(ts, True), fill=WHITE)
        draw_wrapped(draw, body, px + 18, 696, 15, False, GREY, 258, 21, 4)

    # 6. Also today.
    draw.text((MARGIN, 820), "ALSO TODAY", font=F(14, True), fill=GOLD)
    pair(draw, "Kyiv: drones hit the power grid again",
         "COP31 opens in Antalya", 44, 842)
    pair(draw, "United Airlines cancels hundreds of flights",
         "Asia bears the worst air pollution of 2026", 44, 868)

    # 7. Rule and footer.
    draw.rectangle([44, 900, 980, 900], fill=EDGE)

    fright = "THE HAGUE · BEIJING · TEHRAN · WASHINGTON"
    rw = tw(draw, fright, 14, False)
    draw.text((int(round(980 - rw)), 922), fright, font=F(14, False), fill=MUTED)

    fleft = "19 NOVEMBER 2026 · THE DAY IN ONE IMAGE"
    fs = fit(draw, fleft, 20, True, 980 - rw - 24 - MARGIN)
    draw.text((MARGIN, 918), fleft, font=F(fs, True), fill=GOLD)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    img.save(path, "PNG")
    print("%s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
