#!/usr/bin/env python3
"""Куратор Telegram-канала Алины: парсит новости/исследования о спорте и ЗОЖ,
переписывает их в голос Алины (от первого лица, «на ты») и постит в канал.

Конвейер: фиды → дедуп/фильтр по теме → выбор лучшего → выкачка статьи →
переписывание через DeepSeek (суть + вывод + цитата + ссылка, спрятанная в слове)
→ отправка (картинка og:image если есть, иначе текст).

Режим ревью: REVIEW=True → черновик уходит в DM Виталию (VITALIY_CHAT_ID),
REVIEW=False → сразу в канал (TELEGRAM_CHANNEL_ID). Первые 2 дня — ревью.

Запуск:
  python3 scripts/curate_channel.py [--dry-run] [--limit N] [--publish]

Секреты на рантайме: TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID из
~/credentials/telegram.env; DEEPSEEK_API_KEY из ~/.hermes/.env. Не выводятся.
"""
import os
import sys
import io
import json
import re
import time
import html
import fcntl
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

BASE = "/home/hermes/alina-body"
TELEGRAM_ENV = os.path.expanduser("~/credentials/telegram.env")
DEEPSEEK_ENV = os.path.expanduser("~/.hermes/.env")
STATE_FILE = f"{BASE}/content/curate_state.json"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
MAX_TOKENS = 1500
MAX_BODY = 900  # потолок текста поста (caption sendPhoto ≤ 1024)

# --- Режим публикации: False = посты сразу в канал @alinabodyfree (True = черновики в DM Виталию) ---
REVIEW = False
VITALIY_CHAT_ID = "1066756284"  # fallback, если нет VITALIY_CHAT_ID в env

# --- Источники: наука/здоровье/ЗОЖ, НЕ фитнес-тренеры ---
SOURCES = [
    ("Reminder (здоровье, RU)", "https://reminder.media/feed"),
    ("ScienceDaily Health (EN)", "https://www.sciencedaily.com/rss/health_medicine.xml"),
    ("ScienceDaily Mind (EN)", "https://www.sciencedaily.com/rss/mind_brain.xml"),
    ("Medical Xpress (EN)", "https://medicalxpress.com/rss-feed/"),
    ("The Conversation Health (EN)", "https://theconversation.com/us/health/articles.atom"),
    ("N+1 (наука, RU)", "https://nplus1.ru/rss"),
    ("Naked Science (RU)", "https://naked-science.ru/rss"),
]

# --- Тема ниши: тренировки / питание / сон / цикл / осанка / менталка ---
TOPIC_TERMS = [
    # RU
    "трениров", "фитнес", "спорт", "упражнен", "мышц", "белок", "белка", "питани",
    "диет", "похуд", "лишн", "вес ", "сон", "стресс", "осанк", "менстру", "цикл",
    "гормон", "сердц", "давлени", "метаболизм", "инсулин", "сахар", "холестерин",
    "сустав", "спин", "поясниц", "растяжк", "йог", "пилатес", "кардио", "силов",
    "вынослив", "восстановлени", "усталост", "энерг", "иммунит", "витамин",
    "кишечн", "микроби", "ожирени", "калори", "завтрак", "перекус", "аппетит",
    "голод", "сытост", "гидратац", "кортизол", "мелатонин", "ходьб", "шаг",
    "пресс", "ягодиц", "жир", "клетчатк", "омега", "тревож", "депресс", "мозг",
    "памят", "концентрац", "самочувств",
    # EN
    "exercise", "workout", "fitness", "muscle", "protein", "nutrition", "diet",
    "weight loss", "obesity", "sleep", "stress", "posture", "menstrual", "cycle",
    "hormone", "heart", "blood pressure", "metabolism", "insulin", "sugar",
    "cholesterol", "joint", "back pain", "stretch", "yoga", "pilates", "cardio",
    "strength", "endurance", "recovery", "fatigue", "energy", "immune", "vitamin",
    "gut", "microbiome", "calorie", "breakfast", "snack", "appetite", "hunger",
    "hydration", "cortisol", "melatonin", "walking", "steps", "fat", "fiber",
    "omega", "anxiety", "depression", "brain", "memory", "wellbeing", "wellness",
]

