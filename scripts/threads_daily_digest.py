#!/usr/bin/env python3
"""Ежедневная подборка постов Threads для ручной публикации Виталием.

Читает пулы вопросов (Алина + Виталий) и лид-магниты (матрицы с link:),
собирает 7 постов (4 Алина + 3 Виталий), 2 из них — со ссылкой на канал
(1 на аккаунт), и шлёт их Виталию в Telegram (чат из VITALIY_CHAT_ID).

Посты выходят ЧИСТЫМИ (без ссылок), кроме 2 «ссылочных» — под ними Виталий
ставит ссылку первым комментарием. Ротация по кругу, состояние в
content/digest_state.json (идемпотентно: при сбое отправки состояние не пишется).

Секреты — ~/credentials/telegram.env (TELEGRAM_BOT_TOKEN, VITALIY_CHAT_ID).
Запуск: python3 scripts/threads_daily_digest.py [--dry-run]
"""

import os
import sys
import json
import glob
import re
import urllib.request
import urllib.parse
from datetime import datetime

BASE = "/home/hermes/alina-body"
ENV_PATH = os.path.expanduser("~/credentials/telegram.env")
ALINA_Q = os.path.join(BASE, "content/threads-questions.md")
VITALIY_Q = os.path.join(BASE, "content/vitaliy-questions.md")
ALINA_M = os.path.join(BASE, "content/threads-matrix/matrix-*.md")
VITALIY_M = os.path.join(BASE, "content/threads-matrix-vitaliy/matrix-*.md")
STATE = os.path.join(BASE, "content/digest_state.json")

# --- настройки ---
ALINA_POSTS = 4        # постов Алины в день
VITALIY_POSTS = 3      # постов Виталия в день
LINK_ALINA = 1         # ссылочных постов у Алины
LINK_VITALIY = 1       # ссылочных постов у Виталия

# Шаблоны ссылочных постов (тема берётся из лид-магнита, ссылка — 1-м комментарием).
ALINA_LINK_TEMPLATES = [
    "Разобрала «{title}» в коротком гайде — по шагам и без воды. Ссылку оставлю первым комментарием 👇",
    "Собрала «{title}» в одну шпаргалку: что делать и в каком порядке. Забирай в первом комментарии 👇",
    "По теме «{title}» — короткий разбор, который экономит кучу времени. Первым комментарием — ссылка 👇",
]
VITALIY_LINK_TEMPLATES = [
    "Разобрал «{title}» без воды — техника и программа. Ссылку кину первым комментарием 👇",
    "По «{title}» собрал короткую памятку: что, сколько, в каком порядке. Забирай в первом комментарии 👇",
    "«{title}» — коротко и по делу. Первым комментарием — ссылка на программу 👇",
]

# Магниты, под которыми обязателен дисклеймер про БАД (по ключевым словам в заголовке).
BAD_DISCLAIMER = "Перед применением БАД — консультация со специалистом."


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def tg_api(token, method, **p):
    url = "https://api.telegram.org/bot{}/{}".format(token, method)
    data = urllib.parse.urlencode(p).encode()
    req = urllib.request.Request(url, data=data)
    resp = json.loads(urllib.request.urlopen(req, timeout=70).read())
    if not resp.get("ok"):
        raise RuntimeError("Telegram API error {}: {}".format(method, resp))
    return resp


def parse_pool(path):
    """[(index, text), ...] из файла вида 'N. текст' (пустые строки — разделители)."""
    out = []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for m in re.finditer(r"^(\d+)\.\s+(.+)$", text, re.M):
        out.append((int(m.group(1)), m.group(2).strip()))
    return out


def parse_magnets(pattern):
    """[{title, link, is_bad}, ...] из матриц (заголовок '# Матрица: X', ссылка 'link: URL')."""
    out = []
    for f in sorted(glob.glob(pattern)):
        with open(f, encoding="utf-8") as fh:
            text = fh.read()
        t = re.search(r"^#\s*Матрица:\s*(.+)$", text, re.M)
        l = re.search(r"^link:\s*(\S+)$", text, re.M)
        if t and l:
            title = t.group(1).strip()
            out.append({
                "title": title,
                "link": l.group(1).strip(),
                "is_bad": any(w in title.lower() for w in ("бад", "спортпит")),
            })
    return out


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save_state(st):
    with open(STATE, "w") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def pick_questions(pool, n, state_key, state):
    idx = state.get(state_key, 0)
    picked = [pool[(idx + i) % len(pool)][1] for i in range(n)]
    state[state_key] = (idx + n) % len(pool)
    return picked


