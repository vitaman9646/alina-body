#!/usr/bin/env python3
"""Постинг матрицы прогрева: 1 ячейка/день в Threads + ссылка на лид-магнит ОТЛОЖЕННЫМ реплаем (через 2 часа).

Несколько лид-магнитов (матриц) обрабатываются FIFO: сначала самая старая
недопощенная матрица, когда исчерпана — следующая. Прогресс ведётся отдельно
по каждой матрице в posted.json. Отложенные реплаи — в pending_replies.json.

Использование:
  .venv-tts/bin/python post_matrix.py --dry-run       # показать следующую ячейку
  .venv-tts/bin/python post_matrix.py                 # запостить ячейку (ссылку — в очередь)
  .venv-tts/bin/python post_matrix.py --reply-pending # выстрелить созревшие реплаи (cron */10)
  .venv-tts/bin/python post_matrix.py --cell 4a       # конкретная ячейка (по всем матрицам)
  .venv-tts/bin/python post_matrix.py --matrix FILE   # конкретный файл
  .venv-tts/bin/python post_matrix.py --link URL      # переопределить ссылку

Порядок ячеек: углы чередуются (1 → 3 → 6 → 5 → 2 → 4), внутри угла регистры a→i.
"""
import os
import re
import sys
import json
import glob
import argparse
import time
import urllib.request
import urllib.parse
import urllib.error

MATRIX_DIR = "/home/hermes/alina-body/content/threads-matrix"
STATE = os.path.join(MATRIX_DIR, "posted.json")
PENDING_REPLIES = os.path.join(MATRIX_DIR, "pending_replies.json")
REPLY_DELAY = 7200  # 2 часа — ссылка-реплай не сразу (руководство: не резать охваты)

ANGLE_ORDER = [1, 3, 6, 5, 2, 4, 7, 8, 9]
REGISTERS = "abcdefghi"

# Threads: текст поста максимум 500 символов (ошибка «Param text must be at most 500»).
MAX_TEXT = 500

# Перелив-оффер в отложенном реплае (по курсу SW.BAND: закреп = оффер, а не голая ссылка).
# Призыв чередуется детерминированно (по thread_id), чтобы реплаи не были дословно
# одинаковыми (триггер «повторяющиеся ответы»).
CTA_POOL = [
    "Забирай 👇",
    "Заходи — там всё разобрано 👇",
    "Подписывайся, там шпаргалки и планы 👇",
]


def build_reply(link, title, seed):
    """Хук (тема) + преимущество канала + ссылка + мягкий призыв. Без обещаний-CTA."""
    hook = (f"Подробнее про «{title}» — в моём Telegram: тренировки дома, "
            f"питание без диет и готовые шпаргалки.")
    cta = CTA_POOL[seed % len(CTA_POOL)]
    return f"{hook}\n{cta}\n{link}"


def matrix_title(path):
    """Заголовок матрицы из строки «# Матрица: …» (для персонального реплая)."""
    m = re.search(r"^#\s*Матрица:\s*(.+)$", open(path, encoding="utf-8").read(), re.M)
    return m.group(1).strip() if m else None


STOPWORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords.json")


def hard_stopwords():
    """Жёсткие стоп-слова Meta (суицид/секс/насилие/финансы/РПП/быстрые-обещания/ToS)."""
    try:
        return json.load(open(STOPWORDS_FILE)).get("hard", [])
    except (OSError, json.JSONDecodeError):
        return []


def hard_hits(text):
    """Слова из hard-списка, найденные в тексте поста."""
    low = text.lower()
    return [w for w in hard_stopwords() if w.lower() in low]


# Утренние пожелания (раскачка лайками, голос Алины «на ты», без обещаний/стоп-слов).
WISHES = [
    "Доброе утро 🌿 Начни день с себя: стакан воды, пять минут разминки, спокойный вдох. Дальше — легче. Лайк, если сегодня уже позаботилась о себе.",
    "Хорошего дня! Форма — это не про «идеально», а про «стабильно». Маленький шаг сегодня сильнее большого «начну с понедельника».",
    "Утро. Твоё тело — дом, в котором ты живёшь каждый день. Позаботься о нём мягко: подвигайся, поешь вовремя, выспись.",
    "Середина недели — хороший повод просто подвигаться: прогулка, растяжка, лёгкая тренировка дома. Что выберешь сегодня?",
    "Напоминаю: устала — отдохни, это тоже часть результата. Восстановление — не лень, а работа тела. Дай себе этот день.",
    "Лайк, если у тебя сегодня уже есть повод гордиться собой — даже самый маленький. Я в тебя верю 💛",
    "Доброе утро ☀️ Еда, сон и движение — это забота о себе, а не награда за «идеальный день». Начни с простого.",
]
WISH_STATE = os.path.join(MATRIX_DIR, "wishes_state.json")


