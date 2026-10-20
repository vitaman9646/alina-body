#!/usr/bin/env python3
"""Закреп: «надпись-ссылка на карточку» + лонгрид (текстом, не альбомом)."""
import os, json, html, urllib.request, urllib.parse

def load_env():
    e = {}
    for line in open(os.path.expanduser("~/credentials/telegram.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e
env = load_env()
TOKEN = env["TELEGRAM_BOT_TOKEN"]; CH = env["TELEGRAM_CHANNEL_ID"]

def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=40).read())

LONGRIDS = {
    "sportpit": """💊 <b>Спортпит и БАДы — полный гайд</b>

Аминокислоты — не «химия для качков», а вещества из обычной еды. Три из них закрывают три задачи: сон и спокойствие, работа мышц, кожа и иммунитет.

<b>🧠 ГАМК — спокойствие и сон</b>
Снижает кортизол («гормон стресса»), помогает не «заедать» стресс, поддерживает сон. Доза: 1 г (2×0,5 г) — после тренировки или за 30 мин до сна.

<b>💪 L-Аргинин — кровоток и мышцы</b>
Участвует в выработке оксида азота — расширяет сосуды, улучшает кровоток в мышцах. Доза: 1 г натощак — до тренировки (за 30–60 мин) или до сна.

<b>✨ L-Лизин — кожа и иммунитет</b>
Участвует в синтезе коллагена — эластичность кожи, связки, хрящи. Доза: 1–2 г — во время или после еды.

<b>📅 В день тренировки</b>
До тренировки — аргинин 1 г · сразу после — ГАМК 1 г · через 30–60 мин — лизин 1 г · за 30 мин до сна — аргинин + ГАМК + белок 2 яиц.

<b>🥗 Правила стройности</b>
Убрать глютен (выпечка), лактозу (молочное), сахарозу и фруктозу (сладости, фрукты; ягоды можно).

<i>Перед применением БАД — консультация со специалистом.</i>""",
    "pechen": """🌿 <b>Здоровье печени — полный гайд</b>

Печень — главный «фильтр» организма. Ей не нужна «чистка» — она очищает себя сама. Нужно просто перестать её перегружать.

<b>🍽 Питание</b>
1. 5–6 приёмов в день, порция ~200 г.
2. Соль ≤ 5 г (80% «скрытая» в готовых продуктах).
3. Варка, пар, тушение — без жареного.
4. Достаточно воды.
5. Фастфуд → фрукты, овощи.

<b>🏃♀️ Образ жизни</b>
Ежедневное движение · без алкоголя и курения · без лишних лекарств.

<b>💊 БАДы</b>
Расторопша (силимарин) 70–80 мг — клетки печени · артишок (цинарин) 300 мг — желчегонное · куркума (куркумин) — защита, с пиперином.

<b>⚠️ Когда к врачу</b>
Тяжесть/боль в правом подреберье, желтушность кожи, слабость → гепатолог.

<i>Перед применением БАД — консультация со специалистом.</i>""",
}

def re_pin(gname, urls_json, unpin_id):
    urls = json.load(open(urls_json))
    lines = [f"<b>Карточки гайда</b> (нажми на название):", ""]
    for it in urls:
        lines.append(f'• <a href="{it["url"]}">{html.escape(it["title"])}</a>')
    lines += ["", "──────────", "", LONGRIDS[gname]]
    text = "\n".join(lines)
    r = api("sendMessage", chat_id=CH, text=text, parse_mode="HTML", disable_web_page_preview="true")
    mid = r["result"]["message_id"]
    api("pinChatMessage", chat_id=CH, message_id=mid)
    api("unpinChatMessage", chat_id=CH, message_id=unpin_id)
    print(f"{gname}: новый пин {mid}, старый откреплён {unpin_id}")

re_pin("sportpit", "/tmp/sportpit_urls.json", 43)
re_pin("pechen", "/tmp/pechen_urls.json", 49)
