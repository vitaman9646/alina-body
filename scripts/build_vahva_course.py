#!/usr/bin/env python3
"""Сборка курса «Домашние тренировки: 12 недель» из Vahva в Supabase.

Шаги:
1. Загрузить 99 flat-картинок упражнений в Supabase Storage (alina-media/vahva/exercise/).
2. Создать course + course_modules (фазы/дни/теория/старт) + course_lessons (упражнения/уроки).

Контент: vahva-ru.json (русский). Картинки: vahva-image-map.json (slug → файл), slug из англ. названия.
Запуск: python3 scripts/build_vahva_course.py
"""
import json, os, re, sys, time, urllib.request, urllib.error

SB_URL = None; SB_KEY = None
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line.startswith("SUPABASE_URL="): SB_URL = line.split("=", 1)[1].strip()
    if line.startswith("SUPABASE_SERVICE_ROLE_KEY="): SB_KEY = line.split("=", 1)[1].strip()

ROOT = "/home/hermes/alina-body"
RU = json.load(open(f"{ROOT}/content/vahva-ru.json"))
EN = json.load(open(f"{ROOT}/content/vahva-fitness.json"))
IMGMAP = json.load(open(f"{ROOT}/content/vahva-image-map.json"))["generated"]

DAY_RU = {"monday": "Понедельник", "tuesday": "Вторник", "thursday": "Четверг", "friday": "Пятница"}
TITLE_RU = {
    "Hip Articulations & Abs": "Таз и пресс",
    "Push Upper Body Workout": "Верх тела: жим",
    "Push & Pull Leg Workout": "Ноги: жим и тяга",
    "Pull Upper Body Workout & Obliques": "Верх тела: тяга и косые",
    "Hip Articulations": "Тазобедренные суставы",
    "Push Upper Body Workout & Abs": "Верх тела: жим и пресс",
    "Hip Stability & Balance": "Стабильность таза и баланс",
    "Leg Speed and Agility Drills": "Скорость ног и ловкость",
    "Plyometric Leg Workout": "Ноги: плиометрика",
}


def slugify(n):
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')


