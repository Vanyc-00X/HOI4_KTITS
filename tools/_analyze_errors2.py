# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from collections import Counter
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

LOG = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
ROOT = Path(r"D:/Dowland/Mod/Games/HOI4/mir_kazualnosti")

c = Counter()
other = []
coastal_pids = []
for line in LOG.open(encoding="utf-8", errors="replace"):
    if "X crossing" in line:
        c["x_crossing"] += 1
    elif "Palette in rivers" in line:
        c["rivers"] += 1
    elif "coastal but has no port" in line:
        c["coastal"] += 1
        import re
        m = re.search(r"Province (\d+)", line)
        if m:
            coastal_pids.append(int(m.group(1)))
    elif "too far away" in line:
        c["far"] += 1
    elif "Error:" in line or "error at" in line.lower() or "Unexpected" in line or "MAP_ERROR" in line:
        if "X crossing" not in line:
            c["other"] += 1
            if len(other) < 60:
                other.append(line.strip()[:240])

print("COUNTS", dict(c.most_common()))
print("coastal pids", len(coastal_pids), coastal_pids[:20], "...", coastal_pids[-5:])
print("--- other ---")
for o in other:
    print(o)

# definition coastal
rows = [l.split(";") for l in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
def_coastal = [int(p[0]) for p in rows if p[4] == "land" and p[5] == "true"]
print("definition coastal_true", len(def_coastal))
ports = []
for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines():
    if "naval_base_spawn" in l:
        ports.append(int(l.split(";")[-1]))
print("ports", len(ports), "missing from ports", sorted(set(def_coastal) - set(ports))[:20])

im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
px = im.load()
W, H = im.size
xc = 0
samples = []
for y in range(H - 1):
    for x in range(W - 1):
        a, b = px[x, y], px[x + 1, y]
        c1, d = px[x, y + 1], px[x + 1, y + 1]
        if len({a, b, c1, d}) == 4:
            xc += 1
            if len(samples) < 5:
                samples.append((x, y, a, b, c1, d))
print("4-color corners", xc, "samples", samples)

# game coords invert y
gx, gy = 31, 993
py = H - 1 - gy
print("game", gx, gy, "-> pil", gx, py)
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        x, y = gx + dx, py + dy
        if 0 <= x < W and 0 <= y < H:
            print(" ", x, y, px[x, y])
