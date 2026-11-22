#!/usr/bin/env python3
"""Уникализация уроков «Бюджетное ПП» → голос Алины (на ты, без псевдонауки).

Читает content/budget-pp-recipes.json, для каждого урока гонит через deepseek-chat
переписывание: unique_title / intro / steps (свои слова, факты как есть) / note
(доказательное «почему»). Пишет content/budget-pp-unique.json (структура курса +
поле unique в каждом уроке). Идемпотентно: уже сделанные уроки пропускаются.

Запуск: python3 scripts/adapt_budget_pp.py
"""
import os, sys, json, time, urllib.request, urllib.error

SRC = "/home/hermes/alina-body/content/budget-pp-recipes.json"
OUT = "/home/hermes/alina-body/content/budget-pp-unique.json"
MODEL = "deepseek-chat"

SYSTEM = (
    "Ты переписываешь рецепты и техники для курса фитнес-тренера Алины "
    "«Бюджетное ПП» — недорогое плотное питание без глютена и лишнего сахара. "
    "Аудитория: девушки 18–28. Голос Алины: «на ты», просто, тепло, по-домашнему.\n"
    "Правила:\n"
    "1. unique_title — чистый русский заголовок, понятный, без кликбейта и без упоминания источника.\n"
    "2. intro — 1–2 предложения-хук: зачем это блюдо/техника, чем оно хорошо. Без обещаний результата.\n"
    "3. steps — перепиши СВОИМИ словами, голосом Алины («на ты», императив: «нарежь», «туши»). "
    "Сохрани ВСЕ факты: граммовки, температуры, время, приёмы. Смысл каждого шага не сокращай, "
    "число шагов сохрани.\n"
    "4. note — короткое «почему это работает» ТОЛЬКО доказательное. Без «детокс», «чистка», "
    "«в 3–4 раза полезнее овощей», без медицинских обещаний и псевдонауки. Если в источнике "
    "псевдонаучное — переформулируй нейтрально или опусти.\n"
    "5. НЕ выдумывай цифры, НЕ добавляй дисклеймеры, НЕ упоминай ИИ/нейросеть/автора источника.\n"
    "6. Без мата и сленга («братан», «жиза», «го»).\n"
    "7. Верни СТРОГО JSON-объект без текста вокруг: "
    '{"unique_title":"...","intro":"...","steps":["..."],"note":"..."}'
)


def load_env(path):
    env = {}
    try:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except OSError:
        pass
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
        data=json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            "max_tokens": 1500,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return r["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:300]
    except Exception as e:
        return None, str(e)


def adapt_lesson(key, lesson):
    # ингредиенты НЕ шлём целиком (они не переписываются, остаются как есть) —
    # только имена для контекста intro. Экономия входных токенов.
    payload = {
        "title": lesson.get("title"),
        "type": lesson.get("type"),
        "ingredient_names": [i.get("name", "") for i in lesson.get("ingredients", [])],
        "steps": lesson.get("steps", []),
        "portions": lesson.get("portions", ""),
        "cost": lesson.get("cost", ""),
    }
    user = "Перепиши этот урок в голосе Алины (верни JSON):\n" + json.dumps(payload, ensure_ascii=False)
    out, err = chat(key, user)
    if err or not out:
        return None, err or "пустой ответ"
    try:
        obj = json.loads(out)
        if not obj.get("steps"):
            return None, "нет steps в ответе"
        return obj, None
    except json.JSONDecodeError as e:
        return None, f"JSON: {e} | {out[:200]}"


def main():
    key = get_key()
    if not key:
        sys.exit("DEEPSEEK_API_KEY не найден")

    data = json.load(open(SRC))
    out = None
    if os.path.exists(OUT):
        try:
            out = json.load(open(OUT))
        except (json.JSONDecodeError, OSError):
            out = None
    if out is None:
        out = {"course": data["course"], "modules": []}

    # карта существующих уникализаций по slug
    done = {}
    for m in out.get("modules", []):
        for les in m.get("lessons", []):
            if les.get("unique"):
                done[les["slug"]] = les["unique"]

    ok = fail = 0
    for mi, m in enumerate(data["modules"]):
        # найти/создать модуль в out
        out_mod = None
        for om in out.get("modules", []):
            if om.get("slug") == m["slug"]:
                out_mod = om
                break
        if out_mod is None:
            out_mod = {"slug": m["slug"], "title": m["title"], "lessons": []}
            out["modules"].append(out_mod)
        for les in m["lessons"]:
            if les["slug"] in done:
                # уже сделано — переиспользовать
                continue
            unique, err = adapt_lesson(key, les)
            if err or unique is None:
                print(f"  ❌ {les['slug']}: {err}")
                fail += 1
                continue
            les_copy = dict(les)
            les_copy["unique"] = unique
            out_mod["lessons"].append(les_copy)
            ok += 1
            print(f"  ✅ {les['slug']}: {unique.get('unique_title','')[:50]}")
            json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)  # инкрементально
            time.sleep(0.5)

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nготово: {ok} уроков уникализировано, ошибок {fail} → {OUT}")


if __name__ == "__main__":
    main()