def rest(method, path, payload=None):
    req = urllib.request.Request(f"{SB_URL}/rest/v1/{path}", method=method,
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": "application/json", "Prefer": "return=representation"})
    if payload is not None:
        req.data = json.dumps(payload).encode()
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def upload_image(slug, path):
    data = open(path, "rb").read()
    req = urllib.request.Request(f"{SB_URL}/storage/v1/object/alina-media/vahva/exercise/{slug}.jpg",
        data=data, method="POST",
        headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=120)
    return f"{SB_URL}/storage/v1/object/public/alina-media/vahva/exercise/{slug}.jpg"


def html_exercise(ru_ex):
    sets, reps = ru_ex["sets"], ru_ex.get("reps", "")
    target = ru_ex.get("target", "")
    head = f"<p><strong>{sets} × {reps}</strong>" + (f" · {target}" if target else "") + "</p>"
    cues = ru_ex.get("cues", [])
    if cues:
        body = "<ul>" + "".join(f"<li>{c}</li>" for c in cues) + "</ul>"
    else:
        body = ""
    return head + body


def html_text(text):
    return "".join(f"<p>{p}</p>" for p in text.split("\n\n") if p.strip())


def main():
    # 1) загрузка картинок
    print("Загрузка картинок в Supabase…")
    url_by_slug = {}
    ok = fail = 0
    for slug, path in IMGMAP.items():
        if not os.path.exists(path):
            fail += 1; continue
        try:
            url_by_slug[slug] = upload_image(slug, path); ok += 1
        except Exception as ex:
            fail += 1
            print(f"  !! {slug}: {ex}")
    print(f"картинки: {ok} ок, {fail} ошибок")

    # 2) кросс-вок EN (имя→слаг) ↔ RU (имя/cues), по структуре (phase, week, day, code)
    en_by_key = {}
    for ph in EN["phases"]:
        for wk in ph["weeks"]:
            for d in wk["days"]:
                for e in d["exercises"]:
                    en_by_key[(ph["phase"], wk["week"], d["day"], e["code"])] = e["name"]

    # 3) строим модули
    modules = []
    sort = 0

    def add_module(title, description, lessons):
        nonlocal sort
        sort += 1
        modules.append({"title": title, "description": description or "", "sort_order": sort, "lessons": lessons})

    # Старт
    add_module("Старт", "Как проходит программа и как двигаться по фазам.",
               [{"title": "Как проходить программу", "content": html_text(RU.get("start_here", "")),
                 "file_url": None, "duration_minutes": 6, "is_preview": True, "sort_order": 1}])

    # Фазы
    PHASE_RU = {1: "Фаза 1 · Сила и мобильность", 2: "Фаза 2 · Стабильность и баланс", 3: "Фаза 3 · Скорость и взрывная"}
    for ph in RU["phases"]:
        pnum = ph["phase"]
        for wk in sorted(ph["weeks"], key=lambda w: w["week"]):
            for d in sorted(wk["days"], key=lambda x: ["monday", "tuesday", "thursday", "friday"].index(x["day"])):
                day_ru = DAY_RU.get(d["day"], d["day"])
                title_ru = TITLE_RU.get(d.get("title", ""), d.get("title", ""))
                est = d.get("estimated_time", "")
                rest_txt = d.get("rest", "")
                desc = f"{est}" + (f" · отдых {rest_txt}" if rest_txt else "")
                n = len(d["exercises"])
                est_min = 35
                m = re.search(r'(\d+)-(\d+)', est)
                if m:
                    est_min = (int(m.group(1)) + int(m.group(2))) // 2
                per_ex = max(3, round(est_min / max(1, n)))
                lessons = []
                for i, e in enumerate(d["exercises"], 1):
                    code = e["code"]
                    en_name = en_by_key.get((pnum, wk["week"], d["day"], code), "")
                    slug = slugify(en_name)
                    img_url = url_by_slug.get(slug)
                    lessons.append({
                        "title": f"{code} · {e['name']}",
                        "content": html_exercise(e),
                        "file_url": img_url,
                        "duration_minutes": per_ex,
                        "is_preview": False,
                        "sort_order": i,
                    })
                add_module(f"{PHASE_RU[pnum]} · Неделя {wk['week']} · {day_ru} — {title_ru}", desc, lessons)

    # Теория
    theory = RU.get("lessons", [])
    add_module("Теория", "16 уроков по технике, прогрессии и безопасности.",
               [{"title": f"{l['n']}. {l.get('title','')}", "content": html_text(l.get("text", "")),
                 "file_url": None, "duration_minutes": 5, "is_preview": False, "sort_order": l["n"]}
                for l in sorted(theory, key=lambda x: x["n"])])

    print(f"модулей: {len(modules)}, уроков: {sum(len(m['lessons']) for m in modules)}")

    # 4) вставка
    course = {
        "slug": "home-training-12-weeks",
        "title": "12 недель: домашние тренировки на всё тело",
        "short_description": "Пошаговая программа на 12 недель: сила и мобильность → стабильность → взрывная. 5 тренировок в неделю, дома, без зала.",
        "description": "Трёхфазная программа на 12 недель. Фаза 1 — сила и мобильность (с опорой, чистая техника). Фаза 2 — стабильность и баланс (своим телом, без опоры). Фаза 3 — скорость и взрывная сила. Плюс 16 теоретических уроков по технике, прогрессивной перегрузке и суставам.",
        "price": 2990, "currency": "RUB",
        "duration_days": 84,
        "level": "начинающий и выше",
        "target_audience": "женщины 18–28, тренировки дома без зала",
        "status": "review", "is_free": False,
    }
    created = rest("POST", "courses", course)
    cid = created[0]["id"]
    print(f"course id: {cid}")

    for m in modules:
        mod = rest("POST", "course_modules", {
            "course_id": cid, "title": m["title"], "description": m["description"], "sort_order": m["sort_order"],
        })
        mid = mod[0]["id"]
        for l in m["lessons"]:
            rest("POST", "course_lessons", {
                "module_id": mid, "title": l["title"], "description": None,
                "lesson_type": "text", "video_url": None,
                "content": l["content"], "file_url": l["file_url"],
                "duration_minutes": l["duration_minutes"], "is_preview": l["is_preview"],
                "sort_order": l["sort_order"],
            })
        print(f"  ✓ {m['title'][:55]} → {len(m['lessons'])} уроков")

    print("\nГОТОВО. Курс в Supabase (status=review, slug=home-training-12-weeks).")


if __name__ == "__main__":
    main()
