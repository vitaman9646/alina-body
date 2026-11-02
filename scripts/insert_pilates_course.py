#!/usr/bin/env python3
"""Публикация курса «Пилатес дома для начинающих» в Supabase:
courses (7 дней + трипваер 3 дня) + course_modules + course_lessons + mini_course_themes.
Идемпотентно: сначала удаляет прежние записи с теми же slug.
"""
import os, json, urllib.request, urllib.error
from datetime import datetime, timezone

env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": SKEY, "Authorization": "Bearer " + SKEY, "Content-Type": "application/json",
     "Prefer": "return=representation"}

PHOTOS = json.load(open("/home/hermes/alina-body/content/pilates_photos.json"))
MD = "/home/hermes/alina-body/content/course-pilates-home.md"

PHOTO = {
    "Разминка": "pilates-warmup",
    "Дыхание лёжа": "breathing-lying",
    "Наклон таза": "pelvic-tilt",
    "Скольжение пяткой": "heel-slides",
    "Мостик пилатес": "pilates-bridge",
    "Заминка": "cooldown",
    "«Сто»": "hundred",
    "Подъём головы и лопаток": "chest-lift",
    "Планка на коленях": "knee-plank",
    "«Ракушка»": "clamshell",
    "Подъём ноги лёжа на боку": "side-leg-lift",
    "Круги ногой": "leg-circles",
    "«Кошка-корова»": "cat-cow",
    "«Плавание»": "swimming",
    "«Сфинкс»": "sphinx",
    "Скручивание лёжа": "spine-twist",
    "«Скольжение» у стены": "roll-down-wall",
    "Боковая планка с колен": "side-plank-knee",
}

MODULE_DESC = {
    1: "Дыхание диафрагмой, нейтральный таз, первый мягкий мостик.",
    2: "Кор: облегчённое «сто», подъём лопаток, планка на коленях.",
    3: "Серия на боку: боковые мышцы ягодиц и стабильность таза.",
    4: "Осанка: грудной отдел, мышцы вдоль позвоночника, «сфинкс».",
    5: "Мобильность и скручивания: спина, бок, скольжение у стены.",
    6: "Соединяем знакомые движения в спокойную круговую работу.",
    7: "Поток на 15 минут: всё лучшее из недели подряд.",
}


