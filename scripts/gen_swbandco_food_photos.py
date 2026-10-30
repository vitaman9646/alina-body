#!/usr/bin/env python3
"""Фото блюд для 45 рецептов SWBAND.CO «Еда на ходу» (kie.ai nano-banana-2, 1K = 8 кр).

Читает content/swbandco-food-recipes.json, генерирует фотореалистичное фото блюда
(3:4, 1K) на рецепт, загружает в Supabase alina-media/recipes-photo/<slug>.jpg
(идемпотентно через HEAD), пишет /tmp/swbandco_food_photos.json.
Без LLM — чисто API kie.ai + Supabase.
"""
import json
import os
import re
import sys
import time
import urllib.request

import requests

REPO = "/home/hermes/alina-body"
SRC = f"{REPO}/content/swbandco-food-recipes.json"
OUT = "/tmp/swbandco_food_photos.json"
API = "https://api.kie.ai"
MODEL = "nano-banana-2"

TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# Полное имя рецепта -> английское описание блюда для промпта (food photography)
DISH_EN = {
    "Боул с пшеном, печеной тыквой, куриным филе и семечковым песто": "millet bowl with roasted pumpkin, chicken and sunflower seed pesto",
    "Салат из белой фасоли с вареным яйцом, печеным перцем и петрушкой": "white bean salad with boiled egg, roasted pepper and parsley",
    "Картофельный салат с куриным бедром, яйцом и соленым огурцом": "potato salad with chicken thigh, egg and pickled cucumber",
    "Зеленая гречка с горбушей в собственном соку, огурцом и укропом": "green buckwheat with salmon, cucumber and dill",
    "Салат из красной чечевицы с печеной свеклой, яйцом и квашеной капустой": "red lentil salad with roasted beetroot, egg and sauerkraut",
    "Нутовый боул с куриной печенью и сезонными овощами": "chickpea bowl with chicken liver and seasonal vegetables",
    "Овощная деревенская фриттата с кабачком и зеленью": "rustic vegetable frittata with zucchini and herbs",
    "Бурый рис с тушеным кальмаром, брокколи и кунжутом": "brown rice with braised squid, broccoli and sesame",
    "Салат из фасоли с запеченной скумбрией и маринованным луком": "bean salad with baked mackerel and pickled onion",
    "Оладьи из кабачка и моркови с паштетом из куриных сердечек": "zucchini carrot fritters with chicken heart pate",
    "Боул из зеленой гречки с тушеной индейкой и квашеными овощами": "green buckwheat bowl with braised turkey and fermented vegetables",
    "Пряный чечевичный суп с тыквой, имбирем и куркумой": "spiced lentil soup with pumpkin, ginger and turmeric",
    "Боул с печеной тыквой, пекинской капустой, яйцом и подсолнечным соусом": "bowl with roasted pumpkin, cabbage, egg and sunflower sauce",
    "Деревенский суп минестроне с белой фасолью и пекинской капустой": "rustic minestrone soup with white beans and cabbage",
    "Крем-суп из цветной капусты и кабачка на кокосовом молоке с куриным филе": "creamy cauliflower zucchini coconut soup with chicken",
    "Осеннее рагу из индейки с корнеплодами и розмарином": "autumn turkey stew with root vegetables and rosemary",
    "Быстрое карри из нута и кабачка в кокосовом соусе": "quick chickpea zucchini curry in coconut sauce",
    "Чили кон карне из говяжьего фарша с красной фасолью": "chili con carne with ground beef and red beans",
    "Зеленый овощной боул с брокколи, стручковой фасолью и яйцом всмятку": "green vegetable bowl with broccoli, green beans and soft egg",
    "Теплый боул из цветной капусты с яйцом пашот и соусом из печеного перца": "warm cauliflower bowl with poached egg and roasted pepper sauce",
    "Шакшука-боул томатное рагу с перцем, шпинатом и яйцами": "shakshuka bowl with tomato ragout, peppers, spinach and eggs",
    "Омлетный ролл с куриным филе, огурцом и зеленью": "omelet roll with chicken, cucumber and herbs",
    "Лодочки из салата с пряным говяжьим фаршем и перцем": "lettuce boats with spiced ground beef and peppers",
    "Врап из рисовой бумаги с кальмаром, морковью и подсолнечным кремом": "rice paper wrap with squid, carrot and sunflower cream",
    "Блинчик из зеленой гречки с печеночным паштетом и соленым огурцом": "green buckwheat crepe with liver pate and pickle",
    "Омлетный конверт с горбушей, шпинатом и дижонской горчицей": "omelet envelope with salmon, spinach and mustard",
    "Кабачковые вафли с запеченной скумбрией и зеленым луком": "zucchini waffles with baked mackerel and green onion",
    "Морковно-тыквенные маффины с куриным фаршем и тмином": "carrot pumpkin muffins with chicken and cumin",
    "Вафли из цветной капусты с паштетом из белой фасоли и розмарином": "cauliflower waffles with white bean pate and rosemary",
    "Свекольно-льняные лепешки с отварным яйцом и руколой": "beet flax flatbread with boiled egg and arugula",
    "«Грин-ролл» в листьях савойской капусты с индейкой и перцем": "green roll in savoy cabbage with turkey and pepper",
    "Салат с картофелем, свеклой, красным луком и тунцом": "layered jar salad with potato, beetroot, red onion and tuna",
    "Банка с киноа, куриным бедром, печеным перцем, авокадо и фетой": "jar salad with quinoa, chicken, roasted pepper, avocado and feta",
    "Банка с крупой (булгур или безглютеновый аналог), лососем, оливками и руколой": "jar salad with bulgur, salmon, olives and arugula",
    "Банка с безмолочной «сметаной», зеленой гречкой, нутом, яйцом и салатом": "jar salad with dairy-free cream, buckwheat, chickpeas and egg",
    "Здоровая версия «Оливье» в банке": "healthy olivier salad in a jar",
    "Банка с домашним хумусом, печеным фалафелем и хрустящим салатом": "jar salad with hummus, baked falafel and crunchy greens",
    "Шоколадные батончики из инжира, грецкого ореха и сырого какао": "chocolate bars with fig, walnut and raw cocoa",
    "Трюфели из кураги и миндаля с кардамоном в кокосе": "apricot almond truffles with cardamom in coconut",
    "Энергетические шарики из чернослива и фундука с корицей": "energy balls with prune and hazelnut, cinnamon",
    "Семечковые козинаки из темного изюма с кунжутом": "sunflower seed brittle with dark raisins and sesame",
    "Ягодно-конопляный протеиновый смузи с лесными ягодами": "berry hemp protein smoothie",
    "Согревающий тыквенный протеин-латте с подсолнечной тахини": "warm pumpkin protein latte with sunflower tahini",
    "Рисовые шарики (онигири) с горбушей и кунжутом в нори": "onigiri rice balls with salmon and sesame in nori",
    "Золотистые онигири с куркумой, курицей и зеленью": "golden turmeric onigiri with chicken and herbs",
}

