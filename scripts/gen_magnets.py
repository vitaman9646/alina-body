#!/usr/bin/env python3
"""Генерит 14 лид-магнитов курса «Бюджетное ПП» через DeepSeek.

Для каждого магнита: собирает контент из budget-pp-unique.json (по slug'ам уроков),
гонит через deepseek-chat → спека карточек + лонгрид + матрица 5 постов.
Пишет: content/magnet-<slug>.json, content/<slug>-lonrid.txt,
content/threads-matrix/matrix-<slug>-YYYY-MM-DD.md.

Запуск: python3 scripts/gen_magnets.py
"""
import os, sys, json, time, urllib.request, urllib.error
from datetime import datetime

ROOT = "/home/hermes/alina-body"
DATA = json.load(open(f"{ROOT}/content/budget-pp-unique.json"))
MODEL = "deepseek-chat"
TODAY = datetime.now().strftime("%Y-%m-%d")

MAGNETS = [
    {"slug": "kostnyj-bulon", "title": "Бульон за 110 ₽/литр", "topic": "костный бульон кастрюля", "lessons": ["kostnyj-bulon"]},
    {"slug": "prorostki-bobovye", "title": "Еда на подоконнике", "topic": "проростки банка", "lessons": ["prorostki-bobovye"]},
    {"slug": "prorostki-brokkoli", "title": "Ростки с пользой", "topic": "проростки брокколи", "lessons": ["prorostki-brokkoli"]},
    {"slug": "rzhanye-lepeshki", "title": "Хлеб без дрожжей", "topic": "ржаные лепёшки", "lessons": ["rzhanye-lepeshki"]},
    {"slug": "salaty", "title": "Салаты на неделю", "topic": "салат овощи", "lessons": ["morkovnyj-salat", "kabachki-po-korejski", "salat-metelka"]},
    {"slug": "zavtraki-yaica", "title": "6 завтраков из яиц", "topic": "яйца завтрак", "lessons": ["yaichnica-fasol", "yajca-humus", "omlet-kapusta", "yajchnye-maffiny", "shakshuka", "skrembl-chechevica"]},
    {"slug": "humus", "title": "Хумус за 85 ₽", "topic": "хумус нут", "lessons": ["humus"]},
    {"slug": "pashtet", "title": "Паштет из печени", "topic": "паштет печень", "lessons": ["pashtet"]},
    {"slug": "supy", "title": "Суп за 37 ₽", "topic": "суп кастрюля", "lessons": ["sup-telyachi-hvosty", "uha", "tykvennyj-krem-sup", "sup-nut"]},
    {"slug": "subprodukty", "title": "Дешёвый белок", "topic": "субпродукты сковорода", "lessons": ["kurinye-zheludki", "serdce-befstroganov", "pechen-domashnyaya"]},
    {"slug": "kotlety", "title": "Котлеты за 24 ₽", "topic": "рыбные котлеты", "lessons": ["kotlety-mintaj", "kotlety-skumbriya"]},
    {"slug": "kashi", "title": "Каша без скуки", "topic": "каша тарелка", "lessons": ["formula-kash"]},
    {"slug": "korneplody", "title": "Забытые овощи", "topic": "корнеплоды драники", "lessons": ["draniki-bryukva", "draniki-morkov-repa", "repa-zapechennaya", "tykva-oregano"]},
    {"slug": "meal-prep", "title": "Еда на неделю за 2 часа", "topic": "контейнеры еда", "lessons": ["sistema", "spisok-zakupa"]},
]

SYSTEM = (
    "Ты делаешь лид-магнит (бесплатный тизер) и матрицу постов для фитнес-тренера Алины — "
    "курс «Бюджетное ПП», голос «на ты», просто, тепло, для девушек 18–28.\n"
    "Только факты из переданного материала. НЕ выдумывай цифры, НЕ добавляй мед-обещаний, "
    "псевдонауки («детокс», «жиросжигание»), упоминаний ИИ или источника. Без мата и сленга.\n"
    "Верни СТРОГО JSON-объект без текста вокруг:\n"
    '{"cards":[{"tag":"РУБРИКА КАПСОМ","title":"Заголовок","points":["пункт","пункт","пункт","пункт"]}],'
    '"longread":"несколько абзацев «почему это работает» (не дубль карточек)","matrix":["пост1","пост2","пост3","пост4","пост5"]}\n'
    "Правила по частям:\n"
    "1. cards — 4–5 карточек. Каждая: tag (рубрика капсом, 1–3 слова), title (короткий заголовок), "
    "points (ровно 4 пункта, плотные факты: граммовки, время, температура, цена).\n"
    "2. longread — 4–6 абзацев, объясняет ПОЧЕМУ это работает (смысл и выгода), не повторяет пункты карточек.\n"
    "3. matrix — 5 постов по углам: 1 по шагам, 2 страхи-возражения, 3 миф, 4 вместо дорогого, "
    "5 непопулярное мнение. Каждый пост ~400–500 знаков: хук-первая фраза → факт из материала → "
    "мост к материалу («собрала в гайд…») → в конце «ссылка первым комментарием ↓»."
)


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def get_key():
    for p in ["~/.hermes/profiles/writer/.env", "~/.hermes/profiles/builder/.env", "~/.hermes/.env"]:
        fp = os.path.expanduser(p)
        if os.path.exists(fp):
            e = load_env(fp)
            if e.get("DEEPSEEK_API_KEY"):
                return e["DEEPSEEK_API_KEY"]
    return None


