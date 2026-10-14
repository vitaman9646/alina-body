#!/usr/bin/env python3
"""Ежедневный «Совет дня» в Telegram-канал.

Читает content/telegram_tips.txt (по совету на строку), постит следующий по очереди
(циклически). Идемпотентно: индекс последнего отправленного в content/telegram_tip_idx.txt.

Использование: python3 post_tip.py [--dry-run] [--next N]
"""
import os
import sys
import json
import urllib.request
import urllib.parse

TIPS = "/home/hermes/alina-body/content/telegram_tips.txt"
IDX = "/home/hermes/alina-body/content/telegram_tip_idx.txt"
ENV = os.path.expanduser("~/credentials/telegram.env")


def load_env():
    e = {}
    for line in open(ENV):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e


def main():
    dry = "--dry-run" in sys.argv
    tips = [l.strip() for l in open(TIPS, encoding="utf-8") if l.strip()]
    idx = 0
    if os.path.exists(IDX):
        idx = int(open(IDX).read().strip() or 0)
    if "--next" in sys.argv:
        idx = int(sys.argv[sys.argv.index("--next") + 1])
    tip = tips[idx % len(tips)]
    text = "💡 Совет дня\n\n" + tip

    if dry:
        print(f"[dry-run] ({idx}) {text}")
        return
    env = load_env()
    url = "https://api.telegram.org/bot{}/sendMessage".format(env["TELEGRAM_BOT_TOKEN"])
    data = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHANNEL_ID"], "text": text}).encode()
    resp = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data)).read())
    if resp.get("ok"):
        open(IDX, "w").write(str((idx + 1) % len(tips)))
        print("✅ совет отправлен (индекс {})".format(idx))
    else:
        print("❌", resp)


if __name__ == "__main__":
    main()