def pick_magnets(magnets, n, state_key, state):
    idx = state.get(state_key, 0)
    picked = [magnets[(idx + i) % len(magnets)] for i in range(n)]
    state[state_key] = (idx + n) % len(magnets)
    return picked


def link_post(magnet, templates, seed):
    tpl = templates[seed % len(templates)]
    text = tpl.format(title=magnet["title"])
    if magnet["is_bad"]:
        text += " " + BAD_DISCLAIMER
    return text


def plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n = n % 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def build_account_block(account_label, questions, link_posts):
    """Текст одного аккаунта для сообщения: вопросы + ссылочные посты с ссылкой."""
    total = len(questions) + len(link_posts)
    lines = ["📱 {} ({} {})".format(account_label, total, plural(total, "пост", "поста", "постов"))]
    n = 1
    for q in questions:
        lines.append("")
        lines.append("{}. {}".format(n, q))
        n += 1
    for lp in link_posts:
        lines.append("")
        lines.append("{}. {}".format(n, lp["text"]))
        lines.append("   🔗 ссылка в 1-й комментарий: {}".format(lp["magnet"]["link"]))
        n += 1
    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    alina_q = pick_pool_questions(ALINA_Q)
    vitaliy_q = pick_pool_questions(VITALIY_Q)
    alina_mags = parse_magnets(ALINA_M)
    vitaliy_mags = parse_magnets(VITALIY_M)

    state = load_state()

    # чистые вопросы (без ссылок)
    a_clean = alina_q[: ALINA_POSTS - LINK_ALINA]
    v_clean = vitaliy_q[: VITALIY_POSTS - LINK_VITALIY]

    # ссылочные посты
    a_mags = pick_magnets(alina_mags, LINK_ALINA, "alina_m", state)
    v_mags = pick_magnets(vitaliy_mags, LINK_VITALIY, "vitaliy_m", state)

    a_links = [{"text": link_post(m, ALINA_LINK_TEMPLATES, i), "magnet": m}
               for i, m in enumerate(a_mags)]
    v_links = [{"text": link_post(m, VITALIY_LINK_TEMPLATES, i), "magnet": m}
               for i, m in enumerate(v_mags)]

    # прокачиваем состояние вопросов (после успешной отправки — ниже)
    a_q_advance = ALINA_POSTS - LINK_ALINA
    v_q_advance = VITALIY_POSTS - LINK_VITALIY
    a_new_idx = (state.get("alina_q", 0) + a_q_advance) % len(alina_q)
    v_new_idx = (state.get("vitaliy_q", 0) + v_q_advance) % len(vitaliy_q)

    today = datetime.now().strftime("%d.%m.%Y")
    a_block = build_account_block("Алина", a_clean, a_links)
    v_block = build_account_block("Виталий", v_clean, v_links)

    header = ("📅 Посты на {} — постишь вручную\n"
              "{} постов (Алина {} + Виталий {}), ссылка в {} постах.\n"
              "Ссылку ставишь ПЕРВЫМ комментарием, в сам пост — не надо.".format(
                  today, ALINA_POSTS + VITALIY_POSTS, ALINA_POSTS, VITALIY_POSTS,
                  LINK_ALINA + LINK_VITALIY))

    if dry_run:
        print("=== DRY-RUN ===\n")
        print(header)
        print("\n" + a_block)
        print("\n" + v_block)
        return

    env = load_env()
    token = env["TELEGRAM_BOT_TOKEN"]
    chat = int(env.get("VITALIY_CHAT_ID", "1066756284"))

    tg_api(token, "sendMessage", chat_id=chat, text=header, disable_web_page_preview="true")
    tg_api(token, "sendMessage", chat_id=chat, text=a_block, disable_web_page_preview="true")
    tg_api(token, "sendMessage", chat_id=chat, text=v_block, disable_web_page_preview="true")

    # коммит состояния только после успешной отправки
    state["alina_q"] = a_new_idx
    state["vitaliy_q"] = v_new_idx
    save_state(state)
    print("✅ Подборка отправлена: {} Алина + {} Виталий, ссылок {}".format(
        ALINA_POSTS, VITALIY_POSTS, LINK_ALINA + LINK_VITALIY))


def pick_pool_questions(path):
    return [t for _i, t in parse_pool(path)]


if __name__ == "__main__":
    main()
