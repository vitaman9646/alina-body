#!/usr/bin/env python3
"""Скачивает пины курса из Supabase и пакует в ZIP (для ручной загрузки в Pinterest)."""
import json, os, urllib.request, zipfile

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
OUT_DIR = "/tmp/budget-pp-pins"
ZIP_PATH = f"{ROOT}/content/budget-pp-pins.zip"
BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"

os.makedirs(OUT_DIR, exist_ok=True)

# порядок уроков с фото
slugs = []
for m in DATA["modules"]:
    for les in m["lessons"]:
        s = les["slug"]
        if os.path.exists(f"{ROOT}/inbox/budget-pp-images/{s}.png"):
            slugs.append(s)

zf = zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED)
n = 0
for i, s in enumerate(slugs, 1):
    url = f"{BASE}/course-{s}.jpg"
    data = urllib.request.urlopen(url, timeout=60).read()
    name = f"{i:02d}-{s}.jpg"
    zf.writestr(name, data)
    n += 1
zf.close()
print(f"в ZIP: {n} пинов → {ZIP_PATH}")
print(f"порядок: {' .. '.join(f'{i:02d}' for i in range(1, n+1))}")
