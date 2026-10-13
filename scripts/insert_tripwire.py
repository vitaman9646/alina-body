#!/usr/bin/env python3
"""Вставка трипваера «3 дня активации» (glutes-legs-tripwire) — первые 3 дня курса."""
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
    "Разминка": "warmup", "Ягодичный мостик": "glute-bridge",
    "Разведение коленей в мостике (с резинкой)": "bridge-knee-press",
    "Приседания с паузой": "squat-pause", "Растяжка": "stretch", "Заминка": "stretch",
    "Приседания": "squat", "Выпады назад": "reverse-lunge",
    "Ягодичный мостик на одной ноге": "single-leg-bridge",
    "Разгибание бедра стоя": "hip-extension", "Разведение ног лёжа на боку": "side-leg-raise",
}
photos = json.load(open("/home/hermes/alina-body/content/course_photos.json"))

md = open("/home/hermes/alina-body/content/course-glutes-legs.md", encoding="utf-8").read()
days, cur = [], None
for line in md.splitlines():
    line = line.rstrip()
    if line.startswith("## "):
        cur = {"title": line[3:].strip(), "lessons": []}; days.append(cur)
    elif line.startswith("### ") and cur is not None:
        cur["lessons"].append({"title": line[4:].strip(), "desc": "", "tech": "", "sets": "", "mistakes": ""})
    elif line.startswith("desc:") and cur and cur["lessons"]:
        cur["lessons"][-1]["desc"] = line[5:].strip()
    elif line.startswith("technique:") and cur and cur["lessons"]:
        cur["lessons"][-1]["tech"] = line[10:].strip()
    elif line.startswith("sets:") and cur and cur["lessons"]:
        cur["lessons"][-1]["sets"] = line[5:].strip()
    elif line.startswith("mistakes:") and cur and cur["lessons"]:
        cur["lessons"][-1]["mistakes"] = line[9:].strip()

def post(table, obj):
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}", data=json.dumps(obj).encode(), headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def get(table, params=""):
    req = urllib.request.Request(f"{SUPA}/rest/v1/{table}?{params}", headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# удалить старый трипваер, если есть
for c in get("courses", "slug=eq.glutes-legs-tripwire"):
    for m in get("course_modules", f"course_id=eq.{c['id']}"):
        for l in get("course_lessons", f"module_id=eq.{m['id']}"):
            urllib.request.urlopen(urllib.request.Request(
                f"{SUPA}/rest/v1/course_lessons?id=eq.{l['id']}", headers=H, method="DELETE"), timeout=30).read()
        urllib.request.urlopen(urllib.request.Request(
            f"{SUPA}/rest/v1/course_modules?id=eq.{m['id']}", headers=H, method="DELETE"), timeout=30).read()
    urllib.request.urlopen(urllib.request.Request(
        f"{SUPA}/rest/v1/courses?id=eq.{c['id']}", headers=H, method="DELETE"), timeout=30).read()

course = post("courses", {
    "slug": "glutes-legs-tripwire", "title": "3 дня активации: ягодицы и ноги",
    "short_description": "Короткий вход в программу — 3 дня по 15 минут, чтобы попробовать.",
    "description": "Три дня активации ягодиц и ног: разбудить мышцы, почувствовать технику и войти в ритм. По 15 минут в день, дома, без железа.",
    "price": 399, "currency": "RUB", "duration_days": 3, "level": "beginner",
    "target_audience": "Девушки 18–28, домашний фитнес", "status": "published", "is_free": False, "sort_order": 2,
})
cid = course[0]["id"]
total = 0
for i, day in enumerate(days[:3]):
    m = post("course_modules", {"course_id": cid, "title": day["title"], "description": "", "sort_order": i + 1})[0]
    for j, l in enumerate(day["lessons"]):
        u = photos.get(PHOTO.get(l["title"], ""))
        content_html = "<p>{}</p><p><strong>Подходы:</strong> {}</p>".format(l["tech"].replace("\n", "<br>"), l["sets"])
        if l["mistakes"]:
            content_html += "<p><strong>Частые ошибки:</strong> {}</p>".format(l["mistakes"].replace("\n", "<br>"))
        post("course_lessons", {
            "module_id": m["id"], "title": l["title"], "description": l["desc"],
            "lesson_type": "text", "content": content_html, "file_url": u,
            "duration_minutes": 5 if any(x in l["title"] for x in ("Разминка", "Растяжка", "Заминка")) else 15,
            "is_preview": (i == 0 and j == 0), "sort_order": j + 1,
        })
        total += 1
print(f"Трипваер вставлен: 3 дня, {total} уроков. id={cid}")
