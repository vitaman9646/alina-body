#!/usr/bin/env python3
"""Недельный аудит здоровья Threads-постинга (профиль-параметризован).

Threads API НЕ отдаёт метрики вовлечённости (инсайты/лайки/просмотры — поля
`insights` нет). Доступно только: список своих постов (id, text, timestamp) +
постинг. Поэтому аудит проверяет то, что проверить реально:

1. Консистентность — сколько постов в день за последние N дней, есть ли «дыры»
   (день без постов = пропуск крона или падение постинга).
2. Сходимость с posted.json (матрица) — посты матрицы, которые есть в состоянии,
   но НЕ видны в API (реплай/пост мог не опубликоваться).
3. Очередь отложенных оффер-реплаев — не копятся ли невыстреленные (зависшие).

Итог — цвет-рейтинг (зелёный/оранжевый/красный) как в «контролёре» из SW.BAND,
но по постингу, а не по вовлечённости.

Запуск:
  python3 scripts/threads_health.py [--profile alina|vitaliy] [--days 7] [--report FILE]
"""
import os, sys, json, argparse, datetime, urllib.request, urllib.parse

PROFILES = {
    "alina": {
        "creds": "~/credentials/threads.env",
        "matrix_dir": "/home/hermes/alina-body/content/threads-matrix",
        "default_user_id": "29048751384731011",
        "username": "@alina_body_fitness",
        "report": "/home/hermes/alina-body/content/weekly_audit.md",
    },
    "vitaliy": {
        "creds": "~/credentials/vitaliy-threads.env",
        "matrix_dir": "/home/hermes/alina-body/content/threads-matrix-vitaliy",
        "default_user_id": "29238199995804564",
        "username": "@vitaliy_fitness_coach",
        "report": "/home/hermes/alina-body/content/weekly_audit_vitaliy.md",
    },
}

CREDS_PATH = os.path.expanduser(PROFILES["alina"]["creds"])
DEFAULT_USER_ID = PROFILES["alina"]["default_user_id"]
USERNAME = PROFILES["alina"]["username"]
MATRIX_DIR = PROFILES["alina"]["matrix_dir"]
STATE = os.path.join(MATRIX_DIR, "posted.json")
PENDING = os.path.join(MATRIX_DIR, "pending_replies.json")


def configure(profile):
    """Переключает глобальные пути/creds под профиль (alina|vitaliy)."""
    global CREDS_PATH, DEFAULT_USER_ID, USERNAME, MATRIX_DIR, STATE, PENDING
    c = PROFILES.get(profile)
    if not c:
        sys.exit(f"Неизвестный профиль: {profile}")
    CREDS_PATH = os.path.expanduser(c["creds"])
    DEFAULT_USER_ID = c["default_user_id"]
    USERNAME = c["username"]
    MATRIX_DIR = c["matrix_dir"]
    STATE = os.path.join(MATRIX_DIR, "posted.json")
    PENDING = os.path.join(MATRIX_DIR, "pending_replies.json")


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def api_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def fetch_threads(token, user_id, limit=200):
    """Все свои треды (id, text, timestamp) с пейджингом."""
    out = []
    url = (f"https://graph.threads.net/v1.0/{user_id}/threads"
           f"?fields=id,text,timestamp&limit=100&access_token={token}")
    while url and len(out) < limit:
        data = api_get(url, token)
        out += data.get("data", [])
        url = data.get("paging", {}).get("next")
        if not url:
            break
    return out[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="alina", choices=list(PROFILES))
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    configure(a.profile)

    env = load_env(CREDS_PATH)
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID") or DEFAULT_USER_ID

    threads = fetch_threads(token, uid)
    now = datetime.datetime.now(datetime.timezone.utc)

    # --- 1. посты по дням за последние N дней ---
    per_day = {}
    for t in threads:
        dt = datetime.datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00"))
        per_day.setdefault(dt.date(), 0)
        per_day[dt.date()] += 1

    print(f"=== Threads-аудит {USERNAME} за {a.days} дн. (сейчас {now.date()}) ===")
    print(f"Всего постов в выборке: {len(threads)}")
    print("\nПосты по дням:")
    gaps = 0
    today = now.date()
    for i in range(a.days - 1, -1, -1):
        d = (now - datetime.timedelta(days=i)).date()
        n = per_day.get(d, 0)
        is_today = (d == today)
        # сегодня «дырой» не считаем: аудит идёт утром, посты ещё не вышли
        flag = "" if (n > 0 or is_today) else "  ← ДЫРА"
        if n == 0 and not is_today:
            gaps += 1
        print(f"  {d}: {n}{flag}")

    # --- 2. сходимость с posted.json ---
    posted_ids = set()
    if os.path.exists(STATE):
        st = json.load(open(STATE))
        for m in st.values():
            for cell in m.get("posted", {}).values():
                if cell.get("thread_id"):
                    posted_ids.add(cell["thread_id"])
    api_ids = {t["id"] for t in threads}
    missing = posted_ids - api_ids  # в состоянии есть, в API нет

    # --- 3. очередь реплаев ---
    pending_n = 0
    if os.path.exists(PENDING):
        pend = json.load(open(PENDING))
        pending_n = len(pend.get("pending", []))

    print(f"\nМатрица: запощено ячеек в posted.json = {len(posted_ids)}")
    if missing:
        print(f"⚠️ {len(missing)} постов в posted.json НЕ найдены в API (могли не опубликоваться):")
        for m in list(missing)[:10]:
            print(f"    {m}")
    else:
        print("✅ Все посты из posted.json видны в API.")
    print(f"Очередь отложенных оффер-реплаев: {pending_n} (0 = чисто)")

    # --- рейтинг ---
    if gaps == 0 and not missing and pending_n <= 2:
        grade = "🟢 ЗЕЛЁНЫЙ — постинг здоров"
    elif gaps <= 2 and pending_n <= 5:
        grade = "🟠 ОРАНЖЕВЫЙ — есть дыры или хвост реплаев"
    else:
        grade = "🔴 КРАСНЫЙ — постинг буксует, проверь cron/логи"
    print(f"\nРейтинг: {grade}")

    report = a.report or PROFILES[a.profile]["report"]
    with open(report, "w", encoding="utf-8") as f:
        f.write(f"# Threads-аудит {USERNAME} {now.date()}\n\n")
        f.write(f"Рейтинг: {grade}\n\n")
        f.write("Посты по дням:\n")
        for i in range(a.days - 1, -1, -1):
            d = (now - datetime.timedelta(days=i)).date()
            f.write(f"- {d}: {per_day.get(d, 0)}\n")
        f.write(f"\nМатрица (posted.json): {len(posted_ids)} ячеек; "
                f"потерянных в API: {len(missing)}; очередь реплаев: {pending_n}\n")
    print(f"Отчёт: {report}")


if __name__ == "__main__":
    main()
