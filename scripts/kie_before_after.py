#!/usr/bin/env python3
"""Генерация кейсов «до/после»: before (текст) -> upload -> after (image_input=before)."""
import os, json, time, urllib.request

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
OUT = "/home/hermes/alina-body/content/char"
MODEL = "nano-banana-2"
ASPECT = "4:5"
RES = "2K"

CASES = [
    {
        "name": "anya",
        "before": "Photorealistic full-body amateur photo of a young woman around 24 with a soft average body, standing facing the camera, wearing dark grey leggings and a loose grey t-shirt, plain light wall background, neutral tired expression, no makeup, realistic candid smartphone photo",
        "after": "The same woman as in the reference image, but noticeably slimmer and more toned after months of training: firmer waist, toned arms and legs, better posture, a confident slight smile, wearing the same dark grey leggings and grey t-shirt, same plain light wall background, photorealistic full-body shot",
    },
    {
        "name": "marina",
        "before": "Photorealistic full-body amateur photo of a young woman around 28 with a soft midsection and average body, standing facing the camera, wearing black leggings and a light blue top, plain home background, neutral expression, realistic candid smartphone photo",
        "after": "The same woman as in the reference image, but with a visibly flatter stomach, firmer waist and more toned legs after training, better posture, gentle smile, wearing the same black leggings and light blue top, same plain home background, photorealistic full-body shot",
    },
    {
        "name": "polina",
        "before": "Photorealistic full-body amateur photo of a young woman around 22 with a slight skinny-fat build, standing facing the camera, wearing navy leggings and a white top, plain light background, neutral expression, realistic candid smartphone photo",
        "after": "The same woman as in the reference image, but with more muscle tone in her arms, legs and glutes, a firmer waist and upright posture, bright confident smile, wearing the same navy leggings and white top, same plain light background, photorealistic full-body shot",
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


def generate(key, prompt, reference=None):
    inp = {"prompt": prompt, "aspect_ratio": ASPECT, "resolution": RES, "output_format": "jpg"}
    if reference:
        inp["image_input"] = [reference]
    r = req(f"{API}/api/v1/jobs/createTask", key, {"model": MODEL, "input": inp})
    if r.get("code") != 200:
        raise RuntimeError("createTask fail: " + json.dumps(r)[:300])
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
    headers = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "image/jpeg"}
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
        before_url = generate(kie, c["before"])
        before_path = f"{OUT}/{name}-before.jpg"
        urllib.request.urlretrieve(before_url, before_path)
        pub = upload_supabase(supabase, sup_key, f"{name}-before.jpg", open(before_path, "rb").read())
        print(f"  before загружен: {pub}", flush=True)

        print(f"=== {name}: after ===", flush=True)
        after_url = generate(kie, c["after"], reference=pub)
        after_path = f"{OUT}/{name}-after.jpg"
        urllib.request.urlretrieve(after_url, after_path)
        pub2 = upload_supabase(supabase, sup_key, f"{name}-after.jpg", open(after_path, "rb").read())
        print(f"  after загружен: {pub2}", flush=True)

        result.append({"name": name, "before": pub, "after": pub2})

    print("\n=== ГОТОВО ===")
    for r in result:
        print(f"{r['name']}:")
        print(f"  before: {r['before']}")
        print(f"  after:  {r['after']}")


if __name__ == "__main__":
    main()
