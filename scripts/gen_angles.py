#!/usr/bin/env python3
"""Набор фото Алины с разных ракурсов (каноничное молодое лицо) — для использования на любых площадках."""
import os, io, json, time, urllib.request

KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/"); SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
R1 = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
R2 = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-2.jpg"
REALISM = ("CRITICAL — realistic skin and texture: real human skin with visible pores, fine texture, "
           "subtle natural imperfections, slight redness around the nose and cheeks, faint under-eye shadows, "
           "tiny flyaway hairs around the hairline. Natural matte-to-slightly-oily skin, NOT smooth, NOT airbrushed, "
           "NO plastic CGI look, NO beauty-filter smoothing, NO waxy 3D-render skin. Shot on an iPhone, candid and lifelike.")
POLISH = ("athletic and toned physique, polished and well-groomed appearance, confident poised model-like expression")

SHOTS = [
    ("portrait-front", "head and shoulders portrait, facing camera, warm natural smile, neat sleek hair, front angle"),
    ("portrait-three-quarter", "head and shoulders portrait, three-quarter angle, soft smile, tidy hair"),
    ("portrait-profile", "head and shoulders portrait in profile, looking to the side, neat low bun"),
    ("fullbody-front", "full body standing facing camera, powder-pink athleisure set, front angle, natural home light"),
    ("fullbody-side", "full body standing in three-quarter view, cream knit set, relaxed arms"),
    ("back-over-shoulder", "from behind, looking back over her shoulder, subtle smile, milk ribbed top"),
    ("sitting-casual", "sitting cross-legged on a sofa, casual beige outfit, three-quarter angle"),
    ("selfie-smile", "selfie from above, warm smile, natural light, casual grey top"),
    ("workout-squat", "doing a bodyweight squat with good form, sand leggings, side angle"),
    ("workout-plank", "holding a forearm plank on a mat, mossy green sweatshirt, side angle"),
    ("walking-outdoor", "walking in a park path, cream hoodie, profile angle, daylight"),
    ("confident-standing", "standing tall with confident posture, milk ribbed set, front angle, soft window light"),
]

def req(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}; d = None
    if payload is not None:
        h["Content-Type"] = "application/json"; d = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=d, headers=h), timeout=120).read())

def upload(name, img):
    url = f"{SUPA}/storage/v1/object/alina-media/angles/{name}.jpg"
    urllib.request.urlopen(urllib.request.Request(url, data=img, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"}), timeout=60).read()

def compress(b):
    from PIL import Image
    im = Image.open(io.BytesIO(b)).convert("RGB"); im.thumbnail((1200, 1600))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return buf.getvalue()

done = 0
for name, desc in SHOTS:
    pub = f"{SUPA}/storage/v1/object/public/alina-media/angles/{name}.jpg"
    try:
        urllib.request.urlopen(urllib.request.Request(pub, method="HEAD"), timeout=15)
        print(f"SKIP {name}"); done += 1; continue
    except Exception:
        pass
    prompt = f"Young woman in her early twenties, {desc}, {POLISH}. " + REALISM
    r = req("https://api.kie.ai/api/v1/jobs/createTask", {
        "model": "nano-banana-2",
        "input": {"prompt": prompt, "image_input": [R1, R2], "aspect_ratio": "3:4", "resolution": "2K", "output_format": "jpg"},
    })
    if r.get("code") != 200:
        print(f"ERR {name}: {r.get('msg','')[:80]}"); continue
    tid = r["data"]["taskId"]; url = None
    for _ in range(60):
        time.sleep(8)
        info = req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
        st = info.get("data", {}).get("state")
        if st == "success":
            url = (info["data"].get("response", {}).get("resultUrls") or [None])[0]; break
        if st == "fail":
            print(f"FAIL {name}: {info['data'].get('failMsg') or info['data'].get('failCode')}"); break
    if not url:
        print(f"TIMEOUT {name}"); continue
    raw = urllib.request.urlopen(url, timeout=120).read()
    upload(name, compress(raw)); done += 1
    print(f"OK {name}")

print(f"ГОТОВО: {done}/{len(SHOTS)} ракурсов")
