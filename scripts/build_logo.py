#!/usr/bin/env python3
"""Собирает логотип Alina Body: квадратная иконка + горизонтальный логотип."""
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/hermes/alina-body/alina-media/brand"
ICON_SRC = f"{OUT}/logo-icon.jpg"

CORAL = (232, 131, 122, 255)     # #E8837A
CREAM = (251, 240, 218, 255)     # #FBF0DA
INK   = (45, 42, 50, 255)        # #2D2A32
GREY  = (120, 113, 108, 255)

icon = Image.open(ICON_SRC).convert("RGB")

# ── 1. Квадратная иконка 512×512 (эмблема в круге на белом) ──
S = 512
sq = Image.new("RGB", (S, S), (255, 255, 255))
src = icon.resize((S, S), Image.LANCZOS)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse((4, 4, S - 4, S - 4), fill=255)
sq.paste(src, (0, 0), mask)
sq.save(f"{OUT}/logo-icon.png", optimize=True)
print("OK logo-icon.png")

# ── 2. Горизонтальный логотип 1200×360 ──
W, H = 1200, 360
lg = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(lg)

# эмблема в круге слева
R = 150
circ = icon.resize((2 * R, 2 * R), Image.LANCZOS)
cmask = Image.new("L", (2 * R, 2 * R), 0)
ImageDraw.Draw(cmask).ellipse((3, 3, 2 * R - 3, 2 * R - 3), fill=255)
cx, cy = 40 + R, H // 2
lg.paste(circ, (40, cy - R), cmask)
# обводка круга
d.ellipse((40 + 2, cy - R + 2, 40 + 2 * R - 2, cy + R - 2), outline=CORAL, width=5)

# текст справа
font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 84)
font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
tx = 40 + 2 * R + 44
# "Alina Body" с коралловым акцентом
d.text((tx, cy - 70), "Alina Body", font=font_big, fill=INK)
# подпись
d.text((tx + 4, cy + 34), "фитнес  ·  питание  ·  забота о себе", font=font_tag, fill=GREY)
# тонкая коралловая линия-акцент слева от подписи
d.rectangle((tx + 4, cy + 52, tx + 4 + 640, cy + 58), fill=CORAL)

lg.save(f"{OUT}/logo-horizontal.png", optimize=True)
print("OK logo-horizontal.png")
