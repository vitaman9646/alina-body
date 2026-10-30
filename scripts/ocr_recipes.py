#!/usr/bin/env python3
"""OCR the 51 ПП-сборник recipe cards (recipe-01..51.jpg) -> /tmp/recipes51.json.

Tesseract (rus) extracts name, kbzhu, ingredients, method from each Pillow card.
Name = lines between «ПП-РЕЦЕПТ» and «Калории:»; ingredients between
«ИНГРЕДИЕНТЫ» and «ПРИГОТОВЛЕНИЕ»; method after «ПРИГОТОВЛЕНИЕ» to footer.

Usage: python3 scripts/ocr_recipes.py [--dry-run] [--limit N]
"""
import json
import re
import subprocess
import sys
import urllib.request

BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/recipes"
N = 51
OUT = "/tmp/recipes51.json"


def ocr(path):
    r = subprocess.run(["tesseract", path, "-", "-l", "rus", "--psm", "4"],
                       capture_output=True, text=True, timeout=60)
    return r.stdout


def norm(lines):
    out = []
    for ln in lines:
        s = ln.strip()
        s = re.sub(r"^[·•>*.\-—–]\s*", "", s)
        s = s.replace("|", "").strip()
        if s:
            out.append(s)
    return out


def parse(text):
    lines = text.splitlines()
    name, kbzhu, ingredients, method = "", "", [], []
    section = None
    for ln in lines:
        s = ln.strip()
        up = s.upper()
        if "ПП-РЕЦЕПТ" in up or "ПП-РЕЦЕПТ" in s:
            section = "name"
            continue
        if s.startswith("Калории") or "ккал" in s.lower() and "Белки" in s:
            kbzhu = s
            section = "kbzhu"
            continue
        if "ИНГРЕДИЕНТ" in up:
            section = "ingredients"
            continue
        if "ПРИГОТОВЛЕНИЕ" in up or "СПОСОБ" in up:
            section = "method"
            continue
        if "Больше рецептов" in s or "alina-body" in s.lower() or "t.me" in s:
            break
        if not s:
            continue
        if section == "name":
            name += " " + s
        elif section == "ingredients":
            ingredients.append(s)
        elif section == "method":
            method.append(s)
    return {
        "name": name.strip(),
        "kbzhu": kbzhu,
        "ingredients": " ".join(norm(ingredients)),
        "method": " ".join(norm(method)),
    }


def main():
    dry = "--dry-run" in sys.argv
    limit = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), 0)
    count = min(limit or N, N)

    out = []
    for i in range(1, count + 1):
        num = f"{i:02d}"
        url = f"{BASE}/recipe-{num}.jpg"
        local = f"/tmp/rc_{num}.jpg"
        try:
            urllib.request.urlretrieve(url, local)
            text = ocr(local)
            r = parse(text)
            r["file"] = f"recipe-{num}.jpg"
            out.append(r)
            print(f"[{num}] {r['name'] or '(нет имени)'}")
        except Exception as e:
            print(f"[{num}] ERROR {e}")
            out.append({"name": "", "file": f"recipe-{num}.jpg"})

    if not dry:
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nWrote {len(out)} -> {OUT}")


if __name__ == "__main__":
    main()
