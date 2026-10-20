#!/usr/bin/env python3
"""Универсальный закреп лид-магнита: карточки-ссылки + лонгрид.

Использование: python3 pin_guide.py --title "..." --urls /tmp/x_urls.json --lonrid /path/lonrid.txt
"""
import os, json, html, argparse, urllib.request, urllib.parse

def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e

ap = argparse.ArgumentParser()
ap.add_argument("--title", required=True)
ap.add_argument("--urls", required=True)
ap.add_argument("--lonrid", required=True)
args = ap.parse_args()

env = load_env()
TOKEN = env["TELEGRAM_BOT_TOKEN"]; CH = env["TELEGRAM_CHANNEL_ID"]

def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=40).read())

urls = json.load(open(args.urls))
lonrid = open(args.lonrid).read().strip()

lines = [f"<b>{args.title}</b>", "", "<b>Карточки</b> (нажми на название):"]
for it in urls:
    lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
lines += ["", "──────────", "", lonrid]
text = "\n".join(lines)

r = api("sendMessage", chat_id=CH, text=text, parse_mode="HTML", disable_web_page_preview="true")
mid = r["result"]["message_id"]
api("pinChatMessage", chat_id=CH, message_id=mid)
print("закреплено message_id:", mid)
