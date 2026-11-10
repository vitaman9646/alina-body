#!/usr/bin/env python3
"""Публикует в канал пост с тарифами + реквизитами (для модерации Prodamus)."""
import os, json, urllib.request, urllib.parse

ENV = os.path.expanduser("~/credentials/telegram.env")

def load_env():
    env = {}
    for line in open(ENV):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

text = (
    "Тарифы и курсы Alina Body\n"
    "\n"
    "🏋️‍♀️ Курс «Домашние тренировки на всё тело: 12 недель» — 2 990 ₽\n"
    "• 26 модулей · 147 уроков · фото-демонстрации упражнений\n"
    "\n"
    "🥗 Подписка Alina Body Club — 1 500 ₽/мес\n"
    "• закрытый Telegram-канал: программы тренировок, меню, все рецепты с КБЖУ\n"
    "\n"
    "🍎 Курсы по питанию (рецепты и меню) — скоро\n"
    "\n"
    "Реквизиты:\n"
    "Карпинский Виталий Сергеевич · ИНН 090801464643\n"
    "E-mail: mrvt9646@gmail.com\n"
    "Подробнее: alina-body.fitness/tarify"
)

env = load_env()
token = env["TELEGRAM_BOT_TOKEN"]
channel = env["TELEGRAM_CHANNEL_ID"]

url = f"https://api.telegram.org/bot{token}/sendMessage"
data = urllib.parse.urlencode({"chat_id": channel, "text": text}).encode()
resp = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data)).read())
if not resp.get("ok"):
    raise SystemExit("Telegram API error: " + json.dumps(resp))
mid = resp["result"]["message_id"]
print("message_id:", mid)
print("ссылка: https://t.me/alinabodyfree/" + str(mid))
