#!/usr/bin/env python3
"""Генерация фото Алины для упражнений из распарсенного PDF.

Для каждого упражнения генерит фото Алины (каноничное лицо face-young-1 в
image_input) с позой из описания. Название + промпт пока заданы вручную по
тексту (авто-вывод через DeepSeek — следующий шаг для потока).

Использование:
  .venv-tts/bin/python scripts/gen_exercise_images.py JSON --only "1,6"   # тест
  .venv-tts/bin/python scripts/gen_exercise_images.py JSON                # все
"""
import os, sys, json, time, argparse, urllib.request

API = "https://api.kie.ai"
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
BASE = "The same young woman as in the reference image (same face) "
OUT = "/home/hermes/alina-body/content/exercises"

# Упражнения «Стройность и рельеф. Тренировка №2» (7 шт) — имя + английский промпт
EXERCISES = {
    "1": {
        "name": "Приседание плие",
        "prompt": BASE + "doing a plie squat on a yoga mat: feet wider than shoulders, toes turned outward, lowering into a half-squat with back straight, hands on her hips, high ponytail, black leggings and a pastel pink sports top, bright home living room, natural daylight, photorealistic, full-body shot",
    },
    "2": {
        "name": "Присед с гантелью и махом руки",
        "prompt": BASE + "doing a squat holding one dumbbell: feet wider than shoulders, toes turned out, one hand on her hip, the other arm lowering the dumbbell between her knees on the way down then swinging it forward and slightly up as she stands, high ponytail, grey sports set, bright home, natural light, photorealistic, full-body shot",
    },
    "3": {
        "name": "Вращение с весом вокруг головы",
        "prompt": BASE + "holding a single dumbbell with both hands and circling it around her head, in a lunge stance with one leg forward and one back, centered posture, messy bun, black leggings and a white tank top, bright home, natural light, photorealistic, full-body shot",
    },
    "4": {
        "name": "Наклон в сторону с гантелью над головой",
        "prompt": BASE + "standing with feet wider than shoulders, one arm extended straight overhead holding a dumbbell, bending sideways reaching toward the floor with the free hand, low ponytail, maroon sports top and black leggings, bright home, natural light, photorealistic, full-body shot",
    },
    "5": {
        "name": "Выпад назад скольжением",
        "prompt": BASE + "doing a reverse sliding lunge on a yoga mat: standing balanced on one leg, sliding the other foot straight back along the floor, back straight, hair in a bun, teal sports set, bright home, natural light, photorealistic, full-body shot",
    },
    "6": {
        "name": "Планка на четвереньках с прыжком",
        "prompt": BASE + "in a bear plank on a yoga mat: on all fours with hands under shoulders and knees lifted off the floor, hips low, shifting hips side to side and hopping slightly on the toes, messy bun, black sports top and leggings, bright home, natural light, photorealistic, full-body shot",
    },
    "7": {
        "name": "Медвежья походка",
        "prompt": BASE + "doing a bear crawl on a yoga mat: on all fours with knees hovering just off the floor, stepping opposite hand and foot forward then back, back flat, high ponytail, dark grey sports set, bright home, natural light, photorealistic, full-body shot",
    },
}

SKIP_TITLES = {"Платформа", "Сообщество", "Библиотека", "не в Клубе?"}


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.strip().startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("kie.ai ключ не найден")


def gen(key, prompt, out_path, timeout=600):
    inp = {"prompt": prompt, "aspect_ratio": "3:4", "resolution": "2K", "output_format": "jpg"}
    inp["image_input"] = [REF]
    req = urllib.request.Request(
        f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": "nano-banana-2", "input": inp}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        return None, json.dumps(r)[:400]
    task = r["data"]["taskId"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(8)
        info = json.loads(urllib.request.urlopen(
            urllib.request.Request(f"{API}/api/v1/jobs/recordInfo?taskId={task}",
                                   headers={"Authorization": "Bearer " + key}), timeout=30).read())
        d = info.get("data", {})
        st = d.get("state")
        if st == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if not urls:
                return None, "нет resultUrls"
            urllib.request.urlretrieve(urls[0], out_path)
            return out_path, None
        if st == "fail":
            return None, json.dumps(d)[:400]
    return None, "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--only", help="через запятую номера упражнений, напр. 1,6")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(args.json_path))
    sections = [s for s in data["sections"] if s["title"] not in SKIP_TITLES]

    # сопоставить «N. Упражнение» → номер
    only = set(args.only.split(",")) if args.only else None
    key = load_key()

    results = []
    for s in sections:
        m = None
        import re
        m = re.match(r"(\d+)\.\s*Упражнение", s["title"])
        if not m:
            continue
        num = m.group(1)
        if only and num not in only:
            continue
        ex = EXERCISES.get(num)
        if not ex:
            continue
        out_path = f"{OUT}/exercise-{num}.jpg"
        print(f"[{num}] {ex['name']} …", flush=True)
        path, err = gen(key, ex["prompt"], out_path)
        if err:
            print(f"  ❌ {err}")
            continue
        results.append({"num": num, "name": ex["name"], "path": path})
        print(f"  ✅ {path}")

    print(f"\nготово: {len(results)}")
    for r in results:
        print(f"  {r['num']}. {r['name']} → {r['path']}")


if __name__ == "__main__":
    main()
