#!/usr/bin/env python3
"""Кейсы «до/после»: полнее → заметно худее. after через gpt-image-2-image-to-image."""
import os, json, time, urllib.request

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
OUT = "/home/hermes/alina-body/content/char"
BEFORE_MODEL = "nano-banana-2"
AFTER_MODEL = "gpt-image-2-image-to-image"
ASPECT = "3:4"
RES = "2K"

CASES = [
    {
        "name": "anya",
        "before": "Photorealistic full-body amateur photo of a young woman around 24 with a fuller, softer figure, rounder midsection, fuller arms and thighs, standing facing the camera, wearing dark grey leggings and a loose grey t-shirt, plain light wall background, neutral tired expression, no makeup, realistic candid smartphone photo",
        "after": "The same woman as in the reference image but visibly much slimmer and more toned: flat stomach, slim arms and legs, slimmer face with a confident smile, wearing the same dark grey leggings and grey t-shirt, same plain light wall background, photorealistic full-body shot",
    },
    {
        "name": "marina",
        "before": "Photorealistic full-body amateur photo of a young woman around 28 with a fuller figure, rounder belly and softer arms, standing facing the camera, wearing black leggings and a light blue top, plain home background, neutral expression, realistic candid smartphone photo",
        "after": "The same woman as in the reference image but visibly slimmer with a defined waist, firmer legs, slimmer face, gentle smile, wearing the same black leggings and light blue top, same home background, photorealistic full-body shot",
    },
    {
        "name": "polina",
        "before": "Photorealistic full-body amateur photo of a young woman around 22 with a softer, rounder figure and fuller hips and thighs, standing facing the camera, wearing navy leggings and a white top, plain light background, neutral expression, realistic candid smartphone photo",
        "after": "The same woman as in the reference image but slim and toned: flat stomach, slender legs, slimmer face, bright confident smile, wearing the same navy leggings and white top, same background, photorealistic full-body shot",
    },
]


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def req(url, key, payload=None, method=None):
    headers = {"Authorization": "Bearer " + key}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


def generate(key, model, prompt, reference=None):
    inp = {"prompt": prompt, "aspect_ratio": ASPECT, "resolution": RES, "output_format": "jpg"}
    if reference:
        inp["image_input"] = [reference]
    r = req(f"{API}/api/v1/jobs/createTask", key, {"model": model, "input": inp})
    if r.get("code") != 200:
        raise RuntimeError("createTask fail: " + json.dumps(r)[:400])
    tid = r["data"]["taskId"]
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(8)
        info = req(f"{API}/api/v1/jobs/recordInfo?taskId={tid}", key)
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            return urls[0]
        if d.get("state") == "fail":
            raise RuntimeError("fail: " + json.dumps(d)[:300])
    raise RuntimeError("timeout")


def upload_supabase(supabase, key, path, data):
    url = f"{supabase}/storage/v1/object/alina-media/char/{path}"
    headers = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "image/jpeg", "x-upsert": "true"}
    r = urllib.request.Request(url, data=data, headers=headers, method="POST")
    urllib.request.urlopen(r, timeout=120).read()
    return f"{supabase}/storage/v1/object/public/alina-media/char/{path}"


def main():
    kie = load_env(ENV)["KIE_AI_API_KEY"]
    sup = load_env(os.path.expanduser("~/credentials/threads.env"))
    supabase = sup["SUPABASE_URL"].rstrip("/")
    sup_key = sup["SUPABASE_SERVICE_ROLE_KEY"]
    os.makedirs(OUT, exist_ok=True)

    result = []
    for c in CASES:
        name = c["name"]
        print(f"=== {name}: before ===", flush=True)
        before_url = generate(kie, BEFORE_MODEL, c["before"])
        before_path = f"{OUT}/{name}-before.jpg"
        urllib.request.urlretrieve(before_url, before_path)
        pub = upload_supabase(supabase, sup_key, f"{name}-before.jpg", open(before_path, "rb").read())
        print(f"  before ok", flush=True)

        print(f"=== {name}: after (gpt-image-2 edit) ===", flush=True)
        after_url = generate(kie, AFTER_MODEL, c["after"], reference=pub)
        after_path = f"{OUT}/{name}-after.jpg"
        urllib.request.urlretrieve(after_url, after_path)
        pub2 = upload_supabase(supabase, sup_key, f"{name}-after.jpg", open(after_path, "rb").read())
        print(f"  after ok", flush=True)

        result.append({"name": name, "before": pub, "after": pub2})

    print("\n=== ГОТОВО ===")
    for r in result:
        print(f"{r['name']}: {r['before']} | {r['after']}")


if __name__ == "__main__":
    main()
