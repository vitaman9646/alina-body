#!/usr/bin/env python3
"""Обучающие картинки: фото упражнения (из курса) + текст-подсказка поверх. Загрузка в Supabase social/."""
import os, io, urllib.request
from PIL import Image, ImageDraw, ImageFont

SUPA = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k] = v.strip()
SUPA_URL = env["SUPABASE_URL"].rstrip("/"); SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]

CARDS = [
    ("squat", "Приседания", "Спина ровная · колени над носками · толчок пятками"),
    ("glute-bridge", "Ягодичный мостик", "Сжимайте ягодицы вверху · пауза 1–2 секунды"),
    ("plank", "Планка", "Тело — ровная линия · не провисайте в пояснице"),
    ("warmup", "Разминка", "3–5 минут перед каждой тренировкой"),
]

def upload(name, data):
    url = f"{SUPA_URL}/storage/v1/object/alina-media/social/{name}"
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY,
                 "Content-Type": "image/jpeg", "x-upsert": "true"})
    urllib.request.urlopen(req, timeout=60).read()

for slug, title, cue in CARDS:
    src = urllib.request.urlopen(f"{SUPA}/course/{slug}.jpg", timeout=60).read()
    im = Image.open(io.BytesIO(src)).convert("RGB")
    im.thumbnail((1200, 1600))
    W, H = im.size
    draw = ImageDraw.Draw(im, "RGBA")

    # нижняя плашка с подсказкой
    bar_h = int(H * 0.18)
    draw.rectangle([(0, H - bar_h), (W, H)], fill=(20, 18, 16, 205))

    # заголовок
    tfont = ImageFont.truetype(FONT, int(W * 0.085))
    cfont = ImageFont.truetype(FONT, int(W * 0.048))
    draw.text((int(W*0.05), H - bar_h + int(H*0.015)), title, font=tfont, fill=(255, 255, 255, 255))
    draw.text((int(W*0.05), H - bar_h + int(H*0.095)), cue, font=cfont, fill=(255, 240, 235, 235))

    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    data = buf.getvalue()
    upload(f"edu_{slug}.jpg", data)
    print(f"OK edu_{slug}.jpg ({len(data)//1024}KB)")

print("Готово: 4 обучающих картинки")
