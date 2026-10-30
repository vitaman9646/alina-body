#!/usr/bin/env python3
"""Generate Pinterest pins (2:3, 1000x1500) for lead magnets.

Lead-magnet pins = flat illustration (contained) + big keyword title + tagline
+ brand footer. Unlike article pins (cover-crop photo), these keep the flat
illustration fully visible.

Usage: python3 scripts/gen_lead_pins.py [--dry-run] [--only SLUG]
"""
import io
import os
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pins import load_creds, make_gradient, wrap_text, fit_title  # noqa: E402

PIN_W, PIN_H = 1000, 1500
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

FLAT = "/home/hermes/alina-body/alina-media/illustrations/flat"
PLATE = f"{FLAT}/овощи-тарелка-белки-углеводы.jpg"
SQUAT = f"{FLAT}/squat-exercise.jpg"
GLUTE = f"{FLAT}/glute-bridge-exercise.jpg"
DUMBBELL = f"{FLAT}/home-dumbbell-workout.jpg"
FOOD = "/home/hermes/alina-body/content/demo/food.jpg"
HERBS = "/home/hermes/alina-body/content/demo/herbs.jpg"
DRINKS = f"{FLAT}/травяной-напиток-чай-имбирь.jpg"
FACE = f"{FLAT}/лицо-кожа-маска.jpg"
HAIR = f"{FLAT}/волосы-расчёска-блеск.jpg"
CAT = f"{FLAT}/поза-кошка-корова-спина.jpg"
TWIST = f"{FLAT}/скручивание-сидя-поза.jpg"
LIVER = "/home/hermes/alina-body/content/demo/liver-illustration.jpg"
TAZ_ANATOMY = "/home/hermes/alina-body/alina-media/cartoon/tazodno-anatomy.jpg"
TAZ_RELAX = "/home/hermes/alina-body/alina-media/cartoon/tazodno-relax.jpg"
GI_INSULIN = f"{FLAT}/гликемический-индекс-инсулин-сахар-кровь.jpg"
BERRY = f"{FLAT}/ягоды-черника-малина-смородина.jpg"
SCALE = f"{FLAT}/инсулин-весы-обмен-веществ-жир.jpg"
PROTEIN = f"{FLAT}/белок-яйца-курица-творог-протеин.jpg"
CAPSULES = f"{FLAT}/инозитол-капсулы.jpg"
BERBERINE = f"{FLAT}/берберин-барбарис.jpg"

