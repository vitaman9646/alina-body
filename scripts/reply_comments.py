#!/usr/bin/env python3
"""Ответы на комментарии в Threads + Instagram голосом Алины.

Опрашивает реплаи/комментарии на недавних постах, для новых генерирует ответ
через DeepSeek (голос Алины) и постит. Идемпотентно: отвеченные ID в replied_comments.json.

Использование: python3 reply_comments.py [--dry-run] [--limit N]
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

BASE = "/home/hermes/alina-body/content"
REPLIED_FILE = f"{BASE}/replied_comments.json"

# Alina voice (system prompt для DeepSeek)
SYSTEM = (
    "Ты — Алина, дружелюбный фитнес-тренер по домашним тренировкам для девушек 18–28. "
    "Отвечаешь на комментарии под своими постами. Голос: тёплый, простой, на «вы», коротко (1–3 предложения). "
    "Без ИИ-штампов, без обещаний результата, без медицинских советов, без выдуманных фактов и регалий. "
    "Технику держи в общем виде, без пошаговых инструкций. "
    "Если комментарий — спам, реклама, оскорбление или не по теме — ответь ровно словом SKIP."
)

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); env[k.strip()] = v.strip()
    return env

def http_json(url, token=None, data=None, method=None):
    h = {"Authorization": "Bearer " + token} if token else {}
    d = None
    if data is not None:
        h["Content-Type"] = "application/json"; d = json.dumps(data).encode()
    req = urllib.request.Request(url, data=d, headers=h, method=method)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=40).read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:200]

def post_form(url, token, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=40).read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:200]

def deepseek_reply(comment, key):
    """Генерирует ответ Алины на комментарий. Возвращает None если SKIP."""
    r, err = http_json("https://api.deepseek.com/v1/chat/completions", key, {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": comment},
        ],
        "max_tokens": 120,
        "temperature": 0.7,
    })
    if err or not r:
        return None
    try:
        txt = r["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        return None
    if txt.upper() == "SKIP" or not txt:
        return None
    return txt

def load_replied():
    if not os.path.exists(REPLIED_FILE):
        return set()
    return set(json.load(open(REPLIED_FILE)))

def save_replied(replied):
    json.dump(sorted(replied), open(REPLIED_FILE, "w"), ensure_ascii=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=30, help="сколько последних постов смотреть")
    args = ap.parse_args()

    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ienv = load_env(os.path.expanduser("~/credentials/instagram.env"))
    # DeepSeek key из профиля writer
    dkey = None
    for p in ["~/.hermes/profiles/writer/.env", "~/.hermes/profiles/builder/.env", "~/.hermes/.env"]:
        fp = os.path.expanduser(p)
        if os.path.exists(fp):
            e = load_env(fp)
            if e.get("DEEPSEEK_API_KEY"):
                dkey = e["DEEPSEEK_API_KEY"]; break
    if not dkey:
        print("DEEPSEEK_API_KEY не найден"); sys.exit(2)

    ttok = tenv["THREADS_ACCESS_TOKEN"]; tuid = tenv.get("THREADS_USER_ID", "29048751384731011")
    itok = ienv["INSTAGRAM_ACCESS_TOKEN"]
    replied = load_replied()
    new_count, posted = 0, 0

    # === Threads ===
    resp, err = http_json(f"https://graph.threads.net/v1.0/{tuid}/threads?fields=id,text,timestamp&limit={args.limit}", ttok)
    threads = (resp or {}).get("data", []) if not err else []
    for t in threads:
        tid = t.get("id")
        reps, _ = http_json(f"https://graph.threads.net/v1.0/{tid}/replies?fields=id,text,username&limit=50", ttok)
        for c in (reps or {}).get("data", []):
            cid = c.get("id"); text = (c.get("text") or "").strip()
            if not cid or not text or c.get("username") == "alina_body_fitness":
                continue
            key = f"th:{cid}"
            if key in replied:
                continue
            new_count += 1
            reply = deepseek_reply(text, dkey)
            print(f"[Threads] '{text[:50]}' -> {reply[:50] if reply else 'SKIP'}")
            if reply and not args.dry_run:
                r1, e1 = post_form(f"https://graph.threads.net/v1.0/{tuid}/threads", ttok,
                                   media_type="TEXT", text=reply, reply_to_id=cid)
                if e1:
                    print(f"  ❌ контейнер: {e1}"); continue
                crid = (r1 or {}).get("id")
                r2, e2 = post_form(f"https://graph.threads.net/v1.0/{tuid}/threads_publish", ttok, creation_id=crid)
                if e2:
                    print(f"  ❌ публикация: {e2}"); continue
                posted += 1
            replied.add(key)

    # === Instagram ===
    resp, err = http_json(f"https://graph.instagram.com/v21.0/me/media?fields=id,caption&limit={args.limit}", itok)
    media = (resp or {}).get("data", []) if not err else []
    for m in media:
        mid = m.get("id")
        cs, _ = http_json(f"https://graph.instagram.com/v21.0/{mid}/comments?fields=id,text,username&limit=50", itok)
        for c in (cs or {}).get("data", []):
            cid = c.get("id"); text = (c.get("text") or "").strip()
            if not cid or not text or c.get("username") == "alina_body_fitness":
                continue
            key = f"ig:{cid}"
            if key in replied:
                continue
            new_count += 1
            reply = deepseek_reply(text, dkey)
            print(f"[IG] '{text[:50]}' -> {reply[:50] if reply else 'SKIP'}")
            if reply and not args.dry_run:
                r1, e1 = post_form(f"https://graph.instagram.com/v21.0/{mid}/comments/{cid}/replies", itok, message=reply)
                if e1:
                    print(f"  ❌ IG реплай: {e1}"); continue
                posted += 1
            replied.add(key)

    if not args.dry_run:
        save_replied(replied)
    print(f"Итог: новых {new_count}, отвечено {posted}, всего в истории {len(replied)}")

if __name__ == "__main__":
    main()
