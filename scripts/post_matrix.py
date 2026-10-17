#!/usr/bin/env python3
"""Постинг матрицы прогрева: 1 ячейка/день в Threads + ссылка на лид-магнит первым комментарием.

Использование:
  python3 post_matrix.py --dry-run              # показать следующую ячейку без постинга
  python3 post_matrix.py                        # запостить следующую ячейку (текст + ссылка-реплай)
  python3 post_matrix.py --cell 4a              # запостить конкретную ячейку
  python3 post_matrix.py --link URL             # переопределить ссылку лид-магнита
  python3 post_matrix.py --matrix FILE          # конкретный файл матрицы (по умолчанию — последний)

Порядок ячеек: углы чередуются (1 → 3 → 6 → 5 → 2 → 4), внутри угла регистры a→i.
Итого 54 поста на один лид-магнит. Ссылка на лид-магнит — из фронтматтера (поле link)
или флагом --link; постится reply-комментарием под постом (текст поста заканчивается ↓).
"""
import os
import re
import sys
import json
import glob
import argparse
import urllib.request
import urllib.parse
import urllib.error

MATRIX_DIR = "/home/hermes/alina-body/content/threads-matrix"
STATE = os.path.join(MATRIX_DIR, "posted.json")

ANGLE_ORDER = [1, 3, 6, 5, 2, 4]
REGISTERS = "abcdefghi"


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
    return {"posted": {}, "matrix": None}


def save_state(state):
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", help="файл матрицы (по умолчанию — последний по дате)")
    ap.add_argument("--cell", help="конкретная ячейка, напр. 4a")
    ap.add_argument("--link", help="переопределить ссылку лид-магнита")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Файл матрицы
    if args.matrix:
        path = args.matrix
    else:
        files = sorted(glob.glob(os.path.join(MATRIX_DIR, "matrix-*.md")))
        if not files:
            print("Нет файлов матрицы в", MATRIX_DIR); sys.exit(1)
        path = files[-1]

    cells, link = parse_matrix(path)
    if not cells:
        print(f"В матрице {os.path.basename(path)} не нашёл ячеек постов."); sys.exit(1)
    link = args.link or link

    state = load_state()

    if args.cell:
        cell_id = args.cell
    else:
        cell_id = next_cell(cells, state["posted"])

    if cell_id is None:
        print(f"Матрица {os.path.basename(path)} исчерпана — все {len(cells)} ячеек запощены.")
        print("Переключи на следующий лид-магнит: новый файл matrix-*.md (или --matrix).")
        sys.exit(0)

    text = cells[cell_id]
    print(f"=== Ячейка {cell_id} ===")
    print(text[:400] + ("…" if len(text) > 400 else ""))
    print(f"\nЛид-магнит: {link}")

    if args.dry_run:
        print(f"\n[dry-run] Постинг НЕ выполнялся.")
        return

    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID", "29048751384731011")

    # 1. Контейнер текста
    resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=text)
    if err:
        print(f"  ❌ Создание контейнера: {err}"); sys.exit(1)
    cid = resp.get("id")
    # 2. Публикация
    resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
    if err:
        print(f"  ❌ Публикация: {err}"); sys.exit(1)
    tid = resp.get("id")
    print(f"  ✅ Пост: {tid}")
    # 3. Ссылка на лид-магнит первым комментарием
    if link:
        resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=link, reply_to_id=tid)
        if err:
            print(f"  ❌ Ссылка-реплай: {err}")
        else:
            rcid = resp.get("id")
            resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=rcid)
            if err:
                print(f"  ❌ Публикация ссылки: {err}")
            else:
                print(f"  ✅ Ссылка: {resp.get('id')}")

    # 4. Отметить
    state["posted"][cell_id] = {"thread_id": tid, "link": link, "matrix": os.path.basename(path)}
    save_state(state)
    print(f"Ячейка {cell_id} отмечена. Запощено: {len(state['posted'])}/{len(cells)}.")


if __name__ == "__main__":
    main()
