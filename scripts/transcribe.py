#!/usr/bin/env python3
"""Транскрибация видео/аудио курсов через faster-whisper (локально, бесплатно).

Использование:
  .venv-tts/bin/python transcribe.py FILE [--model small|medium] [--language ru] [--out DIR]
  FILE — mp4/mp3/m4a/wav (видео или аудио)

Пишет расшифровку с таймкодами в <имя>.transcript.txt (рядом с файлом или в --out).
Бенчмарк (2026-10-20, VPS 2×Ryzen 7950X3D, int8, beam=5): small ≈ 0.30× realtime (~18 с на 1 мин аудио).
"""
import os, sys, argparse, subprocess, tempfile, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default="ru")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = os.path.abspath(args.file)
    if not os.path.exists(src):
        sys.exit(f"файл не найден: {src}")

    from faster_whisper import WhisperModel
    m = WhisperModel(args.model, device="cpu", compute_type="int8")

    # аудио → 16kHz mono wav (ffmpeg надёжнее PyAV для любых контейнеров)
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                    "-f", "wav", wav], check=True, capture_output=True)

    t = time.time()
    segments, info = m.transcribe(wav, language=args.language, beam_size=5, vad_filter=True)
    lines = [f"[{s.start:06.1f}-{s.end:06.1f}] {s.text.strip()}" for s in segments]
    elapsed = time.time() - t
    os.remove(wav)

    out = args.out or os.path.dirname(src)
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    outp = os.path.join(out, f"{base}.transcript.txt")
    with open(outp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    dur = info.duration
    print(f"Готово: {os.path.basename(src)} ({dur/60:.1f} мин) -> {outp}")
    print(f"  скорость: {elapsed:.0f} с на {dur:.0f} с аудио (realtime {elapsed/dur:.2f}x)")


if __name__ == "__main__":
    main()
