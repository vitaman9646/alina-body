#!/usr/bin/env python3
"""Одиночный анонс-пост в Threads (текст + ссылка первым реплаем).

Для анонса новой недели программы / нового материала. Профиль-параметризован
(как post_matrix.py). Ссылка в теле поста не постится (Threads режет охват) —
она уходит первым реплаем.

Использование:
  python3 post_announce.py --profile vitaliy --text "..." --link "https://t.me/..."
  python3 post_announce.py --profile vitaliy --text "..." --link "..." --dry-run
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error

API = "https://graph.threads.net/v1.0"

PROFILES = {
    "alina": {"creds": "~/credentials/threads.env", "uid": "29048751384731011"},
    "vitaliy": {"creds": "~/credentials/vitaliy-threads.env", "uid": None},
}


def load_env(path):
    e = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    return e


def api(token, method, **params):
    url = f"{API}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read()), None
    except urllib.error.HTTPError as ex:
        return None, json.loads(ex.read().decode() or "{}").get("error", {}).get("message", f"HTTP {ex.code}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="alina", choices=list(PROFILES))
    ap.add_argument("--text", required=True)
    ap.add_argument("--link", help="ссылка первым реплаем (опц.)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    c = PROFILES[a.profile]
    env = load_env(os.path.expanduser(c["creds"]))
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID") or c["uid"]

    if a.dry_run:
        print(f"[dry-run] profile={a.profile}\n{a.text}\nlink-reply: {a.link}")
        return

    resp, err = api(token, f"{uid}/threads", media_type="TEXT", text=a.text)
    if err:
        print("❌ контейнер:", err)
        sys.exit(1)
    time.sleep(8)
    resp, err = api(token, f"{uid}/threads_publish", creation_id=resp["id"])
    if err:
        print("❌ публикация:", err)
        sys.exit(1)
    tid = resp["id"]
    print(f"✅ анонс: {tid}")

    if a.link:
        time.sleep(8)
        resp, err = api(token, f"{uid}/threads", media_type="TEXT", text=a.link, reply_to_id=tid)
        if err:
            print("❌ контейнер ссылки:", err)
            sys.exit(1)
        time.sleep(8)
        resp, err = api(token, f"{uid}/threads_publish", creation_id=resp["id"])
        if err:
            print("❌ публикация ссылки:", err)
            sys.exit(1)
        print(f"✅ ссылка в первом реплае: {resp['id']}")


if __name__ == "__main__":
    main()
