#!/usr/bin/env python3
"""Публикует пост (текст + картинка) на стену ВК — личного аккаунта или группы.

Аргументы: --caption (текст), --image (локальный путь или публичный URL), --dry-run.
Поток: (если есть картинка) photos.getWallUploadServer -> upload -> photos.saveWallPhoto -> wall.post.

Секреты читает из ~/credentials/vk.env:
  VK_ACCESS_TOKEN  — user-токен (для личной страницы) или community-токен (для группы)
  VK_OWNER_ID      — со знаком: положительный = личный аккаунт (user_id),
                     отрицательный = группа (например -12345678)

ВК-токены бессрочные, рефреш не нужен (в отличие от Threads/IG).
"""

import sys
import argparse
import requests

API = "https://api.vk.com/method/"
V = "5.131"
ENV_PATH = "/home/hermes/credentials/vk.env"


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def vk(token, method, **params):
    params["v"] = V
    params["access_token"] = token
    r = requests.post(API + method, data=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(
            "VK error {}: {}".format(
                data["error"].get("error_code"), data["error"].get("error_msg")
            )
        )
    return data["response"]


def resolve_owner(token, owner):
    """Число со знаком — как есть; короткое имя — резолвим (группа или юзер)."""
    s = str(owner).strip()
    try:
        return int(s)
    except (TypeError, ValueError):
        try:
            r = vk(token, "groups.getById", group_id=s)
            return -r[0]["id"]
        except RuntimeError:
            r = vk(token, "users.get", user_ids=s)
            return r[0]["id"]


def upload_photo(token, owner_id, image_bytes):
    is_group = owner_id < 0
    kwargs = {"group_id": -owner_id} if is_group else {}
    up = vk(token, "photos.getWallUploadServer", **kwargs)
    r = requests.post(
        up["upload_url"],
        files={"photo": ("photo.jpg", image_bytes, "image/jpeg")},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    save_kwargs = dict(kwargs, server=data["server"], photo=data["photo"], hash=data["hash"])
    saved = vk(token, "photos.saveWallPhoto", **save_kwargs)
    p = saved[0]
    return "photo{}_{}".format(p["owner_id"], p["id"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--caption", help="текст поста")
    parser.add_argument("--image", help="локальный путь или публичный URL картинки")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.caption and not args.image:
        print("Нужен --caption или --image.")
        sys.exit(2)

    env = load_env()
    token = env["VK_ACCESS_TOKEN"]
    owner_id = resolve_owner(token, env["VK_OWNER_ID"])
    is_group = owner_id < 0

    image_bytes = None
    if args.image:
        if args.image.startswith("http"):
            image_bytes = requests.get(args.image, timeout=60).content
        else:
            with open(args.image, "rb") as f:
                image_bytes = f.read()

    if args.dry_run:
        print("[dry-run] owner_id:", owner_id, "(группа)" if is_group else "(аккаунт)")
        print("[dry-run] caption:", args.caption)
        print("[dry-run] image:", args.image or "нет",
              "| bytes:", len(image_bytes) if image_bytes else 0)
        return

    attachment = None
    if image_bytes:
        attachment = upload_photo(token, owner_id, image_bytes)
        print("Фото загружено:", attachment)

    params = {"owner_id": owner_id, "message": args.caption or ""}
    if is_group:
        params["from_group"] = 1
    if attachment:
        params["attachments"] = attachment
    r = vk(token, "wall.post", **params)
    print("Пост опубликован: wall{}_{}".format(r["owner_id"], r["post_id"]))


if __name__ == "__main__":
    main()
