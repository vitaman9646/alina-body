#!/usr/bin/env python3
"""Generate photoreal dish photos for the 17 ПП-рецепты + write public/recipes.json.

Reads /tmp/recipes.json (name/ingredients/method/category), computes a Latin slug,
generates a photoreal food photo (kie.ai nano-banana-2, 3:4, 2K) per recipe,
uploads to Supabase alina-media/recipes-photo/<slug>.jpg (idempotent via HEAD),
and writes public/recipes.json (deployed data for the SPA + prerender).

Usage: python3 scripts/gen_recipe_photos.py [--dry-run] [--limit N]
"""
import io
import json
import os
import re
import sys
import time
import urllib.request

import requests

REPO = "/home/hermes/alina-body"
SRC = "/tmp/recipes.json"
OUT_JSON = f"{REPO}/public/recipes.json"
API = "https://api.kie.ai"
MODEL = "nano-banana-2"

# transliteration (same as publish_articles.py)
TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# English dish description per recipe (for the food-photo prompt)
DISH_EN = {
    "Вафли из кабачка": "golden zucchini waffles on a plate",
    "ПП-оливье": "light healthy olivier salad in a bowl",
    "Дорада с луком и грибами": "baked sea bream with onions and mushrooms",
    "Высокобелковый омлет": "high-protein omelet with fresh herbs",
    "Костный бульон": "clear golden bone broth in a bowl",
    "Паста из кабачков с креветками": "zucchini noodles with shrimp in tomato sauce",
    "Куриный паштет": "chicken liver pate spread on toast",
    "Пицца на лаваше": "thin lavash pizza with chicken and tomatoes",
    "ПП-булочка с ягодами": "cottage cheese bun with fresh berries",
    "Брауни из яблок": "chocolate brownie square, dark cocoa",
    "Ботат — индейка с болгарским перцем": "roasted turkey with bell peppers",
    "Грудка с кефиром и сыром": "baked chicken breast with cheese and tomatoes",
    "ПП-вафли из творога": "cottage cheese waffles stack",
    "Пирог из говядины в лаваше": "golden lavash pie with beef filling",
    "Свёкла, запечённая с луком и чесноком": "roasted beets with red onion",
    "Хачапури по-аджарски": "adjarian khachapuri with runny egg",
    "Телятина, тушённая с овощами": "braised veal with vegetables",
}


def slugify(text):
    out = []
    for ch in text.lower().strip():
        if ch in TRANS:
            out.append(TRANS[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in " -—–":
            out.append("-")
    s = re.sub(r"-+", "-", "".join(out)).strip("-")
    return s or "recipe"


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def load_supa():
    d = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d["SUPABASE_URL"], d["SUPABASE_SERVICE_ROLE_KEY"]


def gen_food_photo(key, dish_en):
    inp = {"prompt": f"Photoreal food photography of {dish_en}, top-down angle, natural daylight, on a ceramic plate, appetizing, shallow depth of field, no text, no watermark", "aspect_ratio": "3:4", "resolution": "2K", "output_format": "jpg"}
    req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": MODEL, "input": inp}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        return None, json.dumps(r)[:200]
    task = r["data"]["taskId"]
    for _ in range(60):
        time.sleep(6)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/jobs/recordInfo?taskId={task}",
            headers={"Authorization": "Bearer " + key}), timeout=30).read())
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if urls:
                return urls[0], None
        if d.get("state") == "fail":
            return None, json.dumps(d)[:200]
    return None, "timeout"


def main():
    dry = "--dry-run" in sys.argv
    limit = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), 0)

    recipes = json.load(open(SRC))
    if limit:
        recipes = recipes[:limit]

    key = load_key()
    supa_url, supa_key = load_supa()
    photo_base = f"{supa_url}/storage/v1/object/public/alina-media/recipes-photo"

    out_recipes = []
    for i, r in enumerate(recipes, 1):
        name = r["name"]
        slug = slugify(name)
        dish_en = DISH_EN.get(name, name)
        photo_url = f"{photo_base}/{slug}.jpg"

        # idempotent: skip if photo exists
        try:
            if not dry and requests.head(photo_url, timeout=20, allow_redirects=True).status_code == 200:
                print(f"[{i}/{len(recipes)}] {name}: exists, skip")
        except requests.RequestException:
            pass
        else:
            if dry:
                print(f"[dry] {name}: would generate ({dish_en})")
            else:
                tmp_url, err = gen_food_photo(key, dish_en)
                if err:
                    print(f"[{i}] {name}: GEN FAIL {err}")
                else:
                    img = requests.get(tmp_url, timeout=60).content
                    up = requests.post(
                        f"{supa_url}/storage/v1/object/alina-media/recipes-photo/{slug}.jpg",
                        headers={"Authorization": f"Bearer {supa_key}", "apikey": supa_key,
                                 "x-upsert": "true", "Content-Type": "image/jpeg"},
                        data=img, timeout=120)
                    status = "ok" if up.status_code in (200, 201) else f"FAIL {up.status_code}"
                    print(f"[{i}/{len(recipes)}] {name}: photo {status}")

        out_recipes.append({
            "slug": slug, "name": name, "category": r.get("category", ""),
            "ingredients": r.get("ingredients", ""), "method": r.get("method", ""),
            "image": photo_url,
        })

    if not dry:
        json.dump(out_recipes, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nWrote {len(out_recipes)} recipes -> {OUT_JSON}")


if __name__ == "__main__":
    main()
