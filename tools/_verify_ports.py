# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(r"D:\Dowland\Mod\Games\HOI4\ПРОГЕРЫ МОД")
rows = []
for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines()[1:]:
    p = line.split(";")
    if p[4] == "land" and p[5] == "true":
        rows.append(int(p[0]))
b = (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8")
ports = set()
for line in b.splitlines():
    if "naval_base_spawn" in line:
        parts = line.split(";")
        ports.add(int(parts[-1]))
print("coastal", len(rows), "spawn", len(ports))
print("missing", sorted(set(rows) - ports))
print("extra", sorted(ports - set(rows)))
wp = (ROOT / "map" / "weatherpositions.txt").read_text(encoding="utf-8").splitlines()
print("wp sample", wp[:3], "count", len(wp), "bad", sum(1 for l in wp if len(l.split(";")) != 5))
print("portraits", list((ROOT / "portraits").glob("*")) if (ROOT / "portraits").exists() else "none")
print("ai_strategy", list((ROOT / "common" / "ai_strategy").glob("*")))
desc = (ROOT / "descriptor.mod").read_text(encoding="utf-8")
print("version", re.search(r'version="([^"]+)"', desc).group(1))
print("replace ai", "ai_strategy" in desc, "ai_areas" in desc)
for l in b.splitlines():
    if "naval_base_spawn" in l:
        print("bld", l)
        break
nb = 0
for f in (ROOT / "history" / "states").glob("*.txt"):
    nb += len(re.findall(r"naval_base", f.read_text(encoding="utf-8")))
print("history naval_base entries", nb)
# sample state
sample = next((ROOT / "history" / "states").glob("*.txt"))
print("sample state head:\n", "\n".join(sample.read_text(encoding="utf-8").splitlines()[:40]))
