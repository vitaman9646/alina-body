#!/usr/bin/env python3
"""
Дампер Telegram-групп под user-аккаунт (Telethon).

Читает историю групп, где аккаунт — участник. Только чтение, ничего не шлёт.
Безопасный темп: последовательный обход, пауза между батчами, resume-докачка.

Режимы:
  list                         — показать группы/каналы, где аккаунт состоит
  dump <id|username|link>      — дамп всей истории чата (с докачкой)
  dump-new <id>                — только сообщения с момента последнего дампа
  dump-latest <id> [N]         — последние N сообщений (тест, по умолч. 50)

Параметры (env, необязательные):
  TG_PAUSE      — пауза между батчами, сек (по умолч. 2)
  TG_BATCH      — размер батча iter_messages (по умолч. 100)
  TG_MEDIA      — 1 = качать медиа, 0 = только текст (по умолч. 1)
  TG_DIR        — куда складывать дампы (по умолч. ./content/tg-dumps)

Сессия: ~/credentials/tg-user.session (создаётся при первом логине).
"""
import os, sys, json, time, asyncio, re

from telethon import TelegramClient, functions, types
from telethon.errors import SessionPasswordNeededError

SESSION = os.path.expanduser("~/credentials/tg-user.session")
API_ID = int(os.environ.get("TG_API_ID", 0))
API_HASH = os.environ.get("TG_API_HASH", "")
PAUSE = float(os.environ.get("TG_PAUSE", 2))
BATCH = int(os.environ.get("TG_BATCH", 100))
MEDIA = os.environ.get("TG_MEDIA", "1") == "1"
OUT_DIR = os.environ.get("TG_DIR", "/home/hermes/alina-body/content/tg-dumps")

if not API_ID or not API_HASH:
    print("Нужны TG_API_ID и TG_API_HASH (my.telegram.org → API development tools).")
    sys.exit(1)

os.makedirs(OUT_DIR, exist_ok=True)
client = TelegramClient(SESSION, API_ID, API_HASH)


def slugify(s):
    s = re.sub(r"[^\w\-]+", "-", str(s)).strip("-")
    return s[:60] or "chat"


async def resolve(client, ref):
    """ref = id / username / t.me/c/... ссылка / -100... id"""
    ref = str(ref).strip()
    m = re.search(r"t\.me/c/(\d+)", ref)
    if m:
        return await client.get_entity(int("-100" + m.group(1)))
    if ref.lstrip("-").isdigit():
        return await client.get_entity(int(ref))
    return await client.get_entity(ref)


def message_to_dict(m):
    return {
        "id": m.id,
        "date": m.date.isoformat() if m.date else None,
        "text": m.text or "",
        "sender_id": m.sender_id,
        "reply_to": m.reply_to_msg_id,
        "fwd_from": m.forward.original_date.isoformat() if m.forward else None,
        "media": m.media.__class__.__name__ if m.media else None,
        "views": m.views,
        "reactions": m.reactions.stringify() if m.reactions else None,
    }


async def cmd_list():
    me = await client.get_me()
    print(f"Аккаунт: @{me.username or me.first_name} (id {me.id})")
    print("Группы/каналы:\n")
    rows = []
    async for d in client.iter_dialogs():
        if d.is_channel or d.is_group:
            rows.append((d.id, d.name or "", d.is_channel, d.is_group))
    for cid, name, is_ch, is_gr in sorted(rows, key=lambda r: str(r[1]).lower()):
        kind = "канал" if is_ch else "группа"
        print(f"  {-cid if str(cid).startswith('100') else cid:>16}  {kind:<6}  {name}")


async def cmd_dump(ref, only_new=False, limit=None):
    entity = await resolve(client, ref)
    cid = entity.id
    fname = os.path.join(OUT_DIR, f"{slugify(entity.title or entity.id)}-{abs(cid)}.jsonl")
    print(f"Чат: «{getattr(entity, 'title', '?')}» id={cid}")
    print(f"Файл: {fname}")

    # resume: уже сохранённые id
    seen = set()
    if os.path.exists(fname):
        with open(fname) as f:
            for line in f:
                try:
                    seen.add(json.loads(line)["id"])
                except Exception:
                    pass
        print(f"Докачка: уже сохранено {len(seen)} сообщений")

    kwargs = dict(limit=limit) if limit else {}
    if only_new and seen:
        min_id = min(seen)
        kwargs["min_id"] = min_id

    with open(fname, "a", encoding="utf-8") as out:
        saved = 0
        async for m in client.iter_messages(entity, **kwargs):
            if m.id in seen:
                continue
            if m.text or m.media:
                out.write(json.dumps(message_to_dict(m), ensure_ascii=False) + "\n")
                saved += 1
                if MEDIA and m.media:
                    try:
                        await client.download_media(m, os.path.join(OUT_DIR, "media"), thumb=0)
                    except Exception as e:
                        pass
            if saved % BATCH == 0:
                out.flush()
                print(f"  …{saved} сообщений")
                await asyncio.sleep(PAUSE)
        out.flush()
    print(f"Готово: +{saved} сообщений → {fname}")


async def main():
    await client.start()
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return
    cmd = argv[0]
    if cmd == "list":
        await cmd_list()
    elif cmd == "dump":
        await cmd_dump(argv[1])
    elif cmd == "dump-new":
        await cmd_dump(argv[1], only_new=True)
    elif cmd == "dump-latest":
        n = int(argv[2]) if len(argv) > 2 else 50
        await cmd_dump(argv[1], limit=n)
    else:
        print(__doc__)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
