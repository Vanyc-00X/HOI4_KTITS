# -*- coding: utf-8 -*-
"""List vanilla files (outside the mod's replace_paths) that hard-code state/province ids
beyond what the mod map defines. Those are the load-time crash candidates for a new map."""
import re
from collections import Counter
from pathlib import Path

GAME = Path(r"E:/SteamLibrary/steamapps/common/Hearts of Iron IV")
MOD = Path(__file__).resolve().parents[1]

replaced = [l.split('"')[1] for l in (MOD / "descriptor.mod").read_text().splitlines()
            if l.startswith("replace_path")]
SKIP = ("localisation", "gfx", "interface", "map", "sound", "music", "dlc", "documentation", "pdx_")
max_state = len(list((MOD / "history/states").glob("*.txt")))
max_prov = sum(1 for _ in (MOD / "map/definition.csv").open()) - 1
PAT = re.compile(r"\b(state|province|location|capital|target|states|provinces|highlight_provinces|"
                 r"direction_pointer|highlight_states_trigger|owns_state|controls_state|naval_base)"
                 r"\s*=\s*\{?\s*(\d+)")

hits = Counter()
for p in GAME.rglob("*.txt"):
    rel = p.relative_to(GAME).as_posix()
    if rel.startswith(SKIP) or any(rel.startswith(r + "/") for r in replaced):
        continue
    if rel.startswith(("events/", "common/decisions/", "common/national_focus/", "history/")):
        continue
    try:
        t = re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig", errors="replace"))
    except OSError:
        continue
    for key, num in PAT.findall(t):
        n = int(num)
        if n > (max_prov if "prov" in key or key in ("location", "direction_pointer", "naval_base") else max_state):
            hits[rel] += 1
for rel, n in hits.most_common():
    top = rel.split("/")[0] + "/" + (rel.split("/")[1] if "/" in rel else "")
    print(f"{n:5d}  {rel}")
