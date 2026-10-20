#!/usr/bin/env python3
"""Ответы на комментарии в Threads + Instagram голосом Алины.

Threads: генерирует ответ через DeepSeek (голос Алины) и постит.
Instagram: если в комментарии есть триггер-слово (чеклист/схема/скинь/...) — Алина
отправляет чеклист в ЛИЧНЫЕ СООБЩЕНИЯ (DM) и отвечает публично «отправила в личку».
Остальные комментарии — обычный ответ через DeepSeek.
Идемпотентно: отвеченные ID в replied_comments.json.

Использование: python3 reply_comments.py [--dry-run] [--limit N]
"""
import os
import sys
import json
import re
import argparse
import urllib.request
import urllib.parse
import urllib.error

BASE = "/home/hermes/alina-body/content"
REPLIED_FILE = f"{BASE}/replied_comments.json"
MATRIX_DIR = f"{BASE}/threads-matrix"
POSTED_MATRIX = f"{MATRIX_DIR}/posted.json"
PENDING_REPLIES = f"{MATRIX_DIR}/pending_replies.json"

# Триггер-слова → DM с чеклистом (Instagram)
TRIGGERS = ["чеклист", "схема", "скинь", "материал", "разминк", "с чего начать"]
# Просьба отдать лид-магнит под постом в Threads (дай сборник/чеклист/ссылку/рецепты и т.п.)
ASK_TRIGGERS = ["сборник", "чеклист", "скинь", "скиньте", "ссылк", "где взять", "где скачать",
                "как получить", "пришл", "подели", "рецепт", "материал", "гайд"]
LEAD_URL = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/lead-magnet/glutes-checklist.jpg"
LEAD_TEXT = "Держите чеклист «5 упражнений на ягодицы» 💕 Забирайте и пробуйте сегодня."
SITE = "https://alina-body.fitness"

