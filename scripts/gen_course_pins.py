#!/usr/bin/env python3
"""Пины Pinterest для курса «Бюджетное ПП»: 2:3 из фото блюд + CSV (1 пин/день).

Читает budget-pp-unique.json (slug + unique_title + intro), из локальных PNG
inbox/budget-pp-images/<slug>.png делает пин 1000×1500 с заголовком, льёт в
alina-media/pinterest/course-<slug>.jpg и пишет CSV content/pinterest-budget-pp.csv.
"""
import os, json, csv, io, urllib.request
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/hermes/alina-body"
IMG = f"{ROOT}/inbox/budget-pp-images"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
OUT_CSV = f"{ROOT}/content/pinterest-budget-pp.csv"
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
LANDING = "https://alina-body.fitness/course/budget-pp"
BOARD = "Бюджетное ПП"
BOARD_KW = "пп, правильное питание, рецепты, бюджетное пп"

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line and "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
SB_URL = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_pin(src, title):
    img = Image.open(src).convert("RGB")
    W, H = 1000, 1500
    # кроп в 2:3 по центру
    tw, th = img.size
    target = W / H
    cur = tw / th
    if cur > target:  # шире — режем ширину
        nw = int(th * target)
        x0 = (tw - nw) // 2
        img = img.crop((x0, 0, x0 + nw, th))
    else:  # выше — режем высоту
        nh = int(tw / target)
        y0 = (th - nh) // 2
        img = img.crop((0, y0, tw, y0 + nh))
    img = img.resize((W, H), Image.Resampling.LANCZOS)

    # заголовок: кремовая плашка снизу
    d = ImageDraw.Draw(img)
    tf = ImageFont.truetype(FONT_B, 52)
    lines = wrap(d, title.upper(), tf, W - 120)
    bh = len(lines) * 64 + 72
    d.rectangle([0, H - bh, W, H], fill=(253, 247, 241))
    d.rectangle([0, H - bh, W, H - bh + 8], fill=(214, 122, 140))
    y = H - bh + 30
    for ln in lines:
        d.text((W // 2, y), ln, font=tf, fill=(56, 44, 50), anchor="mm")
        y += 64
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


def upload(slug, data):
    req = urllib.request.Request(f"{SB_URL}/storage/v1/object/alina-media/pinterest/course-{slug}.jpg",
        data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120)
    return f"{PIN_BASE}/course-{slug}.jpg"


def main():
    # собрать уроки с фото (в порядке курса)
    items = []
    for m in DATA["modules"]:
        for les in m["lessons"]:
            slug = les["slug"]
            png = f"{IMG}/{slug}.png"
            if os.path.exists(png):
                items.append((slug, les.get("unique", {}).get("unique_title") or les["title"],
                              les.get("unique", {}).get("intro", "")))

    start = date.today() + timedelta(days=1)
    rows = []
    for i, (slug, title, intro) in enumerate(items):
        print(f"[{i+1}/{len(items)}] {slug}…", flush=True)
        data = make_pin(f"{IMG}/{slug}.png", title)
        url = upload(slug, data)
        desc = intro.split(".")[0].strip() + ". Полный рецепт с граммовками и КБЖУ — в курсе «Бюджетное ПП»."
        rows.append({
            "Title": title,
            "Media URL": url,
            "Pinterest board": BOARD,
            "Thumbnail": "",
            "Description": desc,
            "Link": LANDING,
            "Publish date": (start + timedelta(days=i)).isoformat(),
            "Keywords": f"{title.lower()}, {BOARD_KW}",
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Title", "Media URL", "Pinterest board", "Thumbnail",
            "Description", "Link", "Publish date", "Keywords"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nпинов: {len(rows)} → {OUT_CSV}")
    print(f"расписание: {start.isoformat()} .. {rows[-1]['Publish date']} (1/день)")


if __name__ == "__main__":
    main()
