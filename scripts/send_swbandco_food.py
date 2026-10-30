#!/usr/bin/env python3
"""Публикация 5 закрепов «Еда на ходу» в канал Алины.

На категорию: залить обложку в Supabase -> отправить обложку фото -> отправить
HTML-оглавление (список блюд-ссылок на карточки) -> закрепить оглавление.
Без LLM — только Telegram + Supabase API.
"""
import json
import os
import sys
import urllib.parse

import requests

REPO = "/home/hermes/alina-body"
URLS_SRC = "/tmp/recipe_urls.json"          # name, category(str), url (карточки)
RECIPES_SRC = "/tmp/recipes.json"           # name, category_key
COVERS = f"{REPO}/alina-media/swbandco-food"

CATS = {
    "1-lanchi":      ("🥗", "Холодные ланчи без разогрева"),
    "2-termos":      ("🍲", "Горячие обеды для термоса"),
    "3-na-hodu":     ("🌯", "Еда на ходу: врапы и роллы"),
    "4-salad-banka": ("🫙", "Салат в банке"),
    "5-perekusy":    ("🍫", "Здоровые перекусы"),
}


def load_env(path):
    e = {}
    for line in open(os.path.expanduser(path)):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    return e


def title(s):
    return s[:1].upper() + s[1:]


def main():
    dry = "--dry-run" in sys.argv
    tg = load_env("~/credentials/telegram.env")
    bot = tg["TELEGRAM_BOT_TOKEN"]
    channel = tg["TELEGRAM_CHANNEL_ID"]
    supa = load_env("~/credentials/threads.env")
    supa_url = supa["SUPABASE_URL"].rstrip("/")
    supa_key = supa["SUPABASE_SERVICE_ROLE_KEY"]

    # маппинг name -> category_key
    key_by_name = {r["name"]: r["category_key"] for r in json.load(open(RECIPES_SRC))}
    urls = json.load(open(URLS_SRC))
    by_key = {}
    for u in urls:
        k = key_by_name.get(u["name"])
        by_key.setdefault(k, []).append(u)

    for key, (emoji, label) in CATS.items():
        items = by_key.get(key, [])
        if not items:
            print(f"SKIP {key}: нет рецептов")
            continue

        # 1) залить обложку
        cover_path = os.path.join(COVERS, f"cover-{key}.jpg")
        cover_url = f"{supa_url}/storage/v1/object/public/alina-media/swbandco-food/cover-{key}.jpg"
        if not dry:
            with open(cover_path, "rb") as f:
                r = requests.post(
                    f"{supa_url}/storage/v1/object/alina-media/swbandco-food/cover-{key}.jpg",
                    headers={"Authorization": f"Bearer {supa_key}", "apikey": supa_key,
                             "x-upsert": "true", "Content-Type": "image/jpeg"},
                    data=f.read(), timeout=120)
            if r.status_code not in (200, 201):
                print(f"[{key}] обложка upload FAIL {r.status_code}")

        # 2) отправить обложку
        if not dry:
            r = requests.post(f"https://api.telegram.org/bot{bot}/sendPhoto",
                              data={"chat_id": channel, "photo": cover_url},
                              timeout=60).json()
            if not r.get("ok"):
                print(f"[{key}] sendPhoto FAIL: {r.get('description')}")

        # 3) HTML-оглавление
        lines = [
            f"{emoji} <b>{label}</b> — {len(items)} рецептов",
            "Нажимай на блюдо — откроется карточка с КБЖУ, ингредиентами и готовкой.",
            "",
        ]
        for it in items:
            nm = title(it["name"])
            lines.append(f'• <a href="{it["url"]}">{nm}</a>')
        lines.append("")
        lines.append("Больше шпаргалок и меню — в закрепе канала 👇")
        text = "\n".join(lines)

        msg_id = None
        if not dry:
            r = requests.post(f"https://api.telegram.org/bot{bot}/sendMessage",
                              data={"chat_id": channel, "text": text,
                                    "parse_mode": "HTML", "disable_web_page_preview": "true"},
                              timeout=60).json()
            if r.get("ok"):
                msg_id = r["result"]["message_id"]
                print(f"[{key}] оглавление отправлено, message_id={msg_id}")
            else:
                print(f"[{key}] sendMessage FAIL: {r.get('description')}")

            # 4) закрепить оглавление
            if msg_id:
                pr = requests.post(f"https://api.telegram.org/bot{bot}/pinChatMessage",
                                   data={"chat_id": channel, "message_id": msg_id},
                                   timeout=60).json()
                print(f"[{key}] закреплено: {pr.get('ok')} ({pr.get('description','')})")
        else:
            print(f"[dry] {emoji} {label}: {len(items)} блюд, обложка {cover_url}")


if __name__ == "__main__":
    main()
