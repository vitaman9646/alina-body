#!/usr/bin/env python3
"""Пересборка лид-магнитов в новом формате: карточка-раздел + инлайн-иллюстрация (flux-3/klein).

Генерит плоскую иллюстрацию на каждую секцию (flux-3/klein, 1.6 кр) и собирает
карточку: иллюстрация инлайн слева + плотный нумерованный текст. Заливает в Supabase.

Использование: .venv-tts/bin/python scripts/gen_guides.py
"""
import os, io, json, time, urllib.request
from PIL import Image, ImageDraw, ImageFont

API = "https://api.kie.ai"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG = (253, 247, 241); ACCENT = (214, 122, 140); ACCENT2 = (88, 168, 130)
TEXT = (56, 44, 50); MUTED = (130, 108, 112); WARN = (180, 130, 90)
MODEL = "flux-3/klein-text-to-image"

# --- гайды: секции (title, tag, иллюстрация-prompt, points) ---
GUIDES = {
    "sportpit": {
        "brand_tag": "СПОРТПИТ И БАДЫ",
        "prefix": "supp-new",
        "sections": [
            {
                "title": "ГАМК — спокойствие и сон",
                "prompt": "Flat minimal illustration of a crescent moon and a peaceful sleeping silhouette, soft lavender and cream palette, no text, no faces, calm wellness flat style",
                "points": [
                    "Снижает кортизол — «гормон стресса»",
                    "Меньше тревожность и раздражительность",
                    "Помогает не «заедать» стресс",
                    "Поддерживает спокойный сон",
                    "Доза: 1 г (2×0,5 г) — после тренировки или за 30 мин до сна",
                ],
            },
            {
                "title": "L-Аргинин — кровоток и мышцы",
                "prompt": "Flat minimal illustration of muscle fibers and flowing blood vessels, soft coral and cream palette, no text, no people, fitness flat style",
                "points": [
                    "Участвует в выработке оксида азота — расширяет сосуды",
                    "Улучшает кровоток в мышцах",
                    "Поддерживает работоспособность на тренировке",
                    "Доза: 1 г натощак — до тренировки (за 30–60 мин) или до сна",
                ],
            },
            {
                "title": "L-Лизин — кожа и иммунитет",
                "prompt": "Flat minimal illustration of a soft shield with skin texture and collagen strands, soft pink and cream palette, no text, immunity flat style",
                "points": [
                    "Участвует в синтезе коллагена — эластичность кожи",
                    "Поддерживает связки, хрящи, сухожилия",
                    "Поддерживает иммунитет",
                    "Доза: 1–2 г — во время или после еды",
                ],
            },
            {
                "title": "Схема приёма в день тренировки",
                "prompt": "Flat minimal illustration of a clock with a dumbbell and a moon, morning and night symbols, soft pastel palette, no text, schedule flat style",
                "points": [
                    "До тренировки — L-аргинин 1 г",
                    "Сразу после — ГАМК 1 г (тёплая вода)",
                    "Через 30–60 мин — L-лизин 1 г (с едой)",
                    "За 30 мин до сна — аргинин + ГАМК + белок 2 яиц",
                ],
            },
            {
                "title": "Правила стройности",
                "prompt": "Flat minimal illustration of a balanced plate with crossed-out sugar and bread icons, soft pastel palette, no text, nutrition flat style",
                "points": [
                    "№1 — убрать глютен (выпечка, пшеница)",
                    "№2 — убрать лактозу (молочные продукты)",
                    "№3 — убрать сахарозу и фруктозу (сладости, фрукты — ягоды можно)",
                ],
            },
        ],
    },
    "pechen": {
        "brand_tag": "ЗДОРОВЬЕ ПЕЧЕНИ",
        "prefix": "liver-new",
        "sections": [
            {
                "title": "Питание для печени",
                "prompt": "Flat minimal illustration of a healthy food bowl with vegetables and grains, soft pastel palette, cream background, no text, no people, wellness flat style",
                "points": [
                    "5–6 приёмов в день, порция ~200 г",
                    "Соль ≤ 5 г (80% — «скрытая» в готовом)",
                    "Варка, пар, тушение — без жареного",
                    "Вода, морсы, некрепкий чай",
                    "Фастфуд и снеки → фрукты, овощи",
                ],
            },
            {
                "title": "Образ жизни",
                "prompt": "Flat minimal illustration of a walking person with a small heart, soft pastel palette, cream background, no text, no faces, active lifestyle flat style",
                "points": [
                    "Ежедневное движение: ходьба, бег, плавание, велосипед",
                    "Без алкоголя и курения",
                    "Без лекарств без назначения",
                ],
            },
            {
                "title": "БАДы для печени",
                "prompt": "Flat minimal illustration of herbal supplement capsules with green herbs and a plant, soft pastel palette, cream background, no text, wellness flat style",
                "points": [
                    "Расторопша (силимарин) 70–80 мг — поддержка клеток",
                    "Артишок (цинарин) 300 мг — желчегонное",
                    "Куркума (куркумин) — защита, лучше с пиперином",
                ],
            },
            {
                "title": "Когда к врачу",
                "prompt": "Flat minimal illustration of a stethoscope with a warning heart, soft pastel palette, cream background, no text, healthcare flat style",
                "points": [
                    "Тяжесть или боли в правом подреберье",
                    "Желтушность кожи или белков глаз",
                    "Постоянная слабость, тошнота",
                    "→ к гепатологу или гастроэнтерологу, без самолечения",
                ],
            },
        ],
    },
}


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()


