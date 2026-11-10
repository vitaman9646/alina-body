#!/usr/bin/env python3
"""Карточки смузи для каруселей Threads (3:4, 1000×1500).

На каждый смузи 2 карточки: «Ингредиенты» и «Когда пить». Сохраняет локально в
alina-media/smoothie/cards/ и заливает в Supabase alina-media/smoothie/cards/.
Читает content/smoothie-recipes.json. Использование: python3 gen_smoothie_cards.py [--dry-run]
"""
import io
import json
import os
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

REPO = "/home/hermes/alina-body"
SRC = f"{REPO}/content/smoothie-recipes.json"
LOCAL = f"{REPO}/alina-media/smoothie/cards"
W, H = 1000, 1500
M = 80

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
BOX = (245, 229, 233)


def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_header(d, name, subtitle):
    d.text((W // 2, 90), "ALINA BODY", font=font(52), fill=ACCENT, anchor="mm")
    d.text((W // 2, 150), subtitle, font=font(34, False), fill=MUTED, anchor="mm")
    d.line([(M, 190), (W - M, 190)], fill=ACCENT, width=4)
    d.text((W // 2, 270), name.upper(), font=font(58), fill=TEXT, anchor="mm")


def ingredients_card(s, img_url):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    draw_header(d, s["name"], "СМУЗИ · ИНГРЕДИЕНТЫ")
    y = 380
    f = font(36, False)
    d.text((M, y), "ИНГРЕДИЕНТЫ", font=font(40), fill=ACCENT, anchor="lm")
    y += 78
    for it in s["ingredients"]:
        for ln in wrap(d, "• " + it, f, W - 2 * M):
            d.text((M, y), ln, font=f, fill=TEXT, anchor="lm")
            y += 54
    footer(d, y)
    return img


def when_card(s, method, img_url):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    draw_header(d, s["name"], "СМУЗИ · КОГДА ПИТЬ")
    y = 380
    d.text((M, y), "КОГДА ПИТЬ", font=font(40), fill=ACCENT, anchor="lm")
    y += 78
    f = font(42, False)
    for ln in wrap(d, s["when"], f, W - 2 * M):
        d.text((M, y), ln, font=f, fill=TEXT, anchor="lm")
        y += 64
    y += 40
    # метод
    box_top = y
    for ln in wrap(d, method, font(36, False), W - 2 * M - 48):
        d.text((M + 24, y), ln, font=font(36, False), fill=ACCENT, anchor="lm")
        y += 52
    d.rounded_rectangle([M, box_top - 12, W - M, y + 12], radius=20, outline=ACCENT, width=3)
    y += 40
    footer(d, y)
    return img


def footer(d, y):
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3)
    d.text((W // 2, y + 30), "Полный конструктор — в закрепе канала", font=font(32, False), fill=MUTED, anchor="mm")
    d.text((W // 2, H - 60), "alina-body.fitness", font=font(30, False), fill=MUTED, anchor="mm")


def load_supa():
    env = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip()
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_ROLE_KEY"]


def main():
    dry = "--dry-run" in sys.argv
    data = json.load(open(SRC, encoding="utf-8"))
    method = data["method"]
    smoothies = data["smoothies"]
    supa, skey = load_supa()
    os.makedirs(LOCAL, exist_ok=True)

    made = 0
    for s in smoothies:
        slug = s["slug"]
        cards = [("1", ingredients_card(s, ""), "ингредиенты"),
                 ("2", when_card(s, method, ""), "когда")]
        for suffix, img, label in cards:
            fname = f"{slug}-{suffix}.jpg"
            if dry:
                print(f"[dry] {fname} ({label})")
                made += 1
                continue
            local_path = f"{LOCAL}/{fname}"
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=90, optimize=True, progressive=True)
            with open(local_path, "wb") as f:
                f.write(buf.getvalue())
            r = requests.post(
                f"{supa}/storage/v1/object/alina-media/smoothie/cards/{fname}",
                headers={"Authorization": f"Bearer {skey}", "apikey": skey,
                         "x-upsert": "true", "Content-Type": "image/jpeg"},
                data=buf.getvalue(), timeout=120)
            st = "ok" if r.status_code in (200, 201) else f"FAIL {r.status_code}"
            print(f"[+] {fname} ({label}) {st}")
            made += 1

    print(f"\nГотово: {made} карточек")


if __name__ == "__main__":
    main()
