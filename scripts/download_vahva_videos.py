#!/usr/bin/env python3
"""Скачивает 99 уникальных видео упражнений Vahva (референсы поз) с cloud.mail.ru.

Выход: inbox/vahva-fitness/videos/<slug>.mp4 + обновлённый content/vahva-video-map.json.
Запуск: python3 scripts/download_vahva_videos.py
"""
import json, os, re, sys, time, urllib.parse, requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PUBLIC = "https://cloud.mail.ru/public/ybso/i6PqNAm59"
ROOT = "/home/hermes/alina-body"
OUT = f"{ROOT}/inbox/vahva-fitness/videos"
MAP = f"{ROOT}/content/vahva-video-map.json"

# ручные соответствия (имя в PDF ≠ имя видео)
MANUAL = {
    "explosive-front-knee-raise": "A1 Explosive Front Leg Raise.mp4",
    "rear-delt-good-morning": "D5 Rear Delt Raise Good Morning.mp4",
    "side-plank-bend": "D6 Side Bend.mp4",
    "single-leg-plank": "A6 Single Leg Front Plank.mp4",
    "snatch-grip-deadlift": "D2 Snatch Grip Stability Deadlift.mp4",
}


def slug(n):
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')


def main():
    s = requests.Session(); s.headers.update({"User-Agent": UA})
    r = s.get(PUBLIC, timeout=60); r.raise_for_status()
    wg = re.search(r'"weblink_get"[^}]*"url"\s*:\s*"([^"]+)"', r.text).group(1)
    root_id = "ybso/i6PqNAm59"

    def list_dir(wl):
        d = s.get("https://cloud.mail.ru/api/v4/public/list",
            params={"weblink": wl, "sort": "name", "order": "asc", "offset": "0", "limit": "500", "version": "4"},
            timeout=60).json()
        return (d.get("body", d) or {}).get("list", [])

    # собрать все mp4: имя -> (size, weblink)
    by_name = {}
    def walk(wl):
        for it in list_dir(wl):
            nm = it.get("name")
            if it.get("type") == "folder":
                walk(it["weblink"])
            elif nm.lower().endswith(".mp4"):
                by_name.setdefault(nm, (it.get("size", 0), it["weblink"]))
    walk(root_id)
    print(f"mp4 всего: {len(by_name)}")

    # целевые уникальные упражнения
    en = json.load(open(f"{ROOT}/content/vahva-fitness.json"))
    uniq = {}
    for ph in en["phases"]:
        for wk in ph["weeks"]:
            for d in wk["days"]:
                for e in d["exercises"]:
                    k = slug(e["name"])
                    if k not in uniq:
                        uniq[k] = e["name"]

    # маппинг slug -> видео-имя
    target = {}  # slug -> mp4 filename
    # 1) авто: по regex кода
    for nm in by_name:
        m = re.match(r'^([A-F]\d+)\s+(.+?)\.mp4$', nm, re.I)
        if not m:
            continue
        s_ = slug(m.group(2).strip())
        if s_ in uniq and s_ not in target:
            target[s_] = nm
    # 2) ручные
    for s_, nm in MANUAL.items():
        if s_ in uniq and nm in by_name:
            target[s_] = nm

    missing = [s_ for s_ in uniq if s_ not in target]
    print(f"целевых: {len(uniq)}, скачиваю: {len(target)}, не нашлось: {missing}")

    os.makedirs(OUT, exist_ok=True)

    def dl_url(wl):
        safe = "/".join(urllib.parse.quote(p, safe="") for p in wl.split("/"))
        return f"{wg}/{safe}"

    ok = fail = 0
    total = sum(by_name[nm][0] for nm in target.values())
    print(f"объём: {total//1024//1024} MB")
    done_bytes = 0
    for s_, nm in sorted(target.items()):
        size, wl = by_name[nm]
        dst = os.path.join(OUT, f"{s_}.mp4")
        if os.path.exists(dst) and os.path.getsize(dst) > 100000:
            done_bytes += size; continue
        try:
            r = s.get(dl_url(wl), allow_redirects=True, stream=True, timeout=300)
            if "html" in r.headers.get("Content-Type", "").lower():
                mm = re.search(r'https?://[^"\'\s]+datacloudmail[^"\'\s]+', r.text[:30000])
                if mm:
                    r = s.get(mm.group(0), allow_redirects=True, stream=True, timeout=300)
                else:
                    print(f"  !! {s_}: HTML без ссылки"); fail += 1; continue
            with open(dst, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            sz = os.path.getsize(dst)
            done_bytes += sz
            ok += 1
            print(f"  ✓ {s_}: {sz//1024//1024} MB  [{done_bytes//1024//1024}/{total//1024//1024} MB]")
        except Exception as ex:
            print(f"  !! {s_}: {ex}"); fail += 1
        time.sleep(0.3)

    json.dump({s_: {"name": target[s_], "size": by_name[target[s_]][0]} for s_ in target},
              open(MAP, "w"), ensure_ascii=False, indent=2)
    print(f"\nГОТОВО: {ok} скачано, {fail} ошибок → {OUT}")


if __name__ == "__main__":
    main()
