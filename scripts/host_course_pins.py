#!/usr/bin/env python3
"""Хостит пины курса на alina-body.fitness/pins/ и перегенерирует Pinterest CSV с этими URL."""
import json, os, csv, urllib.request
from datetime import date, timedelta

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
OUT_DIR = f"{ROOT}/public/pins"
OUT_CSV = f"{ROOT}/content/pinterest-budget-pp.csv"
SRC = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
HOST = "https://alina-body.fitness/pins"
LANDING = "https://alina-body.fitness/course/budget-pp"
BOARD = "Бюджетное ПП"

os.makedirs(OUT_DIR, exist_ok=True)

slugs = []
for m in DATA["modules"]:
    for les in m["lessons"]:
        s = les["slug"]
        if os.path.exists(f"{ROOT}/inbox/budget-pp-images/{s}.png"):
            slugs.append((s, les.get("unique", {}).get("unique_title") or les["title"],
                          les.get("unique", {}).get("intro", "")))

start = date.today() + timedelta(days=1)
rows = []
for i, (slug, title, intro) in enumerate(slugs, 1):
    data = urllib.request.urlopen(f"{SRC}/course-{slug}.jpg", timeout=60).read()
    open(f"{OUT_DIR}/course-{slug}.jpg", "wb").write(data)
    desc = intro.split(".")[0].strip() + ". Полный рецепт с граммовками и КБЖУ — в курсе «Бюджетное ПП»."
    rows.append({
        "Title": title,
        "Media URL": f"{HOST}/course-{slug}.jpg",
        "Pinterest board": BOARD,
        "Thumbnail": "",
        "Description": desc,
        "Link": LANDING,
        "Publish date": (start + timedelta(days=i - 1)).isoformat(),
        "Keywords": f"{title.lower()}, пп, правильное питание, рецепты, бюджетное пп",
    })

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "Title", "Media URL", "Pinterest board", "Thumbnail",
        "Description", "Link", "Publish date", "Keywords"])
    w.writeheader()
    w.writerows(rows)
print(f"скопировано пинов: {len(rows)} → {OUT_DIR}/")
print(f"CSV: {OUT_CSV} ({len(rows)} пинов, Media URL = alina-body.fitness/pins/...)")
