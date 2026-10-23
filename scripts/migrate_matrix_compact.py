#!/usr/bin/env python3
"""Миграция матриц 81→компакт: 5 постов (Алина) / 2 поста (Виталий).

Для каждого matrix-*.md извлекает N ячеек (старые cell_id по углам), перезаписывает
файл в компактном формате (ячейки 1..N). posted.json пересопоставляется:
новые ячейки в «posted», старые (включая незамапленные, напр. 1a) в «legacy_posted»
— чтобы reply_comments.py сохранял thread_id→link-маппинг старых постов.

Запуск: python3 migrate_matrix_compact.py [--dry-run]
"""
import os, re, json, glob, sys

ROOT = "/home/hermes/alina-body"

# Компактный набор: (старый cell_id, подпись угла) → новый номер 1..N.
ALINA_PICKS = [
    ("2a", "По шагам"),
    ("3a", "Страхи-возражения"),
    ("4a", "Миф"),
    ("6a", "Вместо дорогого"),
    ("9a", "Непопулярное мнение"),
]
VITALIY_PICKS = [
    ("2a", "По шагам"),
    ("4a", "Миф"),
]


def parse_old(path):
    text = open(path, encoding="utf-8").read()
    link = source = title = None
    m = re.search(r"^link:\s*(\S+)", text, re.M)
    if m:
        link = m.group(1).strip()
    m = re.search(r"^source:\s*(.+)$", text, re.M)
    if m:
        source = m.group(1).strip()
    m = re.search(r"^#\s*Матрица:\s*(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()
    cells = {}
    parts = re.split(r"^###\s+(\d[a-i])\s+—.*$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        cid = parts[i]
        body = parts[i + 1].split("**Запасные хуки:**")[0]
        body = re.sub(r"^\*\*(Читатель|Цифра-доказательство|Кривая дорога):\*\*.*$", "", body, flags=re.M)
        body = body.replace("```", "").strip()
        if body:
            cells[cid] = body
    return link, source, title, cells


def write_compact(path, link, source, title, cells, picks):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    date = m.group(1) if m else "2026-10-23"
    n = len(picks)
    out = [
        "---",
        "type: threads-matrix",
        "status: draft",
        f"date: {date}",
        f"source: {source or ''}",
        f"cells: {n}",
        "published: []",
        f"link: {link or ''}",
        "---",
        "",
        f"# Матрица: {title}",
        "",
    ]
    for j, (old, label) in enumerate(picks, 1):
        body = cells.get(old)
        if not body:
            print(f"  ⚠️ {os.path.basename(path)}: нет ячейки {old}", file=sys.stderr)
            continue
        out.append(f"### {j} — {label}")
        out.append(body)
        out.append("")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    return n


def remap_state(state, name, old_posted, picks):
    new_posted = {}
    for j, (old, _label) in enumerate(picks, 1):
        if old in old_posted:
            new_posted[str(j)] = old_posted[old]
    state[name] = {"posted": new_posted, "legacy_posted": old_posted}
    return new_posted


def main():
    dry = "--dry-run" in sys.argv
    for matrix_dir, picks in [("content/threads-matrix", ALINA_PICKS),
                              ("content/threads-matrix-vitaliy", VITALIY_PICKS)]:
        d = os.path.join(ROOT, matrix_dir)
        state_path = os.path.join(d, "posted.json")
        state = json.load(open(state_path)) if os.path.exists(state_path) else {}
        files = sorted(glob.glob(os.path.join(d, "matrix-*.md")))
        print(f"\n== {matrix_dir} ({len(files)} матриц) → {len(picks)} постов ==")
        for f in files:
            name = os.path.basename(f)
            link, source, title, cells = parse_old(f)
            if not cells:
                print(f"  пропуск {name}: нет ячеек 81-формата")
                continue
            old_posted = state.get(name, {}).get("posted", {})
            if dry:
                new_posted = {}
                for j, (old, _l) in enumerate(picks, 1):
                    if old in old_posted:
                        new_posted[str(j)] = old_posted[old]
                print(f"  [dry] {name}: {len(cells)} ячеек → {len(picks)} постов "
                      f"({len(new_posted)} уже запощено)")
                continue
            write_compact(f, link, source, title, cells, picks)
            new_posted = remap_state(state, name, old_posted, picks)
            done = sum(1 for v in new_posted.values() if v.get("thread_id"))
            print(f"  ✅ {name}: {len(cells)} → {len(picks)} постов ({done} уже запощено)")
        if not dry:
            json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=2)
            print(f"  posted.json обновлён ({state_path})")


if __name__ == "__main__":
    main()
