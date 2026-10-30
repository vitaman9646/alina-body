#!/usr/bin/env python3
"""Set posts.cover_image from the Pinterest pin images (content/pinterest-plan.json).

The RSS feed (api/posts.js) emits `cover_image || default-cover.jpg`, so filling
this column makes every article pin with its own unique image on Pinterest/Dzen.

Usage: python3 scripts/set_cover_images.py [--dry-run]
"""
import json
import os
import sys

import requests

REPO = "/home/hermes/alina-body"
PLAN = os.path.join(REPO, "content/pinterest-plan.json")
CREDS = os.path.expanduser("~/credentials/threads.env")
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"


def load_env(path):
    d = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d


def main():
    dry = "--dry-run" in sys.argv
    env = load_env(CREDS)
    url, key = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    pins = json.load(open(PLAN))["pins"]
    ok, fail = 0, 0
    for pin in pins:
        slug = pin["slug"]
        cover = f"{PIN_BASE}/pin-{slug}.jpg"
        if dry:
            print(f"DRY  {slug[:50]} -> {cover}")
            ok += 1
            continue
        r = requests.patch(
            f"{url}/rest/v1/posts?slug=eq.{slug}",
            headers=headers,
            json={"cover_image": cover},
            timeout=30,
        )
        if r.status_code in (200, 204):
            ok += 1
        else:
            fail += 1
            print(f"FAIL {slug[:50]}: {r.status_code} {r.text[:200]}")

    print(f"\n{'Would set' if dry else 'Set'} {ok} cover_image rows, {fail} failed")


if __name__ == "__main__":
    main()
