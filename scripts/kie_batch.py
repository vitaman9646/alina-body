#!/usr/bin/env python3
"""Сет Алины: разные причёски/одежда/локации под каждое место на сайте."""
import os, json, time, urllib.request

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
REF = "https://alina-body.fitness/images/hero-alina.jpg"
OUT_DIR = "/home/hermes/alina-body/content/char"
MODEL = "nano-banana-2"
ASPECT = "3:4"
RES = "2K"
BASE = "The same woman as in the reference image (same face) "

SHOTS = {
    # hero — спорт-лук, уверенная, светлая студия
    "sportswear": BASE + "standing confidently in a bright modern gym studio, hair in a high ponytail, matching pastel sports set (leggings and sports bra), relaxed confident smile, photorealistic full-body shot, fashion fitness photography",
    # мини-курсы — присед дома
    "squat": BASE + "doing a bodyweight squat in a bright home living room, side profile, hair in a messy bun, black leggings and a grey sports top, photorealistic, natural daylight, full-body shot",
    # об Алине — повседневный, кафе
    "casual": BASE + "sitting relaxed at a cozy cafe with a cup of tea, hair down in soft waves, blue jeans and a cream knit sweater, warm genuine smile, photorealistic, lifestyle photography",
    # выпад — парк
    "lunge": BASE + "doing a forward lunge outdoors in a green park, side profile, hair in a high ponytail, navy athleisure set, golden daylight, photorealistic, full-body shot",
    # планка — дома на коврике
    "plank": BASE + "holding a forearm plank on a yoga mat at home, hair in a low bun, black sports top and leggings, photorealistic, natural light, full-body shot",
    # ягодичный мостик — дома
    "glute-bridge": BASE + "doing a glute bridge on a yoga mat at home, hair in a ponytail, pink sports top and black leggings, photorealistic, full-body shot",
    # растяжка — студия
    "stretch": BASE + "stretching with both arms raised overhead in a bright gym studio, hair down, light blue sports outfit, photorealistic, full-body shot",
    # резинка — дома
    "resistance-band": BASE + "doing a lateral band walk with a fabric resistance band around her thighs, hair in a messy bun, black leggings and a white tank top, bright home, photorealistic, full-body shot",
    # боковая планка — дома, на полу
    "side-plank": BASE + "holding a side plank on a yoga mat, firmly grounded on the floor propped on her forearm, hair in a ponytail, maroon sports top and black leggings, bright home, photorealistic, full-body shot",
    # после тренировки — дома
    "post-workout": BASE + "after a workout, sitting on a yoga mat wiping her face with a small towel, hair in a messy bun, gentle tired smile, water bottle beside her, wearing sports clothes, bright home, photorealistic",
    # улица — парк, бег
    "outdoor": BASE + "jogging lightly on a path in a green park, hair in a ponytail, bright running outfit, golden hour sunlight, photorealistic, outdoor fitness photography, full-body shot",
    # уверенная — студия
    "confident": BASE + "standing with arms crossed and a confident smile, hair down, black sports outfit, bright studio background, photorealistic, professional fitness photography, full-body shot",
    # портрет — крупно, улыбка
    "portrait-smile": BASE + "close-up head-and-shoulders portrait with a warm genuine smile, hair down with soft waves, soft natural window light, photorealistic",
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


if __name__ == "__main__":
    main()
