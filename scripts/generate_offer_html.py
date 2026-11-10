#!/usr/bin/env python3
"""Генерирует public/offer.html из текста оферты. Разбивает на разделы I-XII."""
import re

src = open("/tmp/offer-example.txt").read()

src = re.sub(r"\n?===== СТР \d+ =====\n?", "\n", src)
src = src.replace("\n", " ")
src = re.sub(r"[ \t]+", " ", src).strip()

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

head_re = re.compile(r"(?= (?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|ХII)\.\s+[А-ЯЁA-Z])")
positions = [m.start() for m in head_re.finditer(src)]

# корректные срезы: от позиции до следующей позиции
chunks = [src[:positions[0]].strip()]
for i in range(len(positions)):
    end = positions[i + 1] if i + 1 < len(positions) else len(src)
    chunks.append(src[positions[i]:end].strip())

out = []
m = re.match(r"^(ПУБЛИЧНАЯ ОФЕРТА)\s+(О реализации товаров/работ/услуг)\s+(Дата вступления в силу «10» ноября 2026 г\.)(.*)$", chunks[0], re.S)
if m:
    out.append("<h1>" + esc(m.group(1)) + "</h1>")
    out.append("<p class=\"sub\">" + esc(m.group(2)) + "</p>")
    out.append("<p class=\"date\">" + esc(m.group(3)) + "</p>")
    if m.group(4).strip():
        out.append("<p>" + esc(m.group(4).strip()) + "</p>")
else:
    out.append("<p>" + esc(chunks[0]) + "</p>")

def split_section(ch):
    """Вернуть (title, body) или (None, ch) если заголовок не выделить."""
    # пункты N.M.
    mm = re.search(r"(?= \d{1,2}\.\d{1,2}\.)", ch)
    if mm and mm.start() < 130:
        return ch[:mm.start()].strip(), ch[mm.start():].strip()
    # "Самозанятый" (раздел XII. Сведения об Исполнителе ... Самозанятый ...)
    mm = re.search(r"(?= Самозанятый )", ch)
    if mm and mm.start() < 80:
        return ch[:mm.start()].strip(), ch[mm.start():].strip()
    # двоеточие (раздел I. Термины и определения:)
    mm = re.search(r"(?=: )", ch)
    if mm and mm.start() < 80:
        return ch[:mm.start() + 1].strip(), ch[mm.start() + 1:].strip()
    return None, ch

for ch in chunks[1:]:
    title, body = split_section(ch)
    if title:
        out.append("<h2>" + esc(title) + "</h2>")
        if body:
            out.append("<p>" + esc(body) + "</p>")
    else:
        out.append("<p>" + esc(ch) + "</p>")

html = """<!doctype html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Публичная оферта — Alina Body</title>
<meta name="robots" content="index, follow" />
<style>
  :root { --cream:#FBF7F2; --ink:#2D2A32; --muted:#7A716B; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: var(--cream); color: var(--ink); line-height: 1.65; }
  .wrap { max-width: 760px; margin: 0 auto; padding: 48px 20px 80px; }
  h1 { font-size: 26px; letter-spacing: -0.01em; margin-bottom: 6px; }
  .sub { font-size: 15px; color: var(--muted); margin-bottom: 2px; }
  .date { color: var(--muted); font-size: 14px; margin-bottom: 28px; }
  h2 { font-size: 18px; margin: 26px 0 10px; padding-top: 18px; border-top: 1px solid rgba(45,42,50,0.08); }
  p { font-size: 15px; color: #3a3632; margin: 10px 0; }
</style>
</head>
<body>
<div class="wrap">
""" + "\n".join(out) + """
</div>
</body>
</html>
"""

open("/home/hermes/alina-body/public/offer.html", "w").write(html)
print("OK offer.html:", len(html), "байт; разделов:", len(chunks) - 1)
