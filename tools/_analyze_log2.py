# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from collections import Counter
import re

sys.stdout.reconfigure(encoding="utf-8")
LOG = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
print("mtime", LOG.stat().st_mtime, "size", LOG.stat().st_size)
lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
print("lines", len(lines))
c = Counter()
folders = Counter()
notable = []
for line in lines:
    if "X crossing" in line:
        c["x"] += 1
    elif "TOO LARGE" in line:
        c["large"] += 1
        notable.append(line[:240])
    elif "coastal" in line and "port" in line:
        c["coastal"] += 1
    elif "buildings.txt" in line:
        c["bld"] += 1
        notable.append(line[:240])
    elif "will likely crash" in line:
        c["crash"] += 1
        notable.append(line[:240])
    elif "MAP_ERROR" in line:
        c["map"] += 1
        if sum(1 for n in notable if "MAP_ERROR" in n) < 20:
            notable.append(line[:240])
    elif "Incorrect MOD" in line:
        c["mod"] += 1
        notable.append(line[:240])
    elif "Error:" in line or "Unexpected" in line or "Invalid" in line or "Failed" in line:
        c["err"] += 1
        m = re.search(r"(common/[^\s:]+|history/[^\s:]+|map/[^\s:]+|events/[^\s:]+)", line.replace("\\", "/"))
        if m:
            folders["/".join(m.group(1).split("/")[:2])] += 1
        if len(notable) < 40:
            notable.append(line[:260])

print("COUNTS", dict(c.most_common()))
print("FOLDERS", folders.most_common(20))
print("--- notable ---")
for n in notable[:40]:
    print(n)
print("--- first 25 ---")
for l in lines[:25]:
    print(l[:260])
print("--- last 25 ---")
for l in lines[-25:]:
    print(l[:260])
