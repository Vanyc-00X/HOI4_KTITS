# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
LOG = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
print("mtime", LOG.stat().st_mtime, "size", LOG.stat().st_size)
lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
print("lines", len(lines))

c = Counter()
for line in lines:
    s = line
    if "X crossing" in s:
        c["x"] += 1
    elif "coastal" in s and ("port" in s or "crash" in s):
        c["coastal"] += 1
    elif "TOO LARGE" in s:
        c["large"] += 1
    elif "buildings.txt" in s:
        c["bld"] += 1
    elif "Incorrect MOD" in s:
        c["mod"] += 1
    elif "too far away" in s:
        c["far"] += 1
    elif "MAP_ERROR" in s:
        c["map"] += 1
    elif "Error:" in s or "Unexpected" in s or "Failed" in s or "Unable" in s or "invalid" in s.lower():
        c["err"] += 1
    elif "will likely crash" in s:
        c["crashwarn"] += 1

print("COUNTS", dict(c.most_common()))
print("--- ALL non-far ---")
for l in lines:
    if "too far away" not in l:
        print(l[:300])
