#!/usr/bin/env python3
"""Постинг матрицы прогрева: 1 ячейка/день в Threads + ссылка на лид-магнит первым комментарием.

Несколько лид-магнитов (матриц) обрабатываются FIFO: сначала самая старая
недопощенная матрица, когда исчерпана — следующая. Прогресс ведётся отдельно
по каждой матрице в posted.json.

Использование:
  .venv-tts/bin/python post_matrix.py --dry-run       # показать следующую ячейку
  .venv-tts/bin/python post_matrix.py                 # запостить следующую ячейку
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
    return {}


def save_state(state):
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)


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
    args = ap.parse_args()

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

    text = cells[cell_id]
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

    state.setdefault(name, {}).setdefault("posted", {})[cell_id] = {"thread_id": tid, "link": link}
    save_state(state)
    print(f"Ячейка {cell_id} отмечена. Запощено в этой матрице: {len(state[name]['posted'])}/{len(cells)}.")


if __name__ == "__main__":
    main()
