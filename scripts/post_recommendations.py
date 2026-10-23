#!/usr/bin/env python3
"""Одноразовый постинг 4 рекомендаций SWBAND.CO в Telegram-канал Алины.

Читает content/swbandco-rekomendacii.md, берёт блоки между «## » и «---»,
шлёт каждый через sendMessage в TELEGRAM_CHANNEL_ID. Секреты читает из env на рантайме.
Идемпотентность: отправленные индексы пишутся в content/swbandco_rekomendacii_posted.txt.
"""
import os
import sys
import json
import urllib.request
import urllib.parse

ENV = os.path.expanduser("~/credentials/telegram.env")
SRC = "/home/hermes/alina-body/content/swbandco-rekomendacii.md"
POSTED = "/home/hermes/alina-body/content/swbandco_rekomendacii_posted.txt"


def load_env():
    e = {}
    for line in open(ENV):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    return e


def parse_posts():
    raw = open(SRC, encoding="utf-8").read()
    blocks = []
    # каждая секция начинается с "## N. " и длится до следующей "## " или конца
    import re
    parts = re.split(r"^## \d+\. .*$", raw, flags=re.M)
    for p in parts[1:]:
        body = p.strip().strip("-").strip()
        if body:
            blocks.append(body)
    return blocks


def main():
    dry = "--dry-run" in sys.argv
    posts = parse_posts()
    if len(posts) != 4:
        print("⚠️ ожидал 4 блока, нашёл {}".format(len(posts)))
        if not dry:
            sys.exit(2)
    posted = set()
    if os.path.exists(POSTED):
        posted = {int(l) for l in open(POSTED) if l.strip().isdigit()}

    env = {} if dry else load_env()
    for i, text in enumerate(posts, 1):
        if i in posted:
            print("  - уже отправлено: {}".format(i))
            continue
        if dry:
            print("[dry-run] #{} -> {}\n---".format(i, text[:60]))
            continue
        url = "https://api.telegram.org/bot{}/sendMessage".format(env["TELEGRAM_BOT_TOKEN"])
        data = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHANNEL_ID"], "text": text}).encode()
        resp = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data)).read())
        if resp.get("ok"):
            mid = resp["result"]["message_id"]
            chat = resp["result"]["chat"]["username"]
            print("✅ #{} -> message_id {} @{}".format(i, mid, chat))
            with open(POSTED, "a") as f:
                f.write(str(i) + "\n")
        else:
            print("❌ #{}: {}".format(i, resp))


if __name__ == "__main__":
    main()
