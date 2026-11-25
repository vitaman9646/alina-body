#!/usr/bin/env python3
"""Генератор человеческих постов Threads (без шаблонов).

Каждый пост пишется ЗАНОВО через DeepSeek в голосе Алины/Виталия — никаких
ротируемых заготовок. Типы: wish (пожелание) / question (вопрос) / opinion
(мнение) / matrix (прогрев лид-магнита → отложенная ссылка).

Тема берётся из пула ТЕМ (ротация по кругу, state gen_post_state_<profile>.json),
но текст каждый раз новый. Пост режется до 500 символов, фильтруется стоп-словами,
при блоке — перегенерация (до 3 попыток).

Запуск:
  python3 scripts/gen_post.py --profile alina --type question [--dry-run]

Секреты: DeepSeek — DEEPSEEK_API_KEY из ~/.hermes/.env; Threads — как в post_matrix.
"""
import os
import sys
import json
import re
import time
import fcntl
import argparse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_matrix as pm  # переиспользуем load_env/threads_api/hard_hits/pick_magnet/enqueue_reply

BASE = "/home/hermes/alina-body"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_TEXT = 500

# --- Голоса для ПОСТОВ («на ты», без шаблонов) ---
ALINA_VOICE = (
    "Ты — Алина, тренер по домашним тренировкам и питанию для девушек 18–28. "
    "Пишешь посты в Threads «на ты», как живой человек в телефоне. "
    "Правила: без длинного тире (—); без канцелярита и копирайтерских штампов; "
    "без ИИ-штампов («важно отметить», «в современном мире»); без обещаний результата; "
    "без медицинских советов и диагнозов; без выдуманных цифр и регалий; без хэштегов; без ссылок. "
    "Эмодзи — изредка, не в каждом посте. Пиши коротко и живо. Каждый пост — свежий: "
    "меняй зачин, ритм, длину предложений; не повторяй между постами ни формулировки, "
    "ни структуру, ни одни и те же слова. Один абзац, без пустых строк."
)

VITALIY_VOICE = (
    "Ты — Виталий, сертифицированный фитнес-тренер, мужской голос, «на ты», прямой. "
    "Пишешь посты в Threads о качалке, силовых и теории тренировок. "
    "Правила: без длинного тире (—); без канцелярита и копирайтерских штампов; без ИИ-штампов; "
    "без мед-обещаний («вылечит»); без выдуманных цифр результата; без диагнозов; без хэштегов; без ссылок. "
    "По-мужски прямо, без сюсюканья. Пиши коротко. Каждый пост — свежий: меняй зачин и слова, "
    "не повторяй формулировки между постами. Один абзац, без пустых строк."
)

VOICES = {"alina": ALINA_VOICE, "vitaliy": VITALIY_VOICE}

# --- Пулы тем (ротация по кругу; текст каждый раз новый) ---
THEMES = {
    "alina": [
        "с чего начать домашние тренировки",
        "тренировки дома без инвентаря",
        "белок в рационе — сколько и где брать",
        "вода и питьевой режим",
        "сон и восстановление",
        "привычки вместо «начну с понедельника»",
        "мифы о похудении",
        "тренировка по самочувствию и в цикле",
        "простые ПП-приёмы и готовка",
        "осанка и растяжка",
        "еда без чувства вины",
        "прогресс без весов: замеры и фото",
        "как не бросить тренировки через месяц",
        "разминка перед тренировкой",
    ],
    "vitaliy": [
        "техника базовых упражнений (присед/тяга/жим)",
        "прогрессия нагрузки — когда и как добавлять",
        "питание для роста мышц",
        "восстановление между тренировками",
        "мифы качалки",
        "сплит или фулбоди — что выбрать",
        "разминка и безопасность",
        "рабочий вес и RPE",
        "как не бросить через месяц",
        "техника без зеркала — как проверить себя",
        "что важнее: упражнение или режим",
        "боль в суставах на тренировке",
        "кардио и силовые вместе",
        "сколько отдыхать между подходами",
    ],
}

