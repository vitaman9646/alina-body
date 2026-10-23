#!/usr/bin/env python3
"""Библиотека переиспользуемых иллюстраций лид-магнитов.

Карточки магнитов часто рисуют одни и те же объекты (тарелка, овощи, печень,
дневник, тележка, схема). Вместо генерации заново — ищем в каталоге по теме и
переиспользуем (0 кредитов). Генерим только при промахе.

Каталог: content/illustrations.json
  {"entries": [{id, type: flat|cartoon, topics: [str], file, url, prompt}]}

Генерация:
  flat     = flux-3/klein-text-to-image  (~1.6 кр, текстовый промпт, 1:1)
  cartoon  = nano-banana-2-lite (~4 кр, референс Алины + flat-vector стиль, 3:4)

CLI:
  illib.py list [--type flat|cartoon]
  illib.py search "овощи тарелка" [--type flat|cartoon] [--top N]
  illib.py get --topic "..." --prompt "..." [--type flat|cartoon] [--aspect 1:1]
  illib.py add --id name --topics "a,b" --file /path --type flat
  illib.py stats
"""
import os, sys, json, time, urllib.request

ROOT = "/home/hermes/alina-body"
CATALOG = os.path.join(ROOT, "content", "illustrations.json")
FLAT_DIR = os.path.join(ROOT, "alina-media", "illustrations", "flat")
CARTOON_DIR = os.path.join(ROOT, "alina-media", "cartoon")
API = "https://api.kie.ai"
CREDIT_LOG = os.path.join(ROOT, "content", "kie_credit_log.jsonl")

# ── Модели и референсы ────────────────────────────────────────────────
FLAT_MODEL = "flux-3/klein-text-to-image"
CARTOON_MODEL = "nano-banana-2-lite"
# Референс Алины (каноничное лицо владельца, публичный URL) — для мультяшки.
FACE_REF = "https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/char/face-young-1.jpg"
CARTOON_BASE = ("Flat vector illustration, clean modern flat design, smooth geometric "
                "shapes, subtle flat shading. Warm coral and cream color palette, soft "
                "solid white background, no text.")


def load_key():
    for line in open(os.path.expanduser("~/credentials/kie.env")):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("нет ключа kie.ai в ~/credentials/kie.env")


def load_catalog():
    if os.path.exists(CATALOG):
        try:
            return json.load(open(CATALOG))
        except (json.JSONDecodeError, ValueError):
            pass
    return {"entries": []}


def save_catalog(cat):
    os.makedirs(os.path.dirname(CATALOG), exist_ok=True)
    json.dump(cat, open(CATALOG, "w"), ensure_ascii=False, indent=2)
    return CATALOG


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum() or c.isspace())


def _score(topics, query_words):
    """Очки совпадения темы с запросом. Каждое слово запроса, найденное в теме,
    даёт +1; чем больше пересечений — тем выше приоритет."""
    score = 0
    for qw in query_words:
        for t in topics:
            tt = _norm(t)
            if qw in tt or tt in qw:
                score += 1
    return score


def search(query, type_=None, top=5):
    """Вернуть записи, отсортированные по релевантности (без порога)."""
    scored = _search_scored(query, type_)
    return [e for _, e in scored[:top]]


def _search_scored(query, type_=None):
    cat = load_catalog()
    qwords = [_norm(w) for w in query.split() if _norm(w)]
    scored = []
    for e in cat["entries"]:
        if type_ and e.get("type") != type_:
            continue
        s = _score(e.get("topics", []), qwords) if qwords else 0
        scored.append((s, e))
    scored.sort(key=lambda x: -x[0])
    return scored


def _should_reuse(top_score, n_query_words):
    """Порог переиспользования: 1 слово запроса = хватит 1 совпадения;
    многословный запрос = нужно ≥2 слов, иначе частичное совпадение
    («тарелка» в «меню») выдаст неверную иллюстрацию."""
    return top_score >= (1 if n_query_words <= 1 else 2)


def _post_json(url, payload, key):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _get_json(url, key):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _balance(key):
    """Текущий баланс кредитов kie.ai (или None)."""
    try:
        r = _get_json(f"{API}/api/v1/chat/credit", key)
        v = r.get("data")
        return float(v) if v is not None else None
    except Exception:
        return None


