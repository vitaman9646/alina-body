#!/usr/bin/env python3
"""Считает КБЖУ смузи по ингредиентам (оценка ±10–15%, «пересчёт»).

Читает content/smoothie-course.json, для уроков типа recipe суммирует нутриенты
через приоритетную базу (на 100 г), 1 смузи = 1 порция, дописывает поле
kbzhu {kcal, protein, fat, carbs}. Техники без ingredients — без КБЖУ.
"""
import json, re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "content/smoothie-course.json")

# вес единицы для «шт»/«½ шт», по стему ингредиента (г)
UNIT_W = {
    "огурец": 150, "банан": 120, "киви": 75, "авокадо": 150, "яблок": 150,
    "апельсин": 130, "груш": 170, "морков": 75, "свекл": 100, "лайм": 60, "лимон": 90,
}

# овощи/фрукты: стем -> (ккал, б, ж, у) на 100 г
VEG = {
    "микрозелен": (30, 3, 0.5, 3),
    "сельдере": (16, 0.7, 0.2, 3),
    "петрушк": (36, 3, 0.8, 6),
    "броккол": (34, 2.8, 0.4, 6.6),
    "шпинат": (23, 2.9, 0.4, 3.6),
    "руккол": (25, 2.6, 0.7, 3.7),
    "смородин": (44, 1, 0.4, 7.3),
    "апельсин": (43, 0.9, 0.1, 11.7),
    "авокадо": (160, 2, 14.7, 8.5),
    "черник": (57, 0.7, 0.3, 14.5),
    "ежевик": (43, 1.4, 0.5, 9.6),
    "ананас": (50, 0.5, 0.1, 13),
    "огурец": (15, 0.7, 0.1, 3.6),
    "крапив": (42, 2.7, 0.3, 7.8),
    "морков": (35, 1.3, 0.1, 6.9),
    "свекл": (43, 1.6, 0.2, 8.8),
    "кабач": (24, 0.6, 0.3, 4.6),
    "тыкв": (26, 1, 0.1, 6.5),
    "щавел": (28, 2.3, 0.3, 4.6),
    "банан": (89, 1.1, 0.3, 22.8),
    "гранат": (52, 0.9, 0.1, 13),
    "яблок": (47, 0.4, 0.4, 11.7),
    "вишн": (50, 1, 0.3, 12),
    "малин": (53, 1.2, 0.7, 11.9),
    "киви": (61, 1.1, 0.5, 14.7),
    "кейл": (49, 4.3, 0.9, 8.8),
    "ромэн": (17, 1.2, 0.3, 3.3),
    "кинз": (23, 2.1, 0.5, 3.7),
    "лайм": (30, 0.7, 0.2, 10.5),
    "лимон": (29, 1.1, 0.3, 9.3),
    "груш": (47, 0.4, 0.3, 12),
    "кресс": (32, 2.6, 0.7, 5.5),
    "сныть": (35, 3, 0.4, 5),
    "дикорос": (35, 3, 0.4, 5),
}

IGNORE = ["ванил", "кориц", "имбир", "кардамон", "кайен", "мят", "подсластител",
          "соль", "цедр", "вода", "минеральн", "таурин", "инозитол", "креатин",
          "глутамин", "магний", "цитруллин", "электролит", "бета-глюкан"]


def extract_num(a):
    """Число из граммовки с дробями/диапазонами: '½ шт'→0.5, '200–250 мл'→225."""
    fracs = {"½": 0.5, "¼": 0.25, "¾": 0.75}
    toks = re.findall(r"(\d+(?:[.]\d+)?|[½¼¾])", a)
    if not toks:
        return None
    vals = [fracs[t] if t in fracs else float(t) for t in toks]
    if len(vals) == 1:
        return vals[0]
    if re.search(r"[–—]", a):
        return (vals[0] + vals[1]) / 2.0
    return vals[0]


def to_grams(name, amount):
    if not amount:
        return 0
    a = amount.replace(",", ".").strip().lower()
    if "по вкусу" in a or "по желанию" in a:
        return 0
    num = extract_num(a)
    if num is None:
        return 0

    # ложки — ДО литра («ст. л.» содержит «л»)
    if "ст. л" in a or "ст.л" in a:
        return num * 15
    if "ч. л" in a or "ч.л" in a:
        return num * 5
    if re.search(r"\bмл\b", a):
        return num
    if re.search(r"\bкг\b", a):
        return num * 1000
    if re.search(r"\bг\b", a):
        return num
    if re.search(r"\bл\b", a):
        return num * 1000

    low = name.lower().replace("ё", "е")
    if (re.search(r"\bшт\b", a) or re.search(r"средн", a)
            or re.search(r"небольш", a) or re.search(r"молод", a)):
        w = 100
        for stem, ww in UNIT_W.items():
            if stem in low:
                w = ww
                break
        return num * w
    if "стакан" in a:
        return num * 150
    if "горсть" in a or "пучок" in a:
        return num * 30
    if "стебл" in a or "палочк" in a:
        return num * 40
    if "соцвет" in a:
        return num * 20
    if "слайс" in a or "кусоч" in a:
        return num * 10
    if "щепотк" in a or "листик" in a:
        return num * 1
    return num  # fallback: граммы


