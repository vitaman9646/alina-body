#!/usr/bin/env python3
"""Анализ вовлечённости: сопоставляет engagement.json (комментарии) с текстами постов."""
import json, os

posts = {}
for name in ("alina", "vitaliy"):
    p = f"/tmp/threads_posts_{name}.json"
    if os.path.exists(p):
        for it in json.load(open(p)):
            posts[it["id"]] = {"text": it.get("text", ""), "ts": it.get("timestamp", ""),
                               "link": it.get("permalink", ""), "profile": name}

eng = json.load(open("/home/hermes/alina-body/content/engagement.json"))

rows = []
for tid, e in eng.items():
    rows.append((e.get("count", 0), tid, e.get("profile"), e.get("cell"), e.get("title")))

rows.sort(key=lambda r: -r[0])

print("=== ТОП по числу комментариев (прокси вовлечённости) ===")
for count, tid, prof, cell, title in rows:
    if count >= 2:
        p = posts.get(tid, {})
        text = (p.get("text") or "").replace("\n", " ")
        print(f"\n[{prof}] count={count}  {p.get('link','')}")
        print(f"  title={title} cell={cell}")
        print(f"  text: {text[:220]}")

print("\n\n=== Распределение по count ===")
from collections import Counter
dist = Counter()
byprof = {"alina": Counter(), "vitaliy": Counter()}
for count, tid, prof, cell, title in rows:
    dist[count] += 1
    byprof[prof][count] += 1
for prof in ("alina", "vitaliy"):
    c = byprof[prof]
    total = sum(c.values())
    zero = c.get(0, 0)
    one = c.get(1, 0)
    engaged = total - zero - one
    print(f"[{prof}] всего веток={total}, 0 комментов={zero}, 1 коммент={one}, >=2 комментов={engaged}")

# топ-5 по count для каждого профиля (для отдельного вывода текстов полностью)
print("\n\n=== ТОП-5 АЛИНА (текст целиком) ===")
for count, tid, prof, cell, title in rows:
    if prof == "alina" and tid in posts:
        p = posts[tid]
        print(f"\n--- count={count} {p['link']} ---")
        print(p["text"][:400])
        if count < 3:
            break
