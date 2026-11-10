#!/usr/bin/env python3
"""Постит следующий смузи-карусель (ротация, не чаще 1 раза в 2 суток).

Читает content/smoothie-recipes.json, состояние — content/smoothie-carousel-state.json.
Карусель = фото + карточка «Ингредиенты» + карточка «Когда пить» + подпись.
Идемпотентно: если с прошлого поста меньше 48ч — пропуск.

Использование: python3 post_smoothie_carousel.py [--dry-run] [--force]
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from threads_carousel import post_carousel, load_env, PROFILES  # noqa: E402

REPO = "/home/hermes/alina-body"
SRC = f"{REPO}/content/smoothie-recipes.json"
STATE = f"{REPO}/content/smoothie-carousel-state.json"
PHOTO_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/smoothie"
MIN_INTERVAL = 2 * 24 * 3600  # 2 суток


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    smoothies = data["smoothies"]

    c = PROFILES["alina"]
    env = load_env(os.path.expanduser(c["creds"]))
    token = env["THREADS_ACCESS_TOKEN"]
    uid = env.get("THREADS_USER_ID") or c["user_id"]

    state = {"posted": [], "last_ts": 0}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    dry = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    if not force and not dry:
        elapsed = time.time() - state.get("last_ts", 0)
        if elapsed < MIN_INTERVAL:
            print(f"Рано: прошло {int(elapsed / 3600)}ч из 48ч. Пропуск.")
            return

    nxt = None
    for s in smoothies:
        if s["slug"] not in state["posted"]:
            nxt = s
            break
    if not nxt:
        print("Все карусели смузи опубликованы.")
        return

    images = [
        f"{PHOTO_BASE}/{nxt['slug']}.jpg",
        f"{PHOTO_BASE}/cards/{nxt['slug']}-1.jpg",
        f"{PHOTO_BASE}/cards/{nxt['slug']}-2.jpg",
    ]

    if dry:
        print(f"[dry] {nxt['slug']}: {len(images)} слайдов")
        print(f"[dry] caption: {nxt['caption']}")
        return

    resp, err = post_carousel(token, uid, images, nxt["caption"])
    if err:
        print(f"❌ {nxt['slug']}: {err}")
        sys.exit(1)

    state["posted"].append(nxt["slug"])
    state["last_ts"] = time.time()
    json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)
    print(f"✅ {nxt['slug']} media_id={resp.get('id')}")


if __name__ == "__main__":
    main()
