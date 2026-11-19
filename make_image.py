#!/usr/bin/env python3
"""Draw the make.fun "news-image-20261119" editorial poster.

Deterministic: no randomness, no clocks, no network, no locale-dependent
formatting.  Running this twice produces byte-identical PNG output.
"""

from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# Canvas + palette
# --------------------------------------------------------------------------

W = H = 1024
MARGIN = 56

BG = (11, 18, 32)          # #0B1220
DOT = (27, 38, 60)
BAND = (14, 22, 39)
PANEL = (17, 26, 44)
PANEL_EDGE = (34, 48, 74)
WHITE = (244, 247, 252)
GOLD = (226, 184, 74)
GREY = (140, 152, 172)
MUTED = (104, 116, 136)

BLUE = (59, 130, 246)
RED = (239, 68, 68)
SILVER = (156, 163, 175)

US_RED = (178, 34, 52)
US_BLUE = (60, 59, 110)
CN_RED = (222, 41, 16)
CN_YELLOW = (255, 222, 0)
RU_BLUE = (0, 57, 166)
RU_RED = (213, 43, 30)

# --------------------------------------------------------------------------
# Layout constants (module level so the layout can be audited independently)
# --------------------------------------------------------------------------

MAST_TOP, MAST_BOTTOM = 0, 134
P1_TOP, P1_BOTTOM = 148, 620
P2_TOP, P2_BOTTOM = 636, 920
FOOT_RULE_TOP, FOOT_RULE_BOTTOM = 936, 938

INNER_L = MARGIN + 24
INNER_R = W - MARGIN - 24
INNER_W = INNER_R - INNER_L

FLAG_W, FLAG_H, FLAG_GAP = 72.0, 48.0, 18.0
GAVEL_SIZE = 64

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# The three fonts named by the brief, plus a serif-regular fallback chain so
# the body copy can be set in a regular serif face when one is installed.
SANS_BOLD = [f"{FONT_DIR}/DejaVuSans-Bold.ttf"]
SANS = [f"{FONT_DIR}/DejaVuSans.ttf"]
SERIF_BOLD = [f"{FONT_DIR}/DejaVuSerif-Bold.ttf", f"{FONT_DIR}/DejaVuSans-Bold.ttf"]
SERIF = [
    f"{FONT_DIR}/DejaVuSerif.ttf",
    f"{FONT_DIR}/DejaVuSerif-Bold.ttf",
    f"{FONT_DIR}/DejaVuSans.ttf",
]

HEADLINE_1 = "TRUMP, XI AND PUTIN MEET FOR THE FIRST TIME"
BODY_1 = (
    "The three leaders sign a \u2018Declaration Towards Peace\u2019 in Shenzhen, "
    "and say the US, China and Russia are \u2018uniquely positioned\u2019 to talk "
    "about cutting nuclear arsenals."
)
HEADLINE_2 = "UN COURT: MYANMAR COMMITTED GENOCIDE"
BODY_2 = (
    "The International Court of Justice finds Myanmar\u2019s security forces "
    "\u2018acted with genocidal intent\u2019 against the Rohingya in the 2017 "
    "Rakhine State operations. Rohingya refugees watch the ruling from "
    "Cox\u2019s Bazar."
)

_font_cache: dict[tuple[tuple[str, ...], int], ImageFont.FreeTypeFont] = {}


def load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    """Return the first font in ``candidates`` that exists, at ``size`` px."""
    key = (tuple(candidates), size)
    cached = _font_cache.get(key)
    if cached is not None:
        return cached
    for path in candidates:
        if os.path.exists(path):
            font = ImageFont.truetype(path, size)
            _font_cache[key] = font
            return font
    raise FileNotFoundError(f"none of these fonts exist: {candidates}")


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: float) -> list[str]:
    """Greedy word wrap measured with ``textlength`` so nothing overflows."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_headline(
    draw: ImageDraw.ImageDraw,
    text: str,
    candidates: list[str],
    max_width: float,
    max_lines: int,
    hi: int,
    lo: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest font size in [lo, hi] whose wrap fits in ``max_lines`` lines."""
    for size in range(hi, lo - 1, -1):
        font = load_font(candidates, size)
        lines = wrap(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = load_font(candidates, lo)
    return font, wrap(draw, text, font, max_width)


def tracked_width(draw: ImageDraw.ImageDraw, text: str, font, tracking: float) -> float:
    if not text:
        return 0.0
    total = sum(draw.textlength(ch, font=font) for ch in text)
    return total + tracking * (len(text) - 1)


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font,
    fill,
    tracking: float = 0.0,
    right: bool = False,
) -> float:
    """Draw letter-spaced text; returns the y coordinate just below it."""
    x, y = xy
    if right:
        x -= tracked_width(draw, text, font, tracking)
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return y + font.size * 1.18


