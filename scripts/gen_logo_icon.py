#!/usr/bin/env python3
"""Генерирует эмблему-логотип Alina Body (flat, без текста) через kie.ai."""
import os, sys, json, time, urllib.request

API = "https://api.kie.ai"
OUT = "/home/hermes/alina-body/alina-media/brand"
os.makedirs(OUT, exist_ok=True)

def key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет ключа")

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key()})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key(),
                                          "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

bal = get(f"{API}/api/v1/chat/credit").get("data")
print("баланс до:", bal)

prompt = ("Minimalist logo mark for a women's wellness and fitness brand. "
          "Elegant flat vector emblem of a graceful female silhouette in a flowing "
          "yoga-warrior pose, abstract geometric style, single continuous line feel, "
          "warm coral and cream color palette, solid white background, perfectly "
          "centered, no text, no letters, simple clean modern design, readable at small size.")

r = post(f"{API}/api/v1/jobs/createTask", {
    "model": "flux-3/klein-text-to-image",
    "input": {"prompt": prompt, "aspect_ratio": "1:1"},
})
if r.get("code") != 200:
    sys.exit("createTask fail: " + json.dumps(r)[:300])
task = r["data"]["taskId"]
print("taskId:", task)

for _ in range(90):
    time.sleep(7)
    d = get(f"{API}/api/v1/jobs/recordInfo?taskId={task}").get("data", {})
    st = d.get("state")
    if st == "success":
        urls = (d.get("response", {}).get("resultUrls")
                or d.get("resultJson", {}).get("resultUrls") or [])
        if urls:
            dest = os.path.join(OUT, "logo-icon.jpg")
            urllib.request.urlretrieve(urls[0], dest)
            print("OK:", dest, os.path.getsize(dest), "байт")
            print("баланс после:", get(f"{API}/api/v1/chat/credit").get("data"))
            sys.exit(0)
        sys.exit("нет resultUrls")
    if st == "fail":
        sys.exit("fail: " + json.dumps(d)[:300])
sys.exit("timeout")
