#!/usr/bin/env python3
"""Переписывает вирусные ветки Threads под нишу фитнес-тренера (Алина или Виталий).

Читает текст чужой ветки, сохраняет хук+структуру, переписывает под спорт/фитнес
голосом автора, один пост ≤500 символов, без стоп-слов и обещаний.

Вход: --text "..." | --file путь.txt | stdin (ветки разделяются строкой "---").
Выход: печатает готовый пост + дописывает в content/viral-pool.md (пул на ревью).
Авто-постинга НЕТ — это безопасный режим, включается только после одобрения владельца.

Использование:
  python3 scripts/thread_rewriter.py --text "…"
  python3 scripts/thread_rewriter.py --file ветки.txt
  python3 scripts/thread_rewriter.py --profile vitaliy --text "…"
"""
import os
import sys
import json
import argparse
import time
import urllib.request
import urllib.error

BASE = "/home/hermes/alina-body/content"
POOL = f"{BASE}/viral-pool.md"
STOPWORDS = "/home/hermes/alina-body/scripts/stopwords.json"
MAX_TEXT = 500

ALINA_SYSTEM = (
    "Ты — редактор, переписываешь вирусные посты Threads под нишу фитнес-тренера Алины "
    "(домашние тренировки и питание для девушек 18–28, голос «на ты»). "
    "Сохрани ХУК и СТРУКТУРУ исходной ветки (что заставляет дочитать и ответить), но смени тему "
    "на спорт/фитнес/питание. Никакого дословного копирования — только каркас. "
    "Если исходник — ветка из нескольких постов, сожми в один сильный пост. "
    "Правила: 1) голос Алины — на «ты», тепло, без мата, без «братан/бро/жиза/го», без упоминания ИИ; "
    "2) один пост до 500 символов; "
    "3) без обещаний результата, без медицинских советов, без выдуманных цифр, "
    "без «жиросжигание/детокс/волшебная таблетка»; "
    "4) выведи ТОЛЬКО готовый пост, без кавычек, без пояснений и заголовков."
)

VITALIY_SYSTEM = (
    "Ты — редактор, переписываешь вирусные посты Threads под нишу фитнес-тренера Виталия "
    "(качалка, силовые, теория тренировок, мужской голос «на ты»). "
    "Сохрани ХУК и СТРУКТУРУ исходной ветки (что цепляет), но смени тему на качалку/силовые. "
    "Никакого дословного копирования — только каркас. Ветку из нескольких постов сожми в один. "
    "Правила: 1) голос Виталия — на «ты», по-мужски прямо, без сюсюканья, без «братан/бро/жиза/го», "
    "без упоминания ИИ; 2) один пост до 500 символов; "
    "3) без мед-обещаний, без выдуманных цифр результата, без диагнозов; "
    "4) выведи ТОЛЬКО готовый пост, без кавычек, без пояснений и заголовков."
)

SYSTEMS = {"alina": ALINA_SYSTEM, "vitaliy": VITALIY_SYSTEM}


def load_env(path):
    env = {}
    try:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        pass
    return env


def http_json(url, token, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:200]


def deepseek_rewrite(text, key, system):
    r, err = http_json("https://api.deepseek.com/v1/chat/completions", key, {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Исходная ветка:\n{text.strip()}"},
        ],
        "max_tokens": 400,
        "temperature": 0.8,
    })
    if err or not r:
        return None, err or "пустой ответ"
    try:
        out = r["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        return None, "нет choices"
    out = out.strip().strip('"').strip("«»").strip()
    return out, None


def hard_hits(text):
    if not os.path.exists(STOPWORDS):
        return []
    try:
        sw = json.load(open(STOPWORDS))
    except (json.JSONDecodeError, OSError):
        return []
    hard = sw.get("hard", [])
    low = text.lower()
    return [w for w in hard if str(w).lower() in low]


def truncate500(text):
    text = text.strip()
    if len(text) <= MAX_TEXT:
        return text
    cut = text[:MAX_TEXT]
    for sep in (". ", "! ", "? ", " "):
        i = cut.rfind(sep)
        if i > 300:
            return cut[:i + 1].rstrip()
    return cut


def append_pool(source, post, profile):
    ts = time.strftime("%Y-%m-%d %H:%M")
    head = source.strip().split("\n")[0][:40]
    with open(POOL, "a", encoding="utf-8") as f:
        f.write(f"\n## {ts} [{profile}] — {head}\n{post}\n")
    print(f"  → дописано в {POOL}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--profile", default="alina", choices=list(SYSTEMS))
    args = ap.parse_args()

    if args.text:
        chunks = [args.text]
    elif args.file:
        raw = open(args.file, encoding="utf-8").read()
        chunks = [c.strip() for c in raw.split("\n---\n") if c.strip()]
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
        chunks = [c.strip() for c in raw.split("\n---\n") if c.strip()]
    else:
        print("Нужен --text, --file или stdin."); sys.exit(1)

    key = None
    for p in ["~/.hermes/profiles/writer/.env", "~/.hermes/profiles/builder/.env", "~/.hermes/.env"]:
        fp = os.path.expanduser(p)
        if os.path.exists(fp):
            e = load_env(fp)
            if e.get("DEEPSEEK_API_KEY"):
                key = e["DEEPSEEK_API_KEY"]
                break
    if not key:
        print("DEEPSEEK_API_KEY не найден"); sys.exit(2)

    system = SYSTEMS[args.profile]
    for i, src in enumerate(chunks, 1):
        post, err = deepseek_rewrite(src, key, system)
        if err or not post:
            print(f"[{i}/{len(chunks)}] ❌ ошибка: {err}")
            continue
        post = truncate500(post)
        hits = hard_hits(post)
        print(f"[{i}/{len(chunks)}] ✅ ({len(post)} симв.):\n{post}\n")
        if hits:
            print(f"  ⚠️ стоп-слова: {hits}")
        append_pool(src, post, args.profile)


if __name__ == "__main__":
    main()
