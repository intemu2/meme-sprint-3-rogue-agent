#!/usr/bin/env python3
"""Build-time font extraction (NOT used at runtime by main.py).

Reads DejaVu Sans Bold (free license, Bitstream Vera based, shipped with
the OS at /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf) with PIL,
renders each needed glyph at 200 px into a 1-bit bitmap, and injects the
packed glyph table into main.py, replacing the line containing
`FONT = {}  # __FONT_TABLE__`.

Provenance: only the bitmap outlines of the listed characters are embedded;
no font file is shipped in the repo. The runtime program is pure stdlib and
never touches the system fonts, so its output is identical in the grader
sandbox (which has no PIL and no DejaVu).

Run from this directory:  python3 make_font.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SIZE = 200
CHARSET = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
           " .,:;-#()'!?/")
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "..", "main.py")
PLACEHOLDER = "FONT = {}  # __FONT_TABLE__"


def main():
    font = ImageFont.truetype(FONT_PATH, SIZE)
    ascent, _descent = font.getmetrics()
    lines = ["FONT_SIZE = %d" % SIZE]
    cap_h = None
    total_bytes = 0
    for ch in CHARSET:
        adv = font.getlength(ch)
        if ch == " ":
            lines.append(" %r: (%r, 0, 0, 0, '')," % (ch, adv))
            continue
        im = Image.new("1", (360, 360), 0)
        d = ImageDraw.Draw(im)
        d.text((0, 0), ch, font=font, anchor="la", fill=1)
        bb = im.getbbox()
        if bb is None:
            lines.append(" %r: (%r, 0, 0, 0, '')," % (ch, adv))
            continue
        x0, y0, x1, y1 = bb
        w, h = x1 - x0, y1 - y0
        dy = y0 - ascent  # glyph top relative to the baseline (<= 0)
        px = im.load()
        bits = bytearray()
        for yy in range(y0, y1):
            acc = 0
            n = 0
            for xx in range(x0, x1):
                acc = (acc << 1) | (1 if px[xx, yy] else 0)
                n += 1
                if n == 8:
                    bits.append(acc)
                    acc = 0
                    n = 0
            if n:
                bits.append(acc << (8 - n))
        total_bytes += len(bits)
        if ch == "H":
            cap_h = h
        lines.append(" %r: (%r, %d, %d, %d, %r)," % (ch, adv, w, h, dy, bits.hex()))
    lines.insert(1, "CAP_H = %d" % cap_h)
    table = "\n".join(lines[:2]) + "\nFONT = {\n" + "\n".join(lines[2:]) + "\n}\n"
    with open(MAIN, "r", encoding="utf-8") as f:
        src = f.read()
    if PLACEHOLDER not in src:
        print("STOP: placeholder not found in main.py")
        sys.exit(1)
    with open(MAIN, "w", encoding="utf-8") as f:
        f.write(src.replace(PLACEHOLDER, table.rstrip("\n")))
    print("injected %d glyphs (%d bitmap bytes), CAP_H=%d into %s"
          % (len(CHARSET), total_bytes, cap_h, MAIN))


if __name__ == "__main__":
    main()
