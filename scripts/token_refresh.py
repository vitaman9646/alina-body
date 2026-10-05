#!/usr/bin/env python3
"""Обновление Instagram long-lived access token (ig_refresh_token).

Логика:
  - обновлять, только если возраст токена >= REFRESH_AFTER_DAYS (50 дней);
  - токен должен быть старше 24 часов;
  - атомарная запись в ~/credentials/instagram.env (INSTAGRAM_ACCESS_TOKEN +
    INSTAGRAM_TOKEN_ISSUED_AT), права 600;
  - если обновление не удалось и до конца срока меньше 7 дней (возраст >=
    WARN_AFTER_DAYS), печатает явное предупреждение и выходит с кодом 2.

Секреты не печатаются.
"""
import os
import sys
import json
import datetime
import tempfile
import urllib.request
import urllib.parse
import urllib.error

CRED = os.path.expanduser('~/credentials/instagram.env')
API = 'https://graph.instagram.com'
REFRESH_AFTER_DAYS = 50
WARN_AFTER_DAYS = 53
TOKEN_MIN_AGE_HOURS = 24


def load_env():
    env = {}
    with open(CRED) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def parse_issued_at(s):
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.datetime.fromtimestamp(float(s), tz=datetime.timezone.utc)
    except (ValueError, OverflowError):
        pass
    s2 = s.replace('Z', '+00:00')
    try:
        return datetime.datetime.fromisoformat(s2)
    except ValueError:
        return None


def atomic_write(new_token, issued_at_iso):
    with open(CRED) as f:
        lines = f.readlines()
    out = []
    replaced_tok = False
    replaced_issued = False
    for line in lines:
        if line.startswith('INSTAGRAM_ACCESS_TOKEN='):
            out.append('INSTAGRAM_ACCESS_TOKEN=' + new_token + '\n')
            replaced_tok = True
        elif line.startswith('INSTAGRAM_TOKEN_ISSUED_AT='):
            out.append('INSTAGRAM_TOKEN_ISSUED_AT=' + issued_at_iso + '\n')
            replaced_issued = True
        else:
            out.append(line)
    if not replaced_tok:
        out.append('INSTAGRAM_ACCESS_TOKEN=' + new_token + '\n')
    if not replaced_issued:
        out.append('INSTAGRAM_TOKEN_ISSUED_AT=' + issued_at_iso + '\n')
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(CRED))
    with os.fdopen(fd, 'w') as f:
        f.writelines(out)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CRED)


def main():
    env = load_env()
    token = env.get('INSTAGRAM_ACCESS_TOKEN', '').strip()
    issued_raw = env.get('INSTAGRAM_TOKEN_ISSUED_AT', '').strip()
    if not token:
        print('Нет INSTAGRAM_ACCESS_TOKEN — выход.')
        sys.exit(1)

    issued = parse_issued_at(issued_raw)
    if issued is None:
        print('Не удалось разобрать INSTAGRAM_TOKEN_ISSUED_AT (%r) — пропуск.' % issued_raw)
        sys.exit(1)

    now = datetime.datetime.now(datetime.timezone.utc)
    age_days = (now - issued).total_seconds() / 86400
    print('Возраст токена: %.1f дней' % age_days)

    if age_days < REFRESH_AFTER_DAYS:
        print('Моложе %d дней — обновление не требуется.' % REFRESH_AFTER_DAYS)
        return

    if age_days * 24 < TOKEN_MIN_AGE_HOURS:
        print('Токен моложе %d часов — обновление нельзя выполнить.' % TOKEN_MIN_AGE_HOURS)
        return

    url = API + '/refresh_access_token?' + urllib.parse.urlencode({
        'grant_type': 'ig_refresh_token',
        'access_token': token,
    })

    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = json.dumps(json.loads(e.read().decode()).get('error', {}))
        except Exception:
            err = 'non-json'
        print('Ошибка обновления: HTTP %s %s' % (e.code, err))
        if age_days >= WARN_AFTER_DAYS:
            print('ВНИМАНИЕ: токену %.1f дней (до конца срока <7 дней), обновление НЕ удалось.' % age_days)
            sys.exit(2)
        sys.exit(1)
    except Exception as e:
        print('Ошибка сети: %s' % e)
        if age_days >= WARN_AFTER_DAYS:
            print('ВНИМАНИЕ: токену %.1f дней (до конца срока <7 дней), обновление НЕ удалось.' % age_days)
            sys.exit(2)
        sys.exit(1)

    new_token = data.get('access_token')
    if not new_token:
        print('В ответе нет access_token: %s' % json.dumps(data))
        sys.exit(1)

    atomic_write(new_token, now.isoformat())
    expires_in = data.get('expires_in')
    print('Токен обновлён. expires_in=%s сек (~%.0f дней), файл 600.' % (expires_in, int(expires_in or 0) / 86400))


if __name__ == '__main__':
    main()
