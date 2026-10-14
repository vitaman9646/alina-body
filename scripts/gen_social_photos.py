#!/usr/bin/env python3
"""Генерация/регенерация соц-фото (Threads + Instagram) с каноничным лицом Алины.

Дни по умолчанию 2-30 (день 1 уже запощен — не трогаем). Идемпотентно через
content/social_photos2.json (прогресс пишется после каждого фото — переживает обрыв).

Использование: python3 gen_social_photos.py [--start N] [--end M]
"""
import os
import re
import json
import time
import io
import argparse
import urllib.request

KEY = open(os.path.expanduser("~/credentials/kie.env")).read().split("=", 1)[1].strip()
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
REALISM = ("CRITICAL — realistic skin and texture: real human skin with visible pores, fine texture, "
           "subtle natural imperfections, slight redness around the nose and cheeks, faint under-eye shadows, "
           "tiny flyaway hairs around the hairline. Natural matte-to-slightly-oily skin, NOT smooth, NOT airbrushed, "
           "NO plastic CGI look, NO beauty-filter smoothing, NO waxy 3D-render skin. Shot on an iPhone, candid and lifelike.")
PROGRESS = "/home/hermes/alina-body/content/social_photos2.json"

def parse_prompts(path):
    out = []
    day = 0
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"^### День (\d+)$", s)
        if m:
            day = int(m.group(1))
        elif s.startswith("📸 "):
            out.append((day, s[2:].strip()))
    return out

def api_req(url, payload=None):
    h = {"Authorization": "Bearer " + KEY}
    d = None
    if payload is not None:
        h["Content-Type"] = "application/json"; d = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=d, headers=h), timeout=120).read())

def upload(name, img):
    req = urllib.request.Request(f"{SUPA}/storage/v1/object/alina-media/social/{name}", data=img, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120).read()

def compress(b):
    from PIL import Image
    im = Image.open(io.BytesIO(b)).convert("RGB")
    im.thumbnail((1200, 1600))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return buf.getvalue()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2)
    ap.add_argument("--end", type=int, default=30)
    args = ap.parse_args()

    threads = parse_prompts("/home/hermes/alina-body/content/content_plan.md")
    ig = parse_prompts("/home/hermes/alina-body/content/content_plan_instagram.md")

    jobs, idx = [], {}
    for day, p in threads:
        if args.start <= day <= args.end:
            k = idx.get(day, 0) + 1; idx[day] = k
            jobs.append((day, 0, f"threads_d{day:02d}_p{k}.jpg", p))
    for day, p in ig:
        if args.start <= day <= args.end:
            jobs.append((day, 1, f"ig_d{day:02d}.jpg", p))
    # по порядку дней (сначала день 2 целиком, потом 3...) — чтобы ранние дни успели до исчерпания кредитов
    jobs = [(n, p) for _, _, n, p in sorted(jobs, key=lambda x: (x[0], x[1]))]

    done = json.load(open(PROGRESS)) if os.path.exists(PROGRESS) else {}
    print(f"Всего задач: {len(jobs)} | уже готово: {len(done)}")

    for name, prompt in jobs:
        if name in done:
            print(f"SKIP {name}"); continue
        full = prompt + ". " + REALISM
        r = api_req("https://api.kie.ai/api/v1/jobs/createTask", {
            "model": "nano-banana-2",
            "input": {"prompt": full, "image_input": [REF], "aspect_ratio": "3:4", "resolution": "2K", "output_format": "jpg"},
        })
        if r.get("code") != 200:
            msg = str(r.get("msg", ""))
            print(f"ERR {name}: {msg[:80]}")
            if any(w in msg.lower() for w in ("credit", "balance", "insufficient", "quota")):
                print("КРЕДИТЫ ЗАКОНЧИЛИСЬ — останавливаюсь.")
                break
            continue
        tid = r["data"]["taskId"]; url = None
        for _ in range(60):
            time.sleep(8)
            info = api_req(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={tid}")
            st = info.get("data", {}).get("state")
            if st == "success":
                url = (info["data"].get("response", {}).get("resultUrls") or [None])[0]; break
            if st == "fail":
                print(f"FAIL {name}: {info['data'].get('failMsg') or info['data'].get('failCode')}"); break
        if not url:
            print(f"TIMEOUT {name}"); continue
        raw = urllib.request.urlopen(url, timeout=120).read()
        upload(name, compress(raw))
        done[name] = f"{SUPA}/storage/v1/object/public/alina-media/social/{name}"
        json.dump(done, open(PROGRESS, "w"), ensure_ascii=False)
        print(f"OK {name}")

    print(f"ГОТОВО: {len(done)} фото в social_photos2.json")

if __name__ == "__main__":
    main()