def _log_credit(label, model, before, after):
    """Пишет стоимость вызова (до−после) в журнал кредитов JSONL."""
    cost = (before - after) if (before is not None and after is not None) else None
    rec = {"ts": int(time.time()), "label": label, "model": model,
           "cost": cost, "balance_after": after}
    try:
        with open(CREDIT_LOG, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _generate(key, model, inp, out_path):
    """Создаёт задачу kie.ai и качает результат. Возвращает (path, err)."""
    r = _post_json(f"{API}/api/v1/jobs/createTask", {"model": model, "input": inp}, key)
    if r.get("code") != 200:
        return None, json.dumps(r)[:250]
    task = r["data"]["taskId"]
    for _ in range(90):
        time.sleep(7)
        d = _get_json(f"{API}/api/v1/jobs/recordInfo?taskId={task}", key).get("data", {})
        st = d.get("state")
        if st == "success":
            urls = (d.get("response", {}).get("resultUrls")
                    or d.get("resultJson", {}).get("resultUrls") or [])
            if urls:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                urllib.request.urlretrieve(urls[0], out_path)
                return out_path, None
            return None, "нет resultUrls"
        if st == "fail":
            return None, json.dumps(d)[:250]
    return None, "timeout"


def get_flat(topic, prompt, aspect="1:1", label=None):
    """Переиспользовать или сгенерировать плоскую иллюстрацию (flux-3/klein)."""
    scored = _search_scored(topic, type_="flat")
    qwords = [_norm(w) for w in topic.split() if _norm(w)]
    if scored and _should_reuse(scored[0][0], len(qwords)):
        return {"reused": True, "file": scored[0][1]["file"], "topic": scored[0][1].get("id")}
    key = load_key()
    slug = _norm(topic).replace(" ", "-") or "ill"
    out = os.path.join(FLAT_DIR, f"{slug}.jpg")
    before = _balance(key)
    path, err = _generate(key, FLAT_MODEL, {"prompt": prompt, "aspect_ratio": aspect}, out)
    _log_credit(label or f"flat:{topic}", FLAT_MODEL, before, _balance(key))
    if err:
        raise SystemExit(f"[flat:{topic}] генерация не удалась: {err}")
    cat = load_catalog()
    cat["entries"].append({
        "id": slug, "type": "flat", "topics": [_norm(topic)],
        "file": path, "url": None, "prompt": prompt,
    })
    save_catalog(cat)
    return {"reused": False, "file": path, "topic": slug}


def get_cartoon(topic, prompt, aspect="3:4", label=None):
    """Переиспользовать или сгенерировать мультяшку-демонстратора (nano-banana-2-lite).

    Промпт обязан описывать ПОЗУ/движение; персонаж и стиль держатся референсом
    Алины + CARTOON_BASE (добавляется автоматически).
    """
    hits = _search_scored(topic, type_="cartoon")
    qwords = [_norm(w) for w in topic.split() if _norm(w)]
    if hits and _should_reuse(hits[0][0], len(qwords)):
        return {"reused": True, "file": hits[0][1]["file"], "topic": hits[0][1].get("id")}
    key = load_key()
    slug = _norm(topic).replace(" ", "-") or "pose"
    out = os.path.join(CARTOON_DIR, f"{slug}.jpg")
    full = CARTOON_BASE + " Same cartoon character as this woman, same style and colors: " + prompt
    inp = {"prompt": full, "image_input": [FACE_REF], "aspect_ratio": aspect,
           "resolution": "1K", "output_format": "jpg"}
    before = _balance(key)
    path, err = _generate(key, CARTOON_MODEL, inp, out)
    _log_credit(label or f"cartoon:{topic}", CARTOON_MODEL, before, _balance(key))
    if err:
        raise SystemExit(f"[cartoon:{topic}] генерация не удалась: {err}")
    cat = load_catalog()
    cat["entries"].append({
        "id": slug, "type": "cartoon", "topics": [_norm(topic)],
        "file": path, "url": None, "prompt": prompt,
    })
    save_catalog(cat)
    return {"reused": False, "file": path, "topic": slug}


# ── CLI ───────────────────────────────────────────────────────────────
def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Библиотека иллюстраций лид-магнитов")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list"); p.add_argument("--type", choices=["flat", "cartoon"])
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("--type", choices=["flat", "cartoon"])
    p.add_argument("--top", type=int, default=5)

    p = sub.add_parser("get")
    p.add_argument("--topic", required=True); p.add_argument("--prompt", required=True)
    p.add_argument("--type", choices=["flat", "cartoon"], default="flat")
    p.add_argument("--aspect", default="1:1")

    p = sub.add_parser("add")
    p.add_argument("--id", required=True); p.add_argument("--topics", required=True)
    p.add_argument("--file", required=True); p.add_argument("--type", choices=["flat", "cartoon"], default="flat")

    p = sub.add_parser("stats")
    a = ap.parse_args()

    if a.cmd == "list":
        for e in search("", type_=a.type, top=1000):
            print(f"[{e['type']:7}] {e['id']:24} topics={','.join(e['topics'])}  {e['file']}")
    elif a.cmd == "search":
        for e in search(a.query, type_=a.type, top=a.top):
            print(f"{e['type']:7} {e['id']:24} topics={','.join(e['topics'])}  {e['file']}")
    elif a.cmd == "get":
        r = get_flat(a.topic, a.prompt, a.aspect) if a.type == "flat" else get_cartoon(a.topic, a.prompt, a.aspect)
        print(("REUSED " if r["reused"] else "NEW    ") + r["file"])
    elif a.cmd == "add":
        cat = load_catalog()
        cat["entries"].append({"id": a.id, "type": a.type,
                               "topics": [t.strip() for t in a.topics.split(",")],
                               "file": a.file, "url": None, "prompt": ""})
        save_catalog(cat)
        print("added", a.id)
    elif a.cmd == "stats":
        cat = load_catalog()
        flat = sum(1 for e in cat["entries"] if e["type"] == "flat")
        cart = sum(1 for e in cat["entries"] if e["type"] == "cartoon")
        print(f"flat: {flat}  cartoon: {cart}  всего: {len(cat['entries'])}")


if __name__ == "__main__":
    _cli()
