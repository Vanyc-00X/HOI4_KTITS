# -*- coding: utf-8 -*-
"""Static integrity check for Mir Kazualnosti map + history (no game launch needed)."""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "map"
problems: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig", errors="replace")


def strip_comments(t: str) -> str:
    return re.sub(r"#[^\n]*", "", t)


def block(text: str, key: str) -> str | None:
    m = re.search(r"\b" + re.escape(key) + r"\s*=\s*\{", text)
    if not m:
        return None
    i, depth = m.end(), 1
    while i < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[m.end(): i - 1]


def brace_balance(p: Path) -> None:
    t = strip_comments(read(p))
    t = re.sub(r'"[^"\n]*"', '""', t)
    depth = 0
    for ch in t:
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth < 0:
            bad(f"BRACES extra '}}' in {p.relative_to(ROOT)}")
            return
    if depth:
        bad(f"BRACES unclosed ({depth}) in {p.relative_to(ROOT)}")


# ---------- definition.csv ----------
defs: dict[int, dict] = {}
color_to_id: dict[tuple, int] = {}
for line in read(MAP / "definition.csv").splitlines():
    if not line.strip():
        continue
    f = line.split(";")
    pid = int(f[0])
    col = (int(f[1]), int(f[2]), int(f[3]))
    defs[pid] = {"col": col, "type": f[4], "coastal": f[5], "terrain": f[6], "cont": int(f[7])}
    if pid and col in color_to_id:
        bad(f"DEF duplicate color {col} for {pid} and {color_to_id[col]}")
    color_to_id[col] = pid
ids = sorted(defs)
if ids != list(range(len(ids))):
    bad("DEF ids not contiguous from 0")
n_cont = len(re.findall(r"^\s*\w+\s*$", block(read(MAP / "continent.txt"), "continents") or "", re.M))
valid_terrain = {"unknown", "ocean", "lakes", "forest", "hills", "mountain", "plains", "urban", "jungle",
                 "marsh", "desert", "water_fjords", "water_shallow_sea", "water_deep_ocean"}
KNOWN_RESOURCES = {"steel", "oil", "aluminium", "rubber", "tungsten", "chromium", "coal"}
for pid, d in defs.items():
    if pid == 0:
        continue
    if d["type"] not in ("land", "sea", "lake"):
        bad(f"DEF {pid} bad type {d['type']}")
    if d["terrain"] not in valid_terrain:
        bad(f"DEF {pid} unknown terrain {d['terrain']}")
    if d["type"] == "land" and not (1 <= d["cont"] <= n_cont):
        bad(f"DEF {pid} land continent {d['cont']} outside 1..{n_cont}")

# ---------- provinces.bmp ----------
img = np.array(Image.open(MAP / "provinces.bmp").convert("RGB"))
H, W, _ = img.shape
if W % 256 or H % 256:
    bad(f"BMP size {W}x{H} not multiple of 256")
packed = (img[:, :, 0].astype(np.int64) << 16) | (img[:, :, 1].astype(np.int64) << 8) | img[:, :, 2]
packed_to_id = {(c[0] << 16) | (c[1] << 8) | c[2]: pid for c, pid in color_to_id.items()}
uniq, counts = np.unique(packed, return_counts=True)
pix = {}
for u, c in zip(uniq.tolist(), counts.tolist()):
    if u not in packed_to_id:
        bad(f"BMP color {(u >> 16, (u >> 8) & 255, u & 255)} ({c}px) not in definition.csv")
    else:
        pix[packed_to_id[u]] = c
for pid in ids:
    if pid and pid not in pix:
        bad(f"BMP province {pid} defined but has no pixels")
    elif pid and pix[pid] < 8:
        bad(f"BMP province {pid} tiny ({pix[pid]}px)")
if 0 in pix:
    bad(f"BMP province 0 (black) painted {pix[0]}px")

# adjacency from bitmap
idmap = np.vectorize(lambda u: packed_to_id.get(u, -1), otypes=[np.int32])(packed)
adj = defaultdict(set)
for a, b in ((idmap[:, :-1], idmap[:, 1:]), (idmap[:-1, :], idmap[1:, :])):
    m = a != b
    for x, y in set(zip(a[m].tolist(), b[m].tolist())):
        adj[x].add(y)
        adj[y].add(x)
# horizontal wrap
for x, y in set(zip(idmap[:, 0].tolist(), idmap[:, -1].tolist())):
    if x != y:
        adj[x].add(y)
        adj[y].add(x)
for pid, d in defs.items():
    if pid == 0 or d["type"] != "land":
        continue
    touches_sea = any(defs.get(n, {}).get("type") == "sea" for n in adj[pid])
    if (d["coastal"] == "true") != touches_sea:
        bad(f"DEF {pid} coastal={d['coastal']} but touches_sea={touches_sea}")

