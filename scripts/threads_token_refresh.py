#!/usr/bin/env python3
"""Обновление long-lived Threads access token (th_refresh_token).

Читает текущий токен из ~/credentials/threads.env, запрашивает новый
long-lived токен через refresh_access_token, перезаписывает файл.
Секреты и токены в stdout не выводятся.
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

ENV_PATH = os.path.expanduser('~/credentials/threads.env')


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def save_token(new_token):
    with open(ENV_PATH) as f:
        lines = f.readlines()
    out = []
    replaced = False
    for line in lines:
        if line.startswith('THREADS_ACCESS_TOKEN='):
            out.append('THREADS_ACCESS_TOKEN=' + new_token + '\n')
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append('THREADS_ACCESS_TOKEN=' + new_token + '\n')
    with open(ENV_PATH, 'w') as f:
        f.writelines(out)
    os.chmod(ENV_PATH, 0o600)


def main():
    env = load_env()
    token = env.get('THREADS_ACCESS_TOKEN', '').strip()
    if not token:
        print('Ошибка: THREADS_ACCESS_TOKEN не найден в ' + ENV_PATH)
        sys.exit(1)

    url = 'https://graph.threads.net/refresh_access_token?' + urllib.parse.urlencode({
        'grant_type': 'th_refresh_token',
        'access_token': token,
    })

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode())
        except Exception:
            msg = {}
        print('Ошибка Meta: ' + str(msg.get('error', {}).get('message', msg)))
        sys.exit(1)
    except Exception as e:
        print('Ошибка сети: ' + str(e))
        sys.exit(1)

    new_token = data.get('access_token')
    if not new_token:
        print('Ошибка: в ответе нет access_token')
        sys.exit(1)

    expires_in = data.get('expires_in')
    save_token(new_token)
    days = int(expires_in or 0) / 86400
    print('Токен обновлён. expires_in=%s сек (~%.0f дней), файл 600.' % (expires_in, days))


if __name__ == '__main__':
    main()