# --- Псевдонаука / явно не наша тема (жёсткий отсев) ---
BLOCKLIST = [
    "детокс", "гомеопат", "эзотерик", "астролог", "нумеролог", "экстрасенс",
    "магия", "заговор", "биорезонанс", "чакр", "аура", "карм", "квантов",
    "homeopathy", "astrology", "psychic", "quantum",
]

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

ATOM = "{http://www.w3.org/2005/Atom}"
MRSS = "{http://search.yahoo.com/mrss/}"

SYSTEM = (
    "Ты — Алина, тренер по домашним тренировкам и питанию для девушек 18–28. "
    "Ведёшь Telegram-канал. Нашла свежую новость/исследование и пишешь пост от первого лица, "
    "«на ты», как живой человек, который делится реакцией с подругами. "
    "Правила: без длинного тире (—); без канцелярита и копирайтерских штампов; "
    "без ИИ-штампов («важно отметить», «в современном мире», «стоит отметить»); "
    "без хэштегов; без медицинских обещаний и диагнозов; "
    "цифры и факты из источника передавай как есть, ничего не выдумывай. "
    "Не называй сайт/СМИ источника в тексте (не «нашла у Reminder», не «пишет ScienceDaily») — говори от себя: «учёные выяснили», «наткнулась на свежий разбор». "
    "Пиши живо, тепло, по делу. Каждый пост — свежий: другой зачин, другие слова, не повторяй реакции и формулировки между постами."
)

USER_TMPL = (
    "Вот новость/исследование. Напиши пост для канала — 2–3 абзаца, живо, как рассказываешь подруге.\n"
    "Не держись одной схемы: не начинай каждый пост одинаково, не используй одни и те же слова-реакции. В посте должны быть: суть находки и твоя живая реакция (придумай её сам, без штампов); практический вывод для подписчицы — что с этим делать (без медсоветов-диагнозов); одна короткая дословная цитата в кавычках (если дословной фразы нет — перескажи своими словами БЕЗ кавычек, не выдумывай «цитату»).\n"
    "Ссылку на первоисточник спрячь в существительном — названии самого материала (разбор/исследование/обзор/статья/рекомендации — но не одно и то же слово из поста в пост). Оберни его в <<слово>>. Кликабельным должно быть существительное, а НЕ глагол. Слово-ссылка — в первом предложении.\n"
    "Длина 500–700 символов.\n\n"
    "Верни СТРОГО только текст поста (без полей TEXT/ANCHOR, без пояснений). Слово-ссылку оберни в <<...>>. Больше ничего.\n\n"
    "Заголовок: {title}\n"
    "Текст новости:\n{content}\n"
    "Ссылка: {url}"
)


# ---------- env / state ----------

def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def find_deepseek_key():
    for line in open(DEEPSEEK_ENV):
        line = line.strip()
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {"seen": []}


def save_state(st):
    json.dump(st, open(STATE_FILE, "w"), ensure_ascii=False, indent=2)


# ---------- fetch / parse ----------

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=30).read()


def parse_feed(data):
    try:
        root = ET.fromstring(data)
    except Exception:
        return []
    items = []
    nodes = root.findall(".//item") + root.findall(f".//{ATOM}entry")
    for node in nodes:
        title = node.findtext("title") or node.findtext(f"{ATOM}title") or ""
        link = node.findtext("link") or ""
        if not link:
            lk = node.find(f"{ATOM}link")
            if lk is not None:
                link = lk.get("href", "")
        summary = node.findtext("description") or node.findtext(f"{ATOM}summary") or ""
        img = None
        mc = node.find(f"{MRSS}content") or node.find(f"{MRSS}thumbnail")
        if mc is not None:
            img = mc.get("url")
        if not img:
            enc = node.find("enclosure")
            if enc is not None and (enc.get("type") or "").startswith("image"):
                img = enc.get("url")
        title = (title or "").strip()
        link = (link or "").strip()
        if title and link:
            items.append({
                "title": title,
                "link": link,
                "summary": html_to_text(summary),
                "image": img,
            })
    return items


def html_to_text(h):
    if not h:
        return ""
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|div|li|h[1-6])>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n\n", h)
    return h.strip()


