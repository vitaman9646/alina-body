#!/usr/bin/env python3
"""Generate photoreal dish photos for the 51 ПП-сборник recipes (OCR'd from cards).

Reads /tmp/recipes51.json (from ocr_recipes.py), cleans the names (trim КБЖУ noise),
maps each dish to an English food-photo prompt, generates a 1K photo (nano-banana-2,
8 cr — cheaper than the 17-recipe 2K batch), uploads to alina-media/recipes-photo/<slug>.jpg,
and writes /tmp/recipes51_clean.json.

Usage: python3 scripts/gen_recipe_photos51.py [--dry-run] [--limit N]
"""
import json
import os
import re
import sys
import time
import urllib.request

import requests

REPO = "/home/hermes/alina-body"
SRC = "/tmp/recipes51.json"
OUT = "/tmp/recipes51_clean.json"
API = "https://api.kie.ai"
MODEL = "nano-banana-2"

TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# clean recipe name -> English dish description
DISH_EN = {
    "СЫРНИКИ": "cottage cheese pancakes (syrniki), golden brown",
    "ТВОРОЖНАЯ ЗАПЕКАНКА": "cottage cheese casserole, golden top",
    "ОМЛЕТ ОВОЩНОЙ": "vegetable omelet with peppers and herbs",
    "ХАЧАПУРИ С ТВОРОГОМ": "cottage cheese khachapuri flatbread",
    "ОВСЯНОБЛИН С НАЧИНКОЙ": "oat pancake rolled with filling",
    "ШАУРМА С КУРИЦЕЙ": "chicken shawarma wrap",
    "ОЛАДУШКИ НА РИСОВОЙ МУКЕ": "small rice flour pancakes",
    "БИФШТЕКС": "beef steak, medium",
    "ТЫКВЕННЫЕ ВАФЛИ": "pumpkin waffles",
    "ШОКОЛАДНЫЕ БЛИНЧИКИ С ТВОРОЖНОЙ НАЧИНКОЙ": "chocolate crepes with cottage cheese filling",
    "БЕЛКОВЫЙ СУП ИЗ ФАСОЛИ И ТУНЦА": "white bean and tuna soup",
    "СУП-ПЮРЕ С КУРИЦЕЙ И БРОККОЛИ": "creamy chicken broccoli soup",
    "ПП-БОРЩ": "chicken borscht soup",
    "ОВОЩНОЙ СУП": "vegetable soup",
    "ТЫКВЕННЫЙ СУП": "creamy pumpkin soup",
    "ЗАЛИВНОЙ ПИРОГ С КУРИЦЕЙ И ГРИБАМИ": "chicken and mushroom pie",
    "ГРЕЧКА С МЯСОМ + ОВОЩНОЙ САЛАТ": "buckwheat with meat and side salad",
    "ПЕЧЁНОЧНЫЙ ТОРТ": "liver cake layers",
    "КУРИНАЯ ГРУДКА ПОД СМЕТАННОЙ ШАПОЧКОЙ": "chicken breast with creamy mushroom sauce",
    "СОЧНАЯ СТРУЧКОВАЯ ФАСОЛЬ + СПАГЕТТИ": "green beans with spaghetti",
    "ЛЕНИВЫЕ ГОЛУБЦЫ": "lazy cabbage rolls in tomato sauce",
    "ПИЦЦА": "pizza with melted cheese",
    "СОЧНАЯ КУРИНАЯ ГРУДКА С СЫРОМ ФЕТА": "chicken breast with feta cheese and salad",
    "ФАРШИРОВАННЫЕ ПЕРЦЫ": "stuffed bell peppers",
    "МЯСО В ДУХОВКЕ": "tender roasted meat",
    "БУЛГУР С КУРИЦЕЙ": "bulgur with chicken and vegetables",
    "МИНТАЙ ЗАПЕЧЁННЫЙ": "baked pollock with sweet peppers",
    "КУРИЦА С ОВОЩНЫМ САЛАТОМ": "chicken with fresh vegetable salad",
    "ГРЕЧКА С МЯСОМ И ОВОЩАМИ": "buckwheat with meat and vegetables",
    "МАКАРОНЫ С МЯСОМ И ОВОЩАМИ": "pasta with meat and vegetables",
    "ТУШЁНАЯ ИНДЕЙКА С ОВОЩАМИ И КИНОА": "braised turkey with quinoa",
    "ТЁПЛЫЙ САЛАТ": "warm salad bowl",
    "СЛИВОЧНЫЙ МИНТАЙ": "creamy pollock fillet",
    "ЛЕГКИЙ ОВОЩНОЙ САЛАТ": "light vegetable salad with egg and chicken",
    "ТРЕСКА ЗАПЕЧЁННАЯ С ОВОЩАМИ": "baked cod with vegetables",
    "ДИЕТИЧЕСКИЙ САЛАТ": "fresh diet salad",
    "ПЕЧЕНЬ В СЛИВОЧНОМ СОУСЕ": "liver in cream sauce",
    "КУРИЦА В АПЕЛЬСИНОВОМ СОУСЕ": "chicken in orange sauce",
    "САЛАТ С ТУНЦОМ": "tuna salad",
    "ШАРЛОТКА": "apple charlotte cake",
    "ЧИЗКЕЙК": "cheesecake slice",
    "ОВСЯНЫЕ ПЕЧЕНЬКИ": "oatmeal cookies",
    "ЛИМОННОЕ ПЕЧЕНЬЕ": "lemon cookies",
    "ЯБЛОЧНЫЙ РУЛЕТ": "apple roll pastry",
    "ТЫКВЕННО-АПЕЛЬСИНОВАЯ ЗАПЕКАНКА": "pumpkin orange casserole",
    "ПИРОГ ИЗ МОРКОВИ И ЯБЛОК": "carrot apple pie",
    "НЕЖНЫЙ ШОКОЛАДНЫЙ ДЕСЕРТ": "chocolate dessert",
    "МРАМОРНЫЙ КЕКС": "marble pound cake",
    "ПП ОВСЯНЫЙ ХЛЕБ": "oat bread loaf",
    "БАНАНОВЫЕ СЫРНИКИ": "banana cottage cheese pancakes",
}

