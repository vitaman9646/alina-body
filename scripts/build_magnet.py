#!/usr/bin/env python3
"""Лид-магнит за одну команду.

Собирает полный лид-магнит из JSON-спеки: иллюстрации (через illib.py —
переиспользование или генерация), карточки (Pillow), заливка в Supabase,
файл URL-ов для закрепа. Затем pin_guide.py делает сам закреп.

Спека (JSON):
{
  "slug": "my-magnet",              // префикс файлов и URL-json
  "title": "Название магнита",      // для подписи на карточках
  "style": "flat" | "cartoon",      // flat = инфографика с плоской иллюстрацией,
                                    // cartoon = мультяшка-демонстратор слева
  "footer": "alina-body.fitness · t.me/alinabodyfree",   // опционально
  "disclaimer": "текст предупреждения",                   // опционально (cartoon-бокс)
  "cards": [
    {
      "tag": "ТЕГ",                  // подзаголовок-рубрика (капс)
      "title": "Заголовок карточки",
      "topic": "ключ для поиска в библиотеке",   // напр. "овощи тарелка"
      "prompt": "English prompt на случай генерации",   // flat-иллюстрация
      "points": ["пункт 1", "пункт 2", ...]
    }
  ]
}

Запуск:
  build_magnet.py spec.json              # полный прогон
  build_magnet.py spec.json --dry-run    # показать план, ничего не генерить/лить
  build_magnet.py spec.json --skip-upload  # карточки локально, без Supabase

После прогона: /tmp/<slug>_urls.json → pin_guide.py --title ... --urls ... --lonrid ...
"""
import os, io, json, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import illib  # noqa: E402

ROOT = "/home/hermes/alina-body"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

BG = (253, 247, 241)
ACCENT = (214, 122, 140)
ACCENT2 = (88, 168, 130)
TEXT = (56, 44, 50)
MUTED = (130, 108, 112)
BOX = (245, 229, 233)
WARN = (180, 108, 90)


def parse_hex(h, default):
    """Шестнадцатеричный цвет '#RRGGBB' → RGB-кортеж; иначе дефолт."""
    if not h:
        return default
    h = h.lstrip("#").strip()
    try:
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        pass
    return default

W = 1080


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


