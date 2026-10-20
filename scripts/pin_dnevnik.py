#!/usr/bin/env python3
"""Закреп «Дневника питания»: карточки-ссылки + лонгрид."""
import os, json, html, urllib.request, urllib.parse

def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e
env = load_env()
TOKEN = env["TELEGRAM_BOT_TOKEN"]; CH = env["TELEGRAM_CHANNEL_ID"]

def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=40).read())

urls = json.load(open("/tmp/dnevnik_urls.json"))
lonrid = open("/home/hermes/alina-body/inbox/dnevnik_lonrid.txt").read().strip()

lines = ["<b>Дневник питания + активность — гайд</b>", "", "<b>Карточки</b> (нажми на название):"]
for it in urls:
    lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
lines += ["", "──────────", "", lonrid]
text = "\n".join(lines)

r = api("sendMessage", chat_id=CH, text=text, parse_mode="HTML", disable_web_page_preview="true")
mid = r["result"]["message_id"]
api("pinChatMessage", chat_id=CH, message_id=mid)
print("закреплено message_id:", mid)