CAT_RE = [
    (r"суп|борщ|бульон", "СУПЫ"),
    (r"салат", "САЛАТЫ"),
    (r"печень|торт|шарлотка|чизкейк|печень|кекс|рулет|десерт|запеканка|вафли|сырник|блинчик|оладушк|овсяноблин|булочк|хлеб", "ЗАВТРАКИ И ДЕСЕРТЫ"),
]


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


def clean_name(name):
    n = name.strip()
    n = re.split(r"\s*(?:КБЖУ|Калори|Ккал|ккал|Белки|Жиры|Углеводы|Выход|разделить|если|на 1 порц)", n)[0].strip()
    n = re.sub(r"\s+\d+(?:\.\d+)?\s*$", "", n)
    n = re.sub(r"\s+С\s+[а-яё].*$", "", n)
    n = re.sub(r"[,\s]+$", "", n)
    return n


def category_of(name):
    for pat, cat in CAT_RE:
        if re.search(pat, name.lower()):
            return cat
    return "ОСНОВНЫЕ БЛЮДА"


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


def gen_food(key, dish_en):
    inp = {"prompt": f"Photoreal food photography of {dish_en}, top-down angle, natural daylight, on a ceramic plate, appetizing, shallow depth of field, no text, no watermark", "aspect_ratio": "3:4", "resolution": "1K", "output_format": "jpg"}
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

    raw = json.load(open(SRC))
    if limit:
        raw = raw[:limit]

    key = load_key()
    supa_url, supa_key = load_supa()
    photo_base = f"{supa_url}/storage/v1/object/public/alina-media/recipes-photo"

    out = []
    used_slugs = {}
    for i, r in enumerate(raw, 1):
        name = clean_name(r.get("name", ""))
        if not name:
            print(f"[{i}] SKIP (no name)")
            continue
        dish_en = next((v for k, v in sorted(DISH_EN.items(), key=lambda kv: -len(kv[0])) if k in name), "homemade healthy dish, appetizing")
        slug = slugify(name)
        if slug in used_slugs:
            used_slugs[slug] += 1
            slug = f"{slug}-{used_slugs[slug]}"
        else:
            used_slugs[slug] = 0
        photo_url = f"{photo_base}/{slug}.jpg"

        if dry:
            print(f"[dry] {name} -> {slug} ({dish_en})")
        else:
            try:
                if requests.head(photo_url, timeout=20, allow_redirects=True).status_code == 200:
                    print(f"[{i}] {name}: exists")
                else:
                    tmp_url, err = gen_food(key, dish_en)
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
                        print(f"[{i}] {name}: photo {status}")
            except Exception as e:
                print(f"[{i}] {name}: ERROR {e}")

        out.append({
            "slug": slug, "name": name, "category": category_of(name),
            "ingredients": r.get("ingredients", ""), "method": r.get("method", ""),
            "image": photo_url,
        })

    if not dry:
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nWrote {len(out)} -> {OUT}")


if __name__ == "__main__":
    main()
