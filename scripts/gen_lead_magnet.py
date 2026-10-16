#!/usr/bin/env python3
"""Генерирует лид-магниты (чеклисты) и заливает в Supabase.

Добавлять новые: дописать в MAGNETS (имя файла, заголовок, подзаголовок, пункты).
Каждый пункт: (название, правая метка, подсказка). Правую метку можно оставить пустой.
"""
import io, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)

AVATAR = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/angles/portrait-front.jpg"

MAGNETS = [
    {
        "file": "glutes-checklist.jpg",
        "title": "5 упражнений на ягодицы",
        "subtitle": "мини-чеклист · дома · 15 минут",
        "items": [
            ("Приседания", "3 × 12", "колени над носками, спина ровная"),
            ("Ягодичный мостик", "3 × 15", "сжимайте ягодицы, пауза вверху"),
            ("Выпады назад", "3 × 10 на ногу", "корпус ровно, колено не вперёд"),
            ("Отведение ноги в сторону", "3 × 15", "без наклона корпуса"),
            ("Махи ногой назад", "3 × 15", "без прогиба в пояснице"),
        ],
    },
    {
        "file": "warmup-checklist.jpg",
        "title": "Разминка за 5 минут",
        "subtitle": "перед тренировкой · обязательно",
        "items": [
            ("Вращение головы и плеч", "1 мин", "медленно, без рывков"),
            ("Круговые движения руками", "30 сек", "вперёд и назад"),
            ("Наклоны корпуса в стороны", "30 сек", "тянитесь за рукой"),
            ("Приседания без веса", "1 мин", "колени над носками"),
            ("Подъём коленей на месте", "1 мин", "спина ровная"),
            ("Лёгкая растяжка", "1 мин", "до комфорта, без боли"),
        ],
    },
    {
        "file": "squat-mistakes.jpg",
        "title": "3 ошибки в приседаниях",
        "subtitle": "проверьте технику",
        "items": [
            ("Колени заваливаются внутрь", "❌", "колени по направлению носков"),
            ("Пятки отрываются от пола", "❌", "вес на пятках, толчок через них"),
            ("Спина округляется", "❌", "грудь вперёд, спина ровная"),
        ],
    },
]


def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def make_magnet(title, subtitle, items, fname):
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    try:
        ph = urllib.request.urlopen(AVATAR, timeout=30).read()
        av = Image.open(io.BytesIO(ph)).convert("RGB").resize((220, 220))
        mask = Image.new("L", (220, 220), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
        img.paste(av, (W // 2 - 110, 90), mask)
    except Exception:
        pass

    d.text((W // 2, 350), "ALINA BODY", font=font(40), fill=ACCENT, anchor="mm")
    d.text((W // 2, 415), title, font=font(56), fill=TEXT, anchor="mm")
    d.text((W // 2, 480), subtitle, font=font(32, False), fill=MUTED, anchor="mm")
    d.line([(90, 545), (W - 90, 545)], fill=ACCENT, width=4)

    step = min(128, (1180 - 610) // max(len(items), 1))
    y = 610
    for i, (name, right, cue) in enumerate(items, 1):
        cy = y + 22
        d.ellipse([69, cy - 26, 121, cy + 26], fill=ACCENT)
        d.text((95, cy), str(i), font=font(32), fill=(255, 255, 255), anchor="mm")
        d.text((145, y), name, font=font(38), fill=TEXT, anchor="lm")
        if right:
            d.text((W - 95, y), right, font=font(32), fill=ACCENT, anchor="rm")
        d.text((145, y + 50), cue, font=font(27, False), fill=MUTED, anchor="lm")
        y += step

    d.rectangle([90, 1180, W - 90, 1280], fill=ACCENT)
    d.text((W // 2, 1208), "Больше упражнений и программ", font=font(32), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1252), "alina-body.fitness", font=font(30), fill=(255, 255, 255), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]

for m in MAGNETS:
    data = make_magnet(m["title"], m["subtitle"], m["items"], m["file"])
    url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{m['file']}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()
    print("OK:", url.replace("/object/", "/object/public/"))
