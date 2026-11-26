#!/usr/bin/env python3
"""Генерит обложку курса «Смузи на каждый случай» и грузит в Supabase.

Коллаж 2×2 из 4 фото смузи + тёмный градиент + заголовок/подзаголовок.
Запуск: .venv-tts/bin/python scripts/gen_smoothie_cover.py
"""
import os, io, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

SB_URL = SB_KEY = None
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line.startswith("SUPABASE_URL="):
        SB_URL = line.split("=", 1)[1].strip()
    if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
        SB_KEY = line.split("=", 1)[1].strip()

PUB = f"{SB_URL}/storage/v1/object/public/alina-media/smoothie"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# 4 фото разных цветов для сетки
SHOTS = ["tropicheskiy", "svekolno-granatovy", "chernichno-mindalny", "zeleny-ovoshchnoy"]

W, H = 1200, 800


def fetch(slug):
    data = urllib.request.urlopen(f"{PUB}/{slug}.jpg", timeout=60).read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def cover_cell(img, w, h):
    """Вписать фото в ячейку w×h с обрезкой по центру (object-cover)."""
    sw, sh = img.size
    r = max(w / sw, h / sh)
    nw, nh = int(sw * r), int(sh * r)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return img.crop((x, y, x + w, y + h))


def main():
    canvas = Image.new("RGB", (W, H), (20, 20, 20))
    cells = [(0, 0), (1, 0), (0, 1), (1, 1)]
    cw, ch = W // 2, H // 2
    for (cx, cy), slug in zip(cells, SHOTS):
        img = fetch(slug)
        img = cover_cell(img, cw, ch)
        # чуть притемнить фото
        img = ImageEnhance.Brightness(img).enhance(0.92)
        canvas.paste(img, (cx * cw, cy * ch))

    # тёмный градиент сверху вниз по всей обложке (для читаемости текста)
    overlay = Image.new("L", (1, H), 0)
    for y in range(H):
        # сильнее затемнение сверху и снизу, слабее в центре
        t = abs(y / H - 0.5) * 2  # 0 в центре, 1 у краёв
        overlay.putpixel((0, y), int(150 * t + 60))
    overlay = overlay.resize((W, H))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    canvas = Image.composite(black, canvas, overlay)

    draw = ImageDraw.Draw(canvas)
    title_f = ImageFont.truetype(FONT, 72)
    sub_f = ImageFont.truetype(FONT_REG, 34)
    tag_f = ImageFont.truetype(FONT, 26)

    title = "Смузи на каждый случай"
    sub = "15 напитков под любую задачу"

    # тег сверху
    tag = "ALINA BODY · ПИТАНИЕ"
    draw.text((60, 48), tag, font=tag_f, fill=(255, 255, 255))

    # заголовок по центру-низу
    tb = draw.textbbox((0, 0), title, font=title_f)
    tw = tb[2] - tb[0]
    draw.text(((W - tw) // 2, H - 210), title, font=title_f, fill=(255, 255, 255))

    sb = draw.textbbox((0, 0), sub, font=sub_f)
    sw = sb[2] - sb[0]
    draw.text(((W - sw) // 2, H - 130), sub, font=sub_f, fill=(240, 235, 228))

    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    data = buf.getvalue()

    req = urllib.request.Request(f"{SB_URL}/storage/v1/object/alina-media/smoothie/cover.jpg",
        data=data, method="POST",
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120)
    print(f"OK: {PUB}/cover.jpg ({len(data)} bytes)")


if __name__ == "__main__":
    main()
