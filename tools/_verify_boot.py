# -*- coding: utf-8 -*-
from pathlib import Path
import re
import struct

ROOT = Path(r"D:\Dowland\Mod\Games\HOI4\ПРОГЕРЫ МОД")

rows = [l.split(";") for l in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
coastal = {int(p[0]) for p in rows if p[4] == "land" and p[5] == "true"}
all_pids = {int(p[0]) for p in rows}
ports = set()
bld = (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines()
non_naval = [l for l in bld if l.strip() and "naval_base_spawn" not in l]
for l in bld:
    if "naval_base_spawn" in l:
        ports.add(int(l.split(";")[-1]))
print("coastal==ports", coastal == ports, len(ports), "non_naval_bld", len(non_naval))

# SR coverage
sr_dir = ROOT / "map" / "strategicregions"
covered = set()
sr_ids = []
for f in sr_dir.glob("*.txt"):
    text = f.read_text(encoding="utf-8")
    sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
    sr_ids.append(sid)
    pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
    for x in pm.group(1).split():
        if x.isdigit():
            covered.add(int(x))
print("sr count", len(sr_ids), "max", max(sr_ids), "missing provs", len(all_pids - covered), "dup?", len(covered) != sum(1 for _ in covered))
# check duplicate province assignments
from collections import Counter
c = Counter()
for f in sr_dir.glob("*.txt"):
    text = f.read_text(encoding="utf-8")
    pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
    for x in pm.group(1).split():
        if x.isdigit():
            c[int(x)] += 1
dups = [p for p, n in c.items() if n > 1]
print("duplicate SR assignments", len(dups), "uncovered", sorted(all_pids - covered)[:20], "count", len(all_pids - covered))

wp = (ROOT / "map" / "weatherpositions.txt").read_text(encoding="utf-8").splitlines()
print("wp", len(wp), "bad", sum(1 for l in wp if len(l.split(";")) != 5))
print("portraits", list((ROOT / "portraits").glob("*")) if (ROOT / "portraits").exists() else None)

# flag bpp
for tag in ("SCO", "CSA", "VCI"):
    p = ROOT / "gfx" / "flags" / f"{tag}_neutrality.tga"
    if p.exists():
        print(tag, "bpp", p.read_bytes()[16], "size", p.stat().st_size)
    else:
        print(tag, "MISSING")

desc = (ROOT / "descriptor.mod").read_text(encoding="utf-8")
docs = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV" / "mod" / "mir_kazualnosti.mod"
print("desc version", re.search(r'version="([^"]+)"', desc).group(1))
print("theaters replace", "ai_faction_theaters" in desc)
print("docs path", re.search(r'path="([^"]*)"', docs.read_text(encoding="utf-8")).group(1))