# ── Плоский стиль (иллюстрация слева 230×230, пункты справа) ──────────
def build_flat_card(card, ill_path, magnet_title, idx, total, footer, logo="ALINA BODY", accent=ACCENT):
    M = 64
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M
    img_w = 230
    title_f = font(46); tag_f = font(24, False); logo_f = font(28)
    pt_f = font(29, False); num_f = font(29); disc_f = font(23)

    ill = Image.open(ill_path).convert("RGB").resize((img_w, img_w), Image.LANCZOS)
    mask = Image.new("L", (img_w, img_w), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img_w, img_w), radius=28, fill=255)
    ill.putalpha(mask)

    txt_w = max_w - img_w - 36
    title_lines = wrap(d0, card["title"].upper(), title_f, max_w)
    pt_lines = []
    for it in card["points"]:
        pt_lines += wrap(d0, it, pt_f, txt_w)

    H = 150 + len(title_lines) * 58 + 16
    H += max(img_w + 16, len(pt_lines) * 44 + 40)
    H += 88

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 58
    d.text((W // 2, y), logo, font=logo_f, fill=accent, anchor="mm"); y += 34
    tag = card.get("tag") or f"ЧАСТЬ {idx}/{total}"
    d.text((W // 2, y), f"{magnet_title.upper()} · {tag.upper()}", font=tag_f, fill=MUTED, anchor="mm"); y += 38
    d.line([(M, y), (W - M, y)], fill=accent, width=3); y += 26
    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 58
    y += 8
    ill_y = y
    img.paste(ill, (M, ill_y), ill)
    ty = ill_y + 2
    for i, it in enumerate(card["points"], 1):
        for j, ln in enumerate(wrap(d0, it, pt_f, txt_w)):
            x = M + img_w + 36
            if j == 0:
                d.text((x - 32, ty), f"{i}.", font=num_f, fill=accent, anchor="rm")
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            else:
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            ty += 44
    y = max(ill_y + img_w, ty) + 18
    d.line([(M, y), (W - M, y)], fill=accent, width=2); y += 18
    d.text((W // 2, y), footer, font=disc_f, fill=MUTED, anchor="mm")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=90, optimize=True, progressive=True)
    return buf.getvalue()


# ── Мультяшка-демонстратор (3:4 слева + пункты + дисклеймер) ──────────
def build_cartoon_card(card, ill_path, magnet_title, idx, total, footer, disclaimer, logo="ALINA BODY", accent=ACCENT):
    M = 70
    ILL_W, ILL_H = 340, 453
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    logo_f = font(34); tag_f = font(25, False); title_f = font(46)
    txt_f = font(28, False); disc_f = font(26); foot_f = font(24, False)

    tag = card.get("tag") or f"ЧАСТЬ {idx}/{total}"
    title_lines = wrap(d0, card["title"].upper(), title_f, W - 2 * M)
    col_w = W - 2 * M - ILL_W - 36
    wrapped_points = [wrap(d0, p, txt_f, col_w - 34) for p in card["points"]]
    txt_h = sum(len(ln) * 42 + 12 for ln in wrapped_points)
    body_h = max(ILL_H, txt_h) + 20
    H = 70 + 52 + 36 + 30 + len(title_lines) * 58 + 24 + body_h + 40
    disc_lines = wrap(d0, disclaimer, disc_f, W - 2 * M) if disclaimer else []
    if disc_lines:
        H += len(disc_lines) * 38 + 28
    H += 90

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 62
    d.text((W // 2, y), logo, font=logo_f, fill=accent, anchor="mm"); y += 50
    d.text((W // 2, y), tag, font=tag_f, fill=MUTED, anchor="mm"); y += 34
    d.line([(M, y), (W - M, y)], fill=accent, width=3); y += 28
    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 58
    y += 20

    try:
        ph = Image.open(ill_path).convert("RGB").resize((ILL_W, ILL_H))
        mask = Image.new("L", (ILL_W, ILL_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, ILL_W, ILL_H), radius=26, fill=255)
        img.paste(ph, (M, y), mask)
    except Exception as e:
        print("  иллюстрация не загрузилась:", e)

    tx = M + ILL_W + 36
    ty = y + 6
    for i, lns in enumerate(wrapped_points, 1):
        d.ellipse([tx - 2, ty + 4, tx + 26, ty + 32], fill=accent)
        d.text((tx + 12, ty + 18), str(i), font=font(20), fill=(255, 255, 255), anchor="mm")
        for ln in lns:
            d.text((tx + 42, ty + 6), ln, font=txt_f, fill=TEXT, anchor="lm")
            ty += 42
        ty += 12
    y += body_h + 8

    if disc_lines:
        d.line([(M, y), (W - M, y)], fill=accent, width=2); y += 18
        box_h = len(disc_lines) * 38 + 24
        d.rounded_rectangle([M, y, W - M, y + box_h], radius=16, fill=BOX)
        for i, ln in enumerate(disc_lines):
            d.text((W // 2, y + 14 + i * 38), ln, font=disc_f, fill=WARN, anchor="mm")
        y += box_h + 20

    d.text((W // 2, y), footer, font=foot_f, fill=MUTED, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    return buf.getvalue()


def load_env():
    env = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip()
    return env


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Лид-магнит из JSON-спеки")
    ap.add_argument("spec", help="путь к JSON-спеке")
    ap.add_argument("--dry-run", action="store_true", help="только план")
    ap.add_argument("--skip-upload", action="store_true", help="не лить в Supabase")
    a = ap.parse_args()

    spec = json.load(open(a.spec))
    slug = spec["slug"]
    magnet_title = spec.get("title", slug)
    style = spec.get("style", "flat")
    footer = spec.get("footer", "alina-body.fitness  ·  t.me/alinabodyfree")
    disclaimer = spec.get("disclaimer", "")
    logo = spec.get("logo", "ALINA BODY")
    accent = parse_hex(spec.get("accent"), ACCENT)
    cards = spec["cards"]

    out_dir = os.path.join(ROOT, "content", "demo", slug)
    os.makedirs(out_dir, exist_ok=True)

    urls = []
    for i, card in enumerate(cards, 1):
        topic = card["topic"]
        prompt = card.get("prompt", "")
        tag = f"[{i}/{len(cards)}] {card['title']}"
        print(f"{tag} — иллюстрация «{topic}»…", flush=True)

        if a.dry_run:
            scored = illib._search_scored(topic, type_=style)
            qwords = [illib._norm(w) for w in topic.split() if illib._norm(w)]
            if scored and illib._should_reuse(scored[0][0], len(qwords)):
                print(f"  ↳ REUSED {scored[0][1]['id']}")
            else:
                print(f"  ↳ NEW (генерация {illib.FLAT_MODEL if style=='flat' else illib.CARTOON_MODEL})")
            continue

        if style == "cartoon":
            r = illib.get_cartoon(topic, prompt, aspect="3:4")
        else:
            r = illib.get_flat(topic, prompt, aspect="1:1")
        print(("  ↳ REUSED " if r["reused"] else "  ↳ NEW    ") + r["file"])

        if style == "cartoon":
            data = build_cartoon_card(card, r["file"], magnet_title, i, len(cards), footer, disclaimer, logo, accent)
        else:
            data = build_flat_card(card, r["file"], magnet_title, i, len(cards), footer, logo, accent)

        local = os.path.join(out_dir, f"card-{i}.jpg")
        open(local, "wb").write(data)

        if a.skip_upload:
            urls.append({"title": card["title"], "url": None, "local": local})
            continue

        env = load_env()
        SUPA = env["SUPABASE_URL"].rstrip("/")
        SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
        fname = f"{slug}-{i}.jpg"
        url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{fname}"
        req = urllib.request.Request(url, data=data, method="POST",
            headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY,
                     "Content-Type": "image/jpeg", "x-upsert": "true"})
        urllib.request.urlopen(req, timeout=60).read()
        pub = url.replace("/object/", "/object/public/")
        urls.append({"title": card["title"], "url": pub, "local": local})
        print(f"  ✅ {fname}")

    if not a.dry_run:
        out = f"/tmp/{slug}_urls.json"
        json.dump(urls, open(out, "w"), ensure_ascii=False, indent=2)
        print(f"\nготово карточек: {len(urls)} → {out}")
        print(f"закреп: pin_guide.py --title \"{magnet_title}\" --urls {out} --lonrid <путь-к-лонгриду>")


if __name__ == "__main__":
    main()
