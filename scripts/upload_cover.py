#!/usr/bin/env python3
import json, urllib.request, os
from PIL import Image
env = {}
for line in open(os.path.expanduser("~/credentials/threads.env")):
    line = line.strip()
    if line and "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
url = env["SUPABASE_URL"].rstrip("/")
key = env["SUPABASE_SERVICE_ROLE_KEY"]

img = Image.open("/home/hermes/alina-body/inbox/budget-pp-images/cover-kursa.png").convert("RGB")
img.thumbnail((1400, 1400))
img.save("/tmp/cover-kursa.jpg", "JPEG", quality=85, optimize=True, progressive=True)
data = open("/tmp/cover-kursa.jpg", "rb").read()

req = urllib.request.Request(url + "/storage/v1/object/alina-media/budget-pp/cover-kursa.jpg",
    data=data, method="POST",
    headers={"Authorization": "Bearer " + key, "apikey": key, "Content-Type": "image/jpeg", "x-upsert": "true"})
urllib.request.urlopen(req, timeout=120)
pub = url + "/storage/v1/object/public/alina-media/budget-pp/cover-kursa.jpg"
print("обложка:", pub)

req = urllib.request.Request(url + "/rest/v1/courses?slug=eq.budget-pp",
    data=json.dumps({"cover_url": pub}).encode(), method="PATCH",
    headers={"Authorization": "Bearer " + key, "apikey": key, "Content-Type": "application/json", "Prefer": "return=representation"})
r = json.loads(urllib.request.urlopen(req, timeout=60).read())
print("cover_url поставлен:", r[0].get("cover_url") == pub)
