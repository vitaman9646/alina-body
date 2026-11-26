#!/usr/bin/env python3
"""Вставка курса «Смузи на каждый случай» в Supabase.

Читает content/smoothie-course.json, создаёт course + course_modules +
course_lessons. Фото уже лежат в alina-media/smoothie/<slug>.jpg (грузить не нужно,
ставим только публичные URL). Обложка = alina-media/smoothie/cover.jpg.

Запуск: python3 scripts/insert_smoothie_course.py
"""
import json, os, sys, urllib.request, urllib.error

SB_URL = SB_KEY = None
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line.startswith("SUPABASE_URL="):
        SB_URL = line.split("=", 1)[1].strip()
    if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
        SB_KEY = line.split("=", 1)[1].strip()

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/smoothie-course.json"))
PUB = f"{SB_URL}/storage/v1/object/public/alina-media/smoothie"


def rest(method, path, payload=None):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{path}", method=method,
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    if payload is not None:
        req.data = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def delete_existing(slug):
    """Удалить курс с таким slug (если был), чтобы вставка была идемпотентной."""
    try:
        cur = rest("GET", f"courses?select=id&slug=eq.{slug}")
        if cur:
            cid = cur[0]["id"]
            rest("DELETE", f"course_modules?course_id=eq.{cid}")
            rest("DELETE", f"course_lessons?module_id=in.(select id from course_modules where course_id=eq.{cid})")
            rest("DELETE", f"courses?id=eq.{cid}")
            print(f"удалён старый курс {slug} (id {cid})")
    except Exception as ex:
        print("нет старого курса:", ex)


def html_content(les):
    parts = []
    if les.get("intro"):
        parts.append(f"<p>{les['intro']}</p>")
    if les.get("ingredients"):
        parts.append("<h3>Ингредиенты</h3>")
        parts.append("<ul>" + "".join(
            f"<li><strong>{i['name']}</strong> — {i['amount']}</li>"
            for i in les["ingredients"]) + "</ul>")
    if les.get("steps"):
        parts.append("<h3>Приготовление</h3>")
        parts.append("<ol>" + "".join(f"<li>{s}</li>" for s in les["steps"]) + "</ol>")
    if les.get("kbzhu"):
        k = les["kbzhu"]
        est = " (пересчёт)" if k.get("estimated") else ""
        parts.append(f"<p><strong>КБЖУ на порцию{est}:</strong> {k['kcal']} ккал · белки {k['protein']} г · жиры {k['fat']} г · углеводы {k['carbs']} г</p>")
    if les.get("note"):
        parts.append(f"<p><em>{les['note']}</em></p>")
    return "".join(parts)


def main():
    c = DATA["course"]
    delete_existing(c["slug"])

    course = {
        "slug": c["slug"], "title": c["title"],
        "short_description": c["pitch"],
        "description": c["pitch"] + " Каждый рецепт — с граммовками, пошаговым приготовлением и КБЖУ на порцию.",
        "cover_url": f"{PUB}/cover.jpg",
        "price": c["price"], "currency": c["currency"],
        "duration_days": 7, "level": "любой",
        "target_audience": "женщины 18–28, быстрые и полезные напитки под задачу",
        "status": "review", "is_free": False, "category": "pitanie",
    }
    created = rest("POST", "courses", course)
    cid = created[0]["id"]
    print(f"course id: {cid}")

    for mi, m in enumerate(DATA["modules"], 1):
        mod = rest("POST", "course_modules", {
            "course_id": cid, "title": m["title"], "description": m.get("description"),
            "sort_order": mi,
        })
        mid = mod[0]["id"]
        for i, les in enumerate(m["lessons"], 1):
            is_preview = (m["slug"] == "m0-vvedenie" and i == 1)
            file_url = f"{PUB}/{les['slug']}.jpg" if les.get("type") == "recipe" else None
            rest("POST", "course_lessons", {
                "module_id": mid, "title": les["title"],
                "description": les.get("intro") or les.get("when") or None,
                "lesson_type": "text", "video_url": None,
                "content": html_content(les),
                "file_url": file_url,
                "duration_minutes": 5,
                "is_preview": is_preview,
                "sort_order": i,
            })
        print(f"  ✓ {m['title'][:50]} → {len(m['lessons'])} уроков")

    print(f"\nГОТОВО. Курс «{c['title']}» в Supabase (slug={c['slug']}, status=review, category=pitanie).")


if __name__ == "__main__":
    main()