def lookup(name):
    """Приоритетный матчинг -> (ккал, б, ж, у) на 100 г или None."""
    low = name.lower().replace("ё", "е")
    # жиры/масла
    if "масл" in low or "мст" in low:
        return (884, 0, 100, 0)
    # специфические жидкости (до игнора «вода»)
    if "кокосов" in low:
        if "молок" in low:
            return (197, 2.3, 21.3, 2.8)
        if "вод" in low:
            return (19, 0.7, 0.2, 3.7)
    if "миндальн" in low and "молок" in low:
        return (25, 0.5, 2.2, 0.5)
    if "морковн" in low and "сок" in low:
        return (40, 0.9, 0.2, 9.3)
    if "гранат" in low and "сок" in low:
        return (55, 0.2, 0.1, 13)
    if "лимон" in low and "сок" in low:
        return (22, 0.3, 0, 6.9)
    if "лайм" in low and "сок" in low:
        return (25, 0.4, 0, 8)
    # игнор (вода/специи/добавки)
    for w in IGNORE:
        if re.search(r"\b" + w, low):
            return (0, 0, 0, 0)
    # белки
    if "изолят" in low or "гидролизат" in low:
        return (380, 85, 4, 5)
    if "протеин" in low:
        return (400, 70, 8, 10)
    if "тофу" in low:
        return (55, 4.8, 2.7, 1.9)
    # семена/орехи/жиры
    if "чиа" in low:
        return (486, 16.5, 30.7, 42)
    # лён/семена льна — по ИСХОДНОМУ имени и границе слова: «зелёное»/«миндальная» содержат те же буквы
    if re.search(r"\bлён\b", name) or re.search(r"\bльна\b", name):
        return (534, 18.3, 42, 28.9)
    if "урбеч" in low:
        return (630, 15, 54, 13)
    if "тахини" in low:
        return (600, 20, 52, 15)
    if "паст" in low and "миндальн" in low:
        return (600, 20, 52, 15)
    if "орех" in low:
        return (654, 15, 65, 14)
    if "овсянк" in low:
        return (360, 12, 6, 60)
    if "отруб" in low:
        return (246, 17, 7, 66)
    if "какао" in low:
        return (228, 20, 14, 58)
    if "перг" in low:
        return (330, 20, 5, 65)
    if "коллаген" in low:
        return (360, 90, 0, 0)
    if "аминокислот" in low:
        return (400, 100, 0, 0)
    if "псиллиум" in low:
        return (200, 1, 0.5, 88)
    if "пектин" in low:
        return (300, 0, 0, 80)
    if "глюкоманан" in low:
        return (200, 0, 0, 90)
    if "крахмал" in low:
        return (350, 1, 0, 85)
    # овощи/фрукты
    for stem in sorted(VEG, key=len, reverse=True):
        if stem in low:
            return VEG[stem]
    return None


def calc(lesson):
    if not lesson.get("ingredients"):
        return None
    total = [0.0, 0.0, 0.0, 0.0]
    for ing in lesson["ingredients"]:
        g = to_grams(ing.get("name", ""), ing.get("amount", ""))
        if g <= 0:
            continue
        v = lookup(ing.get("name", ""))
        if not v:
            continue
        for i in range(4):
            total[i] += v[i] * g / 100.0
    per = [round(x) for x in total]
    return {"kcal": int(per[0]), "protein": round(per[1], 1),
            "fat": round(per[2], 1), "carbs": round(per[3], 1),
            "per": "порция (1 смузи)", "estimated": True}


def main():
    data = json.load(open(SRC))
    done = skipped = 0
    for m in data["modules"]:
        for les in m["lessons"]:
            if les.get("type") != "recipe":
                continue
            kb = calc(les)
            if kb:
                les["kbzhu"] = kb
                done += 1
            else:
                skipped += 1
    json.dump(data, open(SRC, "w"), ensure_ascii=False, indent=2)
    print(f"КБЖУ посчитано: {done}, пропущено: {skipped}")


if __name__ == "__main__":
    main()