GENERIC = "homemade healthy dish, appetizing"


def slugify(text):
    out = []
    for ch in text.lower().strip():
        if ch in TRANS:
            out.append(TRANS[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in " -—–":
            out.append("-")
    return re.sub(r"-+", "-", "".join(out)).strip("-") or "recipe"


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
    inp = {
        "prompt": f"Photoreal food photography of {dish_en}, top-down angle, natural daylight, on a ceramic plate, appetizing, shallow depth of field, no text, no watermark",
        "aspect_ratio": "3:4", "resolution": "1K", "output_format": "jpg",
    }
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

    out = []
    for i, r in enumerate(recipes, 1):
        name = r["name"]
        slug = slugify(name)
        dish_en = DISH_EN.get(name, GENERIC)
        photo_url = f"{photo_base}/{slug}.jpg"
        if dry:
            print(f"[dry] {name} -> {slug}")
        else:
            try:
                if requests.head(photo_url, timeout=20, allow_redirects=True).status_code == 200:
                    print(f"[{i}/{len(recipes)}] {name}: exists")
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
                        st = "ok" if up.status_code in (200, 201) else f"FAIL {up.status_code}"
                        print(f"[{i}/{len(recipes)}] {name}: photo {st}")
            except Exception as e:
                print(f"[{i}] {name}: ERROR {e}")
        out.append({"slug": slug, "name": name, "category": r["category"],
                    "category_key": r["category_key"], "image": photo_url,
                    "kcal": r.get("kcal"), "bzhu": r.get("bzhu")})

    if not dry:
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nWrote {len(out)} -> {OUT}")


if __name__ == "__main__":
    main()