# slug -> { board, landing, pins: [(variant, title, tagline, ill), ...] }
LEAD_MAGNETS = {
    "tarelka": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/tarelka",
        "title": "Гарвардская тарелка", "tagline": "Простой способ собрать сбалансированный приём пищи — без подсчёта калорий.",
        "pins": [
            ("", "Гарвардская тарелка", "Сбалансированный приём пищи без подсчёта калорий", PLATE),
            ("-v2", "Правило тарелки: как собрать приём пищи", "Половина — овощи, четверть — белки, четверть — углеводы", PLATE),
        ],
    },
    "dnevnik": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/dnevnik",
        "title": "Дневник питания", "tagline": "Как вести дневник, чтобы увидеть, что на самом деле мешает результату.",
        "pins": [
            ("", "Дневник питания", "Как вести дневник, чтобы понять, что мешает результату", FOOD),
            ("-v2", "Зачем вести дневник питания", "Простой способ увидеть свои привычки в еде", PLATE),
        ],
    },
    "psihologia": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/psihologia",
        "title": "Психология похудения", "tagline": "Как перестать заедать стресс и отличать голод от эмоций.",
        "pins": [
            ("", "Эмоциональное заедание", "Как перестать есть от стресса и скуки", FOOD),
            ("-v2", "Голод или эмоции: как отличить", "Три шага против заедания", FOOD),
        ],
    },
    "faq": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/faq",
        "title": "FAQ похудения", "tagline": "Честные ответы на самые частые вопросы о похудении.",
        "pins": [
            ("", "Почему не уходит вес", "Разбор частых причин, почему вес стоит на месте", PLATE),
            ("-v2", "Похудение без диет и голода", "Что реально работает, а что — миф", FOOD),
        ],
    },
    "menu": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/menu",
        "title": "Меню на неделю", "tagline": "Готовый план питания на 7 дней — без сложных рецептов.",
        "pins": [
            ("", "Меню на неделю", "Готовый план питания на 7 дней", PLATE),
            ("-v2", "План питания на 7 дней", "Сбалансированное меню без сложных рецептов", FOOD),
        ],
    },
    "spisok": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/spisok",
        "title": "Список покупок", "tagline": "Что купить, чтобы дома всегда было из чего приготовить полезно.",
        "pins": [
            ("", "Список покупок для правильного питания", "Что купить, чтобы всегда было из чего готовить", HERBS),
            ("-v2", "Продукты для ПП: список", "База корзины — по принципу радуги", PLATE),
        ],
    },
    "supp": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/supp",
        "title": "Спортпит и БАДы", "tagline": "Что делают аминокислоты и как принимать их с умом.",
        "pins": [
            ("", "Аминокислоты: для чего нужны", "ГАМК, аргинин, лизин — что делает каждая", HERBS),
            ("-v2", "Спортпит для начинающих", "Что принимать и в каких дозах", HERBS),
        ],
    },
    "liver": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/liver",
        "title": "Здоровье печени", "tagline": "Как поддержать печень питанием и привычками — без «чисток».",
        "pins": [
            ("", "Как поддержать печень", "Питание, привычки и БАДы", LIVER),
            ("-v2", "Здоровье печени: с чего начать", "Простые шаги без «чисток» и «детоксов»", HERBS),
        ],
    },
    "tazovoe-dno": {
        "board": "Тренировки дома", "landing": "https://alina-body.fitness/lead/tazovoe-dno",
        "title": "Тазовое дно", "tagline": "Базовые движения для контроля мышц тазового дна — мягко и без стеснения.",
        "pins": [
            ("", "Упражнения для тазового дна", "Базовые движения, доступные каждой", TAZ_ANATOMY),
            ("-v2", "Тазовое дно: базовые движения", "Дыхание, расслабление и контроль мышц", TAZ_RELAX),
        ],
    },
    "domashnie-trenirovki": {
        "board": "Тренировки дома", "landing": "https://alina-body.fitness/lead/domashnie-trenirovki",
        "title": "Тренировки дома", "tagline": "4 экспресс-комплекса на всё тело — без зала и инвентаря.",
        "pins": [
            ("", "Тренировки дома", "4 экспресс-комплекса на всё тело", SQUAT),
            ("-v2", "Экспресс-тренировки на всё тело", "Верх, ягодицы, спина и руки — без зала", DUMBBELL),
        ],
    },
    "metabolic-protocol": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/metabolic-protocol",
        "title": "Метаболический протокол", "tagline": "Домашний режим без жёстких диет: тарелка 80/20, тёплые напитки и 25 минут в день.",
        "pins": [
            ("", "Метаболический протокол", "Тарелка 80/20, тёплые напитки и 25 минут в день — без жёстких диет", PLATE),
            ("-v2", "Правило тарелки 80/20", "Как собрать приём пищи, чтобы не тянуло на сладкое", DRINKS),
        ],
    },
    "domashniy-uhod": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/domashniy-uhod",
        "title": "Домашний уход и витамины", "tagline": "Маски, скрабы и витаминные шоты из того, что уже есть на кухне.",
        "pins": [
            ("", "Домашний уход и витамины", "Маски, скрабы и витаминные шоты из доступных продуктов", FACE),
            ("-v2", "Домашние маски для лица и волос", "Простые рецепты ухода без дорогих средств", HAIR),
        ],
    },
    "asimetriya": {
        "board": "Тренировки дома", "landing": "https://alina-body.fitness/lead/asimetriya",
        "title": "Йога: асимметричное выравнивание", "tagline": "Практика для ровной спины и осанки — 30–40 минут на коврике.",
        "pins": [
            ("", "Йога: асимметричное выравнивание", "Практика для ровной спины и осанки — 30–40 минут на коврике", CAT),
            ("-v2", "Йога для осанки: с чего начать", "Дыхание, разминка, скручивания и балансы — мягко и дома", TWIST),
        ],
    },
    "pitanie-podskazki": {
        "board": "Питание и рецепты", "landing": "https://alina-body.fitness/lead/pitanie-podskazki",
        "title": "Что и когда есть", "tagline": "ГИ, ИИ и три пищевых окна — как время приёма меняет результат.",
        "pins": [
            ("", "Что и когда есть: ГИ и ИИ", "Инсулин важнее сахара — как время приёма меняет результат", GI_INSULIN),
            ("-v2", "Три пищевых окна", "Что можно утром, после тренировки и вечером", BERRY),
        ],
    },
    "pohudenie-bez-ukolov": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/pohudenie-bez-ukolov",
        "title": "Похудение без уколов", "tagline": "Естественный путь к весу, который не возвращается.",
        "pins": [
            ("", "Похудение без уколов", "Естественный путь к весу, который не возвращается", SCALE),
            ("-v2", "Белок — ключ к сытости", "1,2–1,6 г/кг и как белок сохраняет мышцы", PROTEIN),
        ],
    },
    "bady-5": {
        "board": "Здоровье и привычки", "landing": "https://alina-body.fitness/lead/bady-5",
        "title": "5 БАДов с доказательствами", "tagline": "Берберин, инозитол, витамин D, омега-3 и магний — что реально работает, а что маркетинг.",
        "pins": [
            ("", "5 БАДов с доказательствами", "Берберин, инозитол, витамин D, омега-3, магний — механизмы и дозы", CAPSULES),
            ("-v2", "Какие добавки правда работают", "Пять БАДов с исследованиями, а не обещаниями", BERBERINE),
        ],
    },
}


