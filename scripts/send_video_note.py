#!/usr/bin/env python3
"""Круглешка (видеосообщение) с Алиной: видео + озвучка TTS → Telegram video note.

Пайплайн:
  1) кадрируем видео в квадрат (1:1, по центру, 720x720)
  2) генерируем озвучку edge-tts (женский русский голос)
  3) накладываем звук, видео зацикливаем под длину аудио
  4) шлём в канал как video note

Использование:
  python3 send_video_note.py --video file.mp4 --text "Текст озвучки" [--voice ru-RU-DariyaNeural] [--dry-run]
"""
import os
import sys
import json
import argparse
import subprocess

VOICE = "ru-RU-DariyaNeural"
GTTS_PY = "/home/hermes/alina-body/.venv-tts/bin/python"
TMP = "/tmp/alina_vn"


def env_of(path):
    e = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1); e[k.strip()] = v.strip()
    return e


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAIL:", " ".join(cmd), "\n", r.stderr[-400:])
        sys.exit(1)
    return r.stdout.strip()


def crop_square(src, dst):
    w, h = map(int, sh(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", src]).split(","))
    s = min(w, h)
    x, y = (w - s) // 2, (h - s) // 2
    sh(["ffmpeg", "-y", "-i", src, "-vf", f"crop={s}:{s}:{x}:{y},scale=720:720",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "23", dst])


def tts(text, voice, dst):
    # gTTS (Google) — надёжный fallback; edge-tts заблокирован с IP этого сервера (403)
    code = "from gtts import gTTS; import sys; gTTS(sys.argv[1], lang='ru').save(sys.argv[2])"
    sh([GTTS_PY, "-c", code, text, dst])


def mux(video, audio, dst):
    sh(["ffmpeg", "-y", "-stream_loop", "-1", "-i", video, "-i", audio,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart", dst])


def send_note(token, chat_id, fpath):
    sh(["curl", "-sS", "--form-string", f"chat_id={chat_id}", "-F", f"video_note=@{fpath}",
        f"https://api.telegram.org/bot{token}/sendVideoNote"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    os.makedirs(TMP, exist_ok=True)
    sq = f"{TMP}/square.mp4"
    au = f"{TMP}/voice.mp3"
    out = f"{TMP}/note.mp4"

    crop_square(args.video, sq)
    tts(args.text, args.voice, au)
    mux(sq, au, out)

    if args.dry_run:
        print(f"Собрано (без отправки): {out}")
        print("Текст:", args.text[:80])
        return

    env = env_of(os.path.expanduser("~/credentials/telegram.env"))
    token = env["TELEGRAM_BOT_TOKEN"]
    channel = env["TELEGRAM_CHANNEL_ID"]
    send_note(token, channel, out)
    print("✅ video note отправлен в канал")


if __name__ == "__main__":
    main()