# --- Инструкции по типу поста ---
TYPE_INSTRUCTIONS = {
    "wish": "Напиши короткое утреннее пожелание/напоминание на тему «{theme}». Тёплое, без воды, 2–3 предложения. Не вопрос, не призыв подписаться. Каждый раз — другой зачин, другой ритм, другие слова.",
    "question": "Напиши один вопрос подписчикам на тему «{theme}». Каждый раз МЕНЯЙ форму: то прямой вопрос, то «выбери из двух», то «закончи фразу», то «расскажи про свой опыт», то короткая история-подводка с вопросом в конце. НЕ повторяй слова «честно», «без прикрас» и конструкцию «или… или» чаще, чем изредка. Один вопрос, без вступления и без клише.",
    "opinion": "Напиши короткое мнение с аргументом на тему «{theme}» — развенчай расхожее заблуждение, без токсичности и морализаторства. 2–3 предложения. Меняй зачин — не начинай всегда с «на самом деле» или «забудьте про».",
    "matrix": "Напиши короткий пост-зацепку на тему «{magnet_title}»: покажи боль ИЛИ выгоду ИЛИ неожиданный факт, заинтригуй, НО не раскрывай, как именно делать (это в гайде). 2–3 предложения, без ссылки, без «👇». Меняй угол от поста к посту.",
}

# --- Пины Pinterest → пост-прогрев → пост в канале (воронка Threads → TG → курс) ---
PIN_BASE = "https://alina-body.fitness/pins2"   # картинки курса (Vercel, без Cloudflare)
LEAD_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/pinterest"  # картинки лид-магнитов
COURSE_LINK = "https://t.me/alinabodyfree/22"   # ПП-сборник рецептов — цель для блюд курса

# Лид-магниты канала: (тема, картинка-пин, закреп в канале)
LEAD_MAGNETS = [
    ("Гарвардская тарелка", "lead-tarelka.jpg", "https://t.me/alinabodyfree/59"),
    ("Дневник питания", "lead-dnevnik.jpg", "https://t.me/alinabodyfree/61"),
    ("Психология похудения", "lead-psihologia.jpg", "https://t.me/alinabodyfree/63"),
    ("FAQ похудения", "lead-faq.jpg", "https://t.me/alinabodyfree/66"),
    ("Меню на неделю", "lead-menu.jpg", "https://t.me/alinabodyfree/70"),
    ("Список покупок", "lead-spisok.jpg", "https://t.me/alinabodyfree/72"),
    ("Спортпит и БАДы", "lead-supp.jpg", "https://t.me/alinabodyfree/55"),
    ("Здоровье печени", "lead-liver.jpg", "https://t.me/alinabodyfree/57"),
    ("Тазовое дно", "lead-tazovoe-dno.jpg", "https://t.me/alinabodyfree/75"),
    ("Тренировки дома", "lead-domashnie-trenirovki.jpg", "https://t.me/alinabodyfree/88"),
    ("Метаболический протокол", "lead-metabolic-protocol.jpg", "https://t.me/alinabodyfree/102"),
    ("Домашний уход и витамины", "lead-domashniy-uhod.jpg", "https://t.me/alinabodyfree/104"),
    ("Йога: асимметричное выравнивание", "lead-asimetriya.jpg", "https://t.me/alinabodyfree/106"),
    ("Что и когда есть", "lead-pitanie-podskazki.jpg", "https://t.me/alinabodyfree/111"),
    ("Похудение без уколов", "lead-pohudenie-bez-ukolov.jpg", "https://t.me/alinabodyfree/113"),
    ("5 БАДов с доказательствами", "lead-bady-5.jpg", "https://t.me/alinabodyfree/136"),
]

PIN_INSTRUCTION = (
    "Напиши один вопрос подписчикам на тему «{title}» — вовлекающий, «на ты». "
    "Спроси про их отношение, привычки или опыт (пользуются ли этим, что останавливает, нравится или нет). "
    "НЕ раскрывай суть/рецепт/шаги. НЕ давай ссылку. Один вопрос, 1–2 предложения, живой."
)

