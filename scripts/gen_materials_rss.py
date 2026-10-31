#!/usr/bin/env python3
"""Generate public/materials.xml — RSS for lead magnets.

Pinterest auto-imports this feed (same as /rss.xml for articles) so every new
lead magnet auto-pins (1 pin = main variant, landing on /lead/<slug>).
Reads LEAD_MAGNETS from gen_lead_pins.py.

Usage: python3 scripts/gen_materials_rss.py
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_lead_pins import LEAD_MAGNETS  # noqa: E402

SITE = "https://alina-body.fitness"
PIN_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"
OUT = "/home/hermes/alina-body/public/materials.xml"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


PUBDATES = "/home/hermes/alina-body/content/feed_pubdates.json"


def get_pubdate(key):
    """Стабильный pubDate на слага (первый раз — сейчас, дальше не меняется)."""
    try:
        st = json.load(open(PUBDATES))
    except (OSError, json.JSONDecodeError):
        st = {}
    if key not in st:
        st[key] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        try:
            json.dump(st, open(PUBDATES, "w"), ensure_ascii=False, indent=2)
        except OSError:
            pass
    return st[key]


def main():
    items = []
    for slug, meta in LEAD_MAGNETS.items():
        title = meta.get("title") or meta["pins"][0][1]
        tagline = meta.get("tagline", "")
        link = meta["landing"]
        img = f"{PIN_BASE}/lead-{slug}.jpg"
        pd = get_pubdate(f"lead-{slug}")
        items.append(
            f"    <item>\n"
            f"      <title><![CDATA[{title}]]></title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"true\">{link}</guid>\n"
            f"      <pubDate>{pd}</pubDate>\n"
            f"      <description><![CDATA[{tagline}]]></description>\n"
            f"      <media:content url=\"{img}\" medium=\"image\">\n"
            f"        <media:title type=\"plain\">{title}</media:title>\n"
            f"      </media:content>\n"
            f"      <category>lead-magnet</category>\n"
            f"    </item>"
        )

    last_build = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/">\n'
        "  <channel>\n"
        "    <title>Alina Body — материалы и шпаргалки</title>\n"
        f"    <link>{SITE}</link>\n"
        "    <description>Бесплатные шпаргалки и материалы Alina Body — тренировки, питание, забота о себе.</description>\n"
        "    <language>ru</language>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        f'    <atom:link href="{SITE}/materials.xml" rel="self" type="application/rss+xml" xmlns:atom="http://www.w3.org/2005/Atom"/>\n'
        f"    {chr(10).join(items)}\n"
        "  </channel>\n"
        "</rss>"
    )
    open(OUT, "w", encoding="utf-8").write(rss)
    print(f"Wrote {len(items)} lead magnets -> {OUT}")


if __name__ == "__main__":
    main()
