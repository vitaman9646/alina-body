#!/usr/bin/env python3
"""
Обмен Threads OAuth code на long-lived access token.

Читает последнюю неиспользованную запись (provider='threads', used_at IS NULL)
из Supabase oauth_temp_codes, атомарно помечает её использованной (claim),
обменивает code на short-lived токен, затем на long-lived, сохраняет итог в
~/credentials/threads.env (THREADS_ACCESS_TOKEN) с правами 600.

Секреты (client_id, client_secret, Supabase) читаются строго из
~/credentials/threads.env. В stdout/лог НЕ выводятся client_secret, code и
access_token — ни целиком, ни в трассировке.
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error, datetime

CREDS_PATH = os.path.expanduser("~/credentials/threads.env")
REDIRECT_URI = "https://alina-body.fitness/api/threads-callback"
OAUTH_URL = "https://graph.threads.net/oauth/access_token"
EXCHANGE_URL = "https://graph.threads.net/access_token"


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
    """Извлекает только текст ошибки Meta, не тело целиком."""
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
    env = load_env(CREDS_PATH)
    for key in ("THREADS_APP_ID", "THREADS_APP_SECRET",
                "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if not env.get(key):
            sys.exit(f"Ошибка: в {CREDS_PATH} нет ключа {key}")

    sup_headers = {
        "apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
    }

    # 1. Последняя неиспользованная запись (provider='threads', used_at IS NULL)
    q = urllib.parse.urlencode({
        "provider": "eq.threads",
        "used_at": "is.null",
        "order": "id.desc",
        "limit": "1",
    })
    rows = http_json(f"{env['SUPABASE_URL']}/rest/v1/oauth_temp_codes?{q}", headers=sup_headers)
    if not rows:
        print("Нет неиспользованных записей в oauth_temp_codes (provider=threads).")
        return
    row = rows[0]
    code, row_id = row["code"], row["id"]

    # 2. Атомарный claim: помечаем использованной ДО обмена (идемпотентность).
    #    WHERE used_at IS NULL — второй параллельный запуск не заберёт ту же запись.
    claim_req = urllib.request.Request(
        f"{env['SUPABASE_URL']}/rest/v1/oauth_temp_codes?id=eq.{row_id}&used_at=is.null",
        data=json.dumps({"used_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode(),
        method="PATCH",
        headers={**sup_headers, "Content-Type": "application/json", "Prefer": "return=representation"},
    )
    with urllib.request.urlopen(claim_req, timeout=30) as resp:
        claimed = json.loads(resp.read().decode())
    if not claimed:
        print("Запись уже используется другим запуском. Ничего не делаем.")
        return

    # 3. code -> short-lived token
    token_resp = http_json(OAUTH_URL, "POST", {
        "client_id": env["THREADS_APP_ID"],
        "client_secret": env["THREADS_APP_SECRET"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    })
    short_token = token_resp.get("access_token")
    if not short_token:
        sys.exit(f"Ошибка обмена code: {meta_message(token_resp)}")

    # 4. short-lived -> long-lived
    long_url = (EXCHANGE_URL
                + "?grant_type=th_exchange_token"
                + "&client_secret=" + urllib.parse.quote(env["THREADS_APP_SECRET"])
                + "&access_token=" + urllib.parse.quote(short_token))
    long_resp = http_json(long_url)
    long_token = long_resp.get("access_token")
    if not long_token:
        sys.exit(f"Ошибка обмена на long-lived: {meta_message(long_resp)}")

    # 5. Сохранить long-lived токен (в stdout не выводим), права 600
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    save_env(CREDS_PATH, "THREADS_ACCESS_TOKEN", long_token)

    print(f"Готово: long-lived токен сохранён в {CREDS_PATH} (права 600), "
          f"запись id={row_id} помечена использованной.")


if __name__ == "__main__":
    try:
        main()
    except MetaError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except Exception:
        print("Непредвиденная ошибка, скрипт остановлен (трассировка скрыта).")
        sys.exit(1)
