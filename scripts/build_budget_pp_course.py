#!/usr/bin/env python3
"""Сборка курса «Бюджетное ПП» в Supabase.

1. Сжимает картинки inbox/budget-pp-images/<slug>.png → JPG (1200px, q82).
2. Грузит в Supabase Storage alina-media/budget-pp/<slug>.jpg.
3. Создаёт course + 6 course_modules + 38 course_lessons (контент из budget-pp-unique.json).

Запуск: .venv-tts/bin/python scripts/build_budget_pp_course.py
"""
import json, os, re, sys, urllib.request, urllib.error

try:
    from PIL import Image
except ImportError:
    Image = None

SB_URL = None
SB_KEY = None
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line.startswith("SUPABASE_URL="):
        SB_URL = line.split("=", 1)[1].strip()
    if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
        SB_KEY = line.split("=", 1)[1].strip()

ROOT = "/home/hermes/alina-body"
IMG_DIR = f"{ROOT}/inbox/budget-pp-images"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))


def rest(method, path, payload=None):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{path}", method=method,
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    if payload is not None:
        req.data = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def upload_image(slug, png_path):
    # сжатие PNG → JPG (1200px, q82), если Pillow есть; иначе грузим PNG как есть
    src = png_path
    ctype = "image/jpeg"
    if Image:
        img = Image.open(png_path).convert("RGB")
        img.thumbnail((1200, 1200))
        tmp = f"/tmp/{slug}.jpg"
        img.save(tmp, "JPEG", quality=82, optimize=True, progressive=True)
        src = tmp
    data = open(src, "rb").read()
    req = urllib.request.Request(f"{SB_URL}/storage/v1/object/alina-media/budget-pp/{slug}.jpg",
        data=data, method="POST",
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": ctype, "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120)
    return f"{SB_URL}/storage/v1/object/public/alina-media/budget-pp/{slug}.jpg"


def html_content(les):
    u = les.get("unique", {})
    parts = []
    if u.get("intro"):
        parts.append(f"<p>{u['intro']}</p>")
    if les.get("ingredients"):
        parts.append("<h3>Ингредиенты</h3>")
        parts.append("<ul>" + "".join(
            f"<li><strong>{i['name']}</strong> — {i['amount']}</li>"
            for i in les["ingredients"]) + "</ul>")
    if u.get("steps"):
        parts.append("<h3>Приготовление</h3>")
        parts.append("<ol>" + "".join(f"<li>{s}</li>" for s in u["steps"]) + "</ol>")
    if les.get("kbzhu"):
        k = les["kbzhu"]
        parts.append(f"<p><strong>КБЖУ на порцию:</strong> {k['kcal']} ккал · белки {k['protein']} г · жиры {k['fat']} г · углеводы {k['carbs']} г</p>")
    if les.get("cost"):
        parts.append(f"<p><strong>Себестоимость:</strong> {les['cost']}</p>")
    if u.get("note"):
        parts.append(f"<p><em>{u['note']}</em></p>")
    return "".join(parts)


def main():
    # 1) загрузка картинок
    print("Загрузка картинок в Supabase…")
    url_by_slug = {}
    ok = fail = 0
    for m in DATA["modules"]:
        for les in m["lessons"]:
            slug = les["slug"]
            png = f"{IMG_DIR}/{slug}.png"
            if not os.path.exists(png):
                continue
            try:
                url_by_slug[slug] = upload_image(slug, png)
                ok += 1
            except Exception as ex:
                fail += 1
                print(f"  !! {slug}: {ex}")
    print(f"картинки: {ok} ок, {fail} ошибок")

    # 2) вставка курса
    c = DATA["course"]
    course = {
        "slug": c["slug"], "title": c["title"],
        "short_description": c["pitch"],
        "description": c["pitch"] + " Без глютена и лишнего сахара. Рецепты с граммовками, КБЖУ и себестоимостью.",
        "price": c["price"], "currency": c["currency"],
        "duration_days": 30, "level": "любой",
        "target_audience": "женщины 18–28, домашнее питание без переплат",
        "status": "review", "is_free": False,
    }
    created = rest("POST", "courses", course)
    cid = created[0]["id"]
    print(f"course id: {cid}")

    # 3) модули + уроки
    for m in DATA["modules"]:
        mod = rest("POST", "course_modules", {
            "course_id": cid, "title": m["title"], "description": None,
            "sort_order": DATA["modules"].index(m) + 1,
        })
        mid = mod[0]["id"]
        for i, les in enumerate(m["lessons"], 1):
            u = les.get("unique", {})
            title = u.get("unique_title") or les.get("title")
            is_preview = (m["slug"] == "m0-intro" and i == 1)  # первый урок курса — бесплатный
            rest("POST", "course_lessons", {
                "module_id": mid, "title": title,
                "description": (u.get("intro") or None),
                "lesson_type": "text", "video_url": None,
                "content": html_content(les),
                "file_url": url_by_slug.get(les["slug"]),
                "duration_minutes": 10 if les.get("type") == "technique" else 5,
                "is_preview": is_preview,
                "sort_order": i,
            })
        print(f"  ✓ {m['title'][:50]} → {len(m['lessons'])} уроков")

    print("\nГОТОВО. Курс «Бюджетное ПП» в Supabase (status=review, slug=budget-pp).")


if __name__ == "__main__":
    main()
