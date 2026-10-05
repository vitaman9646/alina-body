#!/usr/bin/env python3
"""Пересылает Виталию сообщения, которые люди шлют боту (проверка техники).

Подписчицы закрытого канала шлют фото/видео упражнений в личку боту @writer_alina_bot.
Демон ловит их через long-polling и пересылает Виталию (тренеру) в Telegram.

Токен и id Виталия читает из ~/credentials/telegram.env, в вывод не попадают.
Офсет хранится в файле — после рестарта старые сообщения не дублируются.
"""

import os
import json
import time
import urllib.request
import urllib.parse

ENV_PATH = os.path.expanduser("~/credentials/telegram.env")
OFFSET_FILE = "/home/hermes/alina-body/content/consult_offset.txt"


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def api(token, method, **p):
    url = "https://api.telegram.org/bot{}/{}".format(token, method)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(p).encode())
    return json.loads(urllib.request.urlopen(req, timeout=70).read())


def load_offset():
    try:
        return int(open(OFFSET_FILE).read().strip())
    except Exception:
        return 0


def save_offset(off):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(off))


def main():
    env = load_env()
    token = env["TELEGRAM_BOT_TOKEN"]
    vitaliy = env.get("VITALIY_CHAT_ID", "1066756284")

    offset = load_offset()
    print("consult_bot: старт, offset={}".format(offset), flush=True)

    while True:
        try:
            r = api(token, "getUpdates", offset=offset, timeout=60)
        except Exception as e:
            print("getUpdates ошибка: {}".format(e), flush=True)
            time.sleep(5)
            continue

        if not r.get("ok"):
            print("getUpdates не ok: {}".format(r), flush=True)
            time.sleep(5)
            continue

        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message")
            if not msg:
                continue
            sender = msg.get("from", {})
            if sender.get("is_bot"):
                continue
            chat = msg.get("chat", {})
            if chat.get("type") == "channel":
                continue

            name = sender.get("first_name") or "кто-то"
            uname = sender.get("username")
            who = name + (" (@{})".format(uname) if uname else "")
            sender_id = chat.get("id")

            is_media = any(
                msg.get(k)
                for k in ("photo", "video", "document", "voice", "animation", "video_note")
            )
            header = "👤 {} (id {})".format(who, sender_id)
            try:
                if is_media:
                    cap = header
                    if msg.get("caption"):
                        cap += "\n💬 " + msg["caption"]
                    api(token, "copyMessage", chat_id=vitaliy,
                        from_chat_id=sender_id, message_id=msg["message_id"], caption=cap)
                else:
                    text = header
                    if msg.get("text"):
                        text += "\n\n" + msg["text"]
                    api(token, "sendMessage", chat_id=vitaliy, text=text)
                print("переслано от {}".format(who), flush=True)
            except Exception as e:
                print("пересылка не удалась: {}".format(e), flush=True)

        save_offset(offset)


if __name__ == "__main__":
    main()
