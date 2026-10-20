#!/usr/bin/env python3
"""Генерация дешёвыми моделями (минимальный ввод) + замер цены."""
import json, time, urllib.request

API = "https://api.kie.ai"


def key():
    for line in open("/home/hermes/credentials/kie.env"):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def balance(k):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{API}/api/v1/chat/credit", headers={"Authorization": "Bearer " + k}), timeout=20).read())["data"]


def gen(k, model, inp, out):
    req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": model, "input": inp}).encode(),
        headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        return None, json.dumps(r)[:200]
    task = r["data"]["taskId"]
    for _ in range(70):
        time.sleep(6)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/jobs/recordInfo?taskId={task}",
            headers={"Authorization": "Bearer " + k}), timeout=30).read())
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if urls:
                urllib.request.urlretrieve(urls[0], out)
                return out, None
            return None, "нет resultUrls"
        if d.get("state") == "fail":
            return None, json.dumps(d)[:250]
    return None, "timeout"


k = key()
prompt = ("Flat minimal vector illustration of a healthy food bowl with vegetables and grains, "
          "soft pastel palette, cream background, no text, no letters, no people, clean wellness infographic style")

TESTS = [
    ("flux-3/klein-text-to-image", {"prompt": prompt, "aspect_ratio": "1:1"}, "flux-klein.jpg"),
    ("google/nano-banana", {"prompt": prompt, "aspect_ratio": "1:1"}, "nanobanana.jpg"),
]

b0 = balance(k)
for model, inp, fname in TESTS:
    b = balance(k)
    print(f"[{model}] …", flush=True)
    out, err = gen(k, model, inp, f"/home/hermes/alina-body/content/demo/{fname}")
    b2 = balance(k)
    if out:
        print(f"  ✅ {out} | цена {b - b2} кр")
    else:
        print(f"  ❌ {err}")
print(f"итого: {b0 - balance(k)} кр | остаток {balance(k)}")