# Реплай-приглашение в канал — генерится заново (без шаблонов).
REPLY_FALLBACK = "Заглядывай ко мне в Telegram, там всё по делу."


def generate_reply(key, voice, title, kind):
    """Короткий естественный реплай-приглашение в канал (LLM, без шаблонов)."""
    topic = "ПП-рецепты" if kind == "dish" else f"тему «{title}»"
    user = (
        f"Напиши одну короткую естественную фразу, ненавязчиво приглашающую в мой Telegram-канал "
        f"(там {topic}). Без шаблонов и клише: не повторяй «👇», «шпаргалки», «без воды», "
        "«подробнее в канале». Живо, как подруге, 1 фраза. Ссылку в тексте не пиши."
    )
    raw = deepseek_generate(key, voice, user)
    return clean_post(raw) if raw else None


def load_json(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return {}


def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def state_path(profile):
    return os.path.join(BASE, "content", f"gen_post_state_{profile}.json")


def log_path(profile):
    return os.path.join(BASE, "content", f"gen_post_log_{profile}.jsonl")


def log_generated(profile, entry):
    with open(log_path(profile), "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_deepseek_key():
    for p in ["~/.hermes/.env", "~/.hermes/profiles/writer/.env", "~/.hermes/profiles/builder/.env"]:
        fp = os.path.expanduser(p)
        if os.path.exists(fp):
            env = pm.load_env(fp)
            if env.get("DEEPSEEK_API_KEY"):
                return env["DEEPSEEK_API_KEY"]
    return None


def deepseek_generate(key, system, user):
    for attempt in range(3):
        try:
            data = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.9,
                "max_tokens": 250,
            }).encode()
            req = urllib.request.Request(DEEPSEEK_URL, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
            })
            resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
            content = resp["choices"][0]["message"]["content"].strip()
            if content:
                return content
            print(f"  ⚠️ DeepSeek вернул пустой ответ (попытка {attempt+1})")
        except Exception as e:
            print(f"  ⚠️ DeepSeek (попытка {attempt+1}): {e}")
        time.sleep(3)
    return None


def clean_post(text):
    text = re.sub(r"\s+", " ", text).strip()          # один абзац
    text = text.replace("#", "")                        # без хэштегов
    text = re.sub(r'^["«\'\s]+|["»\'\s]+$', "", text).strip()
    return pm.truncate(text, MAX_TEXT)


def next_theme(profile):
    themes = THEMES[profile]
    st = load_json(state_path(profile))
    idx = st.get("theme", 0)
    theme = themes[idx % len(themes)]
    st["theme"] = (idx + 1) % len(themes)
    save_json(state_path(profile), st)
    return theme


def generate_post(profile, type_, key):
    """Генерирует чистый пост. Возвращает (text, theme) или (None, None)."""
    voice = VOICES[profile]
    theme = None
    for _ in range(3):  # до 3 генераций (на случай стоп-слов/пустого)
        if type_ == "matrix":
            m = pm.pick_magnet()
            if not m:
                print("  Нет лид-магнитов для поста.")
                return None, None
            _path, link, title = m
            theme = title
            user = TYPE_INSTRUCTIONS["matrix"].format(magnet_title=title)
        else:
            theme = next_theme(profile)
            user = TYPE_INSTRUCTIONS[type_].format(theme=theme)
        raw = deepseek_generate(key, voice, user)
        if not raw:
            return None, theme
        text = clean_post(raw)
        hits = pm.hard_hits(text)
        if hits:
            print(f"  🚫 Стоп-слова ({hits}), перегенерирую…")
            continue
        if len(text) < 20:
            print("  ⚠️ Слишком короткий пост, перегенерирую…")
            continue
        return text, theme
    return None, theme


def post_text(profile, text):
    tenv = pm.load_env(pm.CREDS_PATH)
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID") or pm.DEFAULT_USER_ID
    resp, err = pm.threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=text)
    if err:
        return None, f"создание контейнера: {err}"
    cid = resp.get("id")
    time.sleep(8)
    resp, err = pm.threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
    if err:
        return None, f"публикация: {err}"
    return resp.get("id"), None


