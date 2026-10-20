#!/usr/bin/env python3
"""Плотная инфографика-карточка: тонкая иллюстрация + максимум текста."""
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
ACCENT2 = (88, 168, 130)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
WARN = (180, 130, 90)
BOX = (245, 229, 233)
WARNBOX = (255, 240, 228)

ILL = "/home/hermes/alina-body/content/demo/liver-illustration.jpg"
OUT = "/home/hermes/alina-body/content/demo/liver-card-dense.jpg"


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


W = 1080
M = 64
max_w = W - 2 * M
d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))

# иллюстрация — тонкая полоса 1080×170
ill = Image.open(ILL).convert("RGB")
tw, th = ill.size
scale = W / tw
ill = ill.resize((W, int(th * scale)), Image.LANCZOS)
ill = ill.crop((0, int(ill.size[1] * 0.2), W, int(ill.size[1] * 0.2) + 170))

title_f = font(50)
tag_f = font(24, False)
logo_f = font(28)
pt_f = font(30, False)
num_f = font(30)
sec_f = font(32)
disc_f = font(24)

title_lines = wrap(d0, "ЗДОРОВЬЕ ПЕЧЕНИ".upper(), title_f, max_w)

points = [
    ("ПИТАНИЕ", [
        "5–6 приёмов в день, порция ~200 г",
        "Соль ≤ 5 г (80% — «скрытая» в готовых продуктах)",
        "Варка, пар, тушение — без жареного и копчёного",
        "Вода, морсы, некрепкий чай",
        "Фастфуд и снеки → фрукты, овощи",
    ]),
    ("ОБРАЗ ЖИЗНИ", [
        "Ежедневное движение: ходьба, бег, плавание",
        "Без алкоголя и курения, без лекарств без назначения",
    ]),
    ("БАДЫ", [
        "Расторопша (силимарин) 70–80 мг · артишок (цинарин) 300 мг · куркума (куркумин), лучше с пиперином",
    ]),
]
warn = "К врачу: тяжесть/боль в правом подреберье, желтушность кожи, постоянная слабость → гепатолог"

# высота
H = 170 + 90  # полоса + шапка
H += len(title_lines) * 60
for sec, items in points:
    H += 52 + len(items) * 44
H += 46
H += 60 + len(wrap(d0, warn, pt_f, max_w - 56)) * 44
H += 60 + 70

img = Image.new("RGB", (W, H), BG)
img.paste(ill, (0, 0))
d = ImageDraw.Draw(img)
d.line([(0, 170), (W, 170)], fill=ACCENT, width=4)

y = 200
d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 34
d.text((W // 2, y), "ГАЙД · ШПАРГАЛКА", font=tag_f, fill=MUTED, anchor="mm"); y += 44

for ln in title_lines:
    d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 60
y += 6

n = 1
for sec, items in points:
    d.text((M, y), sec, font=sec_f, fill=ACCENT2, anchor="lm"); y += 48
    for it in items:
        d.text((M, y), f"{n}.", font=num_f, fill=ACCENT, anchor="lm")
        for ln in wrap(d0, it, pt_f, max_w - 48):
            d.text((M + 44, y), ln, font=pt_f, fill=TEXT, anchor="lm"); y += 44
        n += 1
    y += 8

y += 12
warn_lines = wrap(d0, "⚠ " + warn, pt_f, max_w - 56)
box_h = len(warn_lines) * 44 + 28
d.rounded_rectangle([M, y - 10, W - M, y - 10 + box_h], radius=14, fill=WARNBOX)
for ln in warn_lines:
    d.text((M + 28, y + 6), ln, font=pt_f, fill=WARN, anchor="lm"); y += 44
y += box_h - 4

d.text((W // 2, y), "Перед применением БАД — консультация со специалистом.", font=disc_f, fill=WARN, anchor="mm"); y += 40
d.text((W // 2, y), "alina-body.fitness  ·  t.me/alinabodyfree", font=disc_f, fill=MUTED, anchor="mm")

img.save(OUT, "JPEG", quality=90, optimize=True, progressive=True)
print("OK:", OUT, img.size)
