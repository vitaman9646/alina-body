#!/usr/bin/env python3
"""Тест: reference-to-video (Kling omni) — держит ли лицо Алины в видео."""
import os, json, time, urllib.request

KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"

def req(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}
    d = None
    if payload is not None:
        h["Content-Type"] = "application/json"; d = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=d, headers=h), timeout=120).read())

r = req("https://api.kie.ai/api/v1/jobs/createTask", {
    "model": "kling-3.0-omni/reference-to-video",
    "input": {
        "prompt": "The same woman smiles warmly and gives a small nod to the camera, subtle natural head movement, realistic",
        "image_urls": [REF],
        "duration": 5,
        "aspect_ratio": "16:9",
        "output_format": "mp4",
    },
})
print("createTask:", r.get("code"), r.get("msg", "")[:120])
if r.get("code") != 200:
    raise SystemExit(1)
tid = r["data"]["taskId"]
url = None
for _ in range(90):
    time.sleep(8)
    info = req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
    d = info.get("data", {})
    st = d.get("state")
    if st == "success":
        url = (d.get("response", {}).get("resultUrls") or [None])[0]; break
    if st == "fail":
        print("FAIL:", d.get("failMsg") or d.get("failCode")); raise SystemExit(1)
    print("state:", st, flush=True)
if not url:
    print("TIMEOUT"); raise SystemExit(1)
print("URL:", url)
data = urllib.request.urlopen(url, timeout=180).read()
out = "/home/hermes/alina-body/content/char/test-video-consistency.mp4"
open(out, "wb").write(data)
print("SAVED:", out, len(data), "bytes")
