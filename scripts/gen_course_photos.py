#!/usr/bin/env python3
"""Генерация фото упражнений для курса «Ягодицы и ноги» + загрузка в Supabase."""
import os, json, time, urllib.request, io, sys

KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/portrait-smile.jpg"
REALISM = ("CRITICAL — realistic skin and texture: real human skin with visible pores, fine texture, "
           "subtle natural imperfections, slight redness around the nose and cheeks, faint under-eye shadows, "
           "tiny flyaway hairs around the hairline. Natural matte-to-slightly-oily skin, NOT smooth, NOT airbrushed, "
           "NO plastic CGI look, NO beauty-filter smoothing, NO waxy 3D-render skin. Shot on an iPhone, candid and lifelike.")

EX = [
    ("warmup", "milk ribbed knit set, standing on a yoga mat doing arm circles and a gentle warm-up in a bright living room, front angle, low loose bun"),
    ("glute-bridge", "powder pink sports bra and high-waist leggings, lying on a mat doing a glute bridge with hips lifted, side profile angle, low ponytail"),
    ("bridge-knee-press", "sand leggings and a cream tank, doing a glute bridge with a resistance band around the knees, knees pressed apart, side angle"),
    ("squat-pause", "milk ribbed set, doing a bodyweight squat holding the bottom position, three-quarter angle, natural light"),
    ("stretch", "cream waffle-knit loungewear, sitting on a mat in a seated forward fold stretching hamstrings, three-quarter angle"),
    ("squat", "clay oversized tee and black bike shorts, doing a bodyweight squat with good form, front angle, low bun"),
    ("reverse-lunge", "mossy green sweatshirt and leggings, doing a reverse lunge in a living room, front angle"),
    ("single-leg-bridge", "sand leggings and a cream tank, doing a single-leg glute bridge on a mat, side profile angle"),
    ("hip-extension", "milk ribbed set, standing holding a chair and raising one leg straight back, side angle"),
    ("side-leg-raise", "powder pink bra and leggings, lying on her side doing a leg raise, front angle"),
    ("sumo-squat", "mossy green sweatshirt and leggings, doing a wide-stance sumo squat, front angle"),
    ("single-leg-deadlift", "sand leggings and a cream tank, doing a single-leg deadlift leaning forward, side profile angle"),
    ("forward-lunge", "cream knit set, doing a forward lunge, front angle, natural light"),
    ("plank", "mossy green sweatshirt and leggings, holding a forearm plank on a mat, side angle, low bun"),
    ("dead-bug", "powder pink bra and leggings, lying on a mat doing a dead bug exercise, front angle"),
    ("side-plank", "clay oversized tee and bike shorts, doing a side plank on knees, front angle"),
    ("circuit", "milk ribbed set, doing a side step in a half-squat on a mat, front angle"),
    ("deep-stretch", "cream waffle-knit loungewear, doing a deep seated forward fold on a mat, three-quarter angle"),
]

def api_req(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}
    data = None
    if payload is not None:
        h["Content-Type"] = "application/json"; data = json.dumps(payload).encode()
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

results = {}
for slug, prompt in EX:
    pub = f"{SUPA}/storage/v1/object/public/alina-media/course/{slug}.jpg"
    try:
        urllib.request.urlopen(urllib.request.Request(pub, method="HEAD"), timeout=15)
        results[slug] = pub
        print(f"SKIP {slug} (уже есть)")
        continue
    except Exception:
        pass
    full = prompt + ". " + REALISM
    r = api_req("https://api.kie.ai/api/v1/jobs/createTask", {
        "model": "nano-banana-2",
        "input": {"prompt": full, "image_input": [REF], "aspect_ratio": "3:4", "resolution": "2K", "output_format": "jpg"},
    })
    if r.get("code") != 200:
        print(f"ERR {slug}: {r.get('msg')}"); continue
    tid = r["data"]["taskId"]
    url = None
    for _ in range(60):
        time.sleep(8)
        info = api_req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
        st = info.get("data", {}).get("state")
        if st == "success":
            url = (info["data"].get("response", {}).get("resultUrls") or [None])[0]
            break
        if st == "fail":
            print(f"FAIL {slug}: {info['data'].get('failMsg')}"); break
    if not url:
        print(f"TIMEOUT {slug}"); continue
    raw = urllib.request.urlopen(url, timeout=120).read()
    small = compress(raw)
    supabase_upload(f"{slug}.jpg", small)
    results[slug] = f"{SUPA}/storage/v1/object/public/alina-media/course/{slug}.jpg"
    print(f"OK {slug}: {results[slug]}  ({len(small)//1024}KB)")

json.dump(results, open("/home/hermes/alina-body/content/course_photos.json", "w"), ensure_ascii=False, indent=2)
print("ГОТОВО:", len(results), "фото")
