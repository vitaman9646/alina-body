#!/usr/bin/env python3
"""Пины Pinterest для 45 рецептов «Еда на ходу» (фото блюда + название).

Читает /tmp/swbandco_food_photos.json, reuses gen_pins.build_pin (cover-crop + градиент + title),
заливает в alina-media/pinterest/recipe-<slug>.jpg. Доска: «Еда на ходу».
"""
import io
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pins import build_pin, resolve_source, load_creds  # noqa: E402

SRC = "/tmp/swbandco_food_photos.json"


def main():
    dry = "--dry-run" in sys.argv
    url, key = load_creds()
    recipes = json.load(open(SRC))

    made = 0
    for r in recipes:
        slug = r["slug"]
        name = r["name"]
        fname = f"recipe-{slug}.jpg"
        if dry:
            print(f"[dry] {fname} <- {name}")
            made += 1
            continue
        try:
            img, mode = resolve_source(f"recipes-photo/{slug}.jpg")
            out = build_pin(img, mode, name)
        except Exception as e:
            print(f"SKIP {name}: {e}")
            continue
        buf = io.BytesIO()
        out.save(buf, "JPEG", quality=88, optimize=True)
        up = requests.post(
            f"{url}/storage/v1/object/alina-media/pinterest/{fname}",
            headers={"Authorization": f"Bearer {key}", "apikey": key,
                     "x-upsert": "true", "Content-Type": "image/jpeg"},
            data=buf.getvalue(), timeout=120)
        st = "uploaded" if up.status_code in (200, 201) else f"FAIL {up.status_code}"
        print(f"[+] {fname} <- {name}  {st}")
        made += 1

    print(f"\nDone: {made} pins")


if __name__ == "__main__":
    main()
