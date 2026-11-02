#!/usr/bin/env python3
"""Перегенерация одного фото курса: python3 scripts/regen_shot.py <slug> '<prompt>'"""
import os, sys, json, time, io, urllib.request
from PIL import Image

slug, prompt = sys.argv[1], sys.argv[2]
KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v.strip()
S = env["SUPABASE_URL"].rstrip("/"); K = env["SUPABASE_SERVICE_ROLE_KEY"]
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
REALISM = ("CRITICAL — realistic skin and texture: real human skin with visible pores, fine texture, subtle natural "
           "imperfections, even natural skin tone, NO redness or flush on the nose and face, tiny flyaway hairs. "
           "Natural matte skin, NOT airbrushed, NO plastic CGI look, NO beauty-filter smoothing, photorealistic photo "
           "shot on an iPhone, candid and lifelike, no text.")
BASE = ("A young woman in her early twenties, athletic toned build, polished and well-groomed, "
        "confident model-like presence, sleek neat hair, ")


def api(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}; d = None
    if payload is not None:
        h["Content-Type"] = "application/json"; d = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=d, headers=h), timeout=120).read())


r = api("https://api.kie.ai/api/v1/jobs/createTask", {"model": "nano-banana-2", "input": {
    "prompt": BASE + prompt + ". " + REALISM, "image_input": [REF], "aspect_ratio": "3:4",
    "resolution": "2K", "output_format": "jpg"}})
tid = r["data"]["taskId"]; print("task", tid, flush=True)
url = None
for _ in range(70):
    time.sleep(8)
    info = api(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
    st = info.get("data", {}).get("state")
    if st == "success":
        url = (info["data"]["response"]["resultUrls"] or [None])[0]; break
    if st == "fail":
        print("FAIL", info["data"].get("failMsg")); raise SystemExit(1)
if not url:
    print("TIMEOUT"); raise SystemExit(1)
raw = urllib.request.urlopen(url, timeout=120).read()
im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((1200, 1600))
buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
body = buf.getvalue()
req = urllib.request.Request(f"{S}/storage/v1/object/alina-media/course/{slug}.jpg", data=body, method="POST",
    headers={"Authorization": "Bearer " + K, "apikey": K, "Content-Type": "image/jpeg", "x-upsert": "true"})
urllib.request.urlopen(req, timeout=120).read()
print(f"OK {slug} reuploaded {len(body)//1024}KB")
