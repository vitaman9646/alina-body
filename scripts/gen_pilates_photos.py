#!/usr/bin/env python3
"""Генерация фото упражнений для курса «Пилатес дома для начинающих» + загрузка в Supabase.
Идемпотентно: существующие объекты пропускаются. Параллельно по 3 задачи.
"""
import os, json, time, io, urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]

REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"

REALISM = (
    "CRITICAL — realistic skin and texture: real human skin with visible pores, fine texture, "
    "subtle natural imperfections, even natural skin tone, NO redness or flush on the nose and face, "
    "faint under-eye shadows, tiny flyaway hairs around the hairline. Natural matte skin, NOT smooth, "
    "NOT airbrushed, NO plastic CGI look, NO beauty-filter smoothing, NO waxy 3D-render skin. "
    "Photorealistic photo shot on an iPhone, candid and lifelike, no text."
)

BASE = (
    "A young woman in her early twenties, athletic toned build, polished and well-groomed, "
    "confident model-like presence, sleek neat hair, "
)

EX = [
    ("pilates-warmup", "milk ribbed knit set, standing on a yoga mat raising both arms overhead and breathing in, bright minimal living room, front angle, loose low bun"),
    ("breathing-lying", "milk ribbed knit set, lying on her back on a yoga mat with knees bent, one hand on her stomach, breathing calmly, side angle, loose low bun"),
    ("pelvic-tilt", "powder pink sports bra and high-waist leggings, lying on a mat with knees bent, gently tilting the pelvis and pressing the lower back into the mat, side profile angle, low ponytail"),
    ("heel-slides", "sand leggings and a cream tank, lying on her back on a mat sliding one heel slowly along the floor, hips stable, side angle"),
    ("pilates-bridge", "powder pink sports bra and leggings, lying on a mat in a pilates bridge with hips lifted and ribs down, smooth spinal curve, side profile angle, low ponytail"),
    ("hundred", "mossy green sweatshirt and leggings, lying on a mat with knees bent and arms lifted low above the floor, doing small pumping arm movements, front angle, low bun"),
    ("chest-lift", "clay oversized tee and black bike shorts, lying on a mat with hands supporting the back of her head, lifting head and shoulder blades slightly, side angle"),
    ("knee-plank", "mossy green sweatshirt and leggings, holding a forearm plank on her knees on a mat, straight line from knees to head, side angle, low bun"),
    ("clamshell", "powder pink bra and leggings, lying on her side with knees bent and feet together, lifting the top knee like a clamshell, side angle"),
    ("side-leg-lift", "sand leggings and a cream tank, lying on her side with legs long, lifting the top leg, hips stacked, front angle"),
    ("leg-circles", "powder pink bra and leggings, lying on her side with the top leg raised, drawing small circles with the leg, hips still, front angle"),
    ("cat-cow", "milk ribbed knit set, on hands and knees on a mat arching and rounding her spine slowly, side angle, loose low bun"),
    ("swimming", "mossy green sweatshirt and leggings, lying on her stomach on a mat with arms extended forward, lifting the opposite arm and leg slightly, side angle"),
    ("sphinx", "clay oversized tee and bike shorts, lying on her stomach propped on forearms in a sphinx position, chest lifted, shoulders relaxed, side angle"),
    ("spine-twist", "powder pink bra and leggings, lying on her back on a mat with arms out to the sides and knees falling to one side, shoulders on the floor, front angle"),
    ("roll-down-wall", "milk ribbed knit set, standing with her back against a wall, slowly rolling down the spine with rounded back, side angle, loose low bun"),
    ("side-plank-knee", "clay oversized tee and bike shorts, side plank on her knees with elbow under shoulder, hips lifted, straight line, front angle"),
    ("cooldown", "cream waffle-knit loungewear, lying on a mat hugging both knees to her chest, relaxed face, three-quarter angle"),
    ("pilates-cover", "cream waffle-knit loungewear, sitting cross-legged on a yoga mat in a bright living room, hands resting on knees, warm friendly smile, three-quarter angle, soft natural window light"),
]


def api_req(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}
    data = None
    if payload is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=120).read())


def supabase_upload(path, image_bytes):
    url = f"{SUPA}/storage/v1/object/alina-media/course/{path}"
    req = urllib.request.Request(url, data=image_bytes, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120).read()


def compress(img_bytes):
    from PIL import Image
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    im.thumbnail((1200, 1600))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return buf.getvalue()


def one(item):
    slug, prompt = item
    pub = f"{SUPA}/storage/v1/object/public/alina-media/course/{slug}.jpg"
    try:
        urllib.request.urlopen(urllib.request.Request(pub, method="HEAD"), timeout=15)
        print(f"SKIP {slug}", flush=True)
        return slug, pub
    except Exception:
        pass
    full = BASE + prompt + ". " + REALISM
    try:
        r = api_req("https://api.kie.ai/api/v1/jobs/createTask", {
            "model": "nano-banana-2",
            "input": {"prompt": full, "image_input": [REF], "aspect_ratio": "3:4",
                      "resolution": "2K", "output_format": "jpg"},
        })
    except Exception as e:
        print(f"ERR {slug}: createTask {e}", flush=True)
        return slug, None
    if r.get("code") != 200:
        print(f"ERR {slug}: {r.get('msg')}", flush=True)
        return slug, None
    tid = r["data"]["taskId"]
    url = None
    for _ in range(70):
        time.sleep(8)
        try:
            info = api_req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
        except Exception:
            continue
        st = info.get("data", {}).get("state")
        if st == "success":
            url = (info["data"].get("response", {}).get("resultUrls") or [None])[0]
            break
        if st == "fail":
            print(f"FAIL {slug}: {info['data'].get('failMsg')}", flush=True)
            return slug, None
    if not url:
        print(f"TIMEOUT {slug}", flush=True)
        return slug, None
    raw = urllib.request.urlopen(url, timeout=120).read()
    small = compress(raw)
    supabase_upload(f"{slug}.jpg", small)
    print(f"OK {slug} ({len(small)//1024}KB)", flush=True)
    return slug, f"{SUPA}/storage/v1/object/public/alina-media/course/{slug}.jpg"


if __name__ == "__main__":
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for slug, url in pool.map(one, EX):
            if url:
                results[slug] = url
    out = "/home/hermes/alina-body/content/pilates_photos.json"
    json.dump(results, open(out, "w"), ensure_ascii=False, indent=2)
    missing = [s for s, _ in EX if s not in results]
    print(f"ГОТОВО: {len(results)}/{len(EX)} фото. Нет: {missing}")
