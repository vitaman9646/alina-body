#!/usr/bin/env python3
"""Скачивает файлы из публичной ссылки cloud.mail.ru (public/<hash>/<key>).

Использование:
  python3 cloudmail_download.py 'https://cloud.mail.ru/public/XXXX/YYYY' [--dir OUT] [--ext .pdf,.txt,.docx]
  python3 cloudmail_download.py 'https://cloud.mail.ru/public/XXXX/YYYY' --all   # включая видео

Флоу: страница -> regex weblink_get -> API v4 public/list -> download = weblink_get_url + urlencoded weblink.
Требуется `requests` (есть в .venv-tts и в системном python3).
"""
import re, os, sys, argparse, urllib.parse
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--dir", default=None)
    ap.add_argument("--ext", default=".pdf,.txt,.docx,.doc", help="расширения через запятую")
    ap.add_argument("--all", action="store_true", help="качать все файлы (включая видео)")
    args = ap.parse_args()

    root = urllib.parse.urlparse(args.url).path.strip("/").split("/")
    if len(root) < 3 or root[0] != "public":
        sys.exit(f"Не похоже на публичную ссылку cloud.mail.ru: {args.url}")
    root_id = f"{root[1]}/{root[2]}"
    out = args.dir or f"/tmp/cloudmail_{root[1]}"
    os.makedirs(out, exist_ok=True)

    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    r = s.get(args.url, timeout=60); r.raise_for_status()
    m = re.search(r'"weblink_get"[^}]*"url"\s*:\s*"([^"]+)"', r.text)
    assert m, "weblink_get не найден в странице (ссылка может быть недействительна)"
    wg = m.group(1)

    data = s.get("https://cloud.mail.ru/api/v4/public/list",
                 params={"weblink": root_id, "sort": "name", "order": "asc",
                         "offset": "0", "limit": "500", "version": "4"}, timeout=60).json()
    items = data.get("list", []) or (data.get("body", {}) or {}).get("list", [])
    print(f"всего элементов: {len(items)}")

    exts = tuple(e.strip().lower() for e in args.ext.split(",")) if not args.all else ()
    targets = [it for it in items if it.get("type") == "file"
               and (args.all or it["name"].lower().endswith(exts))]

    def dl_url(wl):
        safe = "/".join(urllib.parse.quote(p, safe="") for p in wl.split("/"))
        return f"{wg}/{safe}"

    for it in targets:
        name = it["name"]
        r = s.get(dl_url(it["weblink"]), allow_redirects=True, stream=True, timeout=120)
        if "html" in r.headers.get("Content-Type", "").lower():
            mm = re.search(r'https?://[^"\'\s]+datacloudmail[^"\'\s]+', r.text[:30000])
            if mm:
                r = s.get(mm.group(0), allow_redirects=True, stream=True, timeout=120)
            else:
                print(f"  !! {name}: HTML без ссылки (len={len(r.text)})")
                continue
        with open(os.path.join(out, name), "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
        print(f"  OK {name}: {os.path.getsize(os.path.join(out, name))} байт")
    print("готово:", out)


if __name__ == "__main__":
    main()
