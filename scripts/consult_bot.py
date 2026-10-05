#!/usr/bin/env python3
"""Мост между подписчицами и тренером (Виталием) через бота @writer_alina_bot.

В одну сторону: подписчица шлёт фото/видео боту → бот пересылает Виталию с подписью отправителя.
В обратную: Виталий отвечает (Reply) на пересланное сообщение → бот шлёт ответ подписчице.

Токен и id Виталия читает из ~/credentials/telegram.env, в вывод не попадают.
Офсет — в consult_offset.txt; соответствие «сообщение Виталию → id подписчицы» — в consult_mapping.json.
"""

import os
import json
import time
import urllib.request
import urllib.parse

ENV_PATH = os.path.expanduser("~/credentials/telegram.env")
OFFSET_FILE = "/home/hermes/alina-body/content/consult_offset.txt"
MAPPING_FILE = "/home/hermes/alina-body/content/consult_mapping.json"
MEDIA_KEYS = ("photo", "video", "document", "voice", "animation", "video_note", "sticker")


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


def load_mapping():
    try:
        return json.load(open(MAPPING_FILE))
    except Exception:
        return {}


def save_mapping(m):
    # лёгкая обрезка: держим последние ~1000 соответствий
    if len(m) > 2000:
        keys = sorted(m, key=int)[-1000:]
        m = {k: m[k] for k in keys}
    with open(MAPPING_FILE, "w") as f:
        json.dump(m, f)


def is_media(msg):
    return any(msg.get(k) for k in MEDIA_KEYS)


def main():
    env = load_env()
    token = env["TELEGRAM_BOT_TOKEN"]
    vitaliy = int(env.get("VITALIY_CHAT_ID", "1066756284"))

    offset = load_offset()
    mapping = load_mapping()
    print("consult_bot: старт, offset={}, mapping={}".format(offset, len(mapping)), flush=True)

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
            chat_id = chat.get("id")

            if chat_id == vitaliy:
                # --- сообщение от тренера: переслать ответ подписчице ---
                reply_to = msg.get("reply_to_message")
                if not reply_to:
                    api(token, "sendMessage", chat_id=vitaliy,
                        text="Чтобы ответить подписчице, ответь (Reply) на её пересланное сообщение.")
                    continue
                sub_id = mapping.get(str(reply_to.get("message_id")))
                if not sub_id:
                    api(token, "sendMessage", chat_id=vitaliy,
                        text="Не знаю, кому это отправить. Ответь именно на пересланное сообщение подписчицы.")
                    continue
                try:
                    if is_media(msg):
                        api(token, "copyMessage", chat_id=sub_id, from_chat_id=vitaliy,
                            message_id=msg["message_id"], caption=msg.get("caption") or "")
                    else:
                        api(token, "sendMessage", chat_id=sub_id, text=msg.get("text") or "")
                    print("ответ отправлен подписчице {}".format(sub_id), flush=True)
                except Exception as e:
                    print("ответ не ушёл: {}".format(e), flush=True)
                continue

            if chat.get("type") == "channel":
                continue

            # --- сообщение от подписчицы: переслать Виталию ---
            name = sender.get("first_name") or "кто-то"
            uname = sender.get("username")
            who = name + (" (@{})".format(uname) if uname else "")
            header = "👤 {} (id {})".format(who, chat_id)
            try:
                if is_media(msg):
                    cap = header
                    if msg.get("caption"):
                        cap += "\n💬 " + msg["caption"]
                    res = api(token, "copyMessage", chat_id=vitaliy, from_chat_id=chat_id,
                              message_id=msg["message_id"], caption=cap)
                else:
                    text = header
                    if msg.get("text"):
                        text += "\n\n" + msg["text"]
                    res = api(token, "sendMessage", chat_id=vitaliy, text=text)
                vid = res["result"]["message_id"]
                mapping[str(vid)] = str(chat_id)
                save_mapping(mapping)
                print("переслано от {} -> Виталию (id {})".format(who, vid), flush=True)
            except Exception as e:
                print("пересылка не удалась: {}".format(e), flush=True)

        save_offset(offset)


if __name__ == "__main__":
    main()
