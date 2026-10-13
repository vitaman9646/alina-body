#!/usr/bin/env python3
"""Постинг одного дня контент-плана в Threads + Instagram.

Использование: python3 post_day.py --day 1 [--dry-run]
Парсит content_plan.md (Threads) и content_plan_instagram.md (Instagram),
берёт фото из Supabase alina-media/social/ (threads_dNN_pM.jpg, ig_dNN.jpg),
постит: Threads = 3 поста (2 лёгких + 1 конверсия с реплаем-ссылкой), Instagram = 1 пост.
"""
import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

BASE = "/home/hermes/alina-body/content"
SOCIAL = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/social"

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); env[k.strip()] = v.strip()
    return env

def parse_threads(path, day):
    """Возвращает список постов дня: (kind, text, reply_text), kind in ('light','conversion')."""
    posts, cur_day = [], 0
    cur_kind = cur_text = cur_reply = None
    def flush():
        if cur_kind:
            posts.append((cur_kind, cur_text, cur_reply))
    for line in open(path, encoding="utf-8"):
        st = line.rstrip().strip()
        m = re.match(r"^### День (\d+)$", st)
        if m:
            flush()
            cur_day = int(m.group(1)); cur_kind = cur_text = cur_reply = None
            continue
        if cur_day != day:
            continue
        if st.startswith("🟢 "):
            flush()
            cur_kind, cur_text, cur_reply = "light", st[len("🟢 "):].strip().strip('"'), None
        elif st.startswith("🔴"):
            flush()
            cur_kind, cur_text, cur_reply = "conversion", None, None
        elif st.startswith("Пост: "):
            cur_text = st[len("Пост: "):].strip().strip('"')
        elif st.startswith("💬 Реплай: "):
            cur_reply = st[len("💬 Реплай: "):].strip().strip('"')
    flush()
    return posts

def parse_ig(path, day):
    """Возвращает caption дня (текст + хэштеги)."""
    cur_day, caption_lines, hashtags, in_caption = 0, [], [], False
    for line in open(path, encoding="utf-8"):
        s = line.rstrip()
        m = re.match(r"^### День (\d+)$", s.strip())
        if m:
            cur_day = int(m.group(1)); in_caption = False
            continue
        if cur_day != day:
            continue
        st = s.strip()
        if st.startswith("✍️ "):
            in_caption = True; caption_lines = [st[2:].strip()]
        elif in_caption and st.startswith("#"):
            hashtags.append(st)
        elif in_caption and st and not st.startswith(("🟢", "🔴", "📸")):
            caption_lines.append(st)
        elif in_caption and st.startswith("📸"):
            in_caption = False
    cap = "\n".join(caption_lines)
    if hashtags:
        cap += "\n\n" + " ".join(hashtags)
    return cap

def threads_api(token, method, **params):
    url = f"https://graph.threads.net/v1.0/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read().decode() or "{}").get("error", {}).get("message", f"HTTP {e.code}")
    if "error" in resp:
        return None, resp["error"].get("message", "unknown")
    return resp, None

