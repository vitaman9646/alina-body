#!/usr/bin/env python3
"""Генерация одного изображения через kie.ai (Market jobs API)."""
import os
import sys
import json
import time
import urllib.request
import argparse

ENV = os.path.expanduser("~/credentials/kie.env")
API = "https://api.kie.ai"


def load_key():
    for line in open(ENV):
        if "=" in line and not line.strip().startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("kie.ai ключ не найден")


def api_get(url, key):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def api_post(url, key, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--reference", default=None, help="URL референсного изображения (для консистентности)")
    ap.add_argument("--model", default="nano-banana-2")
    ap.add_argument("--aspect", default="3:4")
    ap.add_argument("--resolution", default="2K")
    ap.add_argument("--out", required=True, help="путь для сохранения jpg")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    key = load_key()
    inp = {
        "prompt": args.prompt,
        "aspect_ratio": args.aspect,
        "resolution": args.resolution,
        "output_format": "jpg",
    }
    if args.reference:
        inp["image_input"] = [args.reference]

    r = api_post(f"{API}/api/v1/jobs/createTask", key, {"model": args.model, "input": inp})
    if r.get("code") != 200:
        print("createTask error:", json.dumps(r)[:500])
        sys.exit(1)
    task = r["data"]["taskId"]
    print("taskId:", task, flush=True)

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(8)
        info = api_get(f"{API}/api/v1/jobs/recordInfo?taskId={task}", key)
        d = info.get("data", {})
        state = d.get("state")
        print("  state:", state, flush=True)
        if state == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if not urls:
                print("нет resultUrls:", json.dumps(d)[:500])
                sys.exit(1)
            urllib.request.urlretrieve(urls[0], args.out)
            print("SAVED:", args.out, flush=True)
            return
        if state == "fail":
            print("FAIL:", json.dumps(d)[:500])
            sys.exit(1)
    print("timeout")
    sys.exit(1)


if __name__ == "__main__":
    main()