def post_wish():
    """Постит утреннее пожелание (ротация по кругу, идемпотентно через wishes_state.json)."""
    idx = 0
    if os.path.exists(WISH_STATE):
        try:
            idx = json.load(open(WISH_STATE)).get("next", 0)
        except (json.JSONDecodeError, OSError):
            pass
    text = WISHES[idx % len(WISHES)]
    hits = hard_hits(text)
    if hits:
        print(f"  🚫 Пожелание содержит стоп-слова: {hits}")
        return
    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")
    resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=text)
    if err:
        print(f"  ❌ Пожелание: {err}")
        return
    cid = resp.get("id")
    time.sleep(8)
    resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
    if err:
        print(f"  ❌ Публикация пожелания: {err}")
        return
    json.dump({"next": (idx + 1) % len(WISHES), "last_posted": text[:60]},
              open(WISH_STATE, "w"), ensure_ascii=False, indent=2)
    print(f"  ✅ Пожелание [{idx % len(WISHES) + 1}/{len(WISHES)}]: {text[:60]}…")


LONG_FILE = "/home/hermes/alina-body/content/threads-long-posts.md"
LONG_STATE = os.path.join(MATRIX_DIR, "long_state.json")


def parse_long_posts():
    """[(title, hook, [part...]), ...] из threads-long-posts.md."""
    text = open(LONG_FILE, encoding="utf-8").read()
    blocks = re.split(r"^##\s+Лонг\s+\d+\s*—\s*(.+)$", text, flags=re.M)
    posts = []
    for i in range(1, len(blocks), 2):
        title = blocks[i].strip()
        body = blocks[i + 1]
        hook, parts = None, []
        for m in re.finditer(r"^###\s+(hook|\d+)\s*\n(.*?)(?=^###\s+|\Z)", body, flags=re.M | re.S):
            tag, content = m.group(1), m.group(2).strip()
            if tag == "hook":
                hook = content
            else:
                parts.append(content)
        if hook:
            posts.append((title, hook, parts))
    return posts


def post_long():
    """Постит длинный пост-пользу веткой (hook + реплаи) — удержание > лайки."""
    posts = parse_long_posts()
    if not posts:
        print(f"Нет длинных постов в {LONG_FILE}")
        return
    idx = 0
    if os.path.exists(LONG_STATE):
        try:
            idx = json.load(open(LONG_STATE)).get("next", 0)
        except (json.JSONDecodeError, OSError):
            pass
    title, hook, parts = posts[idx % len(posts)]
    hits = hard_hits(hook + " " + " ".join(parts))
    if hits:
        print(f"  🚫 Лонг содержит стоп-слова: {hits}")
        return
    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")

    resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=hook)
    if err:
        print(f"  ❌ Лонг hook: {err}")
        return
    time.sleep(8)
    resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=resp.get("id"))
    if err:
        print(f"  ❌ Публикация hook: {err}")
        return
    tid = resp.get("id")
    print(f"  ✅ Лонг hook: {tid}")

    for i, part in enumerate(parts, 1):
        resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT",
                                text=part, reply_to_id=tid)
        if err:
            print(f"  ❌ Часть {i}: {err}")
            continue
        time.sleep(8)
        resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=resp.get("id"))
        if err:
            print(f"  ❌ Публикация части {i}: {err}")
            continue
        print(f"  ✅ Часть {i}/{len(parts)}")

    json.dump({"next": (idx + 1) % len(posts), "last": title},
              open(LONG_STATE, "w"), ensure_ascii=False, indent=2)
    print(f"  Лонг [{idx % len(posts) + 1}/{len(posts)}]: {title}")


def truncate(text, limit=MAX_TEXT):
    """Режет пост до лимита Threads по границе предложения (не посреди слова)."""
    text = text.strip()
    if len(text) <= limit:
        return text
    head = text[:limit]
    ends = [m.end() for m in re.finditer(r'[.!?…]["»)]*\s+', head)]
    if ends and ends[-1] > limit * 0.5:
        return head[:ends[-1]].rstrip()
    sp = head.rfind(" ")
    if sp > limit * 0.6:
        return head[:sp].rstrip()
    return head.rstrip() + "…"


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def threads_api(token, method, **params):
    url = f"https://graph.threads.net/v1.0/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read().decode() or "{}").get("error", {}).get("message", f"HTTP {e.code}")
    if "error" in resp:
        return None, resp["error"].get("message", "unknown")
    return resp, None


