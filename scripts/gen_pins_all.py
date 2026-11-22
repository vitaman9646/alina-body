#!/usr/bin/env python3
"""Один CSV на все 37 пинов курса: даты с сегодня, ~3 пина/день в пределах 14 дней."""
import json, os, csv
from datetime import date, timedelta

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
HOST = "https://alina-body.fitness/pins2"
LANDING = "https://alina-body.fitness/course/budget-pp"
BOARD = "Бюджетное ПП"
OUT = f"{ROOT}/content/pinterest-budget-pp-all.csv"

items = []
for m in DATA["modules"]:
    for les in m["lessons"]:
        s = les["slug"]
        if os.path.exists(f"{ROOT}/inbox/budget-pp-images/{s}.png"):
            items.append((s, les.get("unique", {}).get("unique_title") or les["title"],
                          les.get("unique", {}).get("intro", "")))

n = len(items)
n_days = 14
start = date.today()  # с сегодняшнего дня
base = n // n_days
extra = n % n_days

dates = []
for d in range(n_days):
    cnt = base + (1 if d < extra else 0)
    dates += [start + timedelta(days=d)] * cnt

rows = []
for (slug, title, intro), d in zip(items, dates):
    desc = intro.split(".")[0].strip() + ". Полный рецепт с граммовками и КБЖУ — в курсе «Бюджетное ПП»."
    rows.append({
        "Title": title,
        "Media URL": f"{HOST}/course-{slug}.jpg",
        "Pinterest board": BOARD,
        "Thumbnail": "",
        "Description": desc,
        "Link": f"{LANDING}?utm_content={slug}",
        "Publish date": d.isoformat(),
        "Keywords": f"{title.lower()}, пп, правильное питание, рецепты, бюджетное пп",
    })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["Title", "Media URL", "Pinterest board", "Thumbnail",
                                      "Description", "Link", "Publish date", "Keywords"])
    w.writeheader()
    w.writerows(rows)

from collections import Counter
c = Counter(r["Publish date"] for r in rows)
print(f"пинов: {len(rows)}")
print(f"даты: {rows[0]['Publish date']} .. {rows[-1]['Publish date']} ({n_days} дней)")
print("по дням:", dict(sorted(c.items())))
print("→", OUT)
