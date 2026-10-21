#!/usr/bin/env python3
"""Генерит 3 пробных стиля мультяшной Алины через kie.ai, пишет кредиты."""
import os, json, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
OUT = "/home/hermes/alina-body/alina-media/cartoon"

def key():
    for line in open(ENV):
        if "=" in line and not line.strip().startswith("#"):
            return line.split("=", 1)[1].strip()

K = key()

def get(u):
    r = urllib.request.Request(u, headers={"Authorization": "Bearer " + K})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def post(u, p):
    r = urllib.request.Request(u, data=json.dumps(p).encode(),
                               headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def balance():
    return get(f"{API}/api/v1/chat/credit").get("data")

def gen(name, prompt):
    inp = {"prompt": prompt, "image_input": [REF], "aspect_ratio": "3:4",
           "resolution": "2K", "output_format": "jpg"}
    r = post(f"{API}/api/v1/jobs/createTask", {"model": "nano-banana-2", "input": inp})
    if r.get("code") != 200:
        print(f"[{name}] createTask ERROR: {json.dumps(r)[:300]}")
        return
    task = r["data"]["taskId"]
    for _ in range(90):
        time.sleep(8)
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
            print(f"[{name}] FAIL: {json.dumps(d)[:300]}")
            return
    print(f"[{name}] timeout")

STYLES = {
    "style-flat": "Flat vector illustration, clean modern flat design, smooth geometric shapes, subtle flat shading. Cartoon version of this woman as a full-body character: athletic young woman, sleek dark hair in a high ponytail, wearing a coral sports top and black leggings, standing confidently with hands on hips and a friendly smile. Warm coral and cream color palette, soft solid white background, no text.",
    "style-cute": "Cute rounded cartoon character, soft chibi-leaning proportions, big warm friendly eyes, smooth rounded shapes and soft gradients. Cartoon version of this woman as a full-body character: athletic young woman, sleek dark hair, wearing a pastel sports outfit, standing with one hand raised in a cheerful wave. Pastel pink and cream palette, soft solid white background, no text.",
    "style-line": "Minimal clean line-art illustration, thin elegant single-color outlines with flat accent fills, refined and airy. Cartoon version of this woman as a full-body character: athletic young woman, sleek dark hair in a neat bun, wearing simple sportswear, standing in a graceful confident pose. Coral line-art on a warm cream background, minimal color accents, no text.",
}

if __name__ == "__main__":
    b0 = balance()
    print("баланс до:", b0)
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda kv: gen(kv[0], kv[1]), STYLES.items()))
    b1 = balance()
    print("баланс после:", b1)
    print(f"ПОТРАЧЕНО: {b0 - b1} кредитов")
