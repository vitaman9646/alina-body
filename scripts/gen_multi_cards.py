#!/usr/bin/env python3
"""Мульти-карточки: одна секция на карточку, маленькая иллюстрация инлайн + плотный текст."""
import os, io, json, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = "https://api.kie.ai"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG = (253, 247, 241); ACCENT = (214, 122, 140); ACCENT2 = (88, 168, 130)
TEXT = (56, 44, 50); MUTED = (130, 108, 112); WARN = (180, 130, 90)
OUT = "/home/hermes/alina-body/content/demo"


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def gen(key, prompt, out, aspect="1:1"):
    inp = {"prompt": prompt, "aspect_ratio": aspect, "resolution": "1K", "output_format": "jpg"}
    req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": "nano-banana-2", "input": inp}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        print("createTask:", json.dumps(r)[:200]); return None
    task = r["data"]["taskId"]
    for _ in range(70):
        time.sleep(6)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/jobs/recordInfo?taskId={task}",
            headers={"Authorization": "Bearer " + key}), timeout=30).read())
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            urllib.request.urlretrieve(urls[0], out); return out
        if d.get("state") == "fail":
            print("FAIL", json.dumps(d)[:200]); return None
    return None


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


def build_card(title, tag, ill_path, points, out_path, img_w=230):
    W = 1080
    M = 64
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M
    title_f = font(50); tag_f = font(24, False); logo_f = font(28)
    pt_f = font(30, False); num_f = font(30); sec_f = font(32); disc_f = font(24)

    # иллюстрация — маленькая, инлайн (слева)
    ill = Image.open(ill_path).convert("RGB").resize((img_w, img_w), Image.LANCZOS)
    mask = Image.new("L", (img_w, img_w), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img_w, img_w), radius=28, fill=255)
    ill.putalpha(mask)

    # высота: title + точки (справа от иллюстрации)
    txt_w = max_w - img_w - 36
    title_lines = wrap(d0, title.upper(), title_f, max_w)
    pt_lines = []
    for it in points:
        pt_lines += wrap(d0, it, pt_f, txt_w)
    H = 150 + len(title_lines) * 60 + 20
    H += max(img_w + 16, len(pt_lines) * 46 + 40)
    H += 90  # футер + дисклеймер

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    y = 60
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 36
    d.text((W // 2, y), tag, font=tag_f, fill=MUTED, anchor="mm"); y += 40
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3); y += 28
    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 60
    y += 10

    # иллюстрация слева + точки справа
    ill_y = y
    img.paste(ill, (M, ill_y), ill)
    ty = ill_y + 4
    for i, it in enumerate(points, 1):
        for j, ln in enumerate(wrap(d0, it, pt_f, txt_w)):
            x = M + img_w + 36
            if j == 0:
                d.text((x - 32, ty), f"{i}.", font=num_f, fill=ACCENT, anchor="rm")
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            else:
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            ty += 46
    y = max(ill_y + img_w, ty) + 20

    d.line([(M, y), (W - M, y)], fill=ACCENT, width=2); y += 20
    d.text((W // 2, y), "Перед применением БАД — консультация со специалистом.", font=disc_f, fill=WARN, anchor="mm"); y += 40
    d.text((W // 2, y), "alina-body.fitness  ·  t.me/alinabodyfree", font=disc_f, fill=MUTED, anchor="mm")

    img.convert("RGB").save(out_path, "JPEG", quality=90, optimize=True, progressive=True)
    return out_path


if __name__ == "__main__":
    key = load_key()
    os.makedirs(OUT, exist_ok=True)

    # 2 иллюстрации (маленькие, 1:1)
    ill1 = gen(key, "Flat minimal illustration of a healthy meal bowl with vegetables and grains, soft pastel colors, cream background, no text, no people, wellness food flat style", f"{OUT}/food.jpg")
    ill2 = gen(key, "Flat minimal illustration of herbal supplement capsules with green herbs and a plant, soft pastel colors, cream background, no text, no people, wellness flat style", f"{OUT}/herbs.jpg")
    if not ill1 or not ill2:
        raise SystemExit("иллюстрации не сгенерились")

    build_card("Питание для печени", "ГАЙД · ЧАСТЬ 1/4", ill1, [
        "5–6 приёмов в день, порция ~200 г",
        "Соль ≤ 5 г (80% — «скрытая» в готовом)",
        "Варка, пар, тушение — без жареного",
        "Вода, морсы, некрепкий чай",
        "Фастфуд → фрукты, овощи, мюсли без сахара",
    ], f"{OUT}/card-pitanie.jpg")

    build_card("БАДы для печени", "ГАЙД · ЧАСТЬ 3/4", ill2, [
        "Расторопша (силимарин) 70–80 мг — поддержка клеток",
        "Артишок (цинарин) 300 мг — желчегонное",
        "Куркума (куркумин) — защита, лучше с пиперином",
    ], f"{OUT}/card-bady.jpg")

    print("готово:", os.listdir(OUT))