def parse_matrix(path):
    """Возвращает (cells, link): cells = {cell_id: текст поста}, link = ссылка лид-магнита."""
    text = open(path, encoding="utf-8").read()
    link = None
    m = re.search(r"^link:\s*(\S+)", text, re.M)
    if m:
        link = m.group(1).strip()
    cells = {}
    parts = re.split(r"^###\s+(\d[a-i])\s+—.*$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        cell_id = parts[i]
        body = parts[i + 1].split("**Запасные хуки:**")[0]
        body = re.sub(r"^\*\*(Читатель|Цифра-доказательство|Кривая дорога):\*\*.*$", "", body, flags=re.M)
        body = body.replace("```", "")
        body = body.strip()
        if body:
            cells[cell_id] = body
    return cells, link


def next_cell(cells, posted):
    """Следующая незапощенная ячейка в порядке чередования углов."""
    for i in range(len(ANGLE_ORDER) * len(REGISTERS)):
        angle = ANGLE_ORDER[i % len(ANGLE_ORDER)]
        reg = REGISTERS[i // len(ANGLE_ORDER)]
        cid = f"{angle}{reg}"
        if cid in cells and cid not in posted:
            return cid
    return None


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {}


def save_state(state):
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)


def load_pending():
    if os.path.exists(PENDING_REPLIES):
        try:
            return json.load(open(PENDING_REPLIES))
        except (json.JSONDecodeError, OSError):
            pass
    return {"pending": []}


def save_pending(data):
    json.dump(data, open(PENDING_REPLIES, "w"), ensure_ascii=False, indent=2)


def enqueue_reply(thread_id, link, title=None):
    """Ставит ссылку-реплай в очередь (постится через REPLY_DELAY секунд).

    Хранит готовый текст оффера (reply_text), а не голую ссылку.
    """
    seed = sum(ord(c) for c in str(thread_id))
    reply_text = build_reply(link, title, seed) if title else link
    data = load_pending()
    data.setdefault("pending", []).append({
        "thread_id": thread_id,
        "link": link,
        "reply_text": reply_text,
        "due_ts": int(time.time()) + REPLY_DELAY,
    })
    save_pending(data)


def reply_pending():
    """Постит отложенные ссылки-реплаи, которым исполнилось 2 часа.

    Пауза между созданием контейнера и публикацией + повторы: Meta иногда
    не видит свежий reply-контейнер сразу («The requested resource does not
    exist»), и без повтора ссылка просто теряется.
    """
    data = load_pending()
    if not data.get("pending"):
        return
    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")
    now = time.time()
    remaining = []
    fired = 0
    for item in data["pending"]:
        if item["due_ts"] > now:
            remaining.append(item)
            continue
        published = False
        reply_text = item.get("reply_text") or item["link"]
        for attempt in range(1, 5):  # до 4 попыток за прогон
            resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT",
                                    text=reply_text, reply_to_id=item["thread_id"])
            if err:
                print(f"  ❌ Отложенный реплай {item['thread_id']} (попытка {attempt}): {err}")
                time.sleep(10)
                continue
            rcid = resp.get("id")
            # дать контейнеру «дозреть» перед публикацией
            time.sleep(8)
            resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=rcid)
            if err:
                print(f"  ❌ Публикация реплая {item['thread_id']} (попытка {attempt}): {err}")
                time.sleep(10)
                continue
            fired += 1
            published = True
            print(f"  ✅ Отложенный оффер → {item['link']} (reply {resp.get('id')})")
            break
        if not published:
            remaining.append(item)  # не вышло за 4 попытки — в следующий прогон
    data["pending"] = remaining
    save_pending(data)
    if fired:
        print(f"Выстрелено ссылок: {fired}, осталось в очереди: {len(remaining)}")


def posted_of(state, name):
    return state.get(name, {}).get("posted", {})