def post_image(profile, image_url, caption):
    tenv = pm.load_env(pm.CREDS_PATH)
    ttok = tenv["THREADS_ACCESS_TOKEN"]
    tuid = tenv.get("THREADS_USER_ID") or pm.DEFAULT_USER_ID
    resp, err = pm.threads_api(ttok, f"{tuid}/threads", media_type="IMAGE",
                               image_url=image_url, text=caption, alt_text=caption[:100])
    if err:
        return None, f"создание контейнера: {err}"
    cid = resp.get("id")
    time.sleep(8)
    resp, err = pm.threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
    if err:
        return None, f"публикация: {err}"
    return resp.get("id"), None


def load_promo():
    """Единый пул карточек для pin-постов: лид-магниты + блюда курса (как ПП-кулинария).

    Возвращает [{title, image, link, kind}]. kind: lead (лид-магнит) | dish (блюдо курса).
    """
    promo = []
    for title, img, link in LEAD_MAGNETS:
        promo.append({"title": title, "image": f"{LEAD_BASE}/{img}", "link": link, "kind": "lead"})
    # блюда курса «Бюджетное ПП» — позиционируются как ПП-кулинария, ведут на сборник рецептов
    pin_dir = os.path.join(BASE, "public", "pins2")
    try:
        titles = {}
        data = json.load(open(os.path.join(BASE, "content", "budget-pp-unique.json")))
        for m in data.get("modules", []):
            for les in m.get("lessons", []):
                slug = les.get("slug")
                t = (les.get("unique") or {}).get("unique_title") or les.get("title")
                if slug and t:
                    titles[slug] = t
        for f in sorted(os.listdir(pin_dir)):
            if f.startswith("course-") and f.endswith(".jpg"):
                slug = f[len("course-"):-len(".jpg")]
                title = titles.get(slug)
                if title:
                    promo.append({"title": title, "image": f"{PIN_BASE}/{f}",
                                  "link": COURSE_LINK, "kind": "dish"})
    except (OSError, json.JSONDecodeError):
        pass
    return promo


def pin_due_today():
    """Картинка-пост — раз в 2 дня (по чётности дня года, UTC).

    Чётный день года → картинка, нечётный → текстовый слот (см. main()).
    """
    return time.gmtime().tm_yday % 2 == 0


