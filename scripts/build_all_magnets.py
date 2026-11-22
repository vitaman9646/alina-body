#!/usr/bin/env python3
"""Собирает 14 лид-магнитов: build_magnet.py (карточки) + pin_guide.py (закреп)
+ проставляет реальную ссылку в матрицу вместо PLACEHOLDER."""
import subprocess, re, os, json, glob

ROOT = "/home/hermes/alina-body"
MAGNETS = ["kostnyj-bulon", "prorostki-bobovye", "prorostki-brokkoli", "rzhanye-lepeshki",
           "salaty", "zavtraki-yaica", "humus", "pashtet", "supy", "subprodukty",
           "kotlety", "kashi", "korneplody", "meal-prep"]
PY = f"{ROOT}/.venv-tts/bin/python"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=600)


for slug in MAGNETS:
    spec = f"{ROOT}/content/magnet-{slug}.json"
    lonrid = f"{ROOT}/content/{slug}-lonrid.txt"
    if not (os.path.exists(spec) and os.path.exists(lonrid)):
        print(f"!! {slug}: нет спеки/лонгрида, пропуск")
        continue
    title = json.load(open(spec))["title"]

    r = run([PY, "scripts/build_magnet.py", spec])
    if "готово карточек" not in r.stdout:
        print(f"!! {slug}: build_magnet fail → {r.stdout[-200:]}")
        continue

    r2 = run([PY, "scripts/pin_guide.py", "--title", title,
              "--urls", f"/tmp/{slug}_urls.json", "--lonrid", lonrid])
    m = re.search(r"message_id: (\d+)", r2.stdout)
    if not m:
        print(f"!! {slug}: pin fail → {r2.stdout[-200:]}")
        continue
    link = f"https://t.me/alinabodyfree/{m.group(1)}"

    mats = glob.glob(f"{ROOT}/content/threads-matrix/matrix-{slug}-*.md")
    for mp in mats:
        txt = open(mp).read().replace("PLACEHOLDER", link)
        open(mp, "w").write(txt)

    print(f"✅ {slug} ({title}) → {link}")
