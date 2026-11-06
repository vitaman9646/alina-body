#!/usr/bin/env python3
"""Кадр видео Vahva (референс позы) → flat-иллюстрация в нашем стиле (image-to-image).

1. Для каждого <slug>.mp4 вытащить кадр (~40% длительности).
2. Загрузить кадр в Supabase (alina-media/vahva/frames/).
3. nano-banana-2 image-to-image: «перерисуй в flat-стиле, та же поза».
4. Сохранить в alina-media/vahva/exercise/<slug>.jpg (перезапись старых).

Запуск: python3 scripts/style_vahva_frames.py [--limit N]
"""
import json, os, re, sys, time, subprocess, urllib.request, urllib.error

ROOT = "/home/hermes/alina-body"
VIDEO_DIR = f"{ROOT}/inbox/vahva-fitness/videos"
FRAME_DIR = f"{ROOT}/alina-media/vahva/frames"
OUT_DIR = f"{ROOT}/alina-media/vahva/exercise"
IMG_MAP = f"{ROOT}/content/vahva-image-map.json"
API = "https://api.kie.ai"

STYLE = ("Flat vector illustration, modern minimal fitness editorial style, faceless female figure with no "
         "facial features, side profile, slim elongated athletic proportions, dark plum hair in a ponytail "
         "with a small coral hair tie, coral-pink sports bra, sage green leggings, white sneakers with coral "
         "soles, peach-coral skin, plain solid cream background, large empty margins, soft blurred beige "
         "ellipse shadow on the floor, no outlines, no black strokes, flat two-tone shading only, no "
         "gradients, no text, no numbers, no arrows, square 1:1, centered single figure, clean negative space")


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет kie.ai")


def sb_creds():
    u = k = None
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if line.startswith("SUPABASE_URL="): u = line.split("=", 1)[1].strip()
        if line.startswith("SUPABASE_SERVICE_ROLE_KEY="): k = line.split("=", 1)[1].strip()
    return u, k


def duration(path):
    try:
        out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", path], text=True).strip()
        return float(out)
    except Exception:
        return None


def extract_frame(video, out_jpg):
    d = duration(video)
    ss = d * 0.4 if d else 5
    subprocess.run(["ffmpeg", "-y", "-ss", str(ss), "-i", video, "-frames:v", "1", "-q:v", "2", out_jpg],
                   check=True, capture_output=True)
    return os.path.exists(out_jpg)


def main():
    key = load_key()
    SB_URL, SB_KEY = sb_creds()
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    os.makedirs(FRAME_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    vids = sorted(f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4"))
    if limit:
        vids = vids[:limit]
    print(f"видео: {len(vids)}")

    mapping = json.load(open(IMG_MAP))["generated"]

    def post(path, payload):
        req = urllib.request.Request(API + path, data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())

    def get(path):
        req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + key})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())

    def upload(src, obj):
        data = open(src, "rb").read()
        req = urllib.request.Request(f"{SB_URL}/storage/v1/object/alina-media/{obj}", data=data,
            method="POST", headers={"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY,
            "Content-Type": "image/jpeg", "x-upsert": "true"})
        urllib.request.urlopen(req, timeout=120)
        return f"{SB_URL}/storage/v1/object/public/alina-media/{obj}"

    ok = fail = 0
    for vf in vids:
        slug = vf[:-4]
        video = os.path.join(VIDEO_DIR, vf)
        frame = os.path.join(FRAME_DIR, f"{slug}.jpg")
        try:
            if not extract_frame(video, frame):
                print(f"  !! {slug}: кадр не извлечён"); fail += 1; continue
        except Exception as ex:
            print(f"  !! {slug}: ffmpeg {ex}"); fail += 1; continue

        try:
            frame_url = upload(frame, f"vahva/frames/{slug}.jpg")
        except Exception as ex:
            print(f"  !! {slug}: upload {ex}"); fail += 1; continue

        prompt = (f"Redraw this image as a {STYLE} Keep the exact same exercise and pose as the reference. "
                  f"The figure is a faceless female, not the original person.")
        try:
            r = post("/api/v1/jobs/createTask", {"model": "nano-banana-2",
                "input": {"prompt": prompt, "image_input": [frame_url], "aspect_ratio": "1:1",
                          "resolution": "1K", "output_format": "jpg"}})
            tid = r["data"]["taskId"]
        except Exception as ex:
            print(f"  !! {slug}: submit {ex}"); fail += 1; continue

        # поллить
        url = None
        t0 = time.time()
        while time.time() - t0 < 240:
            try:
                d = get(f"/api/v1/jobs/recordInfo?taskId={tid}").get("data", {})
            except Exception:
                time.sleep(5); continue
            st = d.get("state")
            if st == "success":
                url = (d["response"].get("resultUrls") or [None])[0]; break
            if st == "fail":
                break
            time.sleep(6)
        if not url:
            print(f"  !! {slug}: не сгенерилось"); fail += 1; continue

        dst = os.path.join(OUT_DIR, f"{slug}.jpg")
        try:
            urllib.request.urlretrieve(url, dst)
            mapping[slug] = dst
            ok += 1
            print(f"  ✓ {slug} ({ok}/{len(vids)})")
        except Exception as ex:
            print(f"  !! {slug}: download {ex}"); fail += 1

    json.dump({"generated": mapping, "total": len(mapping)}, open(IMG_MAP, "w"), ensure_ascii=False, indent=2)
    print(f"\nГОТОВО: {ok} ок, {fail} ошибок")


if __name__ == "__main__":
    main()
