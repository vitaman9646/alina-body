#!/usr/bin/env python3
"""Публикует статьи из content/articles.md в таблицу posts (Supabase).

Автономный шаг пайплайна: researcher (темы) -> writer (статьи) -> этот скрипт (публикация).
После вставки статьи автоматически попадают в блог, RSS (/rss.xml) и, через него, в Дзен.

Формат articles.md (статьи разделяются строкой `---`):
    ## Название статьи
    <пустая строка>
    Один абзац-аннотация (1-2 предложения -> excerpt).
    <пустая строка>
    Тело статьи в Markdown (подзаголовки ###, списки, **жирный**, [ссылки]).
    > Футер CTA (сайт + Telegram).

Идемпотентность: slug (транслитерация заголовка) служит ключом — повторная вставка пропускается.
Секреты читаются на рантайме из ~/credentials/threads.env и НЕ выводятся.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

try:
    import markdown
except ImportError:
    print("Нужна библиотека markdown: pip install markdown")
    sys.exit(2)

ENV_PATH = os.path.expanduser("~/credentials/threads.env")
ARTICLES_PATH = "/home/hermes/alina-body/content/articles.md"

# Транслитерация кириллицы для slug
TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def slugify(text):
    text = text.lower().strip()
    out = []
    for ch in text:
        if ch in TRANS:
            out.append(TRANS[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in " -—–":
            out.append("-")
    s = "".join(out)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "article"


def parse_articles(text):
    """Разбивает articles.md на список {title, excerpt, content_md}."""
    blocks = re.split(r"\n\s*---\s*\n", text)
    articles = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        title = None
        start = 0
        for i, ln in enumerate(lines):
            m = re.match(r"^#{1,3}\s+(.+?)\s*$", ln)
            if m:
                title = m.group(1).strip()
                start = i + 1
                break
        if not title:
            continue
        rest = lines[start:]
        excerpt = ""
        body = rest
        for i, ln in enumerate(rest):
            ln = ln.strip()
            if ln and not ln.startswith("#") and not ln.startswith(">"):
                excerpt = ln
                body = rest[i + 1:]
                break
        while body and not body[0].strip():
            body = body[1:]
        content_md = "\n".join(body).strip()
        articles.append({"title": title, "excerpt": excerpt, "content_md": content_md})
    return articles


def main():
    dry_run = "--dry-run" in sys.argv
    if not os.path.exists(ARTICLES_PATH):
        print(f"Файл {ARTICLES_PATH} не найден — нечего публиковать.")
        return

    env = load_env()
    base = env["SUPABASE_URL"].rstrip("/")
    key = env["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    raw = open(ARTICLES_PATH, encoding="utf-8").read()
    articles = parse_articles(raw)
    if not articles:
        print("Статей в articles.md не найдено (проверь формат: ## заголовок, аннотация, ---).")
        return

    # Существующие slug (идемпотентность)
    req = urllib.request.Request(base + "/rest/v1/posts?select=slug", headers=headers)
    existing = set()
    try:
        for row in json.loads(urllib.request.urlopen(req).read()):
            existing.add(row["slug"])
    except Exception as e:
        print(f"Не удалось прочитать posts: {e}")
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat()
    published, skipped, failed = [], [], []
    for a in articles:
        slug = slugify(a["title"])
        if slug in existing:
            # уже опубликована → идемпотентный пропуск
            skipped.append(a["title"])
            continue
        if dry_run:
            print(f"[dry-run] {a['title']}  ->  /blog/{slug}")
            existing.add(slug)
            continue
        content_html = markdown.markdown(a["content_md"], extensions=["extra"])
        payload = {
            "title": a["title"],
            "slug": slug,
            "excerpt": a["excerpt"],
            "content": content_html,
            "cover_image": None,
            "published_at": now,
        }
        req = urllib.request.Request(
            base + "/rest/v1/posts",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
        )
        try:
            urllib.request.urlopen(req).read()
            existing.add(slug)
            published.append((a["title"], slug, a["excerpt"]))
        except urllib.error.HTTPError as e:
            failed.append((a["title"], e.code, e.read().decode()[:200]))

    if dry_run:
        print(f"Всего к публикации: {len(articles)}")
        return
    print(f"Опубликовано: {len(published)}")
    for t, s, e in published:
        print(f"  + {t}  ->  /blog/{s}")
    # отдаём список свежеопубликованного для Telegram-анонсов (post_telegram.py)
    if published:
        out = [{"title": t, "slug": s, "excerpt": e} for t, s, e in published]
        with open("/home/hermes/alina-body/content/last_published.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    if skipped:
        print(f"Пропущено (slug уже есть): {len(skipped)}")
        for t in skipped:
            print(f"  - {t}")
    if failed:
        print(f"Ошибки: {len(failed)}")
        for t, code, msg in failed:
            print(f"  ! {t}: HTTP {code} {msg}")


if __name__ == "__main__":
    main()
