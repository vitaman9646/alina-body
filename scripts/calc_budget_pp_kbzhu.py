#!/usr/bin/env python3
"""Считает КБЖУ рецептов «Бюджетное ПП» по ингредиентам (оценка ±10–15%).

Читает content/budget-pp-recipes.json, для каждого урока с ingredients суммирует
нутриенты через стем-базу (на 100 г), делит на число порций и дописывает поле
kbzhu {kcal, protein, fat, carbs} на порцию. Техники без ingredients — без КБЖУ.
"""
import json, re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "content/budget-pp-recipes.json")

# Стем -> (ккал, белки, жиры, углеводы) на 100 г. Длинные ключи приоритетнее.
NUTR = {
    # жиры/масла
    "жир": (897, 0, 99.7, 0),          # говяжий/топлёный жир, смалец
    "масл": (884, 0, 100, 0),          # растительное/сливочное/оливковое
    # молочка
    "сметан": (180, 2.6, 16, 3.6),
    # яйца
    "яйц": (157, 12.7, 11.5, 0.7),
    # мясо / субпродукты
    "сердечк": (159, 15.8, 10.3, 0.8),  # куриные сердечки
    "сердц": (96, 16, 3.5, 2),          # говяжье сердце
    "печен": (136, 17, 6, 1.3),         # куриная/говяжья печень
    "желудк": (114, 18, 4.2, 0.5),      # куриные желудки
    "крыл": (186, 18, 12, 0),           # куриные крылья
    "бедр": (185, 18, 12, 0),           # куриные бёдра
    "хвост": (170, 17, 11, 0),          # телячьи/говяжьи хвосты
    "лапк": (40, 4, 3, 0),             # куриные лапки (в бульон уходит мало)
    "кост": (30, 3, 2, 0),             # говяжьи кости (бульонная база) — приблиз.
    # рыба
    "минта": (72, 16, 0.9, 0),
    "скумбри": (205, 18.6, 14, 0),
    "хребт": (120, 18, 5, 0),           # рыбные хребты/головы (мясо)
    "голов": (120, 18, 5, 0),
    "рыб": (120, 18, 5, 0),
    # бобовые / злаки / мука
    "нут": (364, 19, 6, 61),
    "чечевиц": (352, 24, 1.5, 63),
    "маш": (347, 24, 1.2, 63),
    "гречк": (329, 12.6, 3.3, 62),
    "фасол": (298, 21, 0.5, 63),
    "мук": (340, 9, 1.5, 70),           # мука (ржаная/рисовая — усреднено)
    "рис": (344, 6.7, 0.7, 78),         # рис сухой
    # овощи
    "морков": (35, 1.3, 0.1, 6.9),
    "лук": (41, 1.4, 0.2, 8.2),
    "чеснок": (149, 6.4, 0.5, 33),
    "капуст": (28, 1.8, 0.1, 4.7),
    "свекл": (43, 1.6, 0.2, 8.8),
    "кабач": (24, 0.6, 0.3, 4.6),
    "тыкв": (26, 1, 0.1, 6.5),
    "реп": (32, 1.5, 0.1, 6.2),
    "брюкв": (37, 1.2, 0.1, 7.7),
    "картофел": (77, 2, 0.4, 16),
    "томат": (82, 4.8, 0.5, 14),        # томатная паста
    "лимон": (22, 0.4, 0.1, 6.9),
    "горчиц": (162, 5.7, 6.4, 22),
    # семена
    "семечк": (570, 25, 45, 15),        # тыквенные семечки
    "семен": (400, 20, 30, 20),         # семена для проращивания
}

# Приоритетные фразы (матчить раньше стемов)
PRIORITY = {
    "томатная паст": (82, 4.8, 0.5, 14),
}

# Игнор-список (специи/соль/вода/уксус → 0), по границе слова
IGNORE = ["соль", "вода", "бульон", "рассол", "уксус", "лавр", "перец", "кориандр",
          "зира", "кумин", "тмин", "ореган", "мускат", "паприк", "дрожж", "петрушк",
          "укроп", "тимьян", "цедр"]


def parse_grams(amount):
    """Из строки граммовки возвращает граммы (число). шт→50, зубчик→4, ст.л→15, ч.л→5."""
    if not amount:
        return 0
    a = amount.replace(",", ".")
    m = re.search(r"(\d+(?:[.]\d+)?)\s*г\b", a)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:[.]\d+)?)\s*кг\b", a)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r"(\d+(?:[.]\d+)?)\s*мл\b", a)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:[.]\d+)?)\s*л\b", a)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r"(\d+(?:[.]\d+)?)\s*шт\b", a)
    if m:
        return float(m.group(1)) * 50
    m = re.search(r"(\d+(?:[.]\d+)?)\s*зубчик", a)
    if m:
        return float(m.group(1)) * 4
    m = re.search(r"(\d+(?:[.]\d+)?)\s*ст\.\s*л", a)
    if m:
        return float(m.group(1)) * 15
    m = re.search(r"(\d+(?:[.]\d+)?)\s*ч\.\s*л", a)
    if m:
        return float(m.group(1)) * 5
    return 0


def lookup(name):
    """Стем-матчинг ингредиента → (ккал, б, ж, у) на 100 г, или None."""
    low = name.lower().replace("ё", "е")
    # приоритетные фразы
    for ph, v in PRIORITY.items():
        if ph in low:
            return v
    # игнор (специи/соль/вода) по границе слова
    for w in IGNORE:
        if re.search(r"\b" + w, low):
            return (0, 0, 0, 0)
    # семена — до овоща «тыква»
    if "семечк" in low or "семен" in low or "семян" in low:
        return NUTR["семечк"] if "тыкв" in low else NUTR["семен"]
    # масло — до «оливок»
    if "масл" in low:
        return NUTR["масл"]
    # стемы longest-first
    for stem in sorted(NUTR, key=len, reverse=True):
        if stem in low:
            return NUTR[stem]
    return None


def portion_count(portions):
    """Число порций из строки: 'N порц', 'N лепёшек', 'N котлет', 'N шт'."""
    if not portions:
        return None
    m = re.search(r"(\d+)\s*порц", portions)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*(лепёш|котлет|шт)", portions)
    if m:
        return int(m.group(1))
    return None


def calc(lesson):
    if not lesson.get("ingredients"):
        return None
    total = [0.0, 0.0, 0.0, 0.0]
    grams = 0.0
    for ing in lesson["ingredients"]:
        g = parse_grams(ing.get("amount", ""))
        if g <= 0:
            continue
        v = lookup(ing.get("name", ""))
        if not v:
            continue
        grams += g
        for i in range(4):
            total[i] += v[i] * g / 100.0
    n = portion_count(lesson.get("portions", ""))
    if not n:
        n = max(1, round(grams / 250))  # порция ≈ 250 г, если не указано
    per = [round(x / n, 1) for x in total]
    return {"kcal": per[0], "protein": per[1], "fat": per[2], "carbs": per[3],
            "per": "порция", "portions": n}


def main():
    data = json.load(open(SRC))
    done = 0
    for m in data["modules"]:
        for les in m["lessons"]:
            kb = calc(les)
            if kb:
                les["kbzhu"] = kb
                done += 1
    json.dump(data, open(SRC, "w"), ensure_ascii=False, indent=2)
    print("КБЖУ посчитано для уроков:", done)


if __name__ == "__main__":
    main()
