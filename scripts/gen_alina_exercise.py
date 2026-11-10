#!/usr/bin/env python3
"""Фотореалистичная Алина выполняет упражнение (image-to-image с кадра видео Vahva).

Поза берётся с кадра видео (референс), лицо/фигура — с референсов Алины.
Запуск: python3 gen_alina_exercise.py --slug goblet-squat [--body front|back|side] [--aspect 3:4]
"""
import json
import os
import re
import sys
import time
import argparse
import subprocess
import urllib.request

ROOT = "/home/hermes/alina-body"
VIDEO_DIR = f"{ROOT}/inbox/vahva-fitness/videos"
FRAME_DIR = f"{ROOT}/alina-media/vahva/frames"
OUT_DIR = f"{ROOT}/alina-media/vahva/exercise"
API = "https://api.kie.ai"
CHAR_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char"

# русское название упражнения для промпта (ключ — slug видео)
EX_NAME = {
    "goblet-squat": "goblet squat holding a dumbbell at chest height",
    "bulgarian-split-squat": "bulgarian split squat",
    "single-leg-deadlift": "single leg deadlift",
    "push-up-with-protraction": "push-up with scapular protraction",
}


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет kie.ai ключа")


def sb_creds():
    u = k = None
    for line in open(os.path.expanduser("~/credentials/threads.env")):
        line = line.strip()
        if line.startswith("SUPABASE_URL="):
            u = line.split("=", 1)[1].strip()
        if line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
            k = line.split("=", 1)[1].strip()
    return u, k


def duration(path):
    try:
        out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                       "format=duration", "-of", "csv=p=0", path], text=True).strip()
        return float(out)
    except Exception:
        return None


def extract_frame(video, out_jpg, t_frac=0.45):
    d = duration(video)
    ss = d * t_frac if d else 5
    subprocess.run(["ffmpeg", "-y", "-ss", str(ss), "-i", video, "-frames:v", "1",
                    "-q:v", "2", out_jpg], check=True, capture_output=True)
    return os.path.exists(out_jpg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--body", default="front", choices=["front", "back", "side"])
    ap.add_argument("--aspect", default="3:4")
    args = ap.parse_args()

    key = load_key()
    sb_url, sb_key = sb_creds()
    os.makedirs(FRAME_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    video = os.path.join(VIDEO_DIR, args.slug + ".mp4")
    if not os.path.exists(video):
        sys.exit(f"нет видео {video}")
    frame = os.path.join(FRAME_DIR, f"{args.slug}.jpg")
    if not extract_frame(video, frame):
        sys.exit("кадр не извлечён")

    def upload(src, obj):
        data = open(src, "rb").read()
        req = urllib.request.Request(f"{sb_url}/storage/v1/object/alina-media/{obj}", data=data,
            method="POST", headers={"apikey": sb_key, "Authorization": "Bearer " + sb_key,
            "Content-Type": "image/jpeg", "x-upsert": "true"})
        urllib.request.urlopen(req, timeout=120)
        return f"{sb_url}/storage/v1/object/public/alina-media/{obj}"

    frame_url = upload(frame, f"vahva/frames/{args.slug}.jpg")
    face_url = f"{CHAR_BASE}/face-young-1.jpg"
    body_url = f"{CHAR_BASE}/body-{args.body}.jpg"
    print("frame:", frame_url)
    print("face:", face_url)
    print("body:", body_url)

    ex = EX_NAME.get(args.slug, args.slug.replace("-", " "))
    prompt = (
        f"Photorealistic full-body photo of a young athletic woman (Alina, fitness trainer, early 20s, "
        f"sleek dark hair in a ponytail) performing a {ex}. She wears a coral-pink sports bra and sage green "
        f"leggings with white sneakers. Home workout setting, light neutral background, warm natural light, "
        f"even natural skin tone with no redness or flush on the nose and face. Keep the EXACT same exercise "
        f"and pose as the reference frame — do not change the movement or body position. Replace the person "
        f"with Alina's face and figure. Sharp focus, professional fitness photography."
    )

    inp = {"prompt": prompt, "image_input": [frame_url, face_url, body_url],
           "aspect_ratio": args.aspect, "resolution": "1K", "output_format": "jpg"}
    req = urllib.request.Request(API + "/api/v1/jobs/createTask",
        data=json.dumps({"model": "nano-banana-2", "input": inp}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if r.get("code") != 200:
        sys.exit(f"createTask: {json.dumps(r)[:300]}")
    tid = r["data"]["taskId"]
    print("taskId:", tid)

    url = None
    t0 = time.time()
    while time.time() - t0 < 240:
        time.sleep(6)
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            API + f"/api/v1/jobs/recordInfo?taskId={tid}",
            headers={"Authorization": "Bearer " + key}), timeout=60).read()).get("data", {})
        st = d.get("state")
        if st == "success":
            url = (d["response"].get("resultUrls") or [None])[0]
            break
        if st == "fail":
            sys.exit(f"fail: {json.dumps(d)[:300]}")
    if not url:
        sys.exit("timeout")

    out = os.path.join(OUT_DIR, f"{args.slug}-alina.jpg")
    urllib.request.urlretrieve(url, out)
    pub = upload(out, f"vahva/exercise/{args.slug}-alina.jpg")
    print("OK:", out)
    print("PUBLIC:", pub)


if __name__ == "__main__":
    main()