# ---------- supply hubs and railways ----------
seen_supply_nodes = set()
for ln, line in enumerate(read(MAP / "supply_nodes.txt").splitlines(), 1):
    f = line.split()
    if not f:
        continue
    if len(f) != 2 or not all(x.isdigit() for x in f):
        bad(f"SUPPLY line {ln}: expected 'level province_id'")
        continue
    level, pid = map(int, f)
    if not 1 <= level <= 5:
        bad(f"SUPPLY line {ln}: level {level} outside 1..5")
    if pid not in defs or defs[pid]["type"] != "land":
        bad(f"SUPPLY line {ln}: province {pid} is not land")
    if pid in seen_supply_nodes:
        bad(f"SUPPLY line {ln}: duplicate node at province {pid}")
    seen_supply_nodes.add(pid)

for ln, line in enumerate(read(MAP / "railways.txt").splitlines(), 1):
    f = line.split()
    if not f:
        continue
    if len(f) < 4 or not all(x.isdigit() for x in f):
        bad(f"RAILWAY line {ln}: expected 'level path_length province_ids...'")
        continue
    level, path_length, *path = map(int, f)
    if not 1 <= level <= 5:
        bad(f"RAILWAY line {ln}: level {level} outside 1..5")
    if path_length != len(path) or path_length < 2:
        bad(f"RAILWAY line {ln}: path length does not match province list")
        continue
    for pid in path:
        if pid not in defs or defs[pid]["type"] != "land":
            bad(f"RAILWAY line {ln}: province {pid} is not land")
    for left, right in zip(path, path[1:]):
        if right not in adj.get(left, set()):
            bad(f"RAILWAY line {ln}: provinces {left} and {right} are not adjacent")

# ---------- X-crossings (4 provinces meeting at a point) ----------
a, b, c, dd = idmap[:-1, :-1], idmap[:-1, 1:], idmap[1:, :-1], idmap[1:, 1:]
xc = (a != b) & (a != c) & (a != dd) & (b != c) & (b != dd) & (c != dd)
if xc.sum():
    bad(f"BMP {int(xc.sum())} X-crossings (4 provinces at a corner)")

# ---------- states ----------
tags = set()
for p in (ROOT / "common/country_tags").glob("*.txt"):
    tags |= set(re.findall(r"^\s*([A-Z0-9]{3})\s*=", strip_comments(read(p)), re.M))
state_of: dict[int, int] = {}
state_owner: dict[int, str] = {}
state_ids = Counter()
for p in sorted((ROOT / "history/states").glob("*.txt")):
    brace_balance(p)
    t = strip_comments(read(p))
    sid = int(re.search(r"\bid\s*=\s*(\d+)", t).group(1))
    state_ids[sid] += 1
    provs = [int(x) for x in (block(t, "provinces") or "").split()]
    if not provs:
        bad(f"STATE {sid} has no provinces")
    for pr in provs:
        if pr not in defs:
            bad(f"STATE {sid} province {pr} not defined")
        elif defs[pr]["type"] != "land":
            bad(f"STATE {sid} contains non-land province {pr} ({defs[pr]['type']})")
        if pr in state_of:
            bad(f"STATE province {pr} in states {state_of[pr]} and {sid}")
        state_of[pr] = sid
    om = re.search(r"\bowner\s*=\s*(\w+)", t)
    if not om:
        bad(f"STATE {sid} no owner")
    else:
        state_owner[sid] = om.group(1)
        if om.group(1) not in tags:
            bad(f"STATE {sid} owner {om.group(1)} not in country_tags")
    if not re.search(r"\bstate_category\s*=", t):
        bad(f"STATE {sid} no state_category")
    res = block(t, "resources")
    if res is None:
        bad(f"STATE {sid} has no resources block")
    else:
        found: dict[str, int] = {}
        for key, val in re.findall(r"([a-z_]+)\s*=\s*(\d+)", res):
            if key not in KNOWN_RESOURCES:
                bad(f"STATE {sid} unknown resource '{key}'")
            found[key] = int(val)
        for key in sorted(KNOWN_RESOURCES):
            if key not in found:
                bad(f"STATE {sid} missing resource '{key}'")
    if not re.search(r"\bmanpower\s*=", t):
        bad(f"STATE {sid} no manpower")
    hist = block(t, "history") or ""
    for vp in re.findall(r"victory_points\s*=\s*\{\s*(\d+)", hist):
        if int(vp) not in provs:
            bad(f"STATE {sid} victory point province {vp} not in state")
    bl = block(hist, "buildings") or ""
    for pr, _inner in re.findall(r"\b(\d+)\s*=\s*\{([^}]*)\}", bl):
        if int(pr) not in provs:
            bad(f"STATE {sid} province building on {pr} not in state")
        if "naval_base" in _inner and defs.get(int(pr), {}).get("coastal") != "true":
            bad(f"STATE {sid} naval_base on non-coastal {pr}")
