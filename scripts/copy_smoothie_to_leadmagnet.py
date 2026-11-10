#!/usr/bin/env python3
"""Копирует фото смузи из alina-media/smoothie/ в alina-media/lead-magnet/smoothie-<slug>.jpg
(нужно для лендинга лид-магнита, который ссылается через MEDIA=.../lead-magnet)."""
import json
import os
import requests

REPO = "/home/hermes/alina-body"
SRC = f"{REPO}/content/smoothie-recipes.json"
LOCAL = f"{REPO}/alina-media/smoothie"


def load_supa():
    env = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip()
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SERVICE_ROLE_KEY"]


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    supa, skey = load_supa()
    for s in data["smoothies"]:
        slug = s["slug"]
        src = f"{LOCAL}/{slug}.jpg"
        if not os.path.exists(src):
            print(f"[!] нет файла {src}")
            continue
        img = open(src, "rb").read()
        r = requests.post(
            f"{supa}/storage/v1/object/alina-media/lead-magnet/smoothie-{slug}.jpg",
            headers={"Authorization": f"Bearer {skey}", "apikey": skey,
                     "x-upsert": "true", "Content-Type": "image/jpeg"},
            data=img, timeout=120)
        st = "ok" if r.status_code in (200, 201) else f"FAIL {r.status_code}"
        print(f"[+] smoothie-{slug}.jpg {st}")


if __name__ == "__main__":
    main()
