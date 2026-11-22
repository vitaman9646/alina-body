#!/usr/bin/env python3
"""Перенаправляет link в матрицах бюдж.ПП на лендинг курса."""
import glob, re

ROOT = "/home/hermes/alina-body"
LINK = "https://alina-body.fitness/course/budget-pp"

slugs = ["nutryanoj-zhir", "kostnyj-bulon", "prorostki-bobovye", "prorostki-brokkoli",
         "rzhanye-lepeshki", "salaty", "zavtraki-yaica", "humus", "pashtet", "supy",
         "subprodukty", "kotlety", "kashi", "korneplody", "meal-prep"]

n = 0
for s in slugs:
    for f in glob.glob(f"{ROOT}/content/threads-matrix/matrix-{s}-*.md"):
        txt = open(f).read()
        txt2 = re.sub(r"^link:.*$", f"link: {LINK}", txt, flags=re.M)
        if txt2 != txt:
            open(f, "w").write(txt2)
            n += 1
            print(f"✅ {s} → {LINK}")
print(f"обновлено матриц: {n}")
