#!/usr/bin/env python3
"""Генерирует брендированные карточки рецептов (JPG) из /tmp/recipes.json и заливает в Supabase."""
import os, io, json, re, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
BOX = (245, 229, 233)

W = 1080
M = 80  # поля

def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)

def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        test = (cur + " " + w).strip()
        if d.textlength(test, font=f) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def split_items(s):
    # «Ингредиенты…:» → список пунктов (разделяем по заглавной)
    s = re.sub(r"^Ингредиенты[^:]*:\s*", "", s).strip()
    parts = re.split(r"(?<=[а-яё0-9)]) (?=[А-ЯЁA-Z])", s)
    return [p.strip() for p in parts if p.strip()]

def split_steps(s):
    s = re.sub(r"^Приготовление:\s*", "", s).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if p.strip()]

def make_card(recipe, idx):
    name = recipe["name"]
    kbzhu = re.sub(r"^КБЖУ[^:]*:\s*", "", recipe["kbzhu"]).strip()
    ingredients = split_items(recipe["ingredients"])
    steps = split_steps(recipe["method"])

    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M

    title_f = font(46); lbl_f = font(26, False); kbzhu_f = font(28)
    sec_f = font(32); txt_f = font(29, False); logo_f = font(36); foot_f = font(24, False)

    title_lines = wrap(d0, name.upper(), title_f, max_w)
    kbzhu_lines = wrap(d0, kbzhu, kbzhu_f, max_w)
    ingr_lines = []
    for it in ingredients:
        ingr_lines += wrap(d0, "• " + it, txt_f, max_w)
    step_lines = []
    for i, st in enumerate(steps, 1):
        step_lines += wrap(d0, f"{i}. {st}", txt_f, max_w)

    # высота
    H = 160  # шапка
    H += len(title_lines) * 60 + 20
    H += len(kbzhu_lines) * 40 + 30
    H += 60  # «Ингредиенты» заголовок
    H += len(ingr_lines) * 42 + 20
    H += 60  # «Приготовление» заголовок
    H += len(step_lines) * 42 + 30
    H += 130  # футер

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    y = 70
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 55
    d.text((W // 2, y), "ПП-РЕЦЕПТ", font=lbl_f, fill=MUTED, anchor="mm"); y += 40
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3); y += 40

    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 60
    y += 10

    if kbzhu_lines:
        box_h = len(kbzhu_lines) * 40 + 24
        d.rounded_rectangle([M, y - 12, W - M, y - 12 + box_h], radius=18, fill=BOX)
        for ln in kbzhu_lines:
            d.text((M + 24, y), ln, font=kbzhu_f, fill=ACCENT, anchor="lm"); y += 40
        y += 24

    y += 20
    d.text((M, y), "ИНГРЕДИЕНТЫ", font=sec_f, fill=ACCENT, anchor="lm"); y += 52
    for ln in ingr_lines:
        d.text((M, y), ln, font=txt_f, fill=TEXT, anchor="lm"); y += 42
    y += 20

    d.text((M, y), "ПРИГОТОВЛЕНИЕ", font=sec_f, fill=ACCENT, anchor="lm"); y += 52
    for ln in step_lines:
        d.text((M, y), ln, font=txt_f, fill=TEXT, anchor="lm"); y += 42
    y += 10

    d.line([(M, y), (W - M, y)], fill=ACCENT, width=2); y += 24
    d.text((W // 2, y), "Больше рецептов и программ — alina-body.fitness", font=foot_f, fill=MUTED, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()

# --- заливка ---
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]

recipes = json.load(open("/tmp/recipes.json"))
urls = []
for i, r in enumerate(recipes, 1):
    fname = f"recipe-{i:02d}.jpg"
    data = make_card(r, i)
    url = f"{SUPA}/storage/v1/object/alina-media/recipes/{fname}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()
    pub = url.replace("/object/", "/object/public/")
    urls.append({"name": r["name"], "category": r["category"], "url": pub})
    print(f"OK {i:02d} {r['name'][:40]}")

json.dump(urls, open("/tmp/recipe_urls.json", "w"), ensure_ascii=False, indent=2)
print("готово:", len(urls))