def extract_og_image(raw_html):
    for pat in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)',
    ]:
        m = re.search(pat, raw_html, re.I)
        if m:
            return html.unescape(m.group(1))
    return None


def fetch_article(url):
    """Возвращает (текст, og_image) — текст очищенный, og_image URL или None."""
    try:
        raw = fetch(url).decode("utf-8", "ignore")
        img = extract_og_image(raw)
        return html_to_text(raw), img
    except Exception as e:
        print(f"  ⚠️ статья не выкачалась: {type(e).__name__}")
        return None, None


# ---------- отбор ----------

def relevance(entry):
    title = (entry.get("title") or "").lower()
    summary = (entry.get("summary") or "").lower()
    blob = title + " " + summary
    if any(b in blob for b in BLOCKLIST):
        return -1
    score = 0
    for t in TOPIC_TERMS:
        if t in title:
            score += 3
        elif t in summary:
            score += 1
    return score


# ---------- DeepSeek ----------

def deepseek_generate(key, system, user):
    for attempt in range(3):
        try:
            data = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.8,
                "max_tokens": MAX_TOKENS,
            }).encode()
            req = urllib.request.Request(DEEPSEEK_URL, data=data, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
            })
            resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
            content = (resp["choices"][0]["message"]["content"] or "").strip()
            if content:
                return content
            print(f"  ⚠️ DeepSeek вернул пустой ответ (попытка {attempt + 1})")
        except Exception as e:
            print(f"  ⚠️ DeepSeek (попытка {attempt + 1}): {e}")
        time.sleep(3)
    return None


def build_post(key, title, content, url):
    user = USER_TMPL.format(title=title, content=content[:6000], url=url)
    raw = deepseek_generate(key, SYSTEM, user)
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    text, anchor = parse_post(raw)
    if not text:
        print(f"  ⚠️ не распарсить ответ DeepSeek: {raw[:140]}")
        return None
    return {"text": truncate_text(text), "anchor": anchor}


def parse_post(raw):
    # основной формат: слово-ссылка обёрнуто в <<...>> прямо в тексте
    m = re.search(r"<<([^<>]+)>>", raw)
    if m:
        anchor = m.group(1).strip()
        text = re.sub(r"<<[^<>]+>>", "[[LINK]]", raw, count=1)
        return text.strip(), anchor
    # фолбэки на случай, если модель не послушалась
    m2 = re.search(r"TEXT\s*[:：]\s*(.*?)\s*ANCHOR\s*[:：]\s*(.*?)\s*$", raw, re.S)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    jm = re.search(r"\{.*\}", raw, re.S)
    if jm:
        try:
            obj = json.loads(jm.group(0))
            return (obj.get("text") or "").strip(), (obj.get("anchor") or "").strip()
        except Exception:
            pass
    return raw.strip(), ""


def truncate_text(text, limit=MAX_BODY):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for ch in ".!?…":
        idx = cut.rfind(ch)
        if idx >= int(limit * 0.55):
            cut = cut[: idx + 1]
            break
    return cut.strip()


def render_html(text, anchor, url):
    esc_url = html.escape(url, quote=True)
    if "[[LINK]]" in text and anchor:
        before, after = text.split("[[LINK]]", 1)
        link = f'<a href="{esc_url}">{html.escape(anchor)}</a>'
        return html.escape(before) + link + html.escape(after)
    # фолбэк (редко): маркер потерялся — нейтральная ссылка в конце
    return html.escape(text) + f' <a href="{esc_url}">подробнее</a>'


# ---------- Telegram ----------

def tg_api(token, method, params):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    resp = json.loads(urllib.request.urlopen(req, timeout=40).read())
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram error: {resp}")
    return resp


def send_post(token, chat_id, html_text, image_url):
    if image_url:
        jpeg = None
        try:
            raw = fetch(image_url)
            if len(raw) <= 8 * 1024 * 1024:  # до 8 МБ
                jpeg = to_jpeg(raw)
        except Exception as e:
            print(f"  ⚠️ картинка не скачалась ({type(e).__name__})")
        if jpeg:
            try:
                send_photo_file(token, chat_id, jpeg, html_text)
                return "photo"
            except Exception as e:
                print(f"  ⚠️ sendPhoto не прошёл ({e}) — шлю текстом")
    tg_api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
    })
    return "text"


