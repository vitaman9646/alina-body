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

ANGLE_ORDER = [1, 3, 6, 5, 2, 4]
REGISTERS = "abcdefghi"

# Threads: текст поста максимум 500 символов (ошибка «Param text must be at most 500»).
MAX_TEXT = 500


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


def enqueue_reply(thread_id, link):
    """Ставит ссылку-реплай в очередь (постится через REPLY_DELAY секунд)."""
    data = load_pending()
    data.setdefault("pending", []).append({
        "thread_id": thread_id,
        "link": link,
        "due_ts": int(time.time()) + REPLY_DELAY,
    })
    save_pending(data)


def reply_pending():
    """Постит отложенные ссылки-реплаи, которым исполнилось 2 часа."""
    data = load_pending()
    if not data.get("pending"):
        return
    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")
    now = time.time()
    remaining = []
    for item in data["pending"]:
        if item["due_ts"] > now:
            remaining.append(item)
            continue
        resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT",
                                text=item["link"], reply_to_id=item["thread_id"])
        if err:
            print(f"  ❌ Отложенный реплай {item['thread_id']}: {err}")
            remaining.append(item)  # повторим на следующем прогоне
            continue
        rcid = resp.get("id")
        resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=rcid)
        if err:
            print(f"  ❌ Публикация отложенного реплая {item['thread_id']}: {err}")
            remaining.append(item)
            continue
        print(f"  ✅ Отложенная ссылка → {item['link']} (reply {resp.get('id')})")
    data["pending"] = remaining
    save_pending(data)
    if remaining:
        print(f"Осталось в очереди: {len(remaining)}")


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
    args = ap.parse_args()

    if args.reply_pending:
        reply_pending()
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
        # FIFO: самая старая матрица с незапощенными ячейками
        for f in files:
            c, l = parse_matrix(f)
            name = os.path.basename(f)
            cid = next_cell(c, posted_of(state, name))
            if cid:
                path = f; cells = c; link = l; cell_id = cid
                break

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
        enqueue_reply(tid, link)
        print(f"  ⏳ Ссылка-реплай отложена на 2 часа: {link}")

    state.setdefault(name, {}).setdefault("posted", {})[cell_id] = {"thread_id": tid, "link": link}
    save_state(state)
    print(f"Ячейка {cell_id} отмечена. Запощено в этой матрице: {len(state[name]['posted'])}/{len(cells)}.")


if __name__ == "__main__":
    main()
