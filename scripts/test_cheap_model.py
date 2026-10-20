#!/usr/bin/env python3
"""Тест дешёвой модели nano-banana (Gemini 2.5 Flash) для плоских иллюстраций."""
import json, time, urllib.request

API = "https://api.kie.ai"
ENV = "/home/hermes/credentials/kie.env"


def key():
    for line in open(ENV):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def balance(k):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{API}/api/v1/chat/credit", headers={"Authorization": "Bearer " + k}), timeout=20).read())["data"]


k = key()
b0 = balance(k)
print("баланс до:", b0)

prompt = ("Flat minimal illustration, a healthy bowl with vegetables and grains, soft pastel colors, "
          "cream background, no text, no people, wellness food flat vector style")
inp = {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "1K", "output_format": "jpg"}
req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
    data=json.dumps({"model": "nano-banana", "input": inp}).encode(),
    headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"})
r = json.loads(urllib.request.urlopen(req, timeout=30).read())
print("createTask:", r.get("code"), "model=nano-banana")
if r.get("code") != 200:
    print(json.dumps(r)[:300]); raise SystemExit
task = r["data"]["taskId"]
for _ in range(70):
    time.sleep(6)
    info = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{API}/api/v1/jobs/recordInfo?taskId={task}",
        headers={"Authorization": "Bearer " + k}), timeout=30).read())
    d = info.get("data", {})
    if d.get("state") == "success":
        urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
        urllib.request.urlretrieve(urls[0], "/home/hermes/alina-body/content/demo/test-nano-banana.jpg")
        break
    if d.get("state") == "fail":
        print("FAIL", json.dumps(d)[:300]); raise SystemExit

b1 = balance(k)
print("баланс после:", b1)
print("СТОИМОСТЬ 1 иллюстрации (nano-banana, 1K):", b0 - b1, "кредитов")
