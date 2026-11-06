#!/usr/bin/env python3
"""Адаптация упражнений Vahva → курс Alina Body (перевод + голос + замена инвентаря).

Читает content/vahva-fitness.json, гонит через DeepSeek-chat, пишет content/vahva-ru.json
(структура: phases[i].weeks[j].days[k].exercises[l] уже на русском, голос «на вы»).

Использование:
  python3 scripts/adapt_vahva.py --phase 1           # одна фаза
  python3 scripts/adapt_vahva.py --all               # все 3 фазы + старт + уроки (долго)
Запуск: системный python3 (requests есть).
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

SRC = "/home/hermes/alina-body/content/vahva-fitness.json"
OUT = "/home/hermes/alina-body/content/vahva-ru.json"
MODEL = "deepseek-chat"

SYSTEM = (
    "Ты переводишь и адаптируешь упражнения тренировочной программы под фитнес-тренера Алину "
    "(домашние тренировки для девушек 18–28, без зала, мягкий подход «мягкая сила»).\n"
    "Правила:\n"
    "1. Название упражнения — переведи на русский, сохрани смысл. Без имени источника, без «calisthenics/athlete».\n"
    "2. Числа (подходы, повторения) сохрани как есть, переведи только слова (repetitions→повторений, rounds→кругов, sets→подходов).\n"
    "3. Целевые мышцы (target) — переведи на русский.\n"
    "4. Вес (weight), если есть: штангу/гантели/кг — замени на «фитнес-резинка» или «без веса» (контекст: домашние тренировки). Убери «kg/lbs», оставь вилку при необходимости.\n"
    "5. Подсказки (cues) — переведи в голосе Алины: на «вы», просто, тепло, без мата и сленга. Сохрани СМЫСЛ каждой подсказки, не сокращай.\n"
    "6. НЕ выдумывай цифры, НЕ добавляй медицинских обещаний, НЕ добавляй дисклеймеры (их добавим отдельно).\n"
    "7. Верни СТРОГО JSON-массив без текста вокруг, ровно по числу упражнений, поля: "
    '{"code":"A1","name":"...","sets":4,"reps":"10–20 повторений","target":"...","weight":"","cues":["..."]}'
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
            "max_tokens": 2000,
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


def adapt_exercises(key, exercises):
    payload = [{"code": e["code"], "name": e["name"], "sets": e["sets"], "reps": e["reps"],
                "target": e["target"], "weight": e.get("weight", ""), "cues": e.get("cues", [])}
               for e in exercises]
    user = "Адаптируй эти упражнения (верни JSON-объект {\"exercises\":[...]}):\n" + json.dumps(payload, ensure_ascii=False)
    out, err = chat(key, user)
    if err or not out:
        return None, err or "пустой ответ"
    try:
        obj = json.loads(out)
        return obj.get("exercises", obj if isinstance(obj, list) else []), None
    except json.JSONDecodeError as e:
        return None, f"JSON: {e} | {out[:200]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

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
        out = {"source": data["source"], "phases": [], "lessons": [], "start_here": ""}

    # индекс существующих адаптаций
    done = set()
    if out.get("phases"):
        for ph in out["phases"]:
            for wk in ph["weeks"]:
                for d in wk["days"]:
                    if d.get("exercises"):
                        done.add((ph["phase"], wk["week"], d["day"]))

    total_ok = total_fail = 0
    for ph in data["phases"]:
        if args.phase and ph["phase"] != args.phase:
            continue
        if not args.all and not args.phase and ph["phase"] != 1:
            continue
        # найти/создать фазу в out
        out_ph = next((p for p in out["phases"] if p["phase"] == ph["phase"]), None)
        if out_ph is None:
            out_ph = {"phase": ph["phase"], "weeks": []}
            out["phases"].append(out_ph)
        for wk in ph["weeks"]:
            out_wk = next((w for w in out_ph["weeks"] if w["week"] == wk["week"]), None)
            if out_wk is None:
                out_wk = {"week": wk["week"], "days": []}
                out_ph["weeks"].append(out_wk)
            for d in wk["days"]:
                if (ph["phase"], wk["week"], d["day"]) in done:
                    continue
                adapted, err = adapt_exercises(key, d["exercises"])
                if err or adapted is None:
                    print(f"  ❌ {ph['phase']}-w{wk['week']} {d['day']}: {err}")
                    total_fail += 1
                    continue
                if len(adapted) != len(d["exercises"]):
                    print(f"  ⚠️ {ph['phase']}-w{wk['week']} {d['day']}: вернул {len(adapted)} из {len(d['exercises'])}")
                out_wk["days"].append({
                    "day": d["day"], "title": d["title"], "estimated_time": d["estimated_time"],
                    "rest": d["rest"], "exercises": adapted,
                })
                total_ok += 1
                print(f"  ✅ {ph['phase']}-w{wk['week']} {d['day']}: {len(adapted)} упр.")
                time.sleep(0.5)

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nготово: {total_ok} тренировок адаптировано, ошибок {total_fail} → {OUT}")


if __name__ == "__main__":
    main()
