#!/usr/bin/env python3
"""Generate the Pinterest bulk CSV for the 17 ПП-рецепты pins.

Board = «Питание и рецепты» (same theme as nutrition article/lead-magnet pins).
Each pin lands on /recipe/<slug>.

Usage: python3 scripts/gen_recipe_pins_csv.py [--start YYYY-MM-DD] [--per-day N]
"""
import argparse
import csv
import json
import sys
from datetime import date, timedelta

sys.path.insert(0, "/home/hermes/alina-body/scripts")
from gen_recipe_photos import slugify  # noqa: E402

SRC = "/tmp/recipes_all.json"
OUT = "/home/hermes/alina-body/content/pinterest-recipes.csv"
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
BOARD = "Питание и рецепты"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--per-day", type=int, default=3)
    args = ap.parse_args()

    start = date.fromisoformat(args.start) if args.start else (date.today() + timedelta(days=1))
    recipes = json.load(open(SRC))

    rows = []
    for i, r in enumerate(recipes):
        name = r["name"]
        slug = r.get("slug") or slugify(name)
        cat = r.get("category", "")
        rows.append({
            "Title": name,
            "Media URL": f"{PIN_BASE}/recipe-{slug}.jpg",
            "Pinterest board": BOARD,
            "Thumbnail": "",
            "Description": f"{cat}. {name} — простой ПП-рецепт: ингредиенты и пошаговое приготовление.",
            "Link": f"https://alina-body.fitness/recipe/{slug}",
            "Publish date": (start + timedelta(days=i // args.per_day)).isoformat(),
            "Keywords": f"{name.lower()}, рецепт, пп, правильное питание",
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Title", "Media URL", "Pinterest board", "Thumbnail",
            "Description", "Link", "Publish date", "Keywords",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} recipe pins -> {OUT}")
    print(f"Schedule: {start.isoformat()} .. {rows[-1]['Publish date']} ({args.per_day}/day)")


if __name__ == "__main__":
    main()