def to_jpeg(data, max_side=1280, quality=82):
    """Конвертирует байты картинки (webp/png/…) в JPEG для sendPhoto."""
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=quality, optimize=True)
    return out.getvalue()


def send_photo_file(token, chat_id, jpeg_bytes, caption):
    """Отправляет фото как локальный файл (multipart) — обходит webp/хотлинк-ограничения."""
    boundary = "alina" + str(int(time.time()))
    buf = io.BytesIO()

    def w(s):
        buf.write(s if isinstance(s, bytes) else s.encode())

    w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n")
    w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n")
    w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n")
    w(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"post.jpg\"\r\n"
      "Content-Type: image/jpeg\r\n\r\n")
    buf.write(jpeg_bytes)
    w(f"\r\n--{boundary}--\r\n")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendPhoto", data=buf.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram error: {resp}")
    return resp


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--publish", action="store_true")  # перекрыть REVIEW и слать в канал
    args = ap.parse_args()

    state = load_state()
    seen = set(state.get("seen", []))

    # 1. Собираем свежие записи из всех фидов
    entries = []
    for name, url in SOURCES:
        try:
            for e in parse_feed(fetch(url)):
                e["source"] = name
                entries.append(e)
        except Exception as e:
            print(f"  ⚠️ фид {name}: {type(e).__name__} {e}")

    # 2. Фильтр: новое + по теме
    fresh = []
    for e in entries:
        if e["link"] in seen:
            continue
        sc = relevance(e)
        if sc >= 4:
            e["score"] = sc
            fresh.append(e)

    if not fresh:
        print("Ничего подходящего и нового — выхожу.")
        return

    fresh.sort(key=lambda e: -e["score"])
    last_source = state.get("last_source")
    # ротация источника: не брать тот же, что в прошлый раз (чтобы картинки не повторялись)
    picked = [e for e in fresh if e["source"] != last_source][: args.limit]
    if len(picked) < args.limit:
        picked += [e for e in fresh if e["source"] == last_source][: args.limit - len(picked)]

    key = find_deepseek_key()
    if not key:
        print("DEEPSEEK_API_KEY не найден в ~/.hermes/.env")
        sys.exit(2)

    env = load_env(TELEGRAM_ENV)
    token = env.get("TELEGRAM_BOT_TOKEN")
    channel = env.get("TELEGRAM_CHANNEL_ID")

    sent = 0
    for e in picked:
        print(f"\n=== {e['source']} (score {e['score']}) ===\n{e['title']}\n{e['link']}")

        text, img = fetch_article(e["link"])
        if not text or len(text) < 300:
            text = e.get("summary") or ""
        if not img:
            img = e.get("image")

        post = build_post(key, e["title"], text, e["link"])
        if not post:
            print("  ❌ не сгенерил пост — пропускаю")
            continue
        html_text = render_html(post["text"], post["anchor"], e["link"])
        print(f"\n--- пост ---\n{post['text']}\n(anchor: {post['anchor']} | картинка: {bool(img)})")

        if args.dry_run:
            print("\n[dry-run] ничего не отправлено, состояние не тронуто.")
            continue

        publish = args.publish or not REVIEW
        if publish:
            target = channel
        else:
            target = env.get("VITALIY_CHAT_ID") or VITALIY_CHAT_ID

        if not token or not target:
            print("  ❌ нет токена/чата — пропускаю отправку")
            continue

        mode = send_post(token, target, html_text, img)
        if not publish:
            tg_api(token, "sendMessage", {"chat_id": target, "text": "🔍 <b>На ревью (куратор канала)</b>", "parse_mode": "HTML"})
        print(f"  ✅ отправлено ({mode}) -> {target}")
        seen.add(e["link"])
        state["last_source"] = e["source"]
        sent += 1

    if not args.dry_run:
        state["seen"] = list(seen)[-500:]
        state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_state(state)
    print(f"\nОтправлено: {sent}")


if __name__ == "__main__":
    # простой лок, чтобы не пересекаться с параллельным прогоном
    try:
        lock = open("/tmp/curate_channel.lock", "w")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Другой запуск curate_channel работает — выхожу")
        sys.exit(0)
    main()
