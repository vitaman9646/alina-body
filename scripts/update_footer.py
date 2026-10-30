#!/usr/bin/env python3
"""Replace the article footer CTA in all posts (strengthen to lead-magnet hook).

Old:  «Больше о домашних тренировках — на сайте … и в Telegram-канале Алины: t.me/alinabodyfree.»
New:  «Бесплатные шпаргалки по тренировкам и меню на неделю — в Telegram-канале Алины: t.me/alinabodyfree.»

Usage: python3 scripts/update_footer.py [--dry-run]
"""
import os
import sys

import requests

CREDS = os.path.expanduser("~/credentials/threads.env")
NEW_FOOTER = ('<blockquote>\n<p>Бесплатные шпаргалки по тренировкам и меню на неделю — '
              'в Telegram-канале Алины: <a href="https://t.me/alinabodyfree">t.me/alinabodyfree</a>.</p>\n</blockquote>')
TG_MARK = "t.me/alinabodyfree"


def load_env():
    d = {}
    for line in open(CREDS):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d


def main():
    dry = "--dry-run" in sys.argv
    env = load_env()
    url, key = env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    posts = requests.get(f"{url}/rest/v1/posts?select=slug,content", headers=headers, timeout=30).json()

    updated = skipped = 0
    for p in posts:
        slug, content = p["slug"], p["content"] or ""
        i = content.rfind("<blockquote>")
        if i < 0 or TG_MARK not in content[i:]:
            skipped += 1
            continue
        new_content = content[:i] + NEW_FOOTER
        if dry:
            print(f"[dry] {slug[:45]}")
            updated += 1
            continue
        r = requests.patch(
            f"{url}/rest/v1/posts?slug=eq.{slug}",
            headers=headers, json={"content": new_content}, timeout=30,
        )
        if r.status_code in (200, 204):
            updated += 1
        else:
            print(f"FAIL {slug[:45]}: {r.status_code} {r.text[:150]}")

    print(f"\n{'Would update' if dry else 'Updated'} {updated} posts, {skipped} skipped")


if __name__ == "__main__":
    main()
