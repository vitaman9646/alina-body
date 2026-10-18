#!/usr/bin/env python3
"""Лид-магнит «Здоровье печени» — брендированные карточки (JPG) → Supabase.

Из материала «ПЕЧЕНЬ» взяты только безопасные факты: привычки питания и образа
жизни + БАДы (расторопша/артишок/куркума). Вырезано: рецептурный препарат УДХК,
диагностика (УЗИ/КТ/МРТ), формулировки «чистка»/«выводит токсины». Вместо
диагностики — карточка «Когда к врачу».

Использование: .venv-tts/bin/python scripts/gen_liver_cards.py
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
WARN = (180, 130, 90)

W = 1080
M = 80
DISC_BAD = "Перед применением БАД проконсультируйтесь со специалистом."


def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


CARDS = [
    {
        "file": "liver-1-pitanie.jpg",
        "tag": "ПИТАНИЕ",
        "title": "Питание для печени",
        "disclaimer": None,
        "blocks": [
            ("ПРИВЫЧКИ", [
                "5–6 приёмов пищи в день, порция ~200 г",
                "Соль не больше 5 г в день (помни про «скрытую» соль)",
                "Готовка: варка, пар, тушение — без жареного и копчёного",
                "Достаточно воды и жидкости",
                "Фастфуд и снеки → фрукты, овощи, мюсли без сахара",
            ]),
        ],
    },
    {
        "file": "liver-2-lifestyle.jpg",
        "tag": "ОБРАЗ ЖИЗНИ",
        "title": "Образ жизни",
        "disclaimer": None,
        "blocks": [
            ("ПРИВЫЧКИ", [
                "Ежедневное движение: ходьба, бег, плавание, велосипед",
                "Исключить алкоголь и курение",
                "Не злоупотреблять лекарствами без назначения",
            ]),
        ],
    },
    {
        "file": "liver-3-rastoropsha.jpg",
        "tag": "БАДЫ",
        "title": "Расторопша",
        "disclaimer": DISC_BAD,
        "blocks": [
            ("ЧТО ДЕЛАЕТ", [
                "Силимарин — поддерживает клетки печени",
                "Поддержка при токсических нагрузках (алкоголь, лекарства, еда)",
            ]),
            ("ДОЗА", ["70–80 мг экстракта силимарина"]),
        ],
    },
    {
        "file": "liver-4-artishok.jpg",
        "tag": "БАДЫ",
        "title": "Артишок",
        "disclaimer": DISC_BAD,
        "blocks": [
            ("ЧТО ДЕЛАЕТ", [
                "Цинарин — мягкое желчегонное действие",
                "Поддерживает холестериновый обмен",
            ]),
            ("ДОЗА", ["300 мг"]),
        ],
    },
    {
        "file": "liver-5-kurkuma.jpg",
        "tag": "БАДЫ",
        "title": "Куркума",
        "disclaimer": DISC_BAD,
        "blocks": [
            ("ЧТО ДЕЛАЕТ", [
                "Куркумин — защита и поддержка печени",
                "Мягкое желчегонное действие",
            ]),
            ("СОВЕТ", ["Лучше с пиперином (экстракт чёрного перца) — улучшает усвоение"]),
        ],
    },
    {
        "file": "liver-6-k-vrachu.jpg",
        "tag": "ВАЖНО",
        "title": "Когда к врачу",
        "disclaimer": None,
        "blocks": [
            ("ИДИ К ВРАЧУ, ЕСЛИ", [
                "Тяжесть или боли в правом подреберье",
                "Желтушность кожи или белков глаз",
                "Постоянная слабость, тошнота",
            ]),
            ("КУДА", ["К гепатологу или гастроэнтерологу — без самолечения"]),
        ],
    },
]


def make_card(card):
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M

    tag_f = font(26, False)
    title_f = font(48)
    sec_f = font(30)
    txt_f = font(29, False)
    logo_f = font(36)
    foot_f = font(24, False)
    disc_f = font(27)

    title_lines = wrap(d0, card["title"].upper(), title_f, max_w)
    all_lines = []
    for sec, items in card["blocks"]:
        all_lines.append(("sec", sec))
        for it in items:
            all_lines.append(("txt", it))

    H = 150
    H += len(title_lines) * 62 + 16
    H += 46
    for kind, t in all_lines:
        H += 56 if kind == "sec" else 46
    H += 30
    if card["disclaimer"]:
        H += 90
    H += 110

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    y = 70
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 55
    d.text((W // 2, y), card["tag"], font=tag_f, fill=MUTED, anchor="mm"); y += 38
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3); y += 36

    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 62
    y += 10

    for kind, t in all_lines:
        if kind == "sec":
            d.text((M, y), t, font=sec_f, fill=ACCENT, anchor="lm"); y += 56
        else:
            for ln in wrap(d0, "• " + t, txt_f, max_w):
                d.text((M + 12, y), ln, font=txt_f, fill=TEXT, anchor="lm"); y += 46
    y += 14

    d.line([(M, y), (W - M, y)], fill=ACCENT, width=2); y += 22
    if card["disclaimer"]:
        disc_lines = wrap(d0, card["disclaimer"], disc_f, max_w)
        box_h = len(disc_lines) * 40 + 24
        d.rounded_rectangle([M, y - 8, W - M, y - 8 + box_h], radius=16, fill=BOX)
        for ln in disc_lines:
            d.text((W // 2, y + 12), ln, font=disc_f, fill=WARN, anchor="mm"); y += 40
        y += box_h - 16

    d.text((W // 2, y), "Больше программ и гайдов — alina-body.fitness", font=foot_f, fill=MUTED, anchor="mm")

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

urls = []
for c in CARDS:
    data = make_card(c)
    url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{c['file']}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()
    pub = url.replace("/object/", "/object/public/")
    urls.append({"title": c["title"], "url": pub})
    print("OK:", c["file"])

json.dump(urls, open("/tmp/liver_urls.json", "w"), ensure_ascii=False, indent=2)
print("готово:", len(urls))
