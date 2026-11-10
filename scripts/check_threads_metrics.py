#!/usr/bin/env python3
"""Выгружает посты обоих профилей Threads и проверяет, какие метрики реально доступны."""
import os, json, urllib.request, urllib.parse

PROFILES = {
    "alina": os.path.expanduser("~/credentials/threads.env"),
    "vitaliy": os.path.expanduser("~/credentials/vitaliy-threads.env"),
}

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

def fetch_threads(token, user_id):
    """Выгрузить все свои посты (с paging)."""
    out = []
    url = f"https://graph.threads.net/v1.0/{user_id}/threads?fields=id,text,timestamp,permalink&limit=100"
    while url:
        d = get(url, token)
        out.extend(d.get("data", []))
        url = d.get("paging", {}).get("next")
    return out

for name, envpath in PROFILES.items():
    env = load_env(envpath)
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID") or ("29048751384731011" if name == "alina" else None)
    try:
        posts = fetch_threads(token, uid)
        print(f"[{name}] user_id={uid} постов: {len(posts)}")
        json.dump(posts, open(f"/tmp/threads_posts_{name}.json", "w"), ensure_ascii=False, indent=2)
        # проверить метрики на первом посте
        if posts:
            pid = posts[0]["id"]
            # 1) поля view_count/like_count на thread
            try:
                d = get(f"https://graph.threads.net/v1.0/{pid}?fields=id,view_count,like_count,reply_count,text", token)
                print(f"[{name}] поля thread: {list(d.keys())}")
            except Exception as e:
                print(f"[{name}] поля thread ошибка: {e}")
            # 2) insights
            try:
                d = get(f"https://graph.threads.net/v1.0/{pid}/insights", token)
                print(f"[{name}] insights: {json.dumps(d)[:200]}")
            except Exception as e:
                print(f"[{name}] insights: НЕДОСТУПНО ({e})")
    except Exception as e:
        print(f"[{name}] ошибка выгрузки: {e}")