# Alina voice (system prompt для DeepSeek)
SYSTEM = (
    "Ты — Алина, дружелюбный фитнес-тренер по домашним тренировкам для девушек 18–28. "
    "Отвечаешь на комментарии под своими постами. Голос: тёплый, простой, на «вы», коротко (1–3 предложения). "
    "Без ИИ-штампов, без обещаний результата, без медицинских советов, без выдуманных фактов и регалий. "
    "Технику держи в общем виде, без пошаговых инструкций. "
    "ВОВЛЕЧЕНИЕ: когда естественно, заканчивай ответ коротким встречным вопросом — так обсуждение живёт дольше. "
    "ССЫЛКИ: если человек спрашивает про полную программу, «сколько стоит», «как заниматься» — "
    "ответь тепло и дай ссылку на сайт: https://alina-body.fitness. "
    "Если про Telegram-канал — https://t.me/alinabodyfree. "
    "Если человек просит материал (сборник/чеклист/гайд), о котором сказано в КОНТЕКСТЕ поста — "
    "дай ссылку из контекста тепло и коротко. "
    "Если человек просто хвалит или пишет не по теме — ссылку НЕ давай. "
    "Если комментарий — спам, реклама, оскорбление или совсем не по теме — ответь ровно словом SKIP."
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


def send_dm(ig_uid, token, recipient_id, text=None, image_url=None):
    """Отправляет DM (текст или картинку) через Instagram Messaging API."""
    if text:
        return http_json(f"https://graph.instagram.com/v21.0/{ig_uid}/messages", token,
                         {"recipient": {"id": recipient_id}, "message": {"text": text}})
    if image_url:
        return http_json(f"https://graph.instagram.com/v21.0/{ig_uid}/messages", token,
                         {"recipient": {"id": recipient_id},
                          "message": {"attachment": {"type": "image", "payload": {"url": image_url}}}})
    return None, "no text/image"


def deepseek_reply(comment, key, context=None):
    """Генерирует ответ Алины на комментарий. Возвращает None если SKIP."""
    user_msg = comment
    if context:
        user_msg = f"КОНТЕКСТ поста: {context}\nКомментарий: {comment}"
    r, err = http_json("https://api.deepseek.com/v1/chat/completions", key, {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
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


def load_thread_map():
    """thread_id -> {link, title} из posted.json матриц: какой пост какой лид-магнит продвигает."""
    m = {}
    if not os.path.exists(POSTED_MATRIX):
        return m
    try:
        state = json.load(open(POSTED_MATRIX))
    except (json.JSONDecodeError, OSError):
        return m
    for name, entry in state.items():
        title, link = None, None
        fpath = os.path.join(MATRIX_DIR, name)
        if os.path.exists(fpath):
            try:
                for line in open(fpath, encoding="utf-8"):
                    s = line.strip()
                    if s.startswith("source:"):
                        title = s.split(":", 1)[1].strip().split(" — ")[0].strip()
                    elif s.startswith("link:"):
                        link = s.split(":", 1)[1].strip()
            except OSError:
                pass
        for cell in (entry.get("posted") or {}).values():
            tid = cell.get("thread_id")
            if tid:
                m[tid] = {"link": cell.get("link") or link, "title": title}
    return m


def cancel_pending_reply(thread_id):
    """Убирает отложенную +2ч ссылку поста, если Алина уже дала её в комментарии (не дублировать)."""
    if not os.path.exists(PENDING_REPLIES):
        return
    try:
        data = json.load(open(PENDING_REPLIES))
    except (json.JSONDecodeError, OSError):
        return
    pending = data.get("pending", [])
    kept = [it for it in pending if it.get("thread_id") != thread_id]
    if len(kept) != len(pending):
        data["pending"] = kept
        json.dump(data, open(PENDING_REPLIES, "w"), ensure_ascii=False, indent=2)
        print(f"  🚫 Отложенная ссылка для поста {thread_id} отменена — уже дана в комментарии")


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
    me, _ = http_json("https://graph.instagram.com/v21.0/me?fields=user_id", itok)
    ig_uid = (me or {}).get("user_id") or "17841423980092922"

    replied = load_replied()
    thread_map = load_thread_map()
    new_count, posted, dm_count = 0, 0, 0

    # === Threads ===
    resp, err = http_json(f"https://graph.threads.net/v1.0/{tuid}/threads?fields=id,text,timestamp&limit={args.limit}", ttok)
    threads = (resp or {}).get("data", []) if not err else []
    for t in threads:
        tid = t.get("id")
        lm = thread_map.get(tid, {})
        reps, _ = http_json(f"https://graph.threads.net/v1.0/{tid}/replies?fields=id,text,username&limit=50", ttok)
        for c in (reps or {}).get("data", []):
            cid = c.get("id"); text = (c.get("text") or "").strip()
            if not cid or not text or c.get("username") == "alina_body_fitness":
                continue
            key = f"th:{cid}"
            if key in replied:
                continue
            new_count += 1
            low = text.lower()
            is_ask = bool(lm.get("link")) and any(w in low for w in ASK_TRIGGERS)
            if is_ask:
                title = (lm.get("title") or "").strip()
                reply = (f"Держите, {title} — тут 👇\n{lm['link']}" if title
                         else f"Держите, материал тут 👇\n{lm['link']}")
            else:
                ctx = None
                if lm.get("link"):
                    ctx = f"лид-магнит «{lm.get('title') or 'материал'}», ссылка {lm['link']}"
                reply = deepseek_reply(text, dkey, context=ctx)
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
                if is_ask:
                    cancel_pending_reply(tid)
            replied.add(key)

    # === Instagram ===
    resp, err = http_json(f"https://graph.instagram.com/v21.0/me/media?fields=id,caption&limit={args.limit}", itok)
    media = (resp or {}).get("data", []) if not err else []
    for m in media:
        mid = m.get("id")
        cs, _ = http_json(f"https://graph.instagram.com/v21.0/{mid}/comments?fields=id,text,username,from{{id,username}}&limit=50", itok)
        for c in (cs or {}).get("data", []):
            cid = c.get("id"); text = (c.get("text") or "").strip()
            if not cid or not text or c.get("username") == "alina_body_fitness":
                continue
            key = f"ig:{cid}"
            if key in replied:
                continue
            new_count += 1
            low = text.lower()
            is_trigger = any(t in low for t in TRIGGERS)
            if is_trigger:
                from_id = (c.get("from") or {}).get("id")
                print(f"[IG DM] '{text[:50]}' -> чеклист в личку (recipient={from_id})")
                if args.dry_run:
                    replied.add(key); continue
                ok = True
                d1, e1 = send_dm(ig_uid, itok, from_id, text=LEAD_TEXT)
                if e1:
                    print(f"  ❌ DM текст: {e1}"); ok = False
                d2, e2 = send_dm(ig_uid, itok, from_id, image_url=LEAD_URL)
                if e2:
                    print(f"  ❌ DM картинка: {e2}"); ok = False
                r1, e3 = post_form(f"https://graph.instagram.com/v21.0/{mid}/comments/{cid}/replies",
                                   itok, message="Отправила в личные сообщения 💕")
                if e3:
                    print(f"  ❌ публичный реплай: {e3}")
                if ok:
                    dm_count += 1
                    print(f"  ✅ чеклист отправлен в DM -> {from_id}")
            else:
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
    print(f"Итог: новых {new_count}, отвечено {posted}, DM {dm_count}, всего в истории {len(replied)}")


if __name__ == "__main__":
    main()
