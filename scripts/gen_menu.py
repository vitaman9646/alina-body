#!/usr/bin/env python3
"""Лид-магнит «Меню на неделю» — 7 карточек (по дню)."""
import os, io, json, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = "https://api.kie.ai"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG = (253, 247, 241); ACCENT = (214, 122, 140); ACCENT2 = (88, 168, 130)
TEXT = (56, 44, 50); MUTED = (130, 108, 112); WARN = (180, 130, 90)
MODEL = "flux-3/klein-text-to-image"

DAYS = [
    ("День 1",
     "Flat minimal illustration of a breakfast wrap with spinach, a rice bowl and baked chicken, soft pastel, no text, meal flat style",
     ["Завтрак — ролл со шпинатом и фетой", "Обед — рисовый боул со свининой в медово-чесночном соусе", "Ужин — куриные наггетсы с пармезаном, запечённые с овощами"]),
    ("День 2",
     "Flat minimal illustration of an egg casserole, meatballs and sheet-pan chicken with vegetables, soft pastel, no text, meal flat style",
     ["Завтрак — запеканка с сосисками, яйцами и помидорами", "Обед — куриные фрикадельки с рисом из цветной капусты", "Ужин — курица на противне с разноцветными овощами"]),
    ("День 3",
     "Flat minimal illustration of a baguette sandwich, pasta and baked salmon in parchment, soft pastel, no text, meal flat style",
     ["Завтрак — багет с песто и яйцами", "Обед — паста с сосисками, шпинатом и томатами", "Ужин — запечённый лосось с кунжутом и имбирём"]),
    ("День 4",
     "Flat minimal illustration of a buckwheat bowl with egg, bulgur with salmon and chicken with cashews, soft pastel, no text, meal flat style",
     ["Завтрак — боул с гречкой, песто из петрушки и яйцом пашот", "Обед — булгур с лососем и помидорами черри", "Ужин — курица с кешью и базиликом"]),
    ("День 5",
     "Flat minimal illustration of a quesadilla, chicken curry and beef stir-fry with broccoli, soft pastel, no text, meal flat style",
     ["Завтрак — кесадилья с омлетом и овощами", "Обед — куриное карри в томатно-сливочном соусе", "Ужин — стир-фрай с говядиной и брокколи"]),
    ("День 6",
     "Flat minimal illustration of sweet potato skillet with eggs, chicken spinach soup and chili, soft pastel, no text, meal flat style",
     ["Завтрак — сковорода с бататом, яйцами и томатами", "Обед — суп с курицей, шпинатом и лимоном", "Ужин — чили из индейки с кукурузными начос"]),
    ("День 7",
     "Flat minimal illustration of beet hash browns, polenta casserole and greek chicken souvlaki, soft pastel, no text, meal flat style",
     ["Завтрак — хашбрауны из свёклы с яйцом и авокадо", "Обед — запеканка с полентой и фасолью", "Ужин — греческая курица сувлаки с картофелем"]),
]


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def gen_illustration(key, prompt, out):
    req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": MODEL, "input": {"prompt": prompt, "aspect_ratio": "1:1"}}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if r.get("code") != 200:
        return None, json.dumps(r)[:200]
    task = r["data"]["taskId"]
    for _ in range(70):
        time.sleep(6)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(
            f"{API}/api/v1/jobs/recordInfo?taskId={task}",
            headers={"Authorization": "Bearer " + key}), timeout=30).read())
        d = info.get("data", {})
        if d.get("state") == "success":
            urls = d.get("response", {}).get("resultUrls") or d.get("resultJson", {}).get("resultUrls") or []
            if urls:
                urllib.request.urlretrieve(urls[0], out)
                return out, None
        if d.get("state") == "fail":
            return None, json.dumps(d)[:200]
    return None, "timeout"


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


def build_card(title, ill_path, points, out_path, total, idx, img_w=230):
    W, M = 1080, 64
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M
    title_f = font(46); tag_f = font(24, False); logo_f = font(28)
    pt_f = font(30, False); num_f = font(30); disc_f = font(23)

    ill = Image.open(ill_path).convert("RGB").resize((img_w, img_w), Image.LANCZOS)
    mask = Image.new("L", (img_w, img_w), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img_w, img_w), radius=28, fill=255)
    ill.putalpha(mask)

    txt_w = max_w - img_w - 36
    title_lines = wrap(d0, title.upper(), title_f, max_w)
    pt_lines = []
    for it in points:
        pt_lines += wrap(d0, it, pt_f, txt_w)

    H = 150 + len(title_lines) * 58 + 16
    H += max(img_w + 16, len(pt_lines) * 44 + 40)
    H += 88

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 58
    d.text((W // 2, y), "ALINA BODY", font=logo_f, fill=ACCENT, anchor="mm"); y += 34
    d.text((W // 2, y), f"МЕНЮ НА НЕДЕЛЮ · {idx}/{total}", font=tag_f, fill=MUTED, anchor="mm"); y += 38
    d.line([(M, y), (W - M, y)], fill=ACCENT, width=3); y += 26
    for ln in title_lines:
        d.text((W // 2, y), ln, font=title_f, fill=TEXT, anchor="mm"); y += 58
    y += 8

    ill_y = y
    img.paste(ill, (M, ill_y), ill)
    ty = ill_y + 2
    for i, it in enumerate(points, 1):
        for j, ln in enumerate(wrap(d0, it, pt_f, txt_w)):
            x = M + img_w + 36
            if j == 0:
                d.text((x - 32, ty), f"{i}.", font=num_f, fill=ACCENT, anchor="rm")
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            else:
                d.text((x, ty), ln, font=pt_f, fill=TEXT, anchor="lm")
            ty += 44
    y = max(ill_y + img_w, ty) + 18

    d.line([(M, y), (W - M, y)], fill=ACCENT, width=2); y += 18
    d.text((W // 2, y), "Завтрак · Обед · Ужин — по правилу тарелки", font=disc_f, fill=ACCENT2, anchor="mm"); y += 36
    d.text((W // 2, y), "alina-body.fitness  ·  t.me/alinabodyfree", font=disc_f, fill=MUTED, anchor="mm")

    img.convert("RGB").save(out_path, "JPEG", quality=90, optimize=True, progressive=True)
    return out_path


def main():
    key = load_key()
    env = {}
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); env[k] = v.strip()
    SUPA = env["SUPABASE_URL"].rstrip("/")
    SKEY = env["SUPABASE_SERVICE_ROLE_KEY"]
    out_dir = "/home/hermes/alina-body/content/demo/menu"
    os.makedirs(out_dir, exist_ok=True)

    urls = []
    total = len(DAYS)
    for i, (title, prompt, points) in enumerate(DAYS, 1):
        ill = f"{out_dir}/ill-{i}.jpg"
        print(f"[{i}/{total}] «{title}»…", flush=True)
        r, err = gen_illustration(key, prompt, ill)
        if err:
            print(f"  ❌ {err}"); continue
        card = f"{out_dir}/card-{i}.jpg"
        build_card(title, ill, points, card, total, i)
        fname = f"menu-{i}.jpg"
        url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{fname}"
        req = urllib.request.Request(url, data=open(card, "rb").read(), method="POST",
            headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
        urllib.request.urlopen(req, timeout=60).read()
        pub = url.replace("/object/", "/object/public/")
        urls.append({"title": title, "url": pub})
        print(f"  ✅ {fname}")
    json.dump(urls, open("/tmp/menu_urls.json", "w"), ensure_ascii=False, indent=2)
    print(f"готово: {len(urls)}")


if __name__ == "__main__":
    main()
