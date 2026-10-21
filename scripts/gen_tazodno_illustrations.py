#!/usr/bin/env python3
"""Генерит 2 недостающие иллюстрации для карточек тазового дна (nano-banana-2-lite)."""
import os, json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
OUT = "/home/hermes/alina-body/alina-media/cartoon"
MODEL = "nano-banana-2-lite"

K = [l.split("=", 1)[1].strip() for l in open(ENV) if "=" in l and not l.strip().startswith("#")][0]

def get(u):
    r = urllib.request.Request(u, headers={"Authorization": "Bearer " + K})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def post(u, p):
    r = urllib.request.Request(u, data=json.dumps(p).encode(),
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def balance():
    return get(f"{API}/api/v1/chat/credit").get("data")

BASE = "Flat vector illustration, clean modern flat design, smooth geometric shapes, subtle flat shading. Warm coral and cream color palette, soft solid white background, no text."

def gen(name, prompt):
    inp = {"prompt": prompt, "image_input": [REF], "aspect_ratio": "3:4",
           "resolution": "1K", "output_format": "jpg"}
    r = post(f"{API}/api/v1/jobs/createTask", {"model": MODEL, "input": inp})
    if r.get("code") != 200:
        print(f"[{name}] createTask ERROR: {json.dumps(r)[:300]}")
        return
    task = r["data"]["taskId"]
    for _ in range(90):
        time.sleep(7)
        d = get(f"{API}/api/v1/jobs/recordInfo?taskId={task}").get("data", {})
        st = d.get("state")
        if st == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if not urls:
                print(f"[{name}] нет resultUrls")
                return
            os.makedirs(OUT, exist_ok=True)
            path = f"{OUT}/{name}.jpg"
            urllib.request.urlretrieve(urls[0], path)
            print(f"[{name}] SAVED {path} ({os.path.getsize(path)} байт)")
            return
        if st == "fail":
            print(f"[{name}] FAIL: {json.dumps(r)[:400]}")
            return
    print(f"[{name}] timeout")

STYLES = {
    "tazodno-anatomy": BASE + " Same cartoon character as this woman, same style and colors: athletic young woman, sleek dark hair in a ponytail, coral sports top and black leggings. Standing three-quarter view, one hand resting on her lower belly, the other hand reaching behind to her lower back, gently smiling, demonstrating the front and back of the pelvic floor.",
    "tazodno-relax": BASE + " Same cartoon character as this woman, same style and colors: athletic young woman, sleek dark hair, coral sports top and black leggings. Lying relaxed on her back on a yoga mat, arms resting out to the sides, knees bent, eyes closed, peaceful calm expression, body fully relaxed.",
}

if __name__ == "__main__":
    b0 = balance()
    print("баланс до:", b0)
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(lambda kv: gen(kv[0], kv[1]), STYLES.items()))
    b1 = balance()
    print(f"ПОТРАЧЕНО: {b0 - b1} кредитов")