def draw_paragraph(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font,
    fill,
    max_width: float,
    line_height: float,
) -> float:
    """Draw a wrapped paragraph; returns the y coordinate just below it."""
    x, y = xy
    for line in wrap(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


# --------------------------------------------------------------------------
# Shape helpers
# --------------------------------------------------------------------------


def star_points(cx: float, cy: float, r: float, rot_deg: float = -90.0):
    """Ten alternating outer/inner vertices of a five-pointed star."""
    pts = []
    for i in range(10):
        ang = math.radians(rot_deg + i * 36.0)
        rad = r if i % 2 == 0 else r * 0.382
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def draw_flag_us(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float) -> None:
    """13 stripes plus a blue canton carrying a grid of white dots."""
    stripe = h / 13.0
    for i in range(13):
        top = y + i * stripe
        colour = US_RED if i % 2 == 0 else WHITE
        draw.rectangle([x, top, x + w, top + stripe], fill=colour)
    canton_w = w * 0.4
    canton_h = stripe * 7
    draw.rectangle([x, y, x + canton_w, y + canton_h], fill=US_BLUE)
    r = max(0.8, h * 0.024)
    for col in range(4):
        for row in range(3):
            cx = x + canton_w * (col + 1) / 5.0
            cy = y + canton_h * (row + 1) / 4.0
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)


def draw_flag_cn(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float) -> None:
    """Red field, one large star and four small stars aimed at its centre."""
    draw.rectangle([x, y, x + w, y + h], fill=CN_RED)
    sx = w / 30.0
    sy = h / 20.0
    big_cx, big_cy = x + 5 * sx, y + 5 * sy
    draw.polygon(star_points(big_cx, big_cy, 3.0 * sx), fill=CN_YELLOW)
    for ux, uy in ((10.0, 2.0), (12.0, 4.0), (12.0, 7.0), (10.0, 9.0)):
        cx, cy = x + ux * sx, y + uy * sy
        # One point of each small star aims at the centre of the large star.
        aim = math.degrees(math.atan2(big_cy - cy, big_cx - cx))
        draw.polygon(star_points(cx, cy, 1.0 * sx, aim), fill=CN_YELLOW)


def draw_flag_ru(draw: ImageDraw.ImageDraw, x: float, y: float, w: float, h: float) -> None:
    """White / blue / red horizontal thirds."""
    third = h / 3.0
    draw.rectangle([x, y, x + w, y + third], fill=WHITE)
    draw.rectangle([x, y + third, x + w, y + 2 * third], fill=RU_BLUE)
    draw.rectangle([x, y + 2 * third, x + w, y + h], fill=RU_RED)