def ig_api(token, method, **params):
    url = f"https://graph.instagram.com/v21.0/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + token})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read().decode() or "{}").get("error", {}).get("message", f"HTTP {e.code}")
    if "error" in resp:
        return None, resp["error"].get("message", "unknown")
    return resp, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int)
    ap.add_argument("--auto", action="store_true", help="постить следующий незапощенный день (1..30)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    POSTED_FILE = f"{BASE}/posted_days.txt"

    if args.auto:
        posted = set()
        if os.path.exists(POSTED_FILE):
            posted = {int(x) for x in open(POSTED_FILE).read().split() if x.isdigit()}
        d = next((n for n in range(1, 31) if n not in posted), None)
        if d is None:
            print("Все 30 дней уже запощены.")
            return
    else:
        d = args.day

    threads = parse_threads(f"{BASE}/content_plan.md", d)
    ig_cap = parse_ig(f"{BASE}/content_plan_instagram.md", d)
    edu_posts = json.load(open(f"{BASE}/edu_posts.json"))
    edu_by_day = {e["day"]: e for e in edu_posts}
    edu_img = {4: "edu_squat", 8: "edu_glute-bridge", 12: "edu_plank", 16: "edu_warmup"}

    tenv = load_env(os.path.expanduser("~/credentials/threads.env"))
    ienv = load_env(os.path.expanduser("~/credentials/instagram.env"))
    ttok = tenv["THREADS_ACCESS_TOKEN"]; tuid = tenv.get("THREADS_USER_ID", "29048751384731011")
    itok = ienv["INSTAGRAM_ACCESS_TOKEN"]

    print(f"=== День {d} ===\nThreads постов: {len(threads)} | Instagram: {'есть' if ig_cap else 'нет'}")

    # Threads
    for i, (kind, text, reply) in enumerate(threads, 1):
        img = f"{SOCIAL}/threads_d{d:02d}_p{i}.jpg"
        if args.dry_run:
            print(f"\n[THREADS {i}/{len(threads)}] ({kind})")
            print(f"  text: {text[:100]}")
            print(f"  image: {img}")
            if reply:
                print(f"  reply: {reply}")
            continue
        resp, err = threads_api(ttok, f"{tuid}/threads", media_type="IMAGE", text=text, image_url=img, alt_text="Алина — домашний фитнес")
        if err:
            print(f"  ❌ Threads пост {i}: {err}"); continue
        cid = resp.get("id")
        resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
        if err:
            print(f"  ❌ Threads публикация {i}: {err}"); continue
        tid = resp.get("id")
        print(f"  ✅ Threads пост {i}: {tid}")
        if reply:
            resp, err = threads_api(ttok, f"{tuid}/threads", media_type="TEXT", text=reply, reply_to_id=tid)
            if err:
                print(f"  ❌ Threads реплай {i}: {err}"); continue
            rcid = resp.get("id")
            resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=rcid)
            if err:
                print(f"  ❌ Threads публикация реплая {i}: {err}"); continue
            print(f"  ✅ Threads реплай {i}: {resp.get('id')}")

    # Instagram
    if ig_cap:
        img = f"{SOCIAL}/ig_d{d:02d}.jpg"
        if args.dry_run:
            print(f"\n[INSTAGRAM]\n  image: {img}\n  caption: {ig_cap[:120]}")
        else:
            import subprocess
            r = subprocess.run(
                ["python3", "/home/hermes/alina-body/scripts/ig_post.py", "--image", img, "--caption", ig_cap],
                capture_output=True, text=True, timeout=400)
            if r.returncode == 0:
                print("  ✅ Instagram опубликован")
            else:
                print(f"  ❌ Instagram: {r.stderr[-200:]}")

    # Обучающий пост (дополнительный, в дни 4/8/12/16)
    edu = edu_by_day.get(d)
    if edu:
        img = f"{SOCIAL}/{edu_img[d]}.jpg"
        if args.dry_run:
            print(f"\n[EDU Threads] {edu['title']}: {edu['threads'][:60]}")
            print(f"[EDU IG] {edu['title']}: {edu['ig'][:60]}")
        else:
            resp, err = threads_api(ttok, f"{tuid}/threads", media_type="IMAGE", text=edu["threads"], image_url=img, alt_text="Алина — техника упражнения")
            if err:
                print(f"  ❌ EDU Threads: {err}")
            else:
                cid = resp.get("id")
                resp, err = threads_api(ttok, f"{tuid}/threads_publish", creation_id=cid)
                if err:
                    print(f"  ❌ EDU Threads publish: {err}")
                else:
                    print(f"  ✅ EDU Threads: {resp.get('id')}")
            import subprocess
            r = subprocess.run(["python3", "/home/hermes/alina-body/scripts/ig_post.py", "--image", img, "--caption", edu["ig"]], capture_output=True, text=True, timeout=400)
            if r.returncode == 0:
                print("  ✅ EDU Instagram опубликован")
            else:
                print(f"  ❌ EDU Instagram: {r.stderr[-200:]}")

    if not args.dry_run:
        with open(POSTED_FILE, "a") as f:
            f.write(f"{d}\n")
        print(f"День {d} отмечен как запощенный.")

if __name__ == "__main__":
    main()
