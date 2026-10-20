#!/usr/bin/env python3
"""Собирает сообщение со всеми рецептами (название → ссылка) и шлёт в канал + закрепляет."""
import os, json, html, urllib.request, urllib.parse

CATS = [
    ("ЗАВТРАКИ", "🌅 Завтраки"),
    ("ОБЕДЫ", "🍲 Обеды"),
    ("УЖИНЫ", "🌙 Ужины"),
    ("ДЕСЕРТЫ И ВЫПЕЧКА", "🍰 Десерты и выпечка"),
]

def title(s):
    s = s.lower().replace("пп", "ПП")
    return s[:1].upper() + s[1:]

def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e

urls = json.load(open("/tmp/recipe_urls.json"))
by_cat = {}
for x in urls:
    by_cat.setdefault(x["category"], []).append(x)

lines = [
    "🍽 <b>ПП-рецепты от Alina Body</b>",
    "Нажимай на блюдо — откроется карточка с КБЖУ, ингредиентами и готовкой.",
    "",
]
for key, label in CATS:
    items = by_cat.get(key, [])
    if not items:
        continue
    lines.append(f"<b>{label}</b>")
    for it in items:
        nm = title(it["name"])
        lines.append(f'<a href="{it["url"]}">{html.escape(nm)}</a>')
    lines.append("")

text = "\n".join(lines).strip()

env = load_env()
token = env["TELEGRAM_BOT_TOKEN"]
channel = env["TELEGRAM_CHANNEL_ID"]

# отправка
data = urllib.parse.urlencode({"chat_id": channel, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
resp = json.loads(urllib.request.urlopen(req).read())
msg_id = resp["result"]["message_id"]
print("отправлено, message_id:", msg_id)

# закрепление
data = urllib.parse.urlencode({"chat_id": channel, "message_id": msg_id}).encode()
req = urllib.request.Request(f"https://api.telegram.org/bot{token}/pinChatMessage", data=data)
resp = json.loads(urllib.request.urlopen(req).read())
print("закреплено:", resp.get("ok"))

print("\nДлина сообщения:", len(text), "символов")
print("Всего рецептов:", len(urls))
