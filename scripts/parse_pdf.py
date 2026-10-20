#!/usr/bin/env python3
"""Универсальный парсер PDF: текст + картинки, заголовки определяются автоматически.

Работает с ЛЮБЫМ шрифтом/вёрсткой — не привязан к конкретному размеру (старый
parse_recipes.py хардкодил 25pt). Заголовок = строка заметно крупнее или жирнее
основного текста. Картинки извлекаются через pymupdf и сохраняются рядом.

Использование:
  .venv-tts/bin/python scripts/parse_pdf.py PDF [--out DIR] [--head-ratio 1.25] [--head-delta 1.5]

Выход: DIR/<имя>.json  +  DIR/images/*.png
JSON: {source, pages, body_size, head_threshold, sections:[{title, level, content, images}]}
"""
import os, sys, re, json, argparse
from pathlib import Path

import pdfplumber
import fitz  # pymupdf — извлечение картинок


def dedup(t):
    """Убирает артефакт задвоения символов (ППДФ-шрифты: «ИИннссттррууммееннтт» → «Инструмент»)."""
    if len(t) < 5:
        return t
    dbl = sum(1 for i in range(len(t) - 1) if t[i] == t[i + 1] and not t[i].isspace())
    if dbl / len(t) > 0.2:
        out = []
        for ch in t:
            if out and out[-1] == ch and not ch.isspace():
                continue
            out.append(ch)
        return "".join(out)
    return t


def is_noise(t):
    """Отсев мусора: пустые строки, номера страниц, колонтитулы."""
    t = t.strip()
    if not t:
        return True
    if re.fullmatch(r"\d{1,4}", t):                      # просто номер страницы
        return True
    if re.fullmatch(r"[А-ЯЁA-Z][А-ЯЁA-Z .\-]{2,}\.{5,}\d+", t):  # оглавление с точками
        return True
    return False


def line_font(line):
    """(max_size, bold) строки."""
    sizes = [c["size"] for c in line["chars"]]
    mx = max(sizes) if sizes else 0.0
    fnames = {c.get("fontname", "") for c in line["chars"]}
    bold = any(re.search(r"bold|black|heavy|semibold|demi", f, re.I) for f in fnames)
    return mx, bold


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default=None, help="папка вывода (по умолчанию рядом с PDF)")
    ap.add_argument("--head-ratio", type=float, default=1.25,
                    help="во сколько раз крупнее основного текста = заголовок")
    ap.add_argument("--head-delta", type=float, default=1.5,
                    help="минимальный прирост размера в pt для заголовка")
    args = ap.parse_args()

    pdf_path = args.pdf
    base = Path(pdf_path).stem
    outdir = Path(args.out) if args.out else Path(pdf_path).parent / (base + "_parsed")
    imgdir = outdir / "images"
    imgdir.mkdir(parents=True, exist_ok=True)

    # 1) Текст с метаданными шрифта (pdfplumber)
    entries = []  # (page, top, size, text, bold)
    n_pages = 0
    with pdfplumber.open(pdf_path) as pdf:
        n_pages = len(pdf.pages)
        for pno, page in enumerate(pdf.pages):
            for ln in page.extract_text_lines():
                sz, bold = line_font(ln)
                t = dedup(ln["text"].strip())
                if is_noise(t):
                    continue
                entries.append((pno, round(ln["top"], 1), sz, t, bold))

    if not entries:
        print("Текст не найден (возможно, PDF — скан/картинки)."); sys.exit(1)

    entries.sort(key=lambda e: (e[0], e[1]))
    body_size = median([e[2] for e in entries])

    # 2) Классификация строк: заголовок / текст
    head_thr = max(body_size * args.head_ratio, body_size + args.head_delta)

    def is_heading(sz, bold, t):
        if len(t) > 90:
            return False
        if sz >= head_thr:
            return True
        if bold and len(t) <= 70 and sz >= body_size * 0.95:
            return True
        if t.isupper() and len(t) <= 70 and sz >= body_size * 1.05:
            return True
        return False

    # 3) Сборка секций: заголовок + следующие строки поменьше
    sections = []
    cur = None
    for pno, top, sz, t, bold in entries:
        if is_heading(sz, bold, t):
            if cur and cur["content"]:
                sections.append(cur)
            level = 1 if sz >= body_size * 1.5 else 2
            cur = {"title": t, "level": level, "content": [], "images": [], "page": pno + 1}
        else:
            if cur is None:
                cur = {"title": "(без заголовка)", "level": 3,
                       "content": [], "images": [], "page": pno + 1}
            cur["content"].append(t)
    if cur and cur["content"]:
        sections.append(cur)

    # 4) Извлечение картинок (fitz)
    image_files = []  # (page_index, rel_path)
    doc = fitz.open(pdf_path)
    for pno, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:  # CMYK и т.п. → RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.width < 60 or pix.height < 60:  # мусор/иконки
                    continue
                fname = f"p{pno + 1:03d}_x{xref}.png"
                pix.save(str(imgdir / fname))
                image_files.append((pno, str(imgdir / fname)))
            except Exception:
                continue
    doc.close()

    # привязка картинок к секциям по странице
    for pno, fpath in image_files:
        for s in sections:
            if s["page"] == pno + 1:
                s["images"].append(fpath)
                break

    out = {
        "source": pdf_path,
        "pages": n_pages,
        "body_size": round(body_size, 1),
        "head_threshold": round(head_thr, 1),
        "sections": [],
    }
    for s in sections:
        if s["content"] or s["images"]:
            out["sections"].append({
                "title": s["title"],
                "level": s["level"],
                "content": s["content"],
                "images": s["images"],
            })

    json_path = outdir / (base + ".json")
    json.dump(out, open(json_path, "w"), ensure_ascii=False, indent=2)
    print(f"страниц: {n_pages}")
    print(f"основной текст: {out['body_size']}pt | заголовок от: {out['head_threshold']}pt")
    print(f"секций: {len(out['sections'])} | картинок: {len(image_files)}")
    print(f"JSON: {json_path}")
    for s in out["sections"][:20]:
        img = f"  📷 {len(s['images'])}" if s["images"] else ""
        print(f"  [{s['level']}] {s['title'][:55]}{img}")


if __name__ == "__main__":
    main()
