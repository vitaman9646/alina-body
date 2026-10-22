#!/usr/bin/env python3
"""Пост программы в канал (без закрепа) + добавление ссылки в хаб «Программы тренировок».

Хаб (оглавление всех программ) хранится в content/hub-programs.json; его текст
пересобирается и правится через editMessageText при каждом новом выпуске.

Использование:
  python3 post_program.py --title "..." --urls /tmp/x_urls.json --lonrid path.txt \
      --desc "короткое описание для хаба" [--channel <id>]
"""
import os, json, html, argparse, urllib.request, urllib.parse

ROOT = "/home/hermes/alina-body"
HUB_FILE = os.path.join(ROOT, "content", "hub-programs.json")
CHANNEL_DEFAULT = "-1004361118998"  # «Подслушано в качалке»


def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e


def api(token, method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def build_hub_text(programs):
    lines = ["🏋️ <b>Программы тренировок</b>", "",
             "Здесь собираются все бесплатные программы канала — готовый банк планов:", ""]
    for i, p in enumerate(programs, 1):
        lines.append(f'{i}. <a href="{p["url"]}">{html.escape(p["title"])}</a> — {html.escape(p["desc"])}')
    lines += ["", "Новые недели добавляются сюда 👇", "Подпишись, чтобы не пропустить"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--urls", required=True)
    ap.add_argument("--lonrid", required=True)
    ap.add_argument("--desc", required=True, help="короткое описание для хаба")
    ap.add_argument("--channel", default=CHANNEL_DEFAULT)
    a = ap.parse_args()

    token = load_env()["TELEGRAM_BOT_TOKEN"]
    urls = json.load(open(a.urls))
    lonrid = open(a.lonrid).read().strip()

    # 1. пост программы (карточки-ссылки + лонгрид)
    lines = [f"<b>{a.title}</b>", "", "<b>Карточки</b> (нажми на название):"]
    for it in urls:
        lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
    lines += ["", "──────────", "", lonrid]
    r = api(token, "sendMessage", chat_id=a.channel, text="\n".join(lines),
            parse_mode="HTML", disable_web_page_preview="true")
    pid = r["result"]["message_id"]

    # 2. обновляем хаб
    state = json.load(open(HUB_FILE)) if os.path.exists(HUB_FILE) else {"hub_id": None, "programs": []}
    state["programs"].append({"title": a.title, "url": f"https://t.me/podslishanovkachke/{pid}", "desc": a.desc})
    hub_text = build_hub_text(state["programs"])

    if state.get("hub_id"):
        api(token, "editMessageText", chat_id=a.channel, message_id=state["hub_id"],
            text=hub_text, parse_mode="HTML", disable_web_page_preview="true")
        print(f"хаб {state['hub_id']} обновлён")
    else:
        print("⚠️ hub_id не задан — хаб не обновлён (пост программы всё равно опубликован)")

    json.dump(state, open(HUB_FILE, "w"), ensure_ascii=False, indent=2)
    print(f"пост программы message_id: {pid}")


if __name__ == "__main__":
    main()
