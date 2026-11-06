#!/usr/bin/env python3
"""Адаптация уроков Vahva → курс Alina Body (извлечь контент из навигации + перевод).

Читает content/vahva-fitness.json (lessons + start_here), пишет в content/vahva-ru.json
поля lessons (русский) и start_here (русский). Рабочие тренировки не трогает.
"""
import os, sys, json, time, urllib.request, urllib.error

SRC = "/home/hermes/alina-body/content/vahva-fitness.json"
OUT = "/home/hermes/alina-body/content/vahva-ru.json"
MODEL = "deepseek-chat"

LESSON_SYSTEM = (
    "Ты переводишь урок фитнес-программы на русский для тренера Алины (домашние тренировки для девушек 18–28, голос «на вы»).\n"
    "Исходник — сырой текст страницы урока, где СОДЕРЖАНИЕ перемешано с навигацией сайта.\n"
    "Правила:\n"
    "1. Извлеки ТОЛЬКО содержательный текст урока. Выброси полностью: «Hi ADEPT», «Community», «Help», «Start Here», «Lessons», «Phase 1/2/3», «Lesson N / Methodology Lessons», «Mark as complete», «◀︎ Previous lesson», «Next lesson ▶︎», «About this lesson», список названий всех 16 уроков («1. ...», «2. ...» и т.д.), «BONUS: How to Rehab your Knees», «Superior Athletic Ankles & Feet Course», «Copyright…», «Terms of Service», «Privacy Policy».\n"
    "2. Переведи на русский голосом Алины: просто, тепло, на «вы», без мата и сленга, без упоминания ИИ и без слова «adept/athlete».\n"
    "3. Сохрани смысл и все факты. Не выдумывай цифры, не добавляй медицинских обещаний и дисклеймеров.\n"
    "4. Верни СТРОГО JSON-объект: {\"title\":\"название урока на русском\",\"text\":\"переведённый текст урока, абзацы через \\n\\n\"}. Без текста вокруг."
)

START_SYSTEM = (
    "Ты переводишь вводную страницу фитнес-программы на русский для тренера Алины (домашние тренировки, девушки 18–28, голос «на вы»).\n"
    "Исходник — сырой текст страницы, где СОДЕРЖАНИЕ перемешано с навигацией сайта.\n"
    "1. Извлеки ТОЛЬКО содержательный текст (про фазы, как проходить программу, как выполнять упражнения). Выброси: «Hi ADEPT», «Community», «Help», «Start Here», «Lessons», «Phase 1/2/3», «Mark as complete», «Checklist», «Copyright…», «Terms of Service», «Privacy Policy» и названия кнопок.\n"
    "2. Переведи на русский голосом Алины: просто, тепло, на «вы», без сленга, без упоминания ИИ. Убери упоминание «Athlete 20XX» — назови просто «программа» или «наш курс».\n"
    "3. Не выдумывай цифры, не добавляй мед-обещаний.\n"
    "4. Верни СТРОГО JSON-объект: {\"text\":\"переведённый текст, абзацы через \\n\\n\"}. Без текста вокруг."
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


def chat(key, system, user):
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 3000,
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        return r["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:300]
    except Exception as e:
        return None, str(e)


def main():
    key = get_key()
    if not key:
        sys.exit("DEEPSEEK_API_KEY не найден")
    data = json.load(open(SRC))
    out = json.load(open(OUT)) if os.path.exists(OUT) else {"source": data["source"], "phases": [], "lessons": [], "start_here": ""}

    # уроки
    lessons_out = []
    for l in data["lessons"]:
        user = f"Название урока: {l['title']}\n\nСырой текст страницы:\n{l['text']}"
        raw, err = chat(key, LESSON_SYSTEM, user)
        if err or not raw:
            print(f"  ❌ урок {l['n']}: {err}")
            continue
        try:
            obj = json.loads(raw)
            lessons_out.append({"n": l["n"], "title": obj.get("title", l["title"]), "text": obj.get("text", "")})
            print(f"  ✅ урок {l['n']}: {obj.get('title','')[:50]} ({len(obj.get('text',''))} симв.)")
        except json.JSONDecodeError as e:
            print(f"  ❌ урок {l['n']}: JSON {e}")
        time.sleep(0.5)

    # старт
    if data.get("start_here"):
        raw, err = chat(key, START_SYSTEM, "Сырой текст вводной страницы:\n" + data["start_here"])
        start_out = ""
        if not err and raw:
            try:
                start_out = json.loads(raw).get("text", "")
                print(f"  ✅ start_here: {len(start_out)} симв.")
            except json.JSONDecodeError as e:
                print(f"  ❌ start_here: JSON {e}")
        out["start_here"] = start_out

    out["lessons"] = lessons_out
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"готово: {len(lessons_out)} уроков → {OUT}")


if __name__ == "__main__":
    main()
