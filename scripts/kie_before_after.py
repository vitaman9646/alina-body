#!/usr/bin/env python3
"""Кейсы «до/после» через мастер-лицо: одно лицо, разное тело (nano-banana-2)."""
import os, json, time, urllib.request

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"
OUT = "/home/hermes/alina-body/content/char"
MODEL = "nano-banana-2"
ASPECT = "3:4"
RES = "2K"

CASES = [
    {
        "name": "anya",
        "face": "Photorealistic portrait of a young woman around 24 with long light-brown hair and brown eyes, round soft face, head and shoulders, neutral background, natural light",
        "before": "The same woman as in the reference image, full-body shot standing facing the camera, with a fuller softer figure and a rounder midsection, wearing dark grey leggings and a loose grey t-shirt, plain light wall background, neutral expression, realistic candid photo",
        "after": "The same woman as in the reference image, full-body shot standing facing the camera, slim and toned with a flat stomach and slender legs, wearing dark grey leggings and a loose grey t-shirt, plain light wall background, confident smile, realistic photo",
    },
    {
        "name": "marina",
        "face": "Photorealistic portrait of a young woman around 28 with shoulder-length blonde hair and blue eyes, head and shoulders, neutral background, natural light",
        "before": "The same woman as in the reference image, full-body shot standing facing the camera, with a fuller figure and softer arms, wearing black leggings and a light blue top, plain home background, neutral expression, realistic candid photo",
        "after": "The same woman as in the reference image, full-body shot standing facing the camera, slim with a defined waist and firm legs, wearing black leggings and a light blue top, plain home background, gentle smile, realistic photo",
    },
    {
        "name": "polina",
        "face": "Photorealistic portrait of a young woman around 22 with dark hair in a short bob and green eyes, head and shoulders, neutral background, natural light",
        "before": "The same woman as in the reference image, full-body shot standing facing the camera, with a softer rounder figure and fuller hips and thighs, wearing navy leggings and a white top, plain light background, neutral expression, realistic candid photo",
        "after": "The same woman as in the reference image, full-body shot standing facing the camera, slim and toned with slender legs and a flat stomach, wearing navy leggings and a white top, plain light background, bright smile, realistic photo",
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

    for c in CASES:
        name = c["name"]
        print(f"=== {name}: master face ===", flush=True)
        face_url = generate(kie, c["face"])
        face_path = f"{OUT}/{name}-face.jpg"
        urllib.request.urlretrieve(face_url, face_path)
        face_pub = upload_supabase(supabase, sup_key, f"{name}-face.jpg", open(face_path, "rb").read())
        print(f"  face ok", flush=True)

        for tag, prompt in (("before", c["before"]), ("after", c["after"])):
            print(f"=== {name}: {tag} ===", flush=True)
            url = generate(kie, prompt, reference=face_pub)
            p = f"{OUT}/{name}-{tag}.jpg"
            urllib.request.urlretrieve(url, p)
            upload_supabase(supabase, sup_key, f"{name}-{tag}.jpg", open(p, "rb").read())
            print(f"  {tag} ok", flush=True)

    print("\n=== ГОТОВО ===")


if __name__ == "__main__":
    main()