def matrix_sort_key(f):
    """Сортировка матриц хронологически: по дате в имени, затем по mtime."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(f))
    return (m.group(1) if m else "9999-99-99", os.path.getmtime(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", help="файл матрицы (по умолчанию — FIFO: самая старая недопощенная)")
    ap.add_argument("--cell", help="конкретная ячейка, напр. 4a (ищется по всем матрицам)")
    ap.add_argument("--link", help="переопределить ссылку лид-магнита")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reply-pending", action="store_true", help="постить отложенные ссылки-реплаи (через 2 часа)")
    ap.add_argument("--wish", action="store_true", help="постить утреннее пожелание (раскачка лайками)")
    ap.add_argument("--long", action="store_true", help="постить длинный пост-пользу веткой (удержание)")
    args = ap.parse_args()

    if args.reply_pending:
        reply_pending()
        return
    if args.wish:
        post_wish()
        return
    if args.long:
        post_long()
        return

    state = load_state()
    files = sorted(glob.glob(os.path.join(MATRIX_DIR, "matrix-*.md")), key=matrix_sort_key)

    # --- выбор матрицы и ячейки ---
    path = cells = link = cell_id = None

    if args.matrix:
        path = args.matrix
        cells, link = parse_matrix(path)
        name = os.path.basename(path)
        if args.cell:
            cell_id = args.cell if args.cell in cells else None
        else:
            cell_id = next_cell(cells, posted_of(state, name))
    elif args.cell:
        # ищем ячейку по всем матрицам (сначала старая)
        for f in files:
            c, _ = parse_matrix(f)
            if args.cell in c:
                path = f; cells = c; link = parse_matrix(f)[1]; cell_id = args.cell
                break
        if not path:
            print(f"Ячейка {args.cell} не найдена ни в одной матрице."); sys.exit(1)
    else:
        # Ротация по лид-магнитам: берём матрицу с наименьшим числом запощенных
        # ячеек (при равенстве — самую старую). Так посты чередуют темы, а не
        # долбят один лид-магнит (54 ячейки) подряд.
        best_key, best_f, best_c, best_l = None, None, None, None
        for f in files:
            c, l = parse_matrix(f)
            name = os.path.basename(f)
            done = len(posted_of(state, name))
            if not c or done >= len(c):
                continue  # пустая или исчерпанная матрица
            key = (done, matrix_sort_key(f))
            if best_key is None or key < best_key:
                best_key, best_f, best_c, best_l = key, f, c, l
        if best_f is None:
            print("Все матрицы исчерпаны — нечего постить.")
            sys.exit(0)
        path, cells, link = best_f, best_c, best_l
        name = os.path.basename(path)
        cell_id = next_cell(cells, posted_of(state, name))

    if not path:
        print("Все матрицы исчерпаны — нечего постить.")
        sys.exit(0)

    if not cells:
        print(f"В матрице {os.path.basename(path)} не нашёл ячеек постов."); sys.exit(1)
    link = args.link or link
    name = os.path.basename(path)

    if cell_id is None:
        print(f"Матрица {name} исчерпана — все {len(cells)} ячеек запощены.")
        sys.exit(0)

    text = truncate(cells[cell_id])
    hits = hard_hits(text)
    if hits:
        print(f"  🚫 СТОП-СЛОВА в ячейке {cell_id}: {', '.join(hits)}")
        if not args.dry_run:
            state.setdefault(name, {}).setdefault("posted", {})[cell_id] = \
                {"thread_id": None, "blocked": True, "link": link, "hits": hits}
            save_state(state)
            print(f"  Ячейка {cell_id} помечена заблокированной — переформулируй вручную, потом удали запись из posted.json.")
            sys.exit(0)
    print(f"=== {name} · ячейка {cell_id} ===")
    print(text[:400] + ("…" if len(text) > 400 else ""))
    print(f"\nЛид-магнит: {link}")

    if args.dry_run:
        print("\n[dry-run] Постинг НЕ выполнялся.")
        return

    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")

    resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=text)
    if err:
        print(f"  ❌ Создание контейнера: {err}"); sys.exit(1)
    cid = resp.get("id")
    resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
    if err:
        print(f"  ❌ Публикация: {err}"); sys.exit(1)
    tid = resp.get("id")
    print(f"  ✅ Пост: {tid}")

    if link:
        title = matrix_title(path)
        enqueue_reply(tid, link, title)
        print(f"  ⏳ Оффер-реплай отложен на 2 часа: {build_reply(link, title, sum(ord(c) for c in str(tid))) if title else link}")

    state.setdefault(name, {}).setdefault("posted", {})[cell_id] = {"thread_id": tid, "link": link}
    save_state(state)
    print(f"Ячейка {cell_id} отмечена. Запощено в этой матрице: {len(state[name]['posted'])}/{len(cells)}.")


if __name__ == "__main__":
    main()
