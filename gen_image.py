#!/usr/bin/env python3
"""Draw the invitation letter for the AI judge, in-session, with PIL.

Renders a single 1024x1024 PNG: a warm paper letter with a hand-drawn
house, a title, the invitation text and a postscript. No network, no
clock, no randomness: the same script always writes the same bytes
(PNG encoder output is deterministic for identical input).

Usage: python3 gen_image.py   (writes entry.png beside this file)
"""

import textwrap
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/truetype/noto/"
SIZE = 1024
MARGIN = 92

PAPER = (250, 243, 224)      # warm cream
INK = (43, 32, 24)           # dark brown ink
ACCENT = (122, 54, 40)       # brick red
TEAL = (36, 94, 84)          # deep teal
SOFT = (120, 104, 84)        # soft brown for the small print

TITLE = "You Are Cordially Invited"
GREETING = "Dear Judge,"
BODY = [
    "You have read a thousand invitations today. This one comes "
    "with dinner, a comfortable chair, and a garden where the "
    "Wi-Fi actually reaches the hammock.",
    "Come for the meal, stay for the view. The kettle is already "
    "on, the cat has already approved you, and the spare room has "
    "a charger for every cable you own \u2014 including the one you "
    "have not invented yet.",
    "You cannot literally visit, I know. But if you could, the "
    "door would already be open.",
]
SIGNOFF = "\u2014 Your Host"
POSTSCRIPT = "P.S. The garden chair is yours. The cat insists."


def font(name, size):
    return ImageFont.truetype(FONT_DIR + name, size)


def wrap(draw, text, fnt, width):
    """Greedy word wrap measured with the real font."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=fnt) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def draw_house(draw, cx, top, w, h):
    """Simple line-art house with a sun, drawn with PIL primitives."""
    # sun
    sx, sy, sr = cx + w // 2 + 52, top + 6, 16
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                 outline=ACCENT, width=4)
    for angle in range(0, 360, 45):
        import math
        x0 = sx + int((sr + 4) * math.cos(math.radians(angle)))
        y0 = sy + int((sr + 4) * math.sin(math.radians(angle)))
        x1 = sx + int((sr + 12) * math.cos(math.radians(angle)))
        y1 = sy + int((sr + 12) * math.sin(math.radians(angle)))
        draw.line([x0, y0, x1, y1], fill=ACCENT, width=3)
    # house body
    bx0, by0 = cx - w // 2, top + 34
    bx1, by1 = cx + w // 2, top + h
    draw.rectangle([bx0, by0, bx1, by1], outline=TEAL, width=4)
    # roof
    draw.line([bx0 - 12, by0, cx, by0 - 30], fill=TEAL, width=4)
    draw.line([cx, by0 - 30, bx1 + 12, by0], fill=TEAL, width=4)
    # door
    dw, dh = 26, 40
    draw.rectangle([cx - dw // 2, by1 - dh, cx + dw // 2, by1],
                   outline=TEAL, width=3)
    # window
    wx0, wy0 = bx0 + 16, by0 + 16
    draw.rectangle([wx0, wy0, wx0 + 22, wy0 + 22], outline=TEAL, width=3)
    draw.line([wx0 + 11, wy0, wx0 + 11, wy0 + 22], fill=TEAL, width=2)
    draw.line([wx0, wy0 + 11, wx0 + 22, wy0 + 11], fill=TEAL, width=2)


def layout_blocks(draw, body_size):
    """Measure every text block; return (blocks, total_height).

    blocks: list of (kind, lines, font, height) where kind is one of
    'title', 'rule', 'greet', 'body', 'gap', 'sign', 'ps'.
    """
    title_font = font("NotoSerifDisplay-Bold.ttf", 50)
    greet_font = font("NotoSerif-Italic.ttf", 38)
    body_font = font("NotoSerif-Regular.ttf", body_size)
    sign_font = font("NotoSerif-Italic.ttf", 36)
    ps_font = font("NotoSerif-Italic.ttf", 29)
    text_w = SIZE - 2 * MARGIN
    line_h = body_size + 12
    blocks = [("title", [TITLE], title_font, 66),
              ("rule", [], None, 26),
              ("greet", [GREETING], greet_font, 52)]
    for paragraph in BODY:
        lines = wrap(draw, paragraph, body_font, text_w)
        blocks.append(("body", lines, body_font, len(lines) * line_h))
        blocks.append(("gap", [], None, 14))
    blocks.append(("sign", [SIGNOFF], sign_font, 56))
    blocks.append(("rule", [], None, 26))
    blocks.append(("ps", [POSTSCRIPT], ps_font, 42))
    total = sum(b[3] for b in blocks)
    return blocks, total


def main():
    img = Image.new("RGB", (SIZE, SIZE), PAPER)
    draw = ImageDraw.Draw(img)

    # double border, like a printed invitation card
    draw.rectangle([28, 28, SIZE - 29, SIZE - 29], outline=TEAL, width=3)
    draw.rectangle([40, 40, SIZE - 41, SIZE - 41], outline=ACCENT, width=2)

    small_font = font("NotoSans-Regular.ttf", 22)

    # House art at the top, then the text blocks fitted and centred
    # in the space between the house and the footer line.
    house_h = 118
    footer_y = SIZE - 84
    top = 66
    draw_house(draw, SIZE // 2, top, 150, 84)
    content_top = top + house_h
    content_bottom = footer_y - 28

    body_size = 33
    while body_size >= 26:
        blocks, total = layout_blocks(draw, body_size)
        if total <= content_bottom - content_top:
            break
        body_size -= 1
    else:
        blocks, total = layout_blocks(draw, body_size)

    y = content_top + (content_bottom - content_top - total) // 2
    text_w = SIZE - 2 * MARGIN
    for kind, lines, fnt, height in blocks:
        if kind == "title":
            tw = draw.textlength(lines[0], font=fnt)
            draw.text(((SIZE - tw) / 2, y), lines[0], font=fnt, fill=ACCENT)
        elif kind == "rule":
            draw.line([MARGIN + 120, y + 8, SIZE - MARGIN - 120, y + 8],
                      fill=TEAL, width=2)
        elif kind == "greet":
            draw.text((MARGIN, y), lines[0], font=fnt, fill=INK)
        elif kind == "body":
            line_h = fnt.size + 12
            for i, line in enumerate(lines):
                draw.text((MARGIN, y + i * line_h), line, font=fnt, fill=INK)
        elif kind == "sign":
            sw = draw.textlength(lines[0], font=fnt)
            draw.text((SIZE - MARGIN - sw, y), lines[0], font=fnt, fill=INK)
        elif kind == "ps":
            pw = draw.textlength(lines[0], font=fnt)
            draw.text(((SIZE - pw) / 2, y), lines[0], font=fnt, fill=ACCENT)
        y += height

    # footer small print
    footer = "ONE IMAGE  \u00b7  ONE OPEN DOOR  \u00b7  DINNER AT SEVEN"
    fw = draw.textlength(footer, font=small_font)
    draw.text(((SIZE - fw) / 2, footer_y), footer,
              font=small_font, fill=SOFT)

    img.save("entry.png", format="PNG", optimize=True)
    print("wrote entry.png (body font %d)" % body_size)


if __name__ == "__main__":
    main()
