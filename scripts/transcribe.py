#!/usr/bin/env python3
"""Транскрибация видео/аудио курсов через faster-whisper (локально, бесплатно).

Обрабатывает ДЛИННЫЕ файлы чанками (по --chunk-seconds, по умолчанию 600 с = 10 мин),
чтобы не грузить в память весь аудиофайл разом (иначе 4-часовое видео → ~1 ГБ float32
→ OOM-kill на 4 ГБ VPS). Каждый чанк = отдельный 16 kHz mono wav.

Использование:
  .venv-tts/bin/python transcribe.py FILE [--model small|medium] [--language ru]
                                         [--chunk-seconds 600] [--out DIR]
Пишет расшифровку с таймкодами в <имя>.transcript.txt (рядом с файлом или в --out).
Бенчмарк (2026-10-20, VPS 2×Ryzen 7950X3D, int8, beam=5): small ≈ 0.30–0.50× realtime.
"""
import os, sys, argparse, subprocess, tempfile, time


def dur_of(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path]).decode().strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default="ru")
    ap.add_argument("--chunk-seconds", type=int, default=600)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = os.path.abspath(args.file)
    if not os.path.exists(src):
        sys.exit(f"файл не найден: {src}")

    from faster_whisper import WhisperModel
    m = WhisperModel(args.model, device="cpu", compute_type="int8")

    dur = dur_of(src)
    lines = []
    start = 0.0
    i = 0
    t0 = time.time()
    while start < dur:
        wav = tempfile.mktemp(suffix=f".c{i}.wav")
        subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", src, "-t", str(args.chunk_seconds),
                        "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", wav],
                       check=True, capture_output=True)
        segments, _ = m.transcribe(wav, language=args.language, beam_size=5, vad_filter=True)
        for s in segments:
            lines.append((start + s.start, start + s.end, s.text.strip()))
        os.remove(wav)
        start += args.chunk_seconds
        i += 1
        print(f"  чанк {i}: до {min(start, dur)/60:.0f} мин из {dur/60:.0f}", flush=True)

    elapsed = time.time() - t0
    out = args.out or os.path.dirname(src)
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    outp = os.path.join(out, f"{base}.transcript.txt")
    with open(outp, "w", encoding="utf-8") as f:
        for a, b, txt in lines:
            f.write(f"[{a:07.1f}-{b:07.1f}] {txt}\n")

    print(f"Готово: {os.path.basename(src)} ({dur/60:.1f} мин) -> {outp}")
    print(f"  скорость: {elapsed:.0f} с на {dur:.0f} с аудио (realtime {elapsed/dur:.2f}x)")


if __name__ == "__main__":
    main()
