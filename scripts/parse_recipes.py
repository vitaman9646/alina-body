#!/usr/bin/env python3
"""Парсит ПП-сборник: рецепты по заголовкам (шрифт >= 25) → JSON."""
import pdfplumber, re, json

PDF = "/home/hermes/.hermes/cache/documents/doc_dd748cc414b8_[SWBAND.CO] ПП СБОРНИК.pdf"

SECTION = {
    "СОДЕРЖАНИЕ", "ЗАВТРАКИ", "ОБЕДЫ", "УЖИНЫ", "ДЕСЕРТЫ И ВЫПЕЧКА",
    "СОУСЫ ДЛЯ ЗАПРАВКИ САЛАТОВ", "ПОЛЕЗНЫЕ ДОМАШНИЕ НАПИТКИ", "ДОПОЛНЕНИЕ",
    "ПРО СЛАДОСТИ", "ПОЛЕЗНЫЕ ЧАИ", "ЗАМЕНА КОФЕ", "МОИ СОЦИАЛЬНЫЕ СЕТИ",
}

def is_noise(t):
    t = t.strip()
    if not t:
        return True
    if re.fullmatch(r"\d+", t):
        return True
    if "Авторское право" in t or "Селиверстова" in t or "skladchik" in t.lower():
        return True
    if re.fullmatch(r"[А-ЯЁA-Z][А-ЯЁA-Z .\-]{2,}\.{5,}\d+", t):
        return True
    return False

pdf = pdfplumber.open(PDF)
entries = []
for pno, p in enumerate(pdf.pages):
    for l in p.extract_text_lines():
        sizes = [c["size"] for c in l["chars"]]
        mx = max(sizes) if sizes else 0
        t = l["text"].strip()
        if is_noise(t):
            continue
        entries.append((pno, round(l["top"], 1), round(l["x0"], 1), t, round(mx, 1)))
entries.sort(key=lambda x: (x[0], x[1], x[2]))

# заголовки = размер >= 25
HEAD = 25.0
recipes = []
cur_name, cur_lines = [], []   # cur_name — список частей многострочного имени
cur_cat = ""
for pno, top, x0, t, sz in entries:
    if sz >= HEAD:
        if t.upper() in SECTION:
            if cur_name:
                recipes.append((" ".join(cur_name), cur_lines, cur_cat))
            cur_name, cur_lines = [], []
            cur_cat = t.strip()
            continue
        if cur_name and not cur_lines:
            cur_name.append(t)          # продолжение многострочного имени
        else:
            if cur_name:
                recipes.append((" ".join(cur_name), cur_lines, cur_cat))
            cur_name, cur_lines = [t], []
    else:
        if cur_name:
            cur_lines.append(t)
if cur_name:
    recipes.append((" ".join(cur_name), cur_lines, cur_cat))

def extract(block):
    kbzhu, ingr, method = [], [], []
    mode = "pre"
    for t in block:
        if re.search(r"КБЖУ|Калории|Белки|Жиры|Углеводы|Выход", t) and mode in ("pre", "kbzhu"):
            mode = "kbzhu"; kbzhu.append(t); continue
        if "Ингредиенты" in t:
            mode = "ingr"; ingr.append(t); continue
        if "Приготовление" in t:
            mode = "method"; method.append(t); continue
        if mode == "kbzhu":
            kbzhu.append(t)
        elif mode == "ingr":
            ingr.append(t)
        elif mode == "method":
            method.append(t)
    return kbzhu, ingr, method

out = []
for name, block, cat in recipes:
    kbzhu, ingr, method = extract(block)
    if not ingr and not method:
        continue  # пустой/не рецепт
    out.append({
        "name": name.strip(),
        "category": cat.strip(),
        "kbzhu": " ".join(kbzhu),
        "ingredients": " ".join(ingr),
        "method": " ".join(method),
    })

# дедуп по имени+категории (два разных рецепта с одинаковым именем в разных категориях — оставляем оба)
seen = {}
for r in out:
    k = (r["name"].lower(), r["category"].lower())
    if k not in seen:
        seen[k] = r
out = list(seen.values())

json.dump(out, open("/tmp/recipes.json", "w"), ensure_ascii=False, indent=2)
print("рецептов:", len(out))
for r in out:
    print(f"- {r['name'][:55]}")
