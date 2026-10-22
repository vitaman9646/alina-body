#!/usr/bin/env python3
"""Скачивает видео-рецепты SWBAND.CO (07–27) — всё, кроме введений/тренировок/рекомендаций."""
import re, os, urllib.parse, requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
URL = "https://cloud.mail.ru/public/MFud/poTzXCfEN"
OUT = "/home/hermes/alina-body/inbox/swbandco-fitness/video"
os.makedirs(OUT, exist_ok=True)

EXCLUDE = ["введение", "тренировк", "екомендаци", "рекомендаци"]

s = requests.Session(); s.headers.update({"User-Agent": UA})
r = s.get(URL, timeout=60); r.raise_for_status()
wg = re.search(r'"weblink_get"[^}]*"url"\s*:\s*"([^"]+)"', r.text).group(1)
data = s.get("https://cloud.mail.ru/api/v4/public/list",
             params={"weblink": "MFud/poTzXCfEN", "sort": "name", "order": "asc",
                     "offset": "0", "limit": "500", "version": "4"}, timeout=60).json()
items = data.get("list", []) or (data.get("body", {}) or {}).get("list", [])

def dl_url(wl):
    safe = "/".join(urllib.parse.quote(p, safe="") for p in wl.split("/"))
    return f"{wg}/{safe}"

n = 0
for it in items:
    if it.get("type") != "file" or not it["name"].lower().endswith(".mp4"):
        continue
    name = it["name"]
    if any(x in name.lower() for x in EXCLUDE):
        continue
    dst = os.path.join(OUT, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 1000000:
        print(f"  skip (уже есть): {name}"); continue
    r = s.get(dl_url(it["weblink"]), allow_redirects=True, stream=True, timeout=120)
    if "html" in r.headers.get("Content-Type", "").lower():
        mm = re.search(r'https?://[^"\'\s]+datacloudmail[^"\'\s]+', r.text[:30000])
        if mm:
            r = s.get(mm.group(0), allow_redirects=True, stream=True, timeout=120)
        else:
            print(f"  !! {name}: HTML без ссылки"); continue
    with open(dst, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    n += 1
    print(f"  OK {name}: {os.path.getsize(dst)} байт")

print(f"готово: скачано {n} рецептов")
