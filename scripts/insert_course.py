#!/usr/bin/env python3
"""Вставка курса «Ягодицы и ноги» (7 дней) в Supabase: courses + course_modules + course_lessons."""
import os, re, json, urllib.request

env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": SKEY, "Authorization": "Bearer " + SKEY, "Content-Type": "application/json",
     "Prefer": "return=representation"}

PHOTO = {
    "Разминка": "warmup",
    "Ягодичный мостик": "glute-bridge",
    "Разведение коленей в мостике (с резинкой)": "bridge-knee-press",
    "Приседания с паузой": "squat-pause",
    "Растяжка": "stretch",
    "Заминка": "stretch",
    "Приседания": "squat",
    "Выпады назад": "reverse-lunge",
    "Ягодичный мостик на одной ноге": "single-leg-bridge",
    "Разгибание бедра стоя": "hip-extension",
    "Разведение ног лёжа на боку": "side-leg-raise",
    "Приседания плие (широкая стойка)": "sumo-squat",
    "Румынская тяга на одной ноге": "single-leg-deadlift",
    "Выпады вперёд": "forward-lunge",
    "Планка на локтях": "plank",
    "Мёртвый жук": "dead-bug",
    "Боковая планка с колен": "side-plank",
    "Полная растяжка": "deep-stretch",
}

photos = json.load(open("/home/hermes/alina-body/content/course_photos.json"))
if len(photos) < 18:
    print("Фото ещё не все готовы:", len(photos), "из 18"); raise SystemExit(1)

def slug_of(title):
    if title.startswith("Круг:") or title.startswith("Комплекс:"):
        return "circuit"
    return PHOTO.get(title)

def photo_url(title):
    return photos.get(slug_of(title) or "")

md = open("/home/hermes/alina-body/content/course-glutes-legs.md", encoding="utf-8").read()
days = []
cur_day = None
for line in md.splitlines():
    line = line.rstrip()
    if line.startswith("## "):
        cur_day = {"title": line[3:].strip(), "lessons": []}
        days.append(cur_day)
    elif line.startswith("### ") and cur_day is not None:
        cur_day["lessons"].append({"title": line[4:].strip(), "desc": "", "tech": "", "sets": "", "mistakes": ""})
    elif line.startswith("desc:") and cur_day and cur_day["lessons"]:
        cur_day["lessons"][-1]["desc"] = line[5:].strip()
    elif line.startswith("technique:") and cur_day and cur_day["lessons"]:
        cur_day["lessons"][-1]["tech"] = line[10:].strip()
    elif line.startswith("sets:") and cur_day and cur_day["lessons"]:
        cur_day["lessons"][-1]["sets"] = line[5:].strip()
    elif line.startswith("mistakes:") and cur_day and cur_day["lessons"]:
        cur_day["lessons"][-1]["mistakes"] = line[9:].strip()

def post(table, obj):
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}", data=json.dumps(obj).encode(), headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# Удаляем старый тестовый курс + его модули/уроки
def get(table, params=""):
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}?{params}", headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

old_courses = get("courses")
for c in old_courses:
    if c.get("slug") in ("test-tonus", "glutes-legs-course"):
        mods = get("course_modules", f"course_id=eq.{c['id']}")
        for m in mods:
            less = get("course_lessons", f"module_id=eq.{m['id']}")
            for l in less:
                urllib.request.urlopen(urllib.request.Request(
                    f"{SUPA}/rest/v1/course_lessons?id=eq.{l['id']}", headers=H, method="DELETE"), timeout=30).read()
            urllib.request.urlopen(urllib.request.Request(
                f"{SUPA}/rest/v1/course_modules?id=eq.{m['id']}", headers=H, method="DELETE"), timeout=30).read()
        urllib.request.urlopen(urllib.request.Request(
            f"{SUPA}/rest/v1/courses?id=eq.{c['id']}", headers=H, method="DELETE"), timeout=30).read()

# Вставляем курс
course = post("courses", {
    "slug": "glutes-legs-course",
    "title": "7 дней: сильные ноги и упругие ягодицы",
    "short_description": "Домашняя программа для ягодиц и ног — 7 дней по 15–20 минут, без зала и железа.",
    "description": "Полная программа для ног и ягодиц: активация, база, изоляция, кор и выносливость. 7 дней по 15–20 минут, дома, с собственным весом (опционально фитнес-резинка).",
    "price": 1490, "currency": "RUB", "duration_days": 7, "level": "beginner",
    "target_audience": "Девушки 18–28, домашний фитнес",
    "status": "published", "is_free": False, "sort_order": 1,
})
cid = course[0]["id"]

total = 0
for i, day in enumerate(days):
    m = post("course_modules", {
        "course_id": cid, "title": day["title"], "description": "", "sort_order": i + 1,
    })[0]
    for j, l in enumerate(day["lessons"]):
        u = photo_url(l["title"])
        content_html = "<p>{}</p><p><strong>Подходы:</strong> {}</p>".format(
            l["tech"].replace("\n", "<br>"), l["sets"])
        if l["mistakes"]:
            content_html += "<p><strong>Частые ошибки:</strong> {}</p>".format(l["mistakes"].replace("\n", "<br>"))
        post("course_lessons", {
            "module_id": m["id"], "title": l["title"], "description": l["desc"],
            "lesson_type": "text", "content": content_html, "file_url": u,
            "duration_minutes": 5 if "Разминка" in l["title"] or "Растяжка" in l["title"] or "Заминка" in l["title"] else 15,
            "is_preview": (i == 0 and j == 0), "sort_order": j + 1,
        })
        total += 1

print(f"Курс вставлен: {len(days)} дней, {total} уроков. course_id={cid}")
