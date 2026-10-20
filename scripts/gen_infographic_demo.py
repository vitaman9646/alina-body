#!/usr/bin/env python3
"""Демо нового гибрид-формата: инфографика-карточка (иллюстрация + текст)."""
import os, io, json, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = "https://api.kie.ai"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
ACCENT2 = (88, 168, 130)   # зелёный для акцентов «польза»
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
WARN = (180, 130, 90)


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def gen_illustration(key, prompt, out, aspect="16:9"):
    inp = {"prompt": prompt, "aspect_ratio": aspect, "resolution": "1K", "output_format": "jpg"}
    req = urllib.request.Request(
        f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": "nano-banana-2", "input": inp}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        print("createTask err:", json.dumps(r)[:300]); return None
    task = r["data"]["taskId"]
    for _ in range(60):
        time.sleep(6)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/jobs/recordInfo?taskId={task}",
            headers={"Authorization": "Bearer " + key}), timeout=30).read())
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            urllib.request.urlretrieve(urls[0], out)
            return out
        if d.get("state") == "fail":
            print("FAIL:", json.dumps(d)[:300]); return None
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
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_card(illustration_path, title, tag, points, stat, disclaimer, out):
    W = 1080
    M = 70
    # иллюстрация сверху (обрезка под 1080×560)
    ill = Image.open(illustration_path).convert("RGB")
    tw, th = ill.size
    scale = W / tw
    ill = ill.resize((W, int(th * scale)), Image.LANCZOS)
    ill = ill.crop((0, 0, W, 560))

    # текстовая панель
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M
    title_f = font(52)
    tag_f = font(26, False)
    txt_f = font(32, False)
    logo_f = font(30)
    disc_f = font(26)
    stat_f = font(34)

    title_lines = wrap(d0, title.upper(), title_f, max_w)
    pt_lines = []
    for p in points:
        pt_lines += wrap(d0, p, txt_f, max_w - 56)
    stat_lines = wrap(d0, stat, stat_f, max_w - 56)
    disc_lines = wrap(d0, disclaimer, disc_f, max_w)

    ph = 560  # высота иллюстрации
    H = ph + 120  # шапка
    H += len(title_lines) * 64
    H += len(pt_lines) * 46
    H += 70 + len(stat_lines) * 46  # бокс-стат
    H += len(disc_lines) * 40
    H += 100

    img = Image.new("RGB", (W, H), BG)
    img.paste(ill, (0, 0))
    d = ImageDraw.Draw(img)
    d.line([(0, ph), (W, ph)], fill=ACCENT, width=4)

    y = ph + 50
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 40
    d.text((W // 2, y), tag, font=tag_f, fill=MUTED, anchor="mm"); y += 48

    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 64
    y += 8

    for i, ln in enumerate(pt_lines, 1):
        d.text((M, y), "•", font=txt_f, fill=ACCENT2, anchor="lm")
        d.text((M + 40, y), ln, font=txt_f, fill=TEXT, anchor="lm"); y += 46
    y += 18

    box_h = len(stat_lines) * 46 + 32
    d.rounded_rectangle([M, y, W - M, y + box_h], radius=18, fill=(245, 229, 233))
    for ln in stat_lines:
        d.text((W // 2, y + 16), ln, font=stat_f, fill=ACCENT, anchor="mm"); y += 46
    y += box_h - 16

    y += 8
    for ln in disc_lines:
        d.text((W // 2, y), ln, font=disc_f, fill=WARN, anchor="mm"); y += 40
    d.text((W // 2, y), "alina-body.fitness  ·  t.me/alinabodyfree", font=disc_f, fill=MUTED, anchor="mm")

    img.save(out, "JPEG", quality=90, optimize=True, progressive=True)
    return out


if __name__ == "__main__":
    key = load_key()
    outdir = "/home/hermes/alina-body/content/demo"
    os.makedirs(outdir, exist_ok=True)

    # 1) плоская иллюстрация (без лица)
    prompt = ("Flat modern infographic illustration, a stylized healthy human liver in soft coral pink, "
              "surrounded by small flat icons: vegetables, a glass of water, green herbs, "
              "clean cream background, soft pastel palette, minimal, no text, no letters, no people, "
              "wellness healthcare flat style")
    ill = gen_illustration(key, prompt, f"{outdir}/liver-illustration.jpg")
    if not ill:
        raise SystemExit("иллюстрация не сгенерилась")
    print("иллюстрация:", ill)

    # 2) карточка
    card = build_card(
        ill,
        title="Здоровье печени",
        tag="ГАЙД · 6 КАРТОЧЕК",
        points=[
            "5–6 приёмов пищи в день, порция ~200 г",
            "Соль не больше 5 г — следи за «скрытой» солью",
            "Готовка на пару или варка, без жареного",
            "Расторопша, артишок, куркума — под задачу",
        ],
        stat="Больше воды · меньше алкоголя · ежедневное движение",
        disclaimer="Перед применением БАД — консультация со специалистом.",
        out=f"{outdir}/liver-card.jpg",
    )
    print("карточка:", card)
