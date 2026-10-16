#!/usr/bin/env python3
"""Генерирует лид-магнит «5 упражнений на ягодицы» (чеклист-картинка) и заливает в Supabase."""
import io, os, json, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)       # cream
ACCENT = (214, 122, 140)   # soft pink
TEXT = (56, 44, 50)        # dark
MUTED = (130, 108, 112)

W, H = 1080, 1350
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)

# --- header: круглое фото Алины + заголовок ---
try:
    ph = urllib.request.urlopen(
        "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/angles/portrait-front.jpg",
        timeout=30).read()
    av = Image.open(io.BytesIO(ph)).convert("RGB")
    av = av.resize((220, 220))
    mask = Image.new("L", (220, 220), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
    img.paste(av, (W // 2 - 110, 90), mask)
except Exception as e:
    print("фото не загрузилось:", e)

# заголовок
d.text((W // 2, 350), "ALINA BODY", font=font(40), fill=ACCENT, anchor="mm")
d.text((W // 2, 415), "5 упражнений на ягодицы", font=font(58), fill=TEXT, anchor="mm")
d.text((W // 2, 480), "мини-чеклист · дома · 15 минут", font=font(34, False), fill=MUTED, anchor="mm")

# --- разделитель ---
d.line([(90, 545), (W - 90, 545)], fill=ACCENT, width=4)

# --- пункты ---
items = [
    ("Приседания", "3 × 12", "колени над носками, спина ровная"),
    ("Ягодичный мостик", "3 × 15", "сжимайте ягодицы, пауза вверху"),
    ("Выпады назад", "3 × 10 на ногу", "корпус ровно, колено не уходит вперёд"),
    ("Отведение ноги в сторону", "3 × 15", "без наклона корпуса"),
    ("Махи ногой назад", "3 × 15", "без прогиба в пояснице"),
]
y = 610
for i, (name, reps, cue) in enumerate(items, 1):
    # номер в кружке
    cx, cy = 95, y + 22
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=ACCENT)
    d.text((cx, cy), str(i), font=font(34), fill=(255, 255, 255), anchor="mm")
    # название + подходы
    d.text((145, y), name, font=font(40), fill=TEXT, anchor="lm")
    d.text((W - 95, y), reps, font=font(34), fill=ACCENT, anchor="rm")
    # подсказка
    d.text((145, y + 52), cue, font=font(28, False), fill=MUTED, anchor="lm")
    y += 128

# --- футер ---
d.rectangle([90, 1180, W - 90, 1280], fill=ACCENT)
d.text((W // 2, 1208), "Полная программа (7 дней)", font=font(34), fill=(255, 255, 255), anchor="mm")
d.text((W // 2, 1252), "alina-body.fitness/tonus-doma", font=font(30), fill=(255, 255, 255), anchor="mm")

buf = io.BytesIO()
img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
data = buf.getvalue()

# --- заливка в Supabase ---
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA = env["SUPABASE_URL"].rstrip("/")
SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/glutes-checklist.jpg"
req = urllib.request.Request(url, data=data, method="POST",
    headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
urllib.request.urlopen(req, timeout=60).read()
print("OK:", url)
print("public:", url.replace("/object/", "/object/public/"))
