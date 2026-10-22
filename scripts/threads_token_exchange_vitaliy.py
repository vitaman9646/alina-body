#!/usr/bin/env python3
"""Обмен Threads OAuth code → long-lived токен для ЛИЧНОГО аккаунта Виталия.

Отличия от threads_token_exchange.py:
- CREDS_PATH = ~/credentials/vitaliy-threads.env (отдельный токен, не мешает Алине).
- Принимает --code напрямую (Виталий шлёт код в чат) — без чтения Supabase.
- После обмена получает user_id через GET /me и сохраняет THREADS_USER_ID.

Секреты (client_secret), code и access_token в stdout НЕ выводятся.
"""
import json, os, sys, argparse, urllib.request, urllib.parse, urllib.error

CREDS_PATH = os.path.expanduser("~/credentials/vitaliy-threads.env")
REDIRECT_URI = "https://alina-body.fitness/api/threads-callback"
OAUTH_URL = "https://graph.threads.net/oauth/access_token"
EXCHANGE_URL = "https://graph.threads.net/access_token"
ME_URL = "https://graph.threads.net/v1.0/me"


class MetaError(Exception):
    """Ошибка от Meta — только текстовое сообщение, без секретов."""


def load_env(path):
    env = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def save_env(path, key, value):
    lines, found = [], False
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.read().splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if s and not s.startswith("#") and s.split("=", 1)[0].strip() == key:
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(path, 0o600)


def meta_message(resp):
    err = resp.get("error") if isinstance(resp, dict) else None
    if isinstance(err, dict):
        return err.get("message") or err.get("type") or "unknown error"
    return "unknown error"


def http_json(url, method="GET", form=None, headers=None):
    body = urllib.parse.urlencode(form).encode() if form else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    if form:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            msg = meta_message(json.loads(e.read().decode()))
        except Exception:
            msg = f"HTTP {e.code}"
        raise MetaError(msg) from None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", help="OAuth code (Виталий шлёт в чат). Без него — не обмениваем.")
    args = ap.parse_args()

    if not args.code:
        print("Нужен --code. Код пришлёт Виталий после авторизации.")
        sys.exit(1)

    env = load_env(CREDS_PATH)
    for key in ("THREADS_APP_ID", "THREADS_APP_SECRET"):
        if not env.get(key):
            sys.exit(f"Ошибка: в {CREDS_PATH} нет ключа {key}")

    # code -> short-lived token
    token_resp = http_json(OAUTH_URL, "POST", {
        "client_id": env["THREADS_APP_ID"],
        "client_secret": env["THREADS_APP_SECRET"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": args.code,
    })
    short_token = token_resp.get("access_token")
    if not short_token:
        sys.exit(f"Ошибка обмена code: {meta_message(token_resp)}")

    # short-lived -> long-lived (60 дней)
    long_url = (EXCHANGE_URL
                + "?grant_type=th_exchange_token"
                + "&client_secret=" + urllib.parse.quote(env["THREADS_APP_SECRET"])
                + "&access_token=" + urllib.parse.quote(short_token))
    long_resp = http_json(long_url)
    long_token = long_resp.get("access_token")
    if not long_token:
        sys.exit(f"Ошибка обмена на long-lived: {meta_message(long_resp)}")

    # user_id через GET /me (нужен для постинга)
    me_headers = {"Authorization": "Bearer " + long_token}
    me_q = urllib.parse.urlencode({"fields": "id,username"})
    me_resp = http_json(f"{ME_URL}?{me_q}", headers=me_headers)
    user_id = me_resp.get("id")
    username = me_resp.get("username")
    if not user_id:
        print("⚠️ Не удалось получить user_id через /me (токен сохранён).")
        user_id = ""

    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    save_env(CREDS_PATH, "THREADS_ACCESS_TOKEN", long_token)
    if user_id:
        save_env(CREDS_PATH, "THREADS_USER_ID", user_id)

    print(f"Готово: long-lived токен сохранён в {CREDS_PATH} (права 600).")
    print(f"Аккаунт: @{username} · user_id={user_id}")


if __name__ == "__main__":
    try:
        main()
    except MetaError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except Exception:
        print("Непредвиденная ошибка, скрипт остановлен (трассировка скрыта).")
        sys.exit(1)