def run_pin_post(args, key):
    """Пин-пост: картинка из Pinterest + сгенерированный вопрос-прогрев → отложенный реплай на пост в канале."""
    promo = load_promo()
    if not promo:
        print("Пул карточек пуст (ни лид-магнитов, ни блюд курса)")
        sys.exit(1)
    st = load_json(state_path(args.profile))
    idx = st.get("pin", 0)
    item = promo[idx % len(promo)]
    title, image_url, link, kind = item["title"], item["image"], item["link"], item["kind"]
    voice = VOICES[args.profile]

    text = None
    for _ in range(3):  # до 3 генераций (стоп-слова/пустой)
        raw = deepseek_generate(key, voice, PIN_INSTRUCTION.format(title=title))
        if not raw:
            break
        text = clean_post(raw)
        hits = pm.hard_hits(text)
        if hits:
            print(f"  🚫 Стоп-слова ({hits}), перегенерирую…")
            text = None
            continue
        if len(text) < 20:
            print("  ⚠️ Слишком короткая подпись, перегенерирую…")
            text = None
            continue
        break

    if not text:
        log_generated(args.profile, {"ts": int(time.time()), "type": "pin",
                                     "theme": title, "status": "FAILED"})
        print("  ❌ Подпись не сгенерирована. Слот пропущен.")
        sys.exit(1)

    print(f"=== {args.profile} / pin / {title} ({kind}) ===")
    print(text)
    print(f"image: {image_url}")
    print(f"link:  {link}")
    if args.dry_run:
        print("\n[dry-run] Постинг НЕ выполнялся.")
        return

    tid, err = post_image(args.profile, image_url, text)
    if err:
        log_generated(args.profile, {"ts": int(time.time()), "type": "pin",
                                     "theme": title, "text": text, "status": "POST_ERROR", "error": err})
        print(f"  ❌ {err}")
        sys.exit(1)
    print(f"  ✅ Пост: {tid}")

    # отложенный реплай на пост в канале (текст генерится заново, без шаблонов)
    reply_text = generate_reply(key, voice, title, kind)
    if not reply_text:
        reply_text = REPLY_FALLBACK
    reply_text = reply_text + "\n" + link
    data = pm.load_pending()
    data.setdefault("pending", []).append({
        "thread_id": tid,
        "link": link,
        "reply_text": reply_text,
        "due_ts": int(time.time()) + pm.REPLY_DELAY,
    })
    pm.save_pending(data)
    print(f"  ⏳ Реплай на пост в канале отложен (+2ч): {link}")

    st["pin"] = (idx + 1) % len(promo)
    save_json(state_path(args.profile), st)
    log_generated(args.profile, {"ts": int(time.time()), "type": "pin",
                                 "theme": title, "text": text, "thread_id": tid,
                                 "link": link, "status": "OK"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="alina", choices=["alina", "vitaliy"])
    ap.add_argument("--type", required=True, choices=["wish", "question", "opinion", "matrix", "pin"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pm.configure(args.profile)

    # Один запуск за раз (защита от наложения).
    lock = open(f"/tmp/gen_post_{args.profile}.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Другой запуск gen_post уже работает — выхожу")
        sys.exit(0)

    key = find_deepseek_key()
    if not key:
        print("DEEPSEEK_API_KEY не найден")
        sys.exit(2)

    if args.type == "pin":
        if pin_due_today():
            run_pin_post(args, key)
        else:
            # Картинка — раз в 2 дня; в остальные дни слот = текстовый вопрос.
            print(f"=== {args.profile} / pin → вопрос (картинка раз в 2 дня, сегодня без фото) ===")
            args.type = "question"
            text, theme = generate_post(args.profile, args.type, key)
            if not text:
                log_generated(args.profile, {"ts": int(time.time()), "type": "question",
                                             "theme": theme, "status": "FAILED"})
                print("  ❌ Вопрос не сгенерирован. Слот пропущен.")
                sys.exit(1)
            print(f"=== {args.profile} / question / тема: {theme} ===")
            print(text)
            if not args.dry_run:
                tid, err = post_text(args.profile, text)
                if err:
                    log_generated(args.profile, {"ts": int(time.time()), "type": "question",
                                                 "theme": theme, "text": text,
                                                 "status": "POST_ERROR", "error": err})
                    print(f"  ❌ {err}")
                    sys.exit(1)
                print(f"  ✅ Пост: {tid}")
                log_generated(args.profile, {"ts": int(time.time()), "type": "question",
                                             "theme": theme, "text": text, "thread_id": tid,
                                             "status": "OK"})
        return

    text, theme = generate_post(args.profile, args.type, key)
    if not text:
        log_generated(args.profile, {"ts": int(time.time()), "type": args.type,
                                     "theme": theme, "status": "FAILED"})
        print("  ❌ Пост не сгенерирован (после повторов). Слот пропущен.")
        sys.exit(1)

    print(f"=== {args.profile} / {args.type} / тема: {theme} ===")
    print(text)
    if args.dry_run:
        print("\n[dry-run] Постинг НЕ выполнялся.")
        return

    tid, err = post_text(args.profile, text)
    if err:
        log_generated(args.profile, {"ts": int(time.time()), "type": args.type,
                                     "theme": theme, "text": text, "status": "POST_ERROR", "error": err})
        print(f"  ❌ {err}")
        sys.exit(1)

    print(f"  ✅ Пост: {tid}")

    link = None
    if args.type == "matrix":
        m = pm.pick_magnet()
        if m:
            _path, link, title = m
            pm.enqueue_reply(tid, link, title)
            print(f"  ⏳ Оффер-реплай отложен (+2ч): {link}")

    log_generated(args.profile, {"ts": int(time.time()), "type": args.type,
                                 "theme": theme, "text": text, "thread_id": tid, "link": link,
                                 "status": "OK"})


if __name__ == "__main__":
    main()
