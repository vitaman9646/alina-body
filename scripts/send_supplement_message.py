#!/usr/bin/env python3
"""Шлёт сообщение с карточками спортпита в канал + закрепляет."""
import os, json, html, urllib.request, urllib.parse

def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e

urls = json.load(open("/tmp/supp_urls.json"))

lines = [
    "💊 <b>Спортпит и БАДы — гайд от Alina Body</b>",
    "Аминокислоты и схема приёма — по факту, без воды.",
    "",
]
for it in urls:
    lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
lines += [
    "",
    "Нажимай на название — откроется карточка.",
    "⚠️ Перед применением БАД — консультация со специалистом.",
]
text = "\n".join(lines).strip()

env = load_env()
token = env["TELEGRAM_BOT_TOKEN"]
channel = env["TELEGRAM_CHANNEL_ID"]

data = urllib.parse.urlencode({"chat_id": channel, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
resp = json.loads(urllib.request.urlopen(req).read())
msg_id = resp["result"]["message_id"]
print("отправлено, message_id:", msg_id)

data = urllib.parse.urlencode({"chat_id": channel, "message_id": msg_id}).encode()
req = urllib.request.Request(f"https://api.telegram.org/bot{token}/pinChatMessage", data=data)
resp = json.loads(urllib.request.urlopen(req).read())
print("закреплено:", resp.get("ok"))
print("длина:", len(text), "символов")
