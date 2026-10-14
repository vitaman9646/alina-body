#!/usr/bin/env python3
"""Склеивает переписанные контент-планы обратно в основные файлы (дни 1-2 оригинальные + дни 3+ новые)."""
import re

def split_at(path, day):
    orig = open(path, encoding="utf-8").read()
    marker = f"### День {day}"
    idx = orig.index(marker)
    return orig[:idx].rstrip() + "\n\n"

# Threads
head = split_at("content_plan.md", 3)
d3 = open("content_plan_threads_d3_16.md", encoding="utf-8").read().strip()
d17 = open("content_plan_threads_d17_30.md", encoding="utf-8").read().strip()
merged = head + d3 + "\n\n" + d17 + "\n"
open("content_plan.md", "w", encoding="utf-8").write(merged)
print("Threads: дней =", len(re.findall(r"^### День", merged, re.M)), "| 📸 =", len(re.findall(r"^📸", merged, re.M)))

# Instagram
head = split_at("content_plan_instagram.md", 3)
new = open("content_plan_instagram_new.md", encoding="utf-8").read().strip()
merged = head + new + "\n"
open("content_plan_instagram.md", "w", encoding="utf-8").write(merged)
print("IG: дней =", len(re.findall(r"^### День", merged, re.M)), "| 📸 =", len(re.findall(r"^📸", merged, re.M)))
