#!/usr/bin/env python3
"""Шлёт сообщение с карточками лид-магнита в канал + закрепляет.

Аргументы: --json /tmp/x_urls.json --title "Заголовок" --subtitle "подзаголовок"
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
ap.add_argument("--json", required=True)
ap.add_argument("--title", required=True)
ap.add_argument("--subtitle", default="")
ap.add_argument("--footer", default="")
args = ap.parse_args()

urls = json.load(open(args.json))
lines = [f"{args.title}"]
if args.subtitle:
    lines.append(args.subtitle)
lines.append("")
for it in urls:
    lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
lines.append("")
lines.append("Нажимай на название — откроется карточка.")
if args.footer:
    lines.append(args.footer)
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
