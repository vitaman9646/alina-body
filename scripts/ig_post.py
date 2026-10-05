#!/usr/bin/env python3
"""Instagram Graph API — публикация поста с изображением.

Аргументы:
  --image    путь к локальному файлу ИЛИ публичный URL (http/https)
  --caption  текст поста (обязателен для публикации)
  --dry-run  подготовить картинку (если локальная) и показать, что будет
             опубликовано, но НЕ создавать контейнер и НЕ публиковать.

Поток (без --dry-run):
  1. Если --image локальный файл: очистить метаданные (clean-metadata.sh),
     проверить отсутствие c2pa/xmp/iptc/creator/software, при необходимости
     конвертировать в JPEG, загрузить в публичный bucket Supabase Storage.
  2. POST /{user_id}/media (image_url, caption) -> контейнер.
  3. Поллить статус до FINISHED.
  4. POST /{user_id}/media_publish.
  3 попытки с паузой 30 сек.

Секреты читаются на рантайме из env-файлов и не печатаются.
"""
import os
import sys
import json
import time
import argparse
import subprocess
import tempfile
import urllib.request
import urllib.parse
import urllib.error

CRED_IG = os.path.expanduser('~/credentials/instagram.env')
CRED_THREADS = os.path.expanduser('~/credentials/threads.env')
CLEAN_SH = '/home/hermes/scripts/clean-metadata.sh'
BUCKET = 'alina-media'
API = 'https://graph.instagram.com/v21.0'
ATTEMPTS = 3
RETRY_PAUSE = 30


def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def api_call(method, path, token=None, data=None, timeout=90):
    url = API + path
    if token:
        url += ('&' if '?' in url else '?') + 'access_token=' + urllib.parse.quote(token)
    body = None
    headers = {}
    if data:
        body = urllib.parse.urlencode(data).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return {'_error': json.loads(e.read().decode())}
        except Exception:
            return {'_error': {'code': e.code, 'raw': 'non-json'}}


def get_user_id(token):
    r = api_call('GET', '/me?fields=user_id', token)
    if '_error' in r:
        return None, r['_error']
    uid = r.get('user_id')
    if not uid:
        return None, {'message': 'нет user_id в ответе', 'response': r}
    return uid, None


def clean_and_verify(src):
    """Очистить метаданные и убедиться, что c2pa/xmp/iptc/creator/software ушли."""
    fd, out = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    subprocess.run([CLEAN_SH, src, out], check=True, capture_output=True, text=True)
    p = subprocess.run(['exiftool', '-G1', '-a', '-s', out], capture_output=True, text=True)
    lower = p.stdout.lower()
    bad = [k for k in ('c2pa', 'xmp', 'iptc', 'creator', 'software') if k in lower]
    if bad:
        raise RuntimeError('Остались метаданные: ' + ', '.join(bad))
    return out


def to_jpeg(path):
    from PIL import Image
    im = Image.open(path)
    if im.format == 'JPEG':
        return path
    im = im.convert('RGB')
    fd, out = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    im.save(out, 'JPEG', quality=95)
    return out


def upload_supabase(supabase_url, service_key, local_path):
    key = 'ig/' + str(int(time.time())) + '.jpg'
    with open(local_path, 'rb') as f:
        raw = f.read()
    url = supabase_url + '/storage/v1/object/' + urllib.parse.quote(BUCKET + '/' + key, safe='/')
    headers = {
        'apikey': service_key,
        'Authorization': 'Bearer ' + service_key,
        'Content-Type': 'image/jpeg',
        'x-upsert': 'true',
    }
    req = urllib.request.Request(url, data=raw, headers=headers, method='POST')
    try:
        urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        raise RuntimeError('Supabase upload: HTTP %s %s' % (e.code, e.read().decode()[:200]))
    return supabase_url + '/storage/v1/object/public/' + BUCKET + '/' + key


def prepare_image(image_arg, supabase_url, service_key):
    if image_arg.startswith('http://') or image_arg.startswith('https://'):
        return image_arg
    if not os.path.isfile(image_arg):
        raise RuntimeError('Файл не найден: ' + image_arg)
    cleaned = clean_and_verify(image_arg)
    jpeg = to_jpeg(cleaned)
    return upload_supabase(supabase_url, service_key, jpeg)


def post_flow(token, user_id, image_url, caption):
    r = api_call('POST', '/%s/media' % user_id, token, {'image_url': image_url, 'caption': caption})
    if '_error' in r:
        raise RuntimeError('контейнер: ' + json.dumps(r['_error'], ensure_ascii=False))
    cid = r.get('id')
    if not cid:
        raise RuntimeError('нет id контейнера: ' + json.dumps(r, ensure_ascii=False))

    for _ in range(60):
        s = api_call('GET', '/%s?fields=status_code,status' % cid, token)
        if '_error' in s:
            raise RuntimeError('статус: ' + json.dumps(s['_error'], ensure_ascii=False))
        sc = s.get('status_code')
        if sc == 'FINISHED':
            break
        if sc == 'ERROR':
            raise RuntimeError('контейнер ERROR: ' + json.dumps(s, ensure_ascii=False))
        time.sleep(3)
    else:
        raise RuntimeError('контейнер не завершился (timeout)')

    r2 = api_call('POST', '/%s/media_publish' % user_id, token, {'creation_id': cid})
    if '_error' in r2:
        raise RuntimeError('publish: ' + json.dumps(r2['_error'], ensure_ascii=False))
    return r2.get('id')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--caption', default='')
    ap.add_argument('--image', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    ig = load_env(CRED_IG)
    token = ig.get('INSTAGRAM_ACCESS_TOKEN', '').strip()
    if not token:
        print('Ошибка: INSTAGRAM_ACCESS_TOKEN не найден в ' + CRED_IG)
        sys.exit(1)

    th = load_env(CRED_THREADS)
    supabase_url = th.get('SUPABASE_URL', '').strip()
    service_key = th.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    if not (supabase_url and service_key):
        print('Ошибка: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY не найдены в ' + CRED_THREADS)
        sys.exit(1)

    try:
        image_url = prepare_image(args.image, supabase_url, service_key)
    except Exception as e:
        print('Ошибка подготовки изображения: ' + str(e))
        sys.exit(1)

    if args.dry_run:
        print('[DRY-RUN] подготовлено, публикация пропущена')
        print('  caption:', args.caption)
        print('  image_url готов')
        return

    user_id, err = get_user_id(token)
    if err:
        print('Ошибка /me: ' + json.dumps(err, ensure_ascii=False))
        sys.exit(1)

    last_err = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            mid = post_flow(token, user_id, image_url, args.caption)
            print('Опубликовано. media id:', mid)
            return
        except Exception as e:
            last_err = e
            print('Попытка %d/%d не удалась: %s' % (attempt, ATTEMPTS, e))
            if attempt < ATTEMPTS:
                print('Пауза %d сек...' % RETRY_PAUSE)
                time.sleep(RETRY_PAUSE)
    print('Не удалось опубликовать за %d попыток: %s' % (ATTEMPTS, last_err))
    sys.exit(1)


if __name__ == '__main__':
    main()
