# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter
from PIL import Image

LOG = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
ROOT = Path(r"D:/Dowland/Mod/Games/HOI4/mir_kazualnosti")

c = Counter()
other = []
for line in LOG.open(encoding="utf-8", errors="replace"):
    if "X crossing" in line:
        c["x_crossing"] += 1
    elif "Palette in rivers" in line:
        c["rivers"] += 1
    elif "coastal but has no port" in line:
        c["coastal"] += 1
    elif "Incorrect MOD" in line:
        c["bad_mod"] += 1
    elif "fractioned" in line:
        c["fractioned"] += 1
        other.append(line.strip()[:200])
    elif "weatherpositions" in line:
        c["weather"] += 1
    elif "will likely crash" in line:
        c["crash_warn"] += 1
    elif "too far away" in line:
        c["far"] += 1
    elif "MAP_ERROR" in line:
        c["map_other"] += 1
        other.append(line.strip()[:200])
    elif "Error:" in line or "error at" in line.lower() or "Unexpected" in line:
        c["script_error"] += 1
        if len(other) < 40:
            other.append(line.strip()[:220])

print("COUNTS", dict(c.most_common()))
print("--- samples ---")
for o in other[:40]:
    print(o)

# X at game (31,993) -> PIL y = H-1-gy if bottom-up game coords
im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
px = im.load()
W, H = im.size
gx, gy = 31, 993
for py in (gy, H - 1 - gy):
    print("check y", py)
    for dx in (-1, 0):
        for dy in (-1, 0):
            x, y = gx + dx, py + dy
            if 0 <= x < W and 0 <= y < H:
                print(" ", x, y, px[x, y])

# count X crossings in image (4 distinct at 2x2)
xc = 0
for y in range(H - 1):
    for x in range(W - 1):
        a, b = px[x, y], px[x + 1, y]
        c1, d = px[x, y + 1], px[x + 1, y + 1]
        if len({a, b, c1, d}) == 4:
            xc += 1
print("true 4-color corners", xc)

# checkerboard X (A==D, B==C, A!=B)
chk = 0
for y in range(H - 1):
    for x in range(W - 1):
        a, b = px[x, y], px[x + 1, y]
        c1, d = px[x, y + 1], px[x + 1, y + 1]
        if a == d and b == c1 and a != b:
            chk += 1
print("checkerboard corners", chk)
