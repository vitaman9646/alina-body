#!/usr/bin/env python3
"""Проверка текстов постов Threads на стоп-слова (из scripts/stopwords.json).

Сканирует все матрицы (content/threads-matrix/matrix-*.md) и пул вопросов/тексты,
выводит ячейки с совпадениями по HARD (нарушение — переформулировать) и SOFT
(контекстозависимо — проверить вручную).

Запуск:
  python3 scripts/check_stopwords.py
  python3 scripts/check_stopwords.py --hard   # только жёсткие нарушения
  python3 scripts/check_stopwords.py --fix    # интерактивно не чинит, только покажет
"""
import os, re, sys, json, glob, argparse

MATRIX_DIR = "/home/hermes/alina-body/content/threads-matrix"
SW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords.json")


def load_stopwords():
    d = json.load(open(SW))
    return d["hard"], d["soft"]


def parse_matrix(path):
    text = open(path, encoding="utf-8").read()
    cells = {}
    parts = re.split(r"^###\s+(\d[a-i])\s+—.*$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        cid = parts[i]
        body = parts[i + 1].split("**Запасные хуки:**")[0]
        body = re.sub(r"^\*\*(Читатель|Цифра-доказательство|Кривая дорога):\*\*.*$", "", body, flags=re.M)
        body = body.replace("```", "").strip()
        if body:
            cells[cid] = body
    return cells


def find_all(text, words):
    """Возвращает {слово: [контексты]} для слов, найденных в тексте."""
    low = text.lower()
    found = {}
    for w in words:
        idx = 0
        while True:
            i = low.find(w.lower(), idx)
            if i == -1:
                break
            ctx = text[max(0, i - 30):i + len(w) + 30].replace("\n", " ")
            found.setdefault(w, []).append(ctx)
            idx = i + len(w)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hard", action="store_true", help="только жёсткие нарушения")
    a = ap.parse_args()
    hard, soft = load_stopwords()

    files = sorted(glob.glob(os.path.join(MATRIX_DIR, "matrix-*.md")))
    total_hard = total_soft = 0
    for f in files:
        name = os.path.basename(f)
        cells = parse_matrix(f)
        for cid, body in cells.items():
            h = find_all(body, hard)
            s = {} if a.hard else find_all(body, soft)
            if h or s:
                print(f"\n=== {name} · ячейка {cid} ===")
                if h:
                    print("  🔴 HARD:")
                    for w, ctxs in h.items():
                        total_hard += 1
                        print(f"    «{w}» → …{ctxs[0]}…")
                if s:
                    print("  🟡 SOFT (проверить):")
                    for w, ctxs in s.items():
                        total_soft += 1
                        print(f"    «{w}» → …{ctxs[0]}…")
    print(f"\nИтого: HARD-нарушений {total_hard}, SOFT-совпадений {total_soft}")


if __name__ == "__main__":
    main()
