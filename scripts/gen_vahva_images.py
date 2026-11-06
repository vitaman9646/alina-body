#!/usr/bin/env python3
"""Генерация 111 flat-иллюстраций упражнений Vahva в стиле Gemini (faceless flat vector).

Читает content/vahva-fitness.json (англ. названия + cues) → генерит flux-3/klein-text-to-image
(1.6 кр/шт) → сохраняет в alina-media/vahva/exercise/<slug>.jpg + маппинг content/vahva-image-map.json.

Запуск: python3 scripts/gen_vahva_images.py
"""
import json, os, time, re, urllib.request, urllib.error

API = "https://api.kie.ai"
SRC = "/home/hermes/alina-body/content/vahva-fitness.json"
OUT_DIR = "/home/hermes/alina-body/alina-media/vahva/exercise"
MAP = "/home/hermes/alina-body/content/vahva-image-map.json"

STYLE = ("Flat vector illustration, modern minimal fitness editorial style, faceless female figure with no "
         "facial features, side profile, slim elongated athletic proportions, dark plum hair in a ponytail "
         "with a small coral hair tie, coral-pink sports bra, sage green leggings, white sneakers with coral "
         "soles, peach-coral skin, plain solid cream background, large empty margins, soft blurred beige "
         "ellipse shadow on the floor, no outlines, no black strokes, flat two-tone shading only, no "
         "gradients, no text, no numbers, no arrows, square 1:1, centered single figure, clean negative space")


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет ключа kie.ai")


def post(key, path, payload):
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def get(key, path):
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + key})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def main():
    key = load_key()
    data = json.load(open(SRC))

    # уникальные упражнения (англ. имена)
    uniq = {}
    for ph in data["phases"]:
        for wk in ph["weeks"]:
            for day in wk["days"]:
                for e in day["exercises"]:
                    k = e["name"].strip().lower()
                    if k not in uniq:
                        uniq[k] = e

    items = sorted(uniq.items())
    print(f"уникальных упражнений: {len(items)}")

    os.makedirs(OUT_DIR, exist_ok=True)
    bal = get(key, "/api/v1/chat/credit"); print("баланс до:", bal.get("data"), "кр")

    # 1) отправить все задачи
    submitted = []  # (slug, tid)
    for name, e in items:
        slug = slugify(name)
        cue = (e.get("cues") or [""])[0]
        prompt = f"{STYLE} A young woman doing a {name}." + (f" Technique: {cue}" if cue else "")
        inp = {"prompt": prompt, "aspect_ratio": "1:1"}
        try:
            r = post(key, "/api/v1/jobs/createTask", {"model": "flux-3/klein-text-to-image", "input": inp})
            submitted.append((slug, r["data"]["taskId"]))
        except Exception as ex:
            print(f"  !! submit {slug}: {ex}")
    print(f"отправлено: {len(submitted)}")

    # 2) поллить до готовности (параллельно обрабатываются на стороне kie)
    results = {}  # slug -> url | None
    pending = submitted[:]
    t0 = time.time()
    while pending and time.time() - t0 < 900:
        still = []
        for slug, tid in pending:
            try:
                d = get(key, f"/api/v1/jobs/recordInfo?taskId={tid}").get("data", {})
            except Exception:
                still.append((slug, tid)); continue
            st = d.get("state")
            if st == "success":
                results[slug] = (d["response"].get("resultUrls") or [None])[0]
            elif st == "fail":
                results[slug] = None
            else:
                still.append((slug, tid))
        pending = still
        if pending:
            time.sleep(5)
    for slug, tid in pending:
        results[slug] = None  # таймаут

    # 3) скачать
    ok = fail = 0
    mapping = {}
    for slug, url in results.items():
        if not url:
            fail += 1; continue
        dst = os.path.join(OUT_DIR, f"{slug}.jpg")
        try:
            urllib.request.urlretrieve(url, dst)
            ok += 1
            mapping[slug] = dst
        except Exception as ex:
            fail += 1
            print(f"  !! download {slug}: {ex}")

    json.dump({"generated": mapping, "total": len(items)}, open(MAP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    bal2 = get(key, "/api/v1/chat/credit")
    print(f"\nготово: {ok} ок, {fail} ошибок из {len(items)}")
    print(f"баланс после: {bal2.get('data')} кр (потрачено {round(bal.get('data')-bal2.get('data'),1)} кр)")
    print(f"маппинг: {MAP}")


if __name__ == "__main__":
    main()
