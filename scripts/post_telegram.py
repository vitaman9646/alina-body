#!/usr/bin/env python3
"""Публикует анонсы статей в Telegram-канал.

Читает content/last_published.json (список свежеопубликованных статей от publish_articles.py)
и для каждой шлёт анонс (заголовок + завлекаловка + ссылка на полную статью) в канал.

Секреты (bot token, channel) читает на рантайме из ~/credentials/telegram.env и не выводит.
Идемпотентность: отправленные slug'и пишутся в content/telegram_posted.txt, повторно не шлются.
"""

import os
import sys
import json
import urllib.request
import urllib.parse

ENV_PATH = os.path.expanduser("~/credentials/telegram.env")
LAST_PUBLISHED = "/home/hermes/alina-body/content/last_published.json"
POSTED_FILE = "/home/hermes/alina-body/content/telegram_posted.txt"
SITE_BASE = "https://alina-body.fitness"


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE) as f:
        return {l.strip() for l in f if l.strip()}


def mark_posted(slug):
    with open(POSTED_FILE, "a") as f:
        f.write(slug + "\n")


def tg_api(token, method, params):
    url = "https://api.telegram.org/bot{}/{}".format(token, method)
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    resp = json.loads(urllib.request.urlopen(req).read())
    if not resp.get("ok"):
        raise RuntimeError("Telegram API error: {}".format(resp))
    return resp


def main():
    dry_run = "--dry-run" in sys.argv
    if not os.path.exists(LAST_PUBLISHED):
        print("{} не найден — нечего анонсировать.".format(LAST_PUBLISHED))
        return
    articles = json.load(open(LAST_PUBLISHED))
    if not articles:
        print("Список статей пуст.")
        return

    token = channel = None
    if not dry_run:
        if not os.path.exists(ENV_PATH):
            print("Нет {} — укажи TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID.".format(ENV_PATH))
            sys.exit(2)
        env = load_env()
        token = env["TELEGRAM_BOT_TOKEN"]
        channel = env["TELEGRAM_CHANNEL_ID"]  # @username или числовой id

    posted = load_posted()
    sent = 0
    for a in articles:
        slug = a.get("slug", "")
        if slug in posted:
            print("  - уже анонсировано: {}".format(slug))
            continue
        title = a.get("title", "")
        teaser = a.get("excerpt", "")
        link = "{}/blog/{}".format(SITE_BASE, slug)
        text = "{}\n\n{}\n\nЧитать полностью → {}".format(title, teaser, link)
        if dry_run:
            print("[dry-run] -> {}\n{}\n---".format(channel, text))
            continue
        tg_api(token, "sendMessage", {"chat_id": channel, "text": text})
        mark_posted(slug)
        sent += 1
        print("  + {}".format(slug))

    if dry_run:
        print("Всего к анонсу: {}".format(len(articles)))
        return
    print("Анонсировано: {}".format(sent))


if __name__ == "__main__":
    main()
