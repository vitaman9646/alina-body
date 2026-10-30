#!/usr/bin/env python3
"""CSV для Pinterest bulk upload: 45 рецептов «Еда на ходу» -> доска «Еда на ходу».

Usage: python3 scripts/gen_swbandco_food_pins_csv.py [--start YYYY-MM-DD] [--per-day N]
"""
import argparse
import csv
import json
from datetime import date, timedelta

SRC = "/tmp/swbandco_food_photos.json"
OUT = "/home/hermes/alina-body/content/pinterest-swbando-food.csv"
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
BOARD = "Еда на ходу"

CAT_LABEL = {
    "1-lanchi": "Холодные ланчи без разогрева",
    "2-termos": "Горячие обеды для термоса",
    "3-na-hodu": "Еда на ходу",
    "4-salad-banka": "Салат в банке",
    "5-perekusy": "Здоровые перекусы",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--per-day", type=int, default=4)
    args = ap.parse_args()

    start = date.fromisoformat(args.start) if args.start else (date.today() + timedelta(days=1))
    recipes = json.load(open(SRC))

    rows = []
    for i, r in enumerate(recipes):
        name = r["name"]
        slug = r["slug"]
        cat = CAT_LABEL.get(r.get("category_key", ""), "Еда на ходу")
        rows.append({
            "Title": name,
            "Media URL": f"{PIN_BASE}/recipe-{slug}.jpg",
            "Pinterest board": BOARD,
            "Thumbnail": "",
            "Description": f"{cat}. {name} — рецепт для ланч-бокса: ингредиенты и пошаговое приготовление.",
            "Link": f"https://alina-body.fitness/recipe/{slug}",
            "Publish date": (start + timedelta(days=i // args.per_day)).isoformat(),
            "Keywords": f"{name.lower()}, еда на ходу, ланч-бокс, пп, рецепт",
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Title", "Media URL", "Pinterest board", "Thumbnail",
            "Description", "Link", "Publish date", "Keywords",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} pins -> {OUT}")
    print(f"Board: {BOARD} | Schedule: {start.isoformat()} .. {rows[-1]['Publish date']} ({args.per_day}/day)")


if __name__ == "__main__":
    main()
