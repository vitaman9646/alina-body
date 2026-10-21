#!/usr/bin/env python3
"""Публикует лид-магниты «Тазовое дно» в Telegram-канал + закрепляет лонгриды.

Флоу на каждый магнит: sendPhoto (карточка-обложка) → sendMessage (лонгрид, чанками)
→ pin первого чанка лонгрида.
"""
import os, json, re, html, urllib.request, urllib.parse

def load_env(path):
    e = {}
    for line in open(os.path.expanduser(path)):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip()
    return e

def tg(method, token, payload):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def chunk(text, limit=3900):
    """Режет текст по границам абзацев до limit символов."""
    paras = text.split("\n")
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 1 > limit and cur:
            chunks.append(cur.strip())
            cur = p
        else:
            cur = cur + "\n" + p if cur else p
    if cur.strip():
        chunks.append(cur.strip())
    return chunks

# --- карточки ---
urls = json.load(open("/tmp/tazodno_urls.json"))
TITLES = [
    "Тазовое дно: два треугольника",
    "Перекаты таза",
    "Напряжение ↔ расслабление",
    "Дыхание и тазовое дно",
]

# --- лонгриды из md ---
md = open("/home/hermes/alina-body/content/lead-magnet-tazovoe-dno.md", encoding="utf-8").read()
blocks = re.split(r"\n## Магнит \d", md)[1:]  # 4 блока

def longread_of(block):
    body = block.split("### Лонгрид", 1)[1]
    body = re.split(r"\n---\s*\n|\n## К врачу", body)[0]
    out = []
    for line in body.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("####"):
            out.append("<b>" + html.escape(s[4:].strip()) + "</b>")
        elif s.startswith("###"):
            continue
        else:
            out.append(html.escape(s))
    return "\n".join(out)

env = load_env("~/credentials/telegram.env")
token = env["TELEGRAM_BOT_TOKEN"]
channel = env["TELEGRAM_CHANNEL_ID"]

for i, (title, block) in enumerate(zip(TITLES, blocks)):
    card_url = urls[i]["url"]
    # 1) карточка-обложка
    r = tg("sendPhoto", token, {
        "chat_id": channel, "photo": card_url, "caption": title,
        "parse_mode": "HTML"})
    print(f"[{i+1}] фото: {r.get('ok')} msg={r.get('result',{}).get('message_id')}")

    # 2) лонгрид
    lr = longread_of(block)
    full = f"<b>{html.escape(title)}</b>\n\n{lr}\n\n📋 <a href=\"{card_url}\">Карточка-шпаргалка</a>\nБольше практик — t.me/alinabodyfree"
    parts = chunk(full)
    first_id = None
    for j, part in enumerate(parts):
        r = tg("sendMessage", token, {"chat_id": channel, "text": part, "parse_mode": "HTML",
                                      "disable_web_page_preview": "true"})
        mid = r.get("result", {}).get("message_id")
        if j == 0:
            first_id = mid
        print(f"    лонгрид ч.{j+1}: {r.get('ok')} msg={mid} ({len(part)} симв)")

    # 3) закреп
    r = tg("pinChatMessage", token, {"chat_id": channel, "message_id": first_id})
    print(f"    закреп: {r.get('ok')}")

print("готово магнитов:", len(TITLES))
