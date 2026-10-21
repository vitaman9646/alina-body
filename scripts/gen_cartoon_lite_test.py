#!/usr/bin/env python3
"""Проверка nano-banana-2-lite: консистентность персонажа + цена."""
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
            print(f"[{name}] FAIL: {json.dumps(d)[:400]}")
            return
    print(f"[{name}] timeout")

STYLES = {
    "lite-master": BASE + " Cartoon version of this woman as a full-body character: athletic young woman, sleek dark hair in a high ponytail, wearing a coral sports top and black leggings, standing confidently with hands on hips and a friendly smile.",
    "lite-pose1": BASE + " Same cartoon character as this woman, same style and colors: athletic young woman, sleek dark hair in a high ponytail, coral sports top and black leggings. Now lying on her back on a yoga mat, knees bent, feet flat on the floor, one hand resting on her lower belly, demonstrating a gentle pelvic tilt.",
    "lite-pose2": BASE + " Same cartoon character as this woman, same style and colors: athletic young woman, sleek dark hair, coral sports top and black leggings. Now sitting cross-legged on a yoga mat, hands resting on her lower belly, eyes gently closed, calm breathing.",
}

if __name__ == "__main__":
    b0 = balance()
    print("баланс до:", b0, "| модель:", MODEL, "1K")
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda kv: gen(kv[0], kv[1]), STYLES.items()))
    b1 = balance()
    print("баланс после:", b1)
    print(f"ПОТРАЧЕНО: {b0 - b1} кредитов (за {len(STYLES)} картинки)")
