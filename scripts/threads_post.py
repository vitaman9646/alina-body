#!/usr/bin/env python3
"""Постинг в Threads: текст + фото (и опционально первый реплай со ссылкой).

Поток: create container (IMAGE + text) -> threads_publish -> (если --reply-text)
create reply container (reply_to_id) -> threads_publish.

Секреты читает из ~/credentials/threads.env (THREADS_ACCESS_TOKEN, THREADS_USER_ID).
Фото — публичный URL (наши фото уже в Supabase alina-media/social/).
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

ENV_PATH = os.path.expanduser("~/credentials/threads.env")
API = "https://graph.threads.net/v1.0"

def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def graph(token, method, **params):
    url = f"{API}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        resp = json.loads(e.read().decode() or "{}")
        return None, resp.get("error", {}).get("message", f"HTTP {e.code}")
    if "error" in resp:
        return None, resp["error"].get("message", "unknown error")
    return resp, None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", help="текст поста (без ссылки)")
    p.add_argument("--image", help="публичный URL фото")
    p.add_argument("--reply-text", help="текст реплая (со ссылкой), опционально")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.text and not args.image:
        print("Нужен --text или --image."); sys.exit(2)

    env = load_env()
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID", "29048751384731011")

    if args.dry_run:
        print("[dry-run] text:", args.text[:80])
        print("[dry-run] image:", args.image)
        print("[dry-run] reply:", args.reply_text)
        return

    # 1. Контейнер поста
    params = {"media_type": "IMAGE", "text": args.text or ""}
    if args.image:
        params["image_url"] = args.image
        params["alt_text"] = "Алина — домашний фитнес"
    resp, err = graph(token, f"{uid}/threads", **params)
    if err:
        print("Ошибка контейнера:", err); sys.exit(1)
    creation_id = resp.get("id")
    print("контейнер:", creation_id)

    # 2. Публикация
    resp, err = graph(token, f"{uid}/threads_publish", creation_id=creation_id)
    if err:
        print("Ошибка публикации:", err); sys.exit(1)
    thread_id = resp.get("id")
    print("опубликовано:", thread_id)

    # 3. Реплай со ссылкой
    if args.reply_text and thread_id:
        resp, err = graph(token, f"{uid}/threads", media_type="TEXT", text=args.reply_text, reply_to_id=thread_id)
        if err:
            print("Ошибка контейнера реплая:", err); sys.exit(1)
        rcid = resp.get("id")
        resp, err = graph(token, f"{uid}/threads_publish", creation_id=rcid)
        if err:
            print("Ошибка публикации реплая:", err); sys.exit(1)
        print("реплай опубликован:", resp.get("id"))

if __name__ == "__main__":
    main()
