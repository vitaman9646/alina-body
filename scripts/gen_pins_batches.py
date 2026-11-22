#!/usr/bin/env python3
"""Генерит 3 партии Pinterest CSV (14+14+9 пинов, каждая в 14-дневном окне)."""
import json, os, csv
from datetime import date, timedelta

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
HOST = "https://alina-body.fitness/pins"
LANDING = "https://alina-body.fitness/course/budget-pp"
BOARD = "Бюджетное ПП"

slugs = []
for m in DATA["modules"]:
    for les in m["lessons"]:
        s = les["slug"]
        if os.path.exists(f"{ROOT}/inbox/budget-pp-images/{s}.png"):
            slugs.append((s, les.get("unique", {}).get("unique_title") or les["title"],
                          les.get("unique", {}).get("intro", "")))

BATCHES = [
    ("1", 0, 14, date.today() + timedelta(days=1)),           # 14.11..
    ("2", 14, 28, date.today() + timedelta(days=15)),          # 28.11..
    ("3", 28, 37, date.today() + timedelta(days=29)),          # 12.12..
]

for tag, a, b, start in BATCHES:
    batch = slugs[a:b]
    rows = []
    for i, (slug, title, intro) in enumerate(batch, 1):
        desc = intro.split(".")[0].strip() + ". Полный рецепт с граммовками и КБЖУ — в курсе «Бюджетное ПП»."
        rows.append({
            "Title": title,
            "Media URL": f"{HOST}/course-{slug}.jpg",
            "Pinterest board": BOARD,
            "Thumbnail": "",
            "Description": desc,
            "Link": f"{LANDING}?utm_content={slug}",
            "Publish date": (start + timedelta(days=i - 1)).isoformat(),
            "Keywords": f"{title.lower()}, пп, правильное питание, рецепты, бюджетное пп",
        })
    out = f"{ROOT}/content/pinterest-budget-pp-{tag}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Title", "Media URL", "Pinterest board", "Thumbnail",
                                          "Description", "Link", "Publish date", "Keywords"])
        w.writeheader()
        w.writerows(rows)
    print(f"партия {tag}: {len(rows)} пинов, {start.isoformat()} .. {(start+timedelta(days=len(batch)-1)).isoformat()} → {out}")
