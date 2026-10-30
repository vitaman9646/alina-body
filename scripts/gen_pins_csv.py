#!/usr/bin/env python3
"""Generate a Pinterest bulk-upload CSV from content/pinterest-plan.json.

Exact Pinterest column headers: Title, Media URL, Pinterest board, Thumbnail,
Description, Link, Publish date, Keywords. Images-only (Thumbnail left empty).

Usage:
  python3 scripts/gen_pins_csv.py                  # staggered 2/day from tomorrow
  python3 scripts/gen_pins_csv.py --immediate      # publish all immediately
  python3 scripts/gen_pins_csv.py --start 2026-10-25 --per-day 2
"""
import argparse
import csv
import json
import os
from datetime import date, timedelta

REPO = "/home/hermes/alina-body"
PLAN = os.path.join(REPO, "content/pinterest-plan.json")
OUT = os.path.join(REPO, "content/pinterest-pins.csv")
SUPABASE_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
BLOG_BASE = "https://alina-body.fitness/blog"

# slug -> Pinterest board (auto-created by Pinterest if absent)
BOARDS = {
    "pochemu-ne-rastut-yagoditsy-doma-i-chto-s-etim-delat": "Тренировки дома",
    "holka-na-shee-i-kompyuternaya-sheya-kak-ubrat-sutulost-doma": "Тренировки дома",
    "kak-nachat-trenirovatsya-doma-s-nulya-i-ne-brosit-cherez-nedelyu": "Тренировки дома",
    "press-doma-bez-skruchivaniy-4-uprazhneniya-kotorye-ne-navredyat-shee": "Тренировки дома",
    "rastyazhka-posle-trenirovki-zachem-ona-nuzhna-i-kak-delat-ee-pravilno": "Тренировки дома",
    "trenirovka-s-rezinkoy-doma-5-uprazhneniy-na-vse-telo": "Тренировки дома",
    "kardio-doma-bez-pryzhkov-kak-razognat-puls-i-ne-razbudit-sosedey": "Тренировки дома",
    "kak-ubrat-lyashki-uprazhneniya-na-vnutrennyuyu-poverhnost-bedra-doma": "Тренировки дома",
    "kak-podtyanut-ruki-doma-bez-ganteley-uprazhneniya-na-tritseps": "Тренировки дома",
    "pilates-doma-dlya-nachinayuschih-myagkaya-trenirovka-dlya-kora-i-osanki": "Тренировки дома",
    "kak-ubrat-zhivot-doma-pochemu-press-ne-delaet-zhivot-ploskim": "Тренировки дома",
    "bolit-poyasnitsa-ot-sidyachey-raboty-chto-delat-doma": "Тренировки дома",
    "vechernyaya-trenirovka-mozhno-li-zanimatsya-pered-snom-i-kak-ne-isportit-son": "Тренировки дома",
    "belok-v-ratsione-kak-est-ego-dostatochno-bez-sportivnyh-dobavok": "Питание и рецепты",
    "trenirovki-po-fazam-tsikla-mozhno-li-zanimatsya-vo-vremya-mesyachnyh": "Здоровье и привычки",
    "kak-ne-brosit-trenirovki-cherez-dve-nedeli-pravilo-treh-minut": "Здоровье и привычки",
    "tsellyulit-chto-realno-pomogaet-doma-i-pochemu-lokalnogo-zhiroszhiganiya-ne-suschestvuet": "Здоровье и привычки",
    "krepatura-pochemu-bolyat-myshtsy-posle-trenirovki-i-mozhno-li-zanimatsya-dalshe": "Здоровье и привычки",
    "skolko-shagov-v-den-realno-nuzhno-pochemu-10-000-ne-meditsinskaya-norma": "Здоровье и привычки",
}

BOARD_KEYWORDS = {
    "Тренировки дома": "тренировки дома, фитнес для женщин, упражнения",
    "Питание и рецепты": "пп, правильное питание, рецепты",
    "Здоровье и привычки": "женское здоровье, привычки, самочувствие",
}


def keywords(pin_title, board):
    return f"{pin_title.lower()}, {BOARD_KEYWORDS[board]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--immediate", action="store_true")
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--only-variants", action="store_true", help="only v2/v3 (skip base v1 pins)")
    args = ap.parse_args()

    plan = json.load(open(PLAN))["pins"]
    if args.only_variants:
        plan = [p for p in plan if p.get("variant")]

    start = date.fromisoformat(args.start) if args.start else (date.today() + timedelta(days=1))

    rows = []
    slot = 0
    for pin in plan:
        slug = pin["slug"]
        board = BOARDS.get(slug, "Тренировки дома")
        title = pin["pin_title"]
        assert len(title) <= 100, f"title >100: {title}"
        assert len(pin["desc"]) <= 500, f"desc >500: {slug}"

        if args.immediate:
            pub = ""
        else:
            day_offset = slot // args.per_day
            pub = (start + timedelta(days=day_offset)).isoformat()
            slot += 1

        rows.append({
            "Title": title,
            "Media URL": f"{SUPABASE_BASE}/pin-{slug}{pin.get('variant', '')}.jpg",
            "Pinterest board": board,
            "Thumbnail": "",
            "Description": pin["desc"],
            "Link": f"{BLOG_BASE}/{slug}",
            "Publish date": pub,
            "Keywords": keywords(title, board),
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Title", "Media URL", "Pinterest board", "Thumbnail",
            "Description", "Link", "Publish date", "Keywords",
        ])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} pins -> {OUT}")
    if not args.immediate:
        last = rows[-1]["Publish date"]
        print(f"Schedule: {start.isoformat()} .. {last} ({args.per_day}/day)")


if __name__ == "__main__":
    main()