def req(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(f"{SUPA}/rest/v1/{path}", data=data, headers=H, method=method)
    try:
        body = urllib.request.urlopen(r, timeout=60).read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Supabase {method} {path} -> {e.code}: {e.read().decode()[:300]}")
    return json.loads(body) if body else []


def parse_md():
    days = []
    cur_day = None
    for line in open(MD, encoding="utf-8").read().splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            cur_day = {"title": line[3:].strip(), "lessons": []}
            days.append(cur_day)
        elif line.startswith("### ") and cur_day is not None:
            cur_day["lessons"].append({"title": line[4:].strip(), "desc": "", "tech": "",
                                       "sets": "", "mistakes": ""})
        elif line.startswith("desc:") and cur_day and cur_day["lessons"]:
            cur_day["lessons"][-1]["desc"] = line[5:].strip()
        elif line.startswith("technique:") and cur_day and cur_day["lessons"]:
            cur_day["lessons"][-1]["tech"] = line[10:].strip()
        elif line.startswith("sets:") and cur_day and cur_day["lessons"]:
            cur_day["lessons"][-1]["sets"] = line[5:].strip()
        elif line.startswith("mistakes:") and cur_day and cur_day["lessons"]:
            cur_day["lessons"][-1]["mistakes"] = line[9:].strip()
    return days


def delete_course(slug):
    rows = req("GET", f"courses?slug=eq.{slug}&select=id")
    for c in rows:
        mods = req("GET", f"course_modules?course_id=eq.{c['id']}&select=id")
        for m in mods:
            req("DELETE", f"course_lessons?module_id=eq.{m['id']}")
            req("DELETE", f"course_modules?id=eq.{m['id']}")
        req("DELETE", f"courses?id=eq.{c['id']}")
        print(f"удалён прежний курс {slug}")


def build_course(slug, title, short_desc, desc, price, days, sort_order, seo_title, seo_desc):
    course = req("POST", "courses", {
        "slug": slug,
        "title": title,
        "short_description": short_desc,
        "description": desc,
        "cover_url": PHOTOS.get("pilates-cover"),
        "preview_video_url": None,
        "price": price,
        "currency": "RUB",
        "duration_days": len(days),
        "level": "beginner",
        "target_audience": "Девушки 18–28, домашний фитнес без инвентаря",
        "status": "published",
        "is_free": False,
        "sort_order": sort_order,
        "seo_title": seo_title,
        "seo_description": seo_desc,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })[0]
    cid = course["id"]
    total = 0
    for i, day in enumerate(days):
        mod = req("POST", "course_modules", {
            "course_id": cid,
            "title": day["title"],
            "description": MODULE_DESC.get(i + 1, ""),
            "sort_order": i + 1,
        })[0]
        for j, l in enumerate(day["lessons"]):
            photo = PHOTOS.get(PHOTO.get(l["title"], ""), "")
            html = f"<p>{l['tech']}</p><p><strong>Подходы:</strong> {l['sets']}</p>"
            if l["mistakes"]:
                html += f"<p><strong>Частые ошибки:</strong> {l['mistakes']}</p>"
            dur = 3 if l["title"] in ("Разминка", "Заминка") else 3
            req("POST", "course_lessons", {
                "module_id": mod["id"],
                "title": l["title"],
                "description": l["desc"],
                "lesson_type": "text",
                "content": html,
                "file_url": photo,
                "duration_minutes": dur,
                "is_preview": (i == 0 and j == 1),
                "sort_order": j + 1,
            })
            total += 1
    print(f"{slug}: {len(days)} дней, {total} уроков, id={cid}")
    return cid


days = parse_md()
assert len(days) == 7, len(days)

DISCLAIMER = ("При болях в спине, шее или суставах — сначала консультация специалиста. "
              "Пилатес — не лечение.")

MAIN = "pilates-home-course"
TRIP = "pilates-start-3"
delete_course(MAIN)
delete_course(TRIP)
req("DELETE", f"mini_course_themes?slug=eq.pilates-home")

build_course(
    MAIN,
    "7 дней: пилатес дома для начинающих",
    "Мягкая программа на кор, осанку и дыхание — 7 дней по 15 минут, дома, без инвентаря.",
    "Пилатес для начинающих дома: дыхание, нейтральный таз, кор, серия на боку, осанка, "
    "мобильность и итоговый поток. Семь занятий по 15 минут, без инвентаря — по желанию коврик "
    "и небольшое полотенце. Учимся двигаться медленно и точно, дышать на усилии и не гнать темп. "
    + DISCLAIMER,
    1490,
    days,
    2,
    "Пилатес дома для начинающих: 7 дней по 15 минут",
    "Домашний пилатес для начинающих: 7 занятий по 15 минут на кор, осанку и дыхание, без инвентаря. Техника каждого упражнения и частые ошибки.",
)

build_course(
    TRIP,
    "3 дня: первый пилатес дома",
    "Три коротких занятия, чтобы почувствовать пилатес: дыхание, нейтральный таз, первый кор.",
    "Стартовый трипваер: три занятия по 15 минут из полной программы. Дыхание диафрагмой, "
    "нейтральный таз, первый мягкий мостик, облегчённое «сто» и планка на коленях, серия на боку. "
    + DISCLAIMER,
    399,
    days[:3],
    3,
    "Первый пилатес дома: 3 дня по 15 минут",
    "Три вводных занятия пилатесом дома по 15 минут: дыхание, нейтральный таз, кор. Техника и частые ошибки — для новичков.",
)

theme = req("POST", "mini_course_themes", {
    "slug": "pilates-home",
    "title": "Пилатес дома",
    "voice_line": "Мягкая сила: дышим, держим нейтральный таз и учим кор работать без гонки за темпом.",
    "status": "published",
    "sort_order": 2,
    "tripwire_title": "3 дня: первый пилатес дома",
    "tripwire_days": 3,
    "tripwire_minutes_per_day": 15,
    "tripwire_price": 399,
    "tripwire_slug": TRIP,
    "tripwire_image_url": PHOTOS.get("pilates-bridge", ""),
    "course_title": "7 дней: пилатес дома для начинающих",
    "course_days": 7,
    "course_price": 1490,
    "course_slug": MAIN,
    "course_image_url": PHOTOS.get("pilates-cover", ""),
    "created_by": "builder",
})[0]
print("theme:", theme["slug"], theme["status"])
