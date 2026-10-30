#!/usr/bin/env python3
"""Обложки 5 категорий «Еда на ходу» (Pillow, 0 кр) -> alina-media/swbandco-food/cover-<slug>.jpg.

Текстовые обложки: название категории + описание + список блюд + CTA на канал.
"""
import json
import os
import sys
import requests

from PIL import Image, ImageDraw, ImageFont

REPO = "/home/hermes/alina-body"
SRC = f"{REPO}/content/swbandco-food-recipes.json"
OUT_DIR = "/home/hermes/alina-body/alina-media/swbandco-food"

FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

PINK = "#E75480"
DARK = "#2D2D2D"
GRAY = "#6B6B6B"
BG = "#FFF7F9"

W, H = 1080, 1350

CATS = {
    "1-lanchi":      ("Холодные ланчи без разогрева", "Сытные ссобойки, которые не нужно греть: собрал утром — ешь днём."),
    "2-termos":      ("Горячие обеды для термоса", "Согревающие супы, рагу и боулы, которые доезжают тёплыми."),
    "3-na-hodu":     ("Еда на ходу", "Врапы, роллы и сэндвичи без глютена и магазинного майонеза."),
    "4-salad-banka": ("Салат в банке", "Многослойный салат: заправка на дне, зелень наверху, встряхнул — и съел."),
    "5-perekusy":    ("Здоровые перекусы", "Сладости без сахара и энергетики без химии."),
}


def font(size, bold=False):
    p = FONT_DIRS[1] if bold else FONT_DIRS[0]
    return ImageFont.truetype(p, size)


def wrap(text, fnt, maxw, draw):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    recipes = json.load(open(SRC))
    by_key = {}
    for r in recipes:
        by_key.setdefault(r["category_key"], []).append(r["name"])

    for key, (title, desc) in CATS.items():
        names = by_key.get(key, [])
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        # бренд
        d.text((80, 70), "ALINA BODY", font=font(40, True), fill=PINK)
        # разделитель
        d.rectangle((80, 140, W - 80, 146), fill=PINK)

        # заголовок
        y = 200
        for line in wrap(title, font(64, True), W - 160, d):
            d.text((80, y), line, font=font(64, True), fill=DARK)
            y += 78
        y += 20
        for line in wrap(desc, font(38), W - 160, d):
            d.text((80, y), line, font=font(38), fill=GRAY)
            y += 50
        y += 30

        # счётчик рецептов
        d.text((80, y), f"{len(names)} рецептов", font=font(44, True), fill=PINK)
        y += 80

        # список блюд в 2 колонки
        col_w = (W - 200) // 2
        half = (len(names) + 1) // 2
        cols = [names[:half], names[half:]]
        y0 = y
        for ci, col in enumerate(cols):
            yy = y0
            for nm in col:
                for line in wrap("• " + nm, font(30), col_w, d):
                    d.text((80 + ci * (col_w + 40), yy), line, font=font(30), fill=DARK)
                    yy += 42
                yy += 8

        # низ CTA
        d.rectangle((0, H - 130, W, H), fill=PINK)
        cta = "Больше рецептов и меню — в Telegram: t.me/alinabodyfree"
        d.text((80, H - 95), cta, font=font(34, True), fill="white")

        out = os.path.join(OUT_DIR, f"cover-{key}.jpg")
        img.save(out, "JPEG", quality=90)
        print(f"OK cover-{key}.jpg ({len(names)} блюд)")


if __name__ == "__main__":
    main()