def chat(key, user):
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({"model": MODEL, "messages": [
            {"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
            "max_tokens": 4000, "temperature": 0.4, "response_format": {"type": "json_object"}}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        return r["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:200]
    except Exception as e:
        return None, str(e)


def lesson_content(les):
    u = les.get("unique", {})
    return {
        "title": u.get("unique_title") or les.get("title"),
        "intro": u.get("intro", ""),
        "ingredients": [i["name"] + " " + i["amount"] for i in les.get("ingredients", [])],
        "steps": u.get("steps", []),
        "note": u.get("note", ""),
        "cost": les.get("cost", ""),
        "kbzhu": les.get("kbzhu"),
    }


def gather(lessons):
    out = []
    for m in DATA["modules"]:
        for les in m["lessons"]:
            if les["slug"] in lessons:
                out.append(lesson_content(les))
    return out


def main():
    key = get_key()
    if not key:
        sys.exit("DEEPSEEK_API_KEY не найден")

    for mg in MAGNETS:
        slug = mg["slug"]
        # пропустить уже готовые
        spec_path = f"{ROOT}/content/magnet-{slug}.json"
        if os.path.exists(spec_path):
            print(f"  ↻ {slug}: уже есть, пропуск")
            continue
        content = gather(mg["lessons"])
        user = (f"Магнит: «{mg['title']}». Материал (уроки курса):\n"
                + json.dumps(content, ensure_ascii=False))
        out, err = chat(key, user)
        if err or not out:
            print(f"  ❌ {slug}: {err}")
            continue
        try:
            obj = json.loads(out)
            cards = obj.get("cards", [])
            longread = obj.get("longread", "")
            matrix = obj.get("matrix", [])
            if not cards or not longread or len(matrix) < 5:
                print(f"  ⚠️ {slug}: неполный ответ (cards={len(cards)}, matrix={len(matrix)})")
                continue
        except json.JSONDecodeError as e:
            print(f"  ❌ {slug}: JSON {e}")
            continue

        # спека
        spec = {
            "slug": slug, "title": mg["title"], "style": "flat",
            "footer": "alina-body.fitness  ·  t.me/alinabodyfree", "disclaimer": "",
            "cards": [{
                "tag": c.get("tag", "БЮДЖЕТ"), "title": c.get("title", ""),
                "topic": mg["topic"], "prompt": f"Flat vector illustration of {mg['topic']}, clean minimal line art, soft warm pastel palette, no text",
                "points": c.get("points", []),
            } for c in cards],
        }
        json.dump(spec, open(spec_path, "w"), ensure_ascii=False, indent=2)
        open(f"{ROOT}/content/{slug}-lonrid.txt", "w").write(longread)

        angles = ["По шагам", "Страхи-возражения", "Миф", "Вместо дорогого", "Непопулярное мнение"]
        md = (f"---\ntype: threads-matrix\nstatus: draft\ndate: {TODAY}\n"
              f"source: лид-магнит «{mg['title']}» (курс «Бюджетное ПП»)\ncells: 5\npublished: []\n"
              f"link: https://t.me/alinabodyfree/PLACEHOLDER\n---\n\n# Матрица: {mg['title']}\n\n")
        for i, a in enumerate(angles, 1):
            md += f"### {i} — {a}\n\n{matrix[i-1]}\n\n"
        open(f"{ROOT}/content/threads-matrix/matrix-{slug}-{TODAY}.md", "w").write(md)
        print(f"  ✅ {slug}: {len(cards)} карточек, лонгрид, матрица 5")
        time.sleep(0.5)

    print("\nГОТОВО. Дальше: build_magnet.py + pin_guide.py для каждого, обновить link в матрицах.")


if __name__ == "__main__":
    main()
