#!/usr/bin/env python3
"""Generate the Pinterest bulk CSV for lead-magnet pins.

Reads LEAD_MAGNETS from gen_lead_pins.py; each pin lands on /lead/<slug>
(claimed domain) and goes to its THEME board (same as article pins of that
theme — owner rule). Schedule staggered after the article-variant batch.

Usage: python3 scripts/gen_lead_pins_csv.py [--start YYYY-MM-DD] [--per-day N]
"""
import argparse
import csv
import sys
from datetime import date, timedelta

sys.path.insert(0, "/home/hermes/alina-body/scripts")
from gen_lead_pins import LEAD_MAGNETS  # noqa: E402

OUT = "/home/hermes/alina-body/content/pinterest-lead-pins.csv"
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"

BOARD_KEYWORDS = {
    "Питание и рецепты": "пп, правильное питание, рецепты",
    "Здоровье и привычки": "женское здоровье, привычки, самочувствие",
    "Тренировки дома": "тренировки дома, фитнес для женщин, упражнения",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--per-day", type=int, default=3)
    args = ap.parse_args()

    start = date.fromisoformat(args.start) if args.start else (date.today() + timedelta(days=1))

    rows = []
    slot = 0
    for slug, meta in LEAD_MAGNETS.items():
        board = meta["board"]
        landing = meta["landing"]
        for variant, title, tagline, _ill in meta["pins"]:
            day_offset = slot // args.per_day
            rows.append({
                "Title": title,
                "Media URL": f"{PIN_BASE}/lead-{slug}{variant}.jpg",
                "Pinterest board": board,
                "Thumbnail": "",
                "Description": tagline,
                "Link": landing,
                "Publish date": (start + timedelta(days=day_offset)).isoformat(),
                "Keywords": f"{title.lower()}, {BOARD_KEYWORDS[board]}",
            })
            slot += 1

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Title", "Media URL", "Pinterest board", "Thumbnail",
            "Description", "Link", "Publish date", "Keywords",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} lead-magnet pins -> {OUT}")
    print(f"Schedule: {start.isoformat()} .. {rows[-1]['Publish date']} ({args.per_day}/day)")


if __name__ == "__main__":
    main()
