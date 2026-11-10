#!/usr/bin/env python3
"""Фото 15 смузи (kie.ai nano-banana-2, 1K = 8 кр) для лид-магнита/курса.

Генерирует фотореалистичное фото смузи в стакане (3:4, 1K), сохраняет локально
в alina-media/smoothie/<slug>.jpg И заливает в Supabase alina-media/smoothie/<slug>.jpg
(идемпотентно через HEAD). Печатает баланс кредитов до/после.
"""
import json
import os
import sys
import time
import urllib.request

import requests

REPO = "/home/hermes/alina-body"
LOCAL_DIR = f"{REPO}/alina-media/smoothie"
API = "https://api.kie.ai"
MODEL = "nano-banana-2"

# slug -> полное английское описание для фото-промпта (смузи + гарнир + окружение)
SMOOTHIES = {
    "ogurechno-laymovy": "a light green refreshing cucumber lime mint smoothie, garnished with mint leaves and a lime wheel on the rim, surrounded by cucumber halves, lime wedges and a green apple",
    "tykvenno-pryany": "an orange creamy roasted pumpkin smoothie, dusted with cinnamon and a cardamom pod, surrounded by roasted pumpkin chunks, cinnamon sticks and a spoon of almond butter",
    "zeleny-ovoshchnoy": "a deep green vegetable smoothie of cucumber, celery, parsley and broccoli, garnished with a parsley sprig, surrounded by cucumber, celery stalks, broccoli florets and a lemon half",
    "chernichno-mindalny": "a thick blue-purple blueberry smoothie, topped with blueberries and chia seeds, surrounded by a handful of blueberries, spinach leaves and a spoon of almond butter",
    "kislo-zeleny-s-kivi": "a green kiwi spinach banana smoothie, topped with thin kiwi slices, surrounded by halved kiwis, spinach leaves and sorrel",
    "vesenniy-s-krapivoy": "a green nettle spinach cucumber smoothie with a faint orange tint from carrot juice, topped with a microgreens sprig, surrounded by fresh herbs, a kiwi and a carrot",
    "yabloko-kivi-s-avokado": "a creamy green avocado apple kiwi smoothie, topped with kiwi slices and chia seeds, surrounded by half an avocado and a green apple",
    "shokoladno-vishnevy": "a dark chocolate cherry smoothie, topped with cherries and a dusting of cocoa powder, surrounded by cherries, cocoa powder and a cinnamon stick",
    "svekolno-granatovy": "a ruby red beetroot pomegranate smoothie, topped with pomegranate seeds, surrounded by a halved beetroot, pomegranate, kiwi and a celery stalk",
    "yagodno-slivochny": "a pink raspberry blackberry smoothie, topped with berries and chia seeds, surrounded by raspberries, blackberries, romaine leaves and a cinnamon stick",
    "tropicheskiy": "a yellow-green tropical pineapple banana spinach smoothie, topped with a pineapple piece and chia seeds, surrounded by pineapple chunks, banana, lime and spinach leaves",
    "smorodinovy": "a dark purple blackcurrant smoothie, topped with blackcurrants and a parsley sprig, surrounded by a blackcurrant cluster, spinach leaves and a banana",
    "grushevo-tykvenny": "a golden orange creamy pear and roasted pumpkin smoothie, topped with flax seeds and a pinch of cinnamon, surrounded by a pear, pumpkin chunks, oat bran and almond butter",
    "kremovy-zeleny": "a green creamy smoothie of arugula, kale, avocado and coconut milk, topped with a pinch of cayenne and a ginger slice, surrounded by arugula, kale leaves, avocado half and a banana",
    "morkovno-apelsinovy": "a bright orange carrot orange pineapple smoothie, topped with orange zest, surrounded by young carrots, an orange, pineapple chunks, walnuts and ginger root",
}

PROMPT_SUFFIX = (" in a tall glass, natural daylight, light minimal background, "
                 "appetizing, shallow depth of field, no text, no watermark")


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("kie.ai ключ не найден")


def load_supa():
    d = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d["SUPABASE_URL"], d["SUPABASE_SERVICE_ROLE_KEY"]


def credit_balance(key):
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/chat/credit", headers={"Authorization": "Bearer " + key}),
            timeout=30).read())
        return r.get("data")
    except Exception as e:
        return f"err:{e}"


def gen_food(key, dish_en):
    inp = {
        "prompt": f"Photoreal food photography of {dish_en}{PROMPT_SUFFIX}",
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

    key = load_key()
    supa_url, supa_key = load_supa()
    photo_base = f"{supa_url}/storage/v1/object/public/alina-media/smoothie"
    os.makedirs(LOCAL_DIR, exist_ok=True)

    bal0 = credit_balance(key)
    print(f"Баланс до: {bal0}", flush=True)

    items = list(SMOOTHIES.items())
    if limit:
        items = items[:limit]

    for i, (slug, dish_en) in enumerate(items, 1):
        photo_url = f"{photo_base}/{slug}.jpg"
        local_path = f"{LOCAL_DIR}/{slug}.jpg"
        if dry:
            print(f"[dry] {slug}")
            continue
        try:
            if requests.head(photo_url, timeout=20, allow_redirects=True).status_code == 200:
                print(f"[{i}/{len(items)}] {slug}: exists (supabase)")
            else:
                tmp_url, err = gen_food(key, dish_en)
                if err:
                    print(f"[{i}] {slug}: GEN FAIL {err}")
                    continue
                img = requests.get(tmp_url, timeout=60).content
                with open(local_path, "wb") as f:
                    f.write(img)
                up = requests.post(
                    f"{supa_url}/storage/v1/object/alina-media/smoothie/{slug}.jpg",
                    headers={"Authorization": f"Bearer {supa_key}", "apikey": supa_key,
                             "x-upsert": "true", "Content-Type": "image/jpeg"},
                    data=img, timeout=120)
                st = "ok" if up.status_code in (200, 201) else f"FAIL {up.status_code}"
                print(f"[{i}/{len(items)}] {slug}: photo {st} ({len(img)} байт)")
        except Exception as e:
            print(f"[{i}] {slug}: ERROR {e}")

    if not dry:
        time.sleep(2)
        bal1 = credit_balance(key)
        print(f"Баланс после: {bal1}", flush=True)


if __name__ == "__main__":
    main()