for sid, n in state_ids.items():
    if n > 1:
        bad(f"STATE id {sid} defined {n} times")
if state_ids and sorted(state_ids) != list(range(1, max(state_ids) + 1)):
    bad("STATE ids not contiguous 1..N")
for pid, d in defs.items():
    if pid and d["type"] == "land" and pid not in state_of:
        bad(f"STATE land province {pid} not in any state")

# ---------- strategic regions ----------
sr_of: dict[int, int] = {}
for p in sorted((MAP / "strategicregions").glob("*.txt")):
    brace_balance(p)
    t = strip_comments(read(p))
    rid = int(re.search(r"\bid\s*=\s*(\d+)", t).group(1))
    for pr in [int(x) for x in (block(t, "provinces") or "").split()]:
        if pr not in defs or pr == 0:
            bad(f"SR {rid} invalid province {pr}")
            continue
        if pr in sr_of:
            bad(f"SR province {pr} in regions {sr_of[pr]} and {rid}")
        sr_of[pr] = rid
    w = block(t, "weather")
    if not w or "period" not in w:
        bad(f"SR {rid} missing weather periods")
for pid, d in defs.items():
    if pid and d["type"] in ("land", "sea") and pid not in sr_of:
        bad(f"SR province {pid} ({d['type']}) not in any strategic region")

# ---------- buildings.txt ----------
for ln, line in enumerate(read(MAP / "buildings.txt").splitlines(), 1):
    f = line.split(";")
    if len(f) < 7:
        continue
    sid, btype = int(f[0]), f[1]
    if sid not in state_ids:
        bad(f"BUILDINGS line {ln}: state {sid} unknown")
    if btype == "naval_base_spawn":
        sea = int(f[6])
        if sea and defs.get(sea, {}).get("type") != "sea":
            bad(f"BUILDINGS line {ln}: naval_base adjacent {sea} is not sea")

# ---------- unitstacks ----------
seen = set()
for line in read(MAP / "unitstacks.txt").splitlines():
    f = line.split(";")
    if f and f[0].isdigit():
        seen.add(int(f[0]))
        if int(f[0]) not in defs:
            bad(f"UNITSTACKS province {f[0]} undefined")

# ---------- countries ----------
hist_files = {p.name[:3]: p for p in (ROOT / "history/countries").glob("*.txt")}
owners = set(state_owner.values())
oob_names = {p.stem for p in (ROOT / "history/units").glob("*.txt")}
for tag in owners:
    if tag not in hist_files:
        bad(f"COUNTRY {tag} owns states but has no history file")
        continue
    t = strip_comments(read(hist_files[tag]))
    m = re.search(r"\bcapital\s*=\s*(\d+)", t)
    if not m:
        bad(f"COUNTRY {tag} no capital")
    elif state_owner.get(int(m.group(1))) != tag:
        bad(f"COUNTRY {tag} capital state {m.group(1)} owned by {state_owner.get(int(m.group(1)))}")
for tag, p in hist_files.items():
    brace_balance(p)
    t = strip_comments(read(p))
    for oob in re.findall(r'\boob\s*=\s*"?([\w]+)"?', t):
        if oob not in oob_names:
            bad(f"COUNTRY {tag} oob {oob} missing")
    m = re.search(r"\bcapital\s*=\s*(\d+)", t)
    if m and int(m.group(1)) not in state_ids:
        bad(f"COUNTRY {tag} capital {m.group(1)} not an existing state")

# ---------- characters ----------
ideologies = set()
for p in Path(sys.argv[1] if len(sys.argv) > 1 else "").glob("common/ideologies/*.txt") if len(sys.argv) > 1 else []:
    pass
for p in (ROOT / "common/characters").glob("*.txt"):
    brace_balance(p)

# ---------- every mod script file ----------
for sub in ("common", "events", "history/units", "map/strategicregions"):
    for p in (ROOT / sub).rglob("*.txt"):
        if "characters" in p.parts or p.parent.name in ("states",):
            continue
        brace_balance(p)

print(f"provinces={len(ids)-1} land={sum(1 for pid, d in defs.items() if pid and d['type']=='land')} "
      f"states={len(state_ids)} SR-provinces={len(sr_of)} tags={len(tags)} owners={len(owners)}")
cnt = Counter(m.split()[0] for m in problems)
print("summary:", dict(cnt))
for m in problems[:200]:
    print(" -", m)
if len(problems) > 200:
    print(f" ... {len(problems)-200} more")
sys.exit(1 if problems else 0)