def draw_gavel(base: Image.Image, x: float, y: float, size: int) -> None:
    """Small gold gavel built from rounded rectangles on a rotated layer."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = size / 120.0
    gold = GOLD + (255,)
    # head of the gavel
    d.rounded_rectangle([30 * s, 24 * s, 94 * s, 48 * s], radius=11 * s, fill=gold)
    # handle
    d.rounded_rectangle([55 * s, 46 * s, 67 * s, 104 * s], radius=6 * s, fill=gold)
    layer = layer.rotate(-38.0, resample=Image.BICUBIC, expand=False)
    base.paste(layer, (int(round(x)), int(round(y))), layer)


def draw_figure(
    draw: ImageDraw.ImageDraw,
    cx: float,
    top: float,
    colour,
    head_r: float,
    body_w: float,
    body_h: float,
) -> None:
    """A seated silhouette: circle head over a rounded-rectangle body."""
    draw.ellipse([cx - head_r, top, cx + head_r, top + 2 * head_r], fill=colour)
    body_top = top + 2 * head_r + 4
    draw.rounded_rectangle(
        [cx - body_w / 2, body_top, cx + body_w / 2, body_top + body_h],
        radius=body_w * 0.42,
        fill=colour,
    )


# --------------------------------------------------------------------------
# Poster
# --------------------------------------------------------------------------


def build() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Faint dot grid.
    step = 32
    for gx in range(step // 2, W, step):
        for gy in range(step // 2, H, step):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=DOT)

    # ---------------- Masthead ----------------
    draw.rectangle([0, MAST_TOP, W, MAST_BOTTOM - 2], fill=BAND)
    draw.rectangle([0, MAST_BOTTOM - 2, W, MAST_BOTTOM], fill=GOLD)

    masthead = load_font(SERIF_BOLD, 54)
    draw.text((MARGIN, 22), "THE WORLD TODAY", font=masthead, fill=WHITE)

    date_font = load_font(SANS_BOLD, 19)
    draw_tracked(
        draw, (MARGIN + 2, 92), "THURSDAY 19 NOVEMBER 2026", date_font, GOLD, tracking=2.4
    )

    small = load_font(SANS, 15)
    draw_tracked(
        draw, (W - MARGIN, 42), "ONE DAY, ONE PICTURE", small, GREY, tracking=1.2, right=True
    )
    draw_tracked(
        draw, (W - MARGIN, 68), "EDITION 19.11.26", small, MUTED, tracking=1.2, right=True
    )

    # ---------------- Panel 1: Shenzhen summit ----------------
    draw.rounded_rectangle(
        [MARGIN, P1_TOP, W - MARGIN, P1_BOTTOM],
        radius=18,
        fill=PANEL,
        outline=PANEL_EDGE,
        width=2,
    )

    # Three flags drawn from shapes.
    fx = INNER_L
    fy = P1_TOP + 24
    for painter in (draw_flag_us, draw_flag_cn, draw_flag_ru):
        painter(draw, fx, fy, FLAG_W, FLAG_H)
        draw.rectangle([fx, fy, fx + FLAG_W, fy + FLAG_H], outline=(70, 84, 110), width=1)
        fx += FLAG_W + FLAG_GAP

    # Gold caption.
    cap_font = load_font(SANS_BOLD, 16)
    y = draw_tracked(
        draw, (INNER_L, fy + FLAG_H + 20), "SHENZHEN  \u00b7  APEC", cap_font, GOLD, tracking=3.0
    )

    # Headline, wrapped to at most two lines.
    head_font, head_lines = fit_headline(
        draw, HEADLINE_1, SANS_BOLD, INNER_W, max_lines=2, hi=46, lo=28
    )
    y += 14
    for line in head_lines:
        draw.text((INNER_L, y), line, font=head_font, fill=WHITE)
        y += head_font.size * 1.2

    # Body paragraph in a regular serif face.
    body_font = load_font(SERIF, 19)
    y = draw_paragraph(draw, (INNER_L, y + 16), BODY_1, body_font, GREY, INNER_W, 27)

    # Three seated-figure silhouettes.
    fig_top = y + 20
    head_r, body_w, body_h = 12.0, 52.0, 46.0
    fig_h = 2 * head_r + 4 + body_h
    spacing = 92.0
    start_cx = (INNER_L + INNER_R) / 2 - spacing
    for i, colour in enumerate((BLUE, RED, SILVER)):
        draw_figure(draw, start_cx + i * spacing, fig_top, colour, head_r, body_w, body_h)

    # Gold kicker and grey sub-line under the figures.
    y = fig_top + fig_h + 18
    kick_font = load_font(SANS_BOLD, 16)
    y = draw_tracked(
        draw, (INNER_L, y), "FIRST-EVER TRILATERAL", kick_font, GOLD, tracking=2.6
    )
    sub_font = load_font(SANS, 14)
    draw_tracked(
        draw, (INNER_L, y + 4), "SUMMIT  \u00b7  SHENZHEN, CHINA", sub_font, MUTED, tracking=1.6
    )

    # ---------------- Panel 2: ICJ ruling ----------------
    draw.rounded_rectangle(
        [MARGIN, P2_TOP, W - MARGIN, P2_BOTTOM],
        radius=18,
        fill=PANEL,
        outline=PANEL_EDGE,
        width=2,
    )

    draw_gavel(img, INNER_L, P2_TOP + 24, GAVEL_SIZE)

    head2_font, head2_lines = fit_headline(
        draw, HEADLINE_2, SANS_BOLD, INNER_W, max_lines=2, hi=34, lo=22
    )
    y = P2_TOP + 24 + GAVEL_SIZE + 12
    for line in head2_lines:
        draw.text((INNER_L, y), line, font=head2_font, fill=WHITE)
        y += head2_font.size * 1.2

    body2_font = load_font(SERIF, 17)
    draw_paragraph(draw, (INNER_L, y + 12), BODY_2, body2_font, GREY, INNER_W, 25)

    # ---------------- Footer ----------------
    draw.rectangle([0, FOOT_RULE_TOP, W, FOOT_RULE_BOTTOM], fill=GOLD)
    foot_font = load_font(SANS_BOLD, 17)
    draw_tracked(
        draw,
        (MARGIN, 962),
        "19 NOVEMBER 2026  \u00b7  THE DAY IN ONE IMAGE",
        foot_font,
        GOLD,
        tracking=2.2,
    )
    foot_right = load_font(SANS, 15)
    draw_tracked(
        draw,
        (W - MARGIN, 964),
        "SHENZHEN  \u00b7  THE HAGUE",
        foot_right,
        MUTED,
        tracking=1.6,
        right=True,
    )

    return img


def main() -> None:
    img = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    print(f"wrote entry.png ({img.width}x{img.height}, {size} bytes)")


if __name__ == "__main__":
    main()
