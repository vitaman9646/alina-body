#!/usr/bin/env python3
"""Транскрибация 21 видео-рецепта SWBAND.CO (2 параллельно, small, ru)."""
import subprocess, os, glob, concurrent.futures

VIDEO_DIR = "/home/hermes/alina-body/inbox/swbandco-fitness/video"
OUT_DIR = "/home/hermes/alina-body/inbox/swbandco-fitness/transcripts"
os.makedirs(OUT_DIR, exist_ok=True)
PY = "/home/hermes/alina-body/.venv-tts/bin/python"
SCRIPT = "/home/hermes/alina-body/scripts/transcribe.py"
EXCLUDE = ["введение", "тренировк", "екомендаци", "рекомендаци"]

videos = [p for p in sorted(glob.glob(f"{VIDEO_DIR}/*.mp4"))
          if not any(x in os.path.basename(p).lower() for x in EXCLUDE)]
print(f"рецептов в очереди: {len(videos)}")

def transcribe(p):
    name = os.path.basename(p)
    out_txt = os.path.join(OUT_DIR, name.rsplit(".", 1)[0] + ".transcript.txt")
    if os.path.exists(out_txt) and os.path.getsize(out_txt) > 100:
        print(f"skip (есть): {name}", flush=True)
        return name
    print(f"▶ {name}", flush=True)
    try:
        r = subprocess.run([PY, SCRIPT, p, "--model", "small", "--language", "ru", "--out", OUT_DIR],
                           capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"❌ {name}: {(r.stdout or '')[-200:]}\n{r.stderr[-200:]}", flush=True)
        else:
            print(f"✅ {name}", flush=True)
    except Exception as e:
        print(f"❌ {name}: {e}", flush=True)
    return name

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    list(ex.map(transcribe, videos))
print("ВСЁ ГОТОВО:", OUT_DIR)
