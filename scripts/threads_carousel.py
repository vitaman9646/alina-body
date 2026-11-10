#!/usr/bin/env python3
"""Карусель (multi-image) постинг в Threads.

3-шаговый флоу Meta: item-контейнеры (is_carousel_item=true) → CAROUSEL-контейнер
(children=id1,id2,...) → threads_publish. Минимум 2, максимум 20 изображений.

Использование:
  python3 threads_carousel.py --images URL1,URL2,URL3 --text "…" [--profile alina|vitaliy] [--dry-run]
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error

PROFILES = {
    "alina": {"creds": "~/credentials/threads.env", "user_id": "29048751384731011"},
    "vitaliy": {"creds": "~/credentials/vitaliy-threads.env", "user_id": None},
}


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def threads_api(token, method, **params):
    url = f"https://graph.threads.net/v1.0/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read().decode() or "{}").get("error", {}).get("message", f"HTTP {e.code}")
    if "error" in resp:
        return None, resp["error"].get("message", "unknown")
    return resp, None


def post_carousel(token, user_id, image_urls, text, dry_run=False):
    n = len(image_urls)
    if n < 2:
        return None, "карусель требует минимум 2 изображения"
    if n > 20:
        return None, "максимум 20 изображений"

    item_ids = []
    for url in image_urls:
        if dry_run:
            item_ids.append(f"<id:{url.split('/')[-1]}>")
            continue
        resp, err = threads_api(token, f"{user_id}/threads",
                                media_type="IMAGE", image_url=url, is_carousel_item="true")
        if err:
            return None, f"item container: {err}"
        item_ids.append(resp.get("id"))

    children = ",".join(item_ids)
    if dry_run:
        return {"id": "<carousel-container>", "children": children, "text": text}, None

    resp, err = threads_api(token, f"{user_id}/threads",
                            media_type="CAROUSEL", children=children, text=text)
    if err:
        return None, f"carousel container: {err}"
    cid = resp.get("id")

    time.sleep(8)
    resp, err = threads_api(token, f"{user_id}/threads_publish", creation_id=cid)
    if err:
        return None, f"publish: {err}"
    return resp, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="публичные URL через запятую (2..20)")
    ap.add_argument("--text", default="", help="подпись к карусели")
    ap.add_argument("--profile", default="alina", choices=["alina", "vitaliy"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    c = PROFILES[args.profile]
    env = load_env(os.path.expanduser(c["creds"]))
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID") or c["user_id"]

    images = [u.strip() for u in args.images.split(",") if u.strip()]
    resp, err = post_carousel(token, uid, images, args.text, args.dry_run)
    if err:
        print(f"❌ {err}")
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] items={len(images)} children={resp['children']}")
        print(f"[dry-run] text={args.text}")
        return

    mid = resp.get("id")
    print(f"✅ Карусель опубликована, media_id={mid}")
    # проверить, на какой аккаунт легла, через permalink
    time.sleep(3)
    info, err = threads_api(token, f"{mid}", fields="permalink,timestamp")
    if not err and info:
        print(f"🔗 {info.get('permalink')}")


if __name__ == "__main__":
    main()