def gen_illustration(key, prompt, out):
    inp = {"prompt": prompt, "aspect_ratio": "1:1"}
    req = urllib.request.Request(f"{API}/api/v1/jobs/createTask",
        data=json.dumps({"model": MODEL, "input": inp}).encode(),
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


def build_card(title, tag, ill_path, points, out_path, img_w=230):
    W, M = 1080, 64
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    max_w = W - 2 * M
    title_f = font(46); tag_f = font(24, False); logo_f = font(28)
    pt_f = font(29, False); num_f = font(29); disc_f = font(23)

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
    d.text((W // 2, y), tag, font=tag_f, fill=MUTED, anchor="mm"); y += 38
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
    d.text((W // 2, y), "Перед применением БАД — консультация со специалистом.", font=disc_f, fill=WARN, anchor="mm"); y += 38
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

    for gname, guide in GUIDES.items():
        out_dir = f"/home/hermes/alina-body/content/demo/{gname}"
        os.makedirs(out_dir, exist_ok=True)
        urls = []
        for i, sec in enumerate(guide["sections"], 1):
            ill = f"{out_dir}/ill-{i}.jpg"
            print(f"[{gname} {i}/{len(guide['sections'])}] иллюстрация…", flush=True)
            r, err = gen_illustration(key, sec["prompt"], ill)
            if err:
                print(f"  ❌ {err}"); continue
            card = f"{out_dir}/card-{i}.jpg"
            build_card(sec["title"], guide["brand_tag"], ill, sec["points"], card)
            # заливка в Supabase
            fname = f"{guide['prefix']}-{i}.jpg"
            url = f"{SUPA}/storage/v1/object/alina-media/lead-magnet/{fname}"
            req = urllib.request.Request(url, data=open(card, "rb").read(), method="POST",
                headers={"Authorization": "Bearer " + SKEY, "apikey": SKEY, "Content-Type": "image/jpeg", "x-upsert": "true"})
            urllib.request.urlopen(req, timeout=60).read()
            pub = url.replace("/object/", "/object/public/")
            urls.append({"title": sec["title"], "url": pub})
            print(f"  ✅ {fname} -> {pub}")
        json.dump(urls, open(f"/tmp/{gname}_urls.json", "w"), ensure_ascii=False, indent=2)
        print(f"[{gname}] готово: {len(urls)} карточек\n")


if __name__ == "__main__":
    main()
