# -*- coding: utf-8 -*-
"""v0.4.1: give every playable country division templates + starting divisions,
restore capital supply nodes."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig", errors="replace")


def block(text: str, key: str) -> str:
    m = re.search(r"\b" + key + r"\s*=\s*\{", text)
    i, depth = m.end(), 1
    while depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[m.end(): i - 1]


states = {}
for p in (ROOT / "history/states").glob("*.txt"):
    t = re.sub(r"#[^\n]*", "", read(p))
    sid = int(re.search(r"\bid\s*=\s*(\d+)", t).group(1))
    provs = [int(x) for x in block(t, "provinces").split()]
    vp = re.search(r"victory_points\s*=\s*\{\s*(\d+)", t)
    states[sid] = {"provs": provs, "vp": int(vp.group(1)) if vp else provs[0]}

OOB = """##### {tag} 1936 OOB #####
division_template = {{
	name = "Infantry Division"
	regiments = {{
		infantry = {{ x = 0 y = 0 }}
		infantry = {{ x = 0 y = 1 }}
		infantry = {{ x = 1 y = 0 }}
		infantry = {{ x = 1 y = 1 }}
	}}
	support = {{
		engineer = {{ x = 0 y = 0 }}
	}}
}}

units = {{
	division = {{
		division_name = {{ is_name_ordered = yes name_order = 1 }}
		location = {prov}
		division_template = "Infantry Division"
		start_experience_factor = 0.2
	}}
	division = {{
		division_name = {{ is_name_ordered = yes name_order = 2 }}
		location = {prov}
		division_template = "Infantry Division"
		start_experience_factor = 0.2
	}}
}}

instant_effect = {{
	add_equipment_to_stockpile = {{ type = infantry_equipment_1 amount = 1000 producer = {tag} }}
	add_equipment_to_stockpile = {{ type = support_equipment_1 amount = 100 producer = {tag} }}
}}
"""

supply = []
for p in sorted((ROOT / "history/countries").glob("*.txt")):
    tag = p.name[:3]
    oob_file = ROOT / "history/units" / f"{tag}_1936.txt"
    if not oob_file.exists():
        continue
    t = read(p)
    cap = int(re.search(r"\bcapital\s*=\s*(\d+)", t).group(1))
    prov = states[cap]["vp"]
    oob_file.write_text(OOB.format(tag=tag, prov=prov), encoding="utf-8")
    supply.append(f"1 {prov}")
    print(tag, "capital state", cap, "province", prov)

(ROOT / "map/supply_nodes.txt").write_text("\n".join(supply) + "\n", encoding="utf-8")
print("supply nodes:", len(supply))
