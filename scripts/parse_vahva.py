#!/usr/bin/env python3
"""Разбор курса Vahva Fitness «Athlete 20XX» в структурированный JSON.

Вход: inbox/vahva-fitness/ (скачанные PDF, без видео).
Выход: content/vahva-fitness.json — {phases:[{phase,weeks:[{week,days:[{day,title,time,rest,exercises:[...]}]}]}], lessons:[...], start_here}.

Дубли недель 3–4 (повтор недель 1–2) отбрасываются по контенту.
Запуск: .venv-tts/bin/python scripts/parse_vahva.py
"""
import os, re, json

BASE = "/home/hermes/alina-body/inbox/vahva-fitness"
OUT = "/home/hermes/alina-body/content/vahva-fitness.json"

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def pdf_text(p):
    d = fitz.open(p)
    return "\n".join(pg.get_text() for pg in d)


def walk_pdfs(root):
    """os.walk вместо glob — в путях есть скобки [SWBAND.CO], которые glob ловит как класс символов."""
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".pdf"):
                yield os.path.join(dirpath, f), f


EX_RE = re.compile(r'^([A-F]\d+)\s+([^\n]+?)\n\s*(\d+)\s+sets x ([^\n]+)', re.M)
NEXT_EX = re.compile(r'\n[A-F]\d+\s+[A-Za-z]')
PAGE_MARK = re.compile(r'^\d+/\d+$')
DAY_ORDER = ["monday", "tuesday", "thursday", "friday"]


def parse_workout(text):
    # убрать номера страниц («3/6») — они разрывают «имя → sets x» на переносах страниц
    text = "\n".join(l for l in text.split("\n") if not PAGE_MARK.match(l.strip()))
    title = text.split("\n")[0].strip()
    m = re.search(r"Estimated time:\s*([^\n]+)", text)
    est = m.group(1).strip() if m else ""
    m = re.search(r"Take\s+([^\n]+?)\s+of rest between sets", text)
    rest = m.group(1).strip() if m else ""
    exs = []
    for m in EX_RE.finditer(text):
        code, name, sets, reps = m.groups()
        seg = text[m.end():]
        nxt = NEXT_EX.search(seg)
        if nxt:
            seg = seg[:nxt.start()]
        tgt = re.search(r'Target areas?:\s*([^\n]+)', seg)
        target = tgt.group(1).strip() if tgt else ""
        w = re.search(r'Recommended weight:\s*([^\n]+)', seg)
        weight = w.group(1).strip() if w else ""
        cues = []
        cm = re.search(r'Important cues:', seg)
        if cm:
            for line in seg[cm.end():].split("\n"):
                l = line.strip()
                if not l or PAGE_MARK.match(l) or l.startswith(("Target", "Recommended", "Important")):
                    continue
                if l.lower().startswith("workout finished"):
                    break
                cues.append(l)
        exs.append({
            "code": code, "name": name.strip(), "sets": int(sets), "reps": reps.strip(),
            "target": target, "weight": weight, "cues": cues,
        })
    return {"title": title, "estimated_time": est, "rest": rest, "exercises": exs}


def main():
    # workout PDFs: day-phase-week, dedupe by (phase, week)
    seen = {}
    for p, fn in walk_pdfs(BASE):
        m = re.match(r'(monday|tuesday|thursday|friday)-phase-(\d)-week-(\d)\.pdf', fn, re.I)
        if not m:
            continue
        day, phase, week = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        key = (phase, week, day)
        if key not in seen:
            seen[key] = p

    phases = {}
    for (phase, week, day), p in sorted(seen.items()):
        w = parse_workout(pdf_text(p))
        w["day"] = day
        w["week"] = week
        phases.setdefault(phase, {}).setdefault(week, []).append(w)

    phases_out = []
    for ph in sorted(phases):
        weeks = []
        for wk in sorted(phases[ph]):
            days = sorted(phases[ph][wk], key=lambda d: DAY_ORDER.index(d["day"]))
            weeks.append({"week": wk, "days": days})
        phases_out.append({"phase": ph, "weeks": weeks})

    # lessons (папка "...2 Lessons", файлы "N SC.pdf")
    lessons = []
    for p, fn in walk_pdfs(BASE):
        if "2 Lessons" not in p:
            continue
        m = re.match(r'(\d+)\s*SC\.pdf', fn, re.I)
        if not m:
            continue
        text = pdf_text(p).strip()
        # заголовок урока — строка после "Mark as complete"
        title = ""
        tm = re.search(r'Mark as complete\s*\n\s*([^\n]+)', text)
        if tm:
            title = tm.group(1).strip()
        lessons.append({"n": int(m.group(1)), "file": fn, "title": title, "text": text})
    lessons.sort(key=lambda x: x["n"])

    # start here
    start_here = ""
    for p, fn in walk_pdfs(BASE):
        if "1 Start Here" in p and fn.lower().startswith("sc"):
            start_here = pdf_text(p).strip()

    out = {
        "source": "Vahva Fitness – Athlete 20XX Method",
        "phases": phases_out,
        "lessons": lessons,
        "start_here": start_here,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    n_ex = sum(len(d["exercises"]) for ph in phases_out for wk in ph["weeks"] for d in wk["days"])
    n_days = sum(len(wk["days"]) for ph in phases_out for wk in ph["weeks"])
    print(f"фаз: {len(phases_out)}, уникальных недель: {sum(len(p['weeks']) for p in phases_out)}, тренировочных дней: {n_days}, упражнений: {n_ex}, уроков: {len(lessons)}")
    print("записано:", OUT)


if __name__ == "__main__":
    main()
