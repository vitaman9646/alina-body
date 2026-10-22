#!/usr/bin/env python3
"""Очередь транскрибации видео SWBAND.CO для Виталия (2 параллельно, small, ru)."""
import subprocess, os, glob, concurrent.futures

VIDEO_DIR = "/home/hermes/alina-body/inbox/swbandco-fitness/video"
OUT_DIR = "/home/hermes/alina-body/inbox/swbandco-fitness/transcripts"
os.makedirs(OUT_DIR, exist_ok=True)
PY = "/home/hermes/alina-body/.venv-tts/bin/python"
SCRIPT = "/home/hermes/alina-body/scripts/transcribe.py"

videos = sorted(glob.glob(f"{VIDEO_DIR}/*.mp4"))
def sort_key(p):
    n = os.path.basename(p).lower()
    if "тренировк" in n:
        return (0, n)
    if "екомендаци" in n or "рекомендаци" in n:
        return (1, n)
    return (2, n)
videos = sorted(videos, key=sort_key)
print(f"видео в очереди: {len(videos)}")

def transcribe(p):
    name = os.path.basename(p)
    print(f"▶ {name}", flush=True)
    try:
        r = subprocess.run([PY, SCRIPT, p, "--model", "small", "--language", "ru", "--out", OUT_DIR],
                           capture_output=True, text=True, timeout=10800)
        tail = (r.stdout or "")[-400:]
        if r.returncode != 0:
            print(f"❌ {name}: {tail}\n{r.stderr[-300:]}", flush=True)
        else:
            print(f"✅ {name}: {tail}", flush=True)
    except Exception as e:
        print(f"❌ {name}: исключение {e}", flush=True)
    return name

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    list(ex.map(transcribe, videos))

print("ВСЁ ГОТОВО: транскрипты в", OUT_DIR)
