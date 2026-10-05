# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(r"D:/Dowland/Mod/Games/HOI4/mir_kazualnosti")
docs = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
mod = (docs / "mod" / "Mir_Kazualnosti.mod").read_text(encoding="utf-8")
print("has good replace", 'replace_path="history/countries"' in mod)
print("has path", f'path="D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"' in mod)
print("bad_replace", mod.count('replace_path="D:'))
print("dlc", (docs / "dlc_load.json").read_text(encoding="utf-8"))
print("--- mod file ---")
print(mod)
bm = (ROOT / "common" / "bookmarks" / "mk_era_of_mad_rulers.txt").read_text(encoding="utf-8")
needed = set()
for block in re.findall(r"ideas\s*=\s*\{([^}]+)\}", bm):
    needed.update(block.split())
found = set()
ideas_dir = ROOT / "common" / "ideas"
if ideas_dir.exists():
    for f in ideas_dir.glob("*.txt"):
        text = f.read_text(encoding="utf-8")
        for n in needed:
            if re.search(rf"\b{n}\b", text):
                found.add(n)
print("ideas needed", len(needed), "found", len(found), "missing", sorted(needed - found))
print("countries", len(list((ROOT / "history" / "countries").glob("*.txt"))))
print("states", len(list((ROOT / "history" / "states").glob("*.txt"))))
print("map ok", (ROOT / "map" / "provinces.bmp").exists(), (ROOT / "map" / "definition.csv").exists())
