#!/usr/bin/env python3
"""Generate Pinterest pins (2:3, 1000x1500) from existing Alina visuals.

Reads content/pinterest-plan.json, cover-crops each source image to 2:3,
adds a bottom dark gradient + SEO title overlay + brand footer, saves locally
to alina-media/pinterest/ and uploads to Supabase alina-media/pinterest/ (x-upsert).

Usage:
  python3 scripts/gen_pins.py --dry-run           # generate locally only, no upload
  python3 scripts/gen_pins.py --limit 2           # only first N pins
  python3 scripts/gen_pins.py --skip-upload       # same as --dry-run
"""
import argparse
import io
import json
import os
import re

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = "/home/hermes/alina-body"
PLAN = os.path.join(REPO, "content/pinterest-plan.json")
OUT_DIR = os.path.join(REPO, "alina-media/pinterest")
CREDS = os.path.expanduser("~/credentials/threads.env")
PUBLIC_BASE = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media"

PIN_W, PIN_H = 1000, 1500
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MAX_TITLE_W = 880
TITLE_SIZE = 76
FOOTER_SIZE = 34


def load_creds():
    d = {}
    for line in open(CREDS):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d["SUPABASE_URL"], d["SUPABASE_SERVICE_ROLE_KEY"]


def resolve_source(img):
    """Return PIL.Image for a plan 'img' entry (Supabase path or local:path)."""
    if img.startswith("local:"):
        path = img[len("local:"):]
        return Image.open(path).convert("RGB"), "contain"
    url = f"{PUBLIC_BASE}/{img}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB"), "cover"


def cover_crop(img, w, h):
    """Scale to cover w×h and center-crop."""
    sw, sh = img.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def contain_on_white(img, w, h):
    """Scale to fit within w×h and center on a white canvas."""
    sw, sh = img.size
    scale = min(w / sw, h / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (250, 249, 246))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    return canvas


def make_gradient(w, h, top_alpha, bottom_alpha):
    """Vertical gradient: transparent at top -> dark at bottom."""
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        alpha = int(top_alpha + (bottom_alpha - top_alpha) * t)
        grad.putpixel((0, y), alpha)
    grad = grad.resize((w, h))
    overlay = Image.new("RGBA", (w, h), (18, 16, 20, 255))
    overlay.putalpha(grad)
    return overlay


def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit_title(draw, text, start_size, max_w, max_lines):
    size = start_size
    while size > 40:
        font = ImageFont.truetype(FONT_BOLD, size)
        lines = wrap_text(draw, text, font, max_w)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    font = ImageFont.truetype(FONT_BOLD, size)
    return font, wrap_text(draw, text, font, max_w)[:max_lines]


def build_pin(src_img, mode, title):
    if mode == "contain":
        base = contain_on_white(src_img, PIN_W, PIN_H)
    else:
        base = cover_crop(src_img, PIN_W, PIN_H)

    # bottom gradient for text legibility
    grad = make_gradient(PIN_W, PIN_H, 0, 235)
    base = base.convert("RGBA")
    base.alpha_composite(grad)
    base = base.convert("RGB")

    draw = ImageDraw.Draw(base)
    # title
    tfont, lines = fit_title(draw, title, TITLE_SIZE, MAX_TITLE_W, 3)
    line_h = tfont.getbbox("Ag")[3] - tfont.getbbox("Ag")[1] + 12
    total_h = line_h * len(lines)
    y = PIN_H - 130 - total_h
    for ln in lines:
        w = draw.textlength(ln, font=tfont)
        x = (PIN_W - w) // 2
        # soft shadow for contrast
        draw.text((x + 2, y + 2), ln, font=tfont, fill=(0, 0, 0, 140))
        draw.text((x, y), ln, font=tfont, fill=(255, 255, 255))
        y += line_h

    # footer brand
    ffont = ImageFont.truetype(FONT_REG, FOOTER_SIZE)
    foot = "alina-body.fitness"
    fw = draw.textlength(foot, font=ffont)
    draw.text(((PIN_W - fw) // 2, PIN_H - 62), foot, font=ffont, fill=(235, 235, 235))
    return base


def slug_filename(slug, variant=""):
    return f"pin-{slug}{variant}.jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="generate locally, skip upload")
    ap.add_argument("--skip-upload", action="store_true", help="alias for --dry-run")
    ap.add_argument("--limit", type=int, default=0, help="only first N pins")
    args = ap.parse_args()
    upload = not (args.dry_run or args.skip_upload)

    plan = json.load(open(PLAN))["pins"]
    if args.limit:
        plan = plan[: args.limit]

    os.makedirs(OUT_DIR, exist_ok=True)
    supabase_url, key = (None, None)
    if upload:
        supabase_url, key = load_creds()

    made = []
    for i, pin in enumerate(plan, 1):
        slug = pin["slug"]
        fname = slug_filename(slug, pin.get("variant", ""))
        local_path = os.path.join(OUT_DIR, fname)
        src_img, mode = resolve_source(pin["img"])
        out = build_pin(src_img, mode, pin["pin_title"])
        out.save(local_path, "JPEG", quality=88, optimize=True)
        size = os.path.getsize(local_path)

        status = "local-only"
        if upload:
            r = requests.post(
                f"{supabase_url}/storage/v1/object/alina-media/pinterest/{fname}",
                headers={
                    "Authorization": f"Bearer {key}",
                    "apikey": key,
                    "x-upsert": "true",
                    "Content-Type": "image/jpeg",
                },
                data=open(local_path, "rb").read(),
                timeout=120,
            )
            if r.status_code in (200, 201):
                status = "uploaded"
            else:
                status = f"UPLOAD FAIL {r.status_code}: {r.text[:200]}"
        made.append(slug)
        print(f"[{i}/{len(plan)}] {slug}  {size//1024}KB  {status}")

    print(f"\nDone: {len(made)} pins -> {OUT_DIR}")
    if upload:
        print("Public base:", f"{PUBLIC_BASE}/pinterest/")


if __name__ == "__main__":
    main()