def build_pin(ill_path, title, tagline):
    base = Image.new("RGB", (PIN_W, PIN_H), (250, 249, 246))
    ill = Image.open(ill_path).convert("RGB")
    box_w, box_h = PIN_W - 120, int(PIN_H * 0.56)
    scale = min(box_w / ill.width, box_h / ill.height)
    nw, nh = max(1, int(ill.width * scale)), max(1, int(ill.height * scale))
    ill = ill.resize((nw, nh), Image.LANCZOS)
    base.paste(ill, ((PIN_W - nw) // 2, (box_h - nh) // 2 + 20))

    grad = make_gradient(PIN_W, PIN_H, 0, 235)
    base = base.convert("RGBA")
    base.alpha_composite(grad)
    base = base.convert("RGB")
    d = ImageDraw.Draw(base)

    tfont, tlines = fit_title(d, title, 74, 880, 3)
    line_h = tfont.getbbox("Ag")[3] - tfont.getbbox("Ag")[1] + 10
    y = PIN_H - 210 - line_h * len(tlines)
    for ln in tlines:
        w = d.textlength(ln, font=tfont)
        d.text(((PIN_W - w) // 2 + 2, y + 2), ln, font=tfont, fill=(0, 0, 0, 140))
        d.text(((PIN_W - w) // 2, y), ln, font=tfont, fill=(255, 255, 255))
        y += line_h

    sfont = ImageFont.truetype(FONT_REG, 40)
    for ln in wrap_text(d, tagline, sfont, 860):
        w = d.textlength(ln, font=sfont)
        d.text(((PIN_W - w) // 2, y + 6), ln, font=sfont, fill=(238, 238, 238))
        y += 48

    ffont = ImageFont.truetype(FONT_REG, 32)
    foot = "alina-body.fitness"
    fw = d.textlength(foot, font=ffont)
    d.text(((PIN_W - fw) // 2, PIN_H - 56), foot, font=ffont, fill=(235, 235, 235))
    return base


def main():
    dry = "--dry-run" in sys.argv
    only = next((a.split("=")[1] for a in sys.argv if a.startswith("--only=")), None)
    url, key = load_creds()

    made = 0
    for slug, meta in LEAD_MAGNETS.items():
        if only and slug != only:
            continue
        for variant, title, tagline, ill_path in meta["pins"]:
            fname = f"lead-{slug}{variant}.jpg"
            if dry:
                print(f"[dry] {fname}  <- {title}")
                made += 1
                continue
            if not os.path.exists(ill_path):
                print(f"[!] MISSING {ill_path}")
                continue
            out = build_pin(ill_path, title, tagline)
            buf = io.BytesIO()
            out.save(buf, "JPEG", quality=88, optimize=True)
            r = requests.post(
                f"{url}/storage/v1/object/alina-media/pinterest/{fname}",
                headers={
                    "Authorization": f"Bearer {key}", "apikey": key,
                    "x-upsert": "true", "Content-Type": "image/jpeg",
                },
                data=buf.getvalue(), timeout=120,
            )
            status = "uploaded" if r.status_code in (200, 201) else f"FAIL {r.status_code}"
            print(f"[+] {fname}  <- {title}  {status}")
            made += 1

    print(f"\nDone: {made} lead-magnet pins")


if __name__ == "__main__":
    main()
