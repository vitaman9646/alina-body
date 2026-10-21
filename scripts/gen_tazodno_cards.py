#!/usr/bin/env python3
"""Карточки лид-магнита «Тазовое дно» — инфографика с мультяшной Алиной слева.

Компоновка: шапка (лого/тег/заголовок) → иллюстрация слева (rounded) + пункты
справа → дисклеймер-бокс → футер CTA. Локально + заливка в Supabase.
"""
import os, io, json, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
BOX = (245, 229, 233)
WARN = (180, 108, 90)

W = 1080
M = 70
ILL_W = 340
ILL_H = 453          # 3:4
OUT = "/home/hermes/alina-body/alina-media/lead-magnet"

DISC = "Это осознавание и движение, не лечение. При недержании, боли, пролапсе — к гинекологу / урологу."
FOOT = "Больше практик и гайдов — alina-body.fitness"

CARDS = [
    {
        "file": "tazodno-1-dva-treugolnika.jpg",
        "tag": "ОСОЗНАВАНИЕ",
        "title": "Тазовое дно: два треугольника",
        "ill": "/home/hermes/alina-body/alina-media/cartoon/tazodno-anatomy.jpg",
        "points": [
            "Передний: лобковая кость сверху, седалищные бугры снизу — здесь уретра и влагалище.",
            "Задний: копчик снизу, седалищные бугры сверху — здесь анус, самая сильная мышца (сфинктер).",
            "Заднюю чувствуешь легко — «сдерживаешь газы».",
            "Передняя чаще «спит» — её почти не ощущаешь.",
            "Обычное «сожми» включает только заднюю часть.",
        ],
    },
    {
        "file": "tazodno-2-perekaty.jpg",
        "tag": "ДВИЖЕНИЕ",
        "title": "Перекаты таза",
        "ill": "/home/hermes/alina-body/alina-media/cartoon/lite-pose1.jpg",
        "points": [
            "Лёжа на спине, колени согнуты, стопы на ширине таза.",
            "Копчик вверх → поясница к полу → подбородок вверх.",
            "Копчик вниз → поясница вверх → подбородок к груди.",
            "Импульс — от таза, остальной скелет просто отвечает.",
            "Медленно, без задержки дыхания, амплитуда в зоне комфорта.",
        ],
    },
    {
        "file": "tazodno-3-napryazhenie.jpg",
        "tag": "БАЛАНС",
        "title": "Напряжение ↔ расслабление",
        "ill": "/home/hermes/alina-body/alina-media/cartoon/tazodno-relax.jpg",
        "points": [
            "После каждого сокращения — полное расслабление.",
            "Слабость и постоянный зажим — обе проблемы.",
            "Зажим даёт тазовую боль и дискомфорт.",
            "«Перестаралась» = не можешь отпустить, напрягаешься без команды.",
            "Сократил → несколько свободных вдохов → отпустил.",
        ],
    },
    {
        "file": "tazodno-4-dyhanie.jpg",
        "tag": "ДЫХАНИЕ",
        "title": "Дыхание и тазовое дно",
        "ill": "/home/hermes/alina-body/alina-media/cartoon/lite-pose2.jpg",
        "points": [
            "Выдох облегчает сокращение.",
            "Вдох — момент расслабления: дыши вниз живота.",
            "Расслабь челюсть, язык, горло — дыхание свободнее.",
            "Дыхание не задерживай.",
            "Найди своё: на вдохе или на выдохе тебе легче?",
        ],
    },
]


def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(card):
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    logo_f = font(34)
    tag_f = font(25, False)
    title_f = font(46)
    txt_f = font(28, False)
    disc_f = font(26)
    foot_f = font(24, False)

    # заголовок
    title_lines = wrap(d0, card["title"].upper(), title_f, W - 2 * M)

    # текстовая колонка справа
    col_w = W - 2 * M - ILL_W - 36   # 1080-140-340-36 = 564
    txt_h = 0
    wrapped_points = []
    for p in card["points"]:
        lns = wrap(d0, p, txt_f, col_w - 34)
        wrapped_points.append(lns)
        txt_h += len(lns) * 42 + 12

    body_h = max(ILL_H, txt_h) + 20
    # высота карточки
    H = 70 + 52 + 36 + 30 + len(title_lines) * 58 + 24 + body_h + 40
    if DISC:
        disc_lines = wrap(d0, DISC, disc_f, W - 2 * M)
        H += len(disc_lines) * 38 + 28
    H += 90

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    y = 62
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 50
    d.text((W // 2, y), card["tag"], font=tag_f, fill=MUTED, anchor="mm"); y += 34
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3); y += 28
    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 58
    y += 20

    # иллюстрация слева
    try:
        ph = Image.open(card["ill"]).convert("RGB")
        ph = ph.resize((ILL_W, ILL_H))
        mask = Image.new("L", (ILL_W, ILL_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, ILL_W, ILL_H), radius=26, fill=255)
        img.paste(ph, (M, y), mask)
    except Exception as e:
        print("  иллюстрация не загрузилась:", e)

    # пункты справа
    tx = M + ILL_W + 36
    ty = y + 6
    for i, lns in enumerate(wrapped_points, 1):
        d.ellipse([tx - 2, ty + 4, tx + 26, ty + 32], fill=ACCENT)
        d.text((tx + 12, ty + 18), str(i), font=font(20), fill=(255, 255, 255), anchor="mm")
        for ln in lns:
            d.text((tx + 42, ty + 6), ln, font=txt_f, fill=TEXT, anchor="lm")
            ty += 42
        ty += 12
    y += body_h + 8

    # дисклеймер
    if DISC:
        d.line([(M, y), (W - M, y)], fill=ACCENT, width=2); y += 18
        box_h = len(disc_lines) * 38 + 24
        d.rounded_rectangle([M, y, W - M, y + box_h], radius=16, fill=BOX)
        for i, ln in enumerate(disc_lines):
            d.text((W // 2, y + 14 + i * 38), ln, font=disc_f, fill=WARN, anchor="mm")
        y += box_h + 20

    d.text((W // 2, y), FOOT, font=foot_f, fill=MUTED, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]

os.makedirs(OUT, exist_ok=True)
urls = []
for c in CARDS:
    data = make_card(c)
    local = os.path.join(OUT, c["file"])
    with open(local, "wb") as f:
        f.write(data)
    url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{c['file']}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()
    pub = url.replace("/object/", "/object/public/")
    urls.append({"title": c["title"], "url": pub, "local": local})
    print("OK:", c["file"])

json.dump(urls, open("/tmp/tazodno_urls.json", "w"), ensure_ascii=False, indent=2)
print("готово карточек:", len(urls))
