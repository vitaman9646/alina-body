#!/usr/bin/env python3
"""Перегенерирует Pinterest CSV корректно: уникальные ссылки (utm_content) + 14-дневное окно."""
import json, os, csv
from datetime import date, timedelta

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
OUT_CSV = f"{ROOT}/content/pinterest-budget-pp.csv"
HOST = "https://alina-body.fitness/pins"
LANDING = "https://alina-body.fitness/course/budget-pp"
BOARD = "Бюджетное ПП"
DAYS = 14  # Pinterest: максимум 14 дней вперёд

slugs = []
for m in DATA["modules"]:
    for les in m["lessons"]:
        s = les["slug"]
        if os.path.exists(f"{ROOT}/inbox/budget-pp-images/{s}.png"):
            slugs.append((s, les.get("unique", {}).get("unique_title") or les["title"],
                          les.get("unique", {}).get("intro", "")))

batch = slugs[:DAYS]  # первая партия (14 пинов, 1/день)
start = date.today() + timedelta(days=1)

rows = []
for i, (slug, title, intro) in enumerate(batch, 1):
    desc = intro.split(".")[0].strip() + ". Полный рецепт с граммовками и КБЖУ — в курсе «Бюджетное ПП»."
    rows.append({
        "Title": title,
        "Media URL": f"{HOST}/course-{slug}.jpg",
        "Pinterest board": BOARD,
        "Thumbnail": "",
        "Description": desc,
        "Link": f"{LANDING}?utm_content={slug}",  # уникальная ссылка на пин
        "Publish date": (start + timedelta(days=i - 1)).isoformat(),
        "Keywords": f"{title.lower()}, пп, правильное питание, рецепты, бюджетное пп",
    })

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "Title", "Media URL", "Pinterest board", "Thumbnail",
        "Description", "Link", "Publish date", "Keywords"])
    w.writeheader()
    w.writerows(rows)

print(f"CSV: {len(rows)} пинов (1/день, {start.isoformat()} .. {(start+timedelta(days=len(batch)-1)).isoformat()})")
print(f"осталось пинов на следующие партии: {len(slugs) - len(batch)}")
