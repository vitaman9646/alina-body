#!/usr/bin/env python3
"""Merge the 17 ПП-рецепты + 51 ПП-сборник recipes -> /tmp/recipes_all.json + public/recipes.json.

Run AFTER gen_recipe_photos.py (writes public/recipes.json with the 17) and
gen_recipe_photos51.py (writes /tmp/recipes51_clean.json with the 51).
"""
import json

PUB = "/home/hermes/alina-body/public/recipes.json"
S51 = "/tmp/recipes51_clean.json"
ALL = "/tmp/recipes_all.json"


def main():
    try:
        a17 = json.load(open(PUB))
    except Exception:
        a17 = []
    try:
        a51 = json.load(open(S51))
    except Exception:
        a51 = []

    all_r = a17 + a51
    json.dump(all_r, open(PUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(all_r, open(ALL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Merged: {len(a17)} + {len(a51)} = {len(all_r)} recipes")
    print(f"  -> {PUB} and {ALL}")


if __name__ == "__main__":
    main()
