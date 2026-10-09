#!/usr/bin/env python3
"""Пакетная генерация сета персонажа Алины (параллельно) через kie.ai."""
import os, json, time, urllib.request

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
REF = "https://alina-body.fitness/images/hero-alina.jpg"
OUT_DIR = "/home/hermes/alina-body/content/char"
MODEL = "nano-banana-2"
ASPECT = "3:4"
RES = "2K"
BASE = "The same woman as in the reference image (same face, same hair, same body type) "

SHOTS = {
    "lunge": BASE + "performing a forward lunge, side profile, black leggings and a grey sports top, bright home living room, photorealistic, natural daylight, full body shot",
    "plank": BASE + "holding a forearm plank on a yoga mat, black leggings and a dark sports top, bright home setting, photorealistic, natural light, full body shot",
    "glute-bridge": BASE + "doing a glute bridge on a yoga mat, black leggings and a pink sports top, bright home setting, photorealistic, full body shot",
    "stretch": BASE + "stretching with both arms raised overhead, light blue sports outfit, bright home, photorealistic, full body shot",
    "resistance-band": BASE + "doing a lateral band walk with a fabric resistance band around her thighs, black leggings and a sports top, bright home, photorealistic, full body shot",
    "side-plank": BASE + "holding a side plank on a yoga mat, maroon sports top and black leggings, bright home, photorealistic, full body shot",
    "sportswear": BASE + "standing in a stylish matching sportswear set (pastel leggings and sports bra), confident pose, bright minimal studio background, photorealistic, fashion fitness photography, full body shot",
    "casual": BASE + "standing in a casual outfit of blue jeans and a white t-shirt, relaxed smile, bright home background, photorealistic, lifestyle photography, full body shot",
    "post-workout": BASE + "after a workout wiping her face with a small towel and holding a water bottle, smiling, wearing sports clothes, bright home setting, photorealistic, candid fitness photography",
    "outdoor": BASE + "standing in a green park with trees in the background, wearing sportswear, golden hour sunlight, photorealistic, outdoor fitness photography, full body shot",
    "confident": BASE + "standing with arms crossed and a confident smile, black sports outfit, bright studio background, photorealistic, professional fitness photography, full body shot",
    "portrait-smile": BASE + "close-up head-and-shoulders portrait with a warm genuine smile looking at camera, soft natural light, photorealistic",
}


def load_key():
    for line in open(ENV):
        if "=" in line and not line.strip().startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("kie.ai ключ не найден")


def req(url, key, payload=None):
    headers = {"Authorization": "Bearer " + key}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    r = urllib.request.Request(url, data=data, headers=headers)
    return json.loads(urllib.request.urlopen(r, timeout=30).read())


def main():
    key = load_key()
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Отправляем все задачи (параллельно)
    tasks = {}
    for name, prompt in SHOTS.items():
        inp = {"prompt": prompt, "aspect_ratio": ASPECT, "resolution": RES, "output_format": "jpg", "image_input": [REF]}
        r = req(f"{API}/api/v1/jobs/createTask", key, {"model": MODEL, "input": inp})
        if r.get("code") != 200:
            print(f"  {name}: createTask fail {json.dumps(r)[:200]}", flush=True)
            continue
        tasks[name] = r["data"]["taskId"]
        print(f"  {name}: отправлено", flush=True)

    print(f"Отправлено задач: {len(tasks)}", flush=True)

    # 2. Поллинг всех до завершения
    done = {}
    deadline = time.time() + 900
    while tasks and time.time() < deadline:
        time.sleep(8)
        for name in list(tasks.keys()):
            tid = tasks[name]
            try:
                info = req(f"{API}/api/v1/jobs/recordInfo?taskId={tid}", key)
            except Exception as e:
                print(f"  {name}: poll error {e}", flush=True)
                continue
            d = info.get("data", {})
            st = d.get("state")
            if st in ("success", "fail"):
                done[name] = d
                del tasks[name]
                print(f"  {name}: {st}", flush=True)

    # 3. Скачиваем
    ok, bad = [], []
    for name, d in done.items():
        if d.get("state") != "success":
            bad.append((name, "fail"))
            continue
        urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
        if not urls:
            bad.append((name, "no urls"))
            continue
        try:
            path = os.path.join(OUT_DIR, f"{name}.jpg")
            urllib.request.urlretrieve(urls[0], path)
            ok.append(name)
        except Exception as e:
            bad.append((name, str(e)[:80]))

    print(f"\nГОТОВО: {len(ok)} успешно, {len(bad)} ошибок")
    for n in ok:
        print(f"  + {n}.jpg")
    for n, err in bad:
        print(f"  ! {n}: {err}")
    if tasks:
        print(f"Таймаут: не завершились {list(tasks.keys())}")


if __name__ == "__main__":
    main()
