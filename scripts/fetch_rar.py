import requests, re, os, urllib.parse, sys
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
s = requests.Session(); s.headers.update({"User-Agent": UA})
root = "z4PM/urqRzPZ5M"
out = "/home/hermes/alina-body/inbox/presnyakov-tg"
r = s.get("https://cloud.mail.ru/public/z4PM/urqRzPZ5M", timeout=60); r.raise_for_status()
m = re.search(r'"weblink_get"[^}]*"url"\s*:\s*"([^"]+)"', r.text)
wg = m.group(1)
def dl_url(wl):
    safe = "/".join(urllib.parse.quote(p, safe="") for p in wl.split("/"))
    return f"{wg}/{safe}"
d0 = s.get("https://cloud.mail.ru/api/v4/public/list",
           params={"weblink": root, "sort":"name","order":"asc","offset":"0","limit":"500","version":"4"}, timeout=60).json()
for it in d0.get("list", []):
    n = it["name"]
    if it["type"] == "file" and n.lower().endswith(".rar"):
        dst = os.path.join(out, n)
        print("скачиваю", n, "цель", it["size"], flush=True)
        rr = s.get(dl_url(it["weblink"]), allow_redirects=True, stream=True, timeout=600)
        if "html" in rr.headers.get("Content-Type","").lower():
            mm = re.search(r'https?://[^"\'\s]+datacloudmail[^"\'\s]+', rr.text[:30000])
            if mm: rr = s.get(mm.group(0), allow_redirects=True, stream=True, timeout=600)
        done = 0
        with open(dst, "wb") as f:
            for chunk in rr.iter_content(1048576):
                f.write(chunk); done += len(chunk)
        print("готово:", done, flush=True)
        break
print("done", flush=True)
