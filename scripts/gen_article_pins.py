#!/usr/bin/env python3
"""Generate pin images for articles that don't have one yet (RSS/Pinterest/Дзен).

Reads posts from Supabase, HEAD-checks each article's deterministic pin URL
(https://…/pinterest/pin-<slug>.jpg) for idempotency, and for any missing pin
picks a topic-matched source image, builds a 2:3 pin via gen_pins.build_pin,
and uploads to Supabase alina-media/pinterest/pin-<slug>.jpg.

MUST run under a python with Pillow + requests — cron uses .venv-tts/bin/python
(NOT /usr/bin/python3, which lacks Pillow).

Usage: python3 scripts/gen_article_pins.py [--dry-run] [--limit N]
"""
import io
import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pins import build_pin, resolve_source, load_creds, PUBLIC_BASE  # noqa: E402

PIN_BASE = PUBLIC_BASE + "/pinterest"
FLAT_PLATE = "/home/hermes/alina-body/alina-media/illustrations/flat/овощи-тарелка-белки-углеводы.jpg"

# topic keyword (regex, matched against lowercased title) -> source image
SOURCES = [
    (r"простуд|болезн|температур|иммунитет|выздоровлен", "char/portrait-smile.jpg"),
    (r"ягодиц|поп(а|ы|у)|glute", "char/squat.jpg"),
    (r"пресс|живот|планк", "char/plank.jpg"),
    (r"растяжк|гибкост|шпагат|мобильност", "char/stretch.jpg"),
    (r"разминк|сустав|заминк", "char/stretch.jpg"),
    (r"рук(и|ами)|трицепс|бицепс", "char/resistance-band.jpg"),
    (r"резинк|эспандер|петл", "char/resistance-band.jpg"),
    (r"спин(а|ы|е)|поясниц|осанк|холка|сутул", "char/confident.jpg"),
    (r"кардио|прыжк|пульс|бег|интервал", "char/side-plank.jpg"),
    (r"пилатес|йог", "char/stretch.jpg"),
    (r"стоп|свод|плоскостоп|голеностоп", "char/lunge.jpg"),
    (r"ног(и|ами)|ляшк|бедр|присед|выпад", "char/lunge.jpg"),
    (r"цикл|месячн|гормон|женск", "char/casual.jpg"),
    (r"сон|вечер|перед сном|бессониц", "char/portrait-smile.jpg"),
    (r"шаг|ходьб|прогулк", "char/outdoor.jpg"),
    (r"белок|питани|еда|рацион|рецепт|продукт|кбжу|калори", f"local:{FLAT_PLATE}"),
    (r"целлюлит", "char/lunge.jpg"),
    (r"бросить|мотивац|привычк|дисциплин|регулярн", "char/master-alina.jpg"),
    (r"крепатур|мышц|боль|восстановлен", "char/post-workout.jpg"),
    (r"нач(ать|ат)|с нуля|нович", "char/sportswear.jpg"),
]
DEFAULT = "char/casual.jpg"


def pick_source(title):
    t = (title or "").lower()
    for pat, src in SOURCES:
        if re.search(pat, t):
            return src
    return DEFAULT


def main():
    dry = "--dry-run" in sys.argv
    limit = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), 0)

    url, key = load_creds()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}

    r = requests.get(
        f"{url}/rest/v1/posts?select=slug,title&order=published_at.asc",
        headers=headers, timeout=30,
    )
    r.raise_for_status()
    posts = r.json()
    if limit:
        posts = posts[:limit]

    generated = skipped = failed = 0
    for p in posts:
        slug, title = p["slug"], p["title"]
        pin_url = f"{PIN_BASE}/pin-{slug}.jpg"
        try:
            if requests.head(pin_url, timeout=30, allow_redirects=True).status_code == 200:
                skipped += 1
                continue
        except requests.RequestException:
            pass

        src = pick_source(title)
        if dry:
            print(f"[dry] {slug[:48]}  <- {src}")
            generated += 1
            continue
        try:
            img, mode = resolve_source(src)
            out = build_pin(img, mode, title)
        except Exception as e:
            failed += 1
            print(f"SKIP {slug[:48]}: source failed: {e}")
            continue

        buf = io.BytesIO()
        out.save(buf, "JPEG", quality=88, optimize=True)
        up = requests.post(
            f"{url}/storage/v1/object/alina-media/pinterest/pin-{slug}.jpg",
            headers={
                "Authorization": f"Bearer {key}", "apikey": key,
                "x-upsert": "true", "Content-Type": "image/jpeg",
            },
            data=buf.getvalue(), timeout=120,
        )
        if up.status_code in (200, 201):
            generated += 1
            print(f"[+] {slug[:48]}  <- {src}")
        else:
            failed += 1
            print(f"[!] {slug[:48]} upload {up.status_code}: {up.text[:150]}")

    print(f"\nDone: {generated} generated, {skipped} already present, {failed} failed")


if __name__ == "__main__":
    main()
