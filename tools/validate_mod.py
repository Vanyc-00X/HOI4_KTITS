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
FOCUS_BASELINES = {
    "ADL": 84, "ART": 84, "BTR": 96, "CLB": 96, "CRE": 96, "DMK": 96,
    "FDP": 96, "HRL": 84, "ISG": 84, "ISL": 84, "KMS": 84, "KRZ": 96,
    "KZS": 84, "MUS": 84, "NBL": 96, "SHF": 96, "SOY": 96, "SVA": 84,
    "TRF": 84, "VCI": 96, "ZKR": 84, "ZLD": 84, "ZML": 84, "ZNS": 84,
}
FOCUS_UNLOCKED_CHARACTERS = {
    "SOY": {"SOY_joe_biden_guest_diplomat": "SOY_diplo_18"},
    "BTR": {"BTR_grandfather_akhtyamov": "BTR_army_18"},
    "CRE": {
        "CRE_adolf_hitler_guest_instructor": "CRE_army_17",
        "CRE_hermann_goering_guest_instructor": "CRE_army_19",
        "CRE_erwin_rommel_guest_instructor": "CRE_army_21",
        "CRE_heinz_guderian_guest_instructor": "CRE_army_23",
    },
    "ZLD": {"ZLD_grigory_yavlinsky": "ZLD_diplo_18"},
}


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


def script_blocks(text: str, key: str) -> list[str]:
    """Return top-level-shaped script blocks for a named key."""
    result = []
    for match in re.finditer(r"^\s*" + re.escape(key) + r"\s*=\s*\{", text, re.M):
        depth, i = 1, match.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        if depth:
            return result
        result.append(text[match.end():i - 1])
    return result


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
terrain_bitmap_index = {
    "plains": 0, "forest": 1, "hills": 2, "desert": 3,
    "marsh": 9, "mountain": 11, "urban": 13, "jungle": 22,
}
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

land_terrain_counts = Counter(
    d["terrain"] for pid, d in defs.items() if pid and d["type"] == "land"
)
land_province_count = sum(
    1 for pid, d in defs.items() if pid and d["type"] == "land"
)
sea_province_count = sum(
    1 for pid, d in defs.items() if pid and d["type"] == "sea"
)
if land_province_count <= 1200:
    bad(f"MAP has only {land_province_count} land provinces; expected more than 1200")
if land_province_count <= sea_province_count:
    bad(f"MAP has fewer land provinces ({land_province_count}) than sea ({sea_province_count})")
for terrain in ("plains", "forest", "hills", "mountain", "marsh", "desert", "jungle"):
    if land_terrain_counts[terrain] == 0:
        bad(f"MAP has no land provinces of terrain {terrain}")

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

# ---------- terrain, rivers, forests, cities, and elevation rasters ----------
terrain_img = Image.open(MAP / "terrain.bmp")
if terrain_img.size != (W, H) or terrain_img.mode not in ("P", "L"):
    bad(f"MAP terrain.bmp expected indexed {W}x{H}, got {terrain_img.mode} {terrain_img.size}")
else:
    terrain_raster = np.asarray(terrain_img.convert("P"), dtype=np.uint8)
    expected_terrain = np.full(max(ids) + 1, -1, dtype=np.int16)
    for pid, d in defs.items():
        if d["type"] == "land":
            expected_terrain[pid] = terrain_bitmap_index.get(d["terrain"], -1)
    safe_ids = np.maximum(idmap, 0)
    terrain_mismatch = (
        (idmap >= 0)
        & (expected_terrain[safe_ids] >= 0)
        & (terrain_raster != expected_terrain[safe_ids])
    )
    if terrain_mismatch.any():
        bad(f"MAP terrain.bmp differs from definition.csv at {int(terrain_mismatch.sum())} pixels")

land_pixels = idmap >= 0
land_pixels &= np.take(
    np.asarray([defs.get(pid, {}).get("type") == "land" for pid in range(max(ids) + 1)]),
    np.maximum(idmap, 0),
)
river_img = Image.open(MAP / "rivers.bmp")
if river_img.size != (W, H) or river_img.mode not in ("P", "L"):
    bad(f"MAP rivers.bmp expected indexed {W}x{H}, got {river_img.mode} {river_img.size}")
else:
    river_raster = np.asarray(river_img.convert("P"), dtype=np.uint8)
    river_mask = ~np.isin(river_raster, (254, 255))
    if int((river_mask & land_pixels).sum()) < 1000:
        bad("MAP rivers.bmp has fewer than 1000 visible river pixels on land")
    if (river_mask & ~land_pixels).any():
        bad(f"MAP rivers.bmp has {int((river_mask & ~land_pixels).sum())} river pixels outside land")

cities_img = Image.open(MAP / "cities.bmp")
if cities_img.size != (W, H) or cities_img.mode not in ("P", "L"):
    bad(f"MAP cities.bmp expected indexed {W}x{H}, got {cities_img.mode} {cities_img.size}")
else:
    cities_raster = np.asarray(cities_img.convert("P"), dtype=np.uint8)
    city_mask = cities_raster == 15
    if int(city_mask.sum()) < 127:
        bad(f"MAP cities.bmp has only {int(city_mask.sum())} urban pixels")
    if (city_mask & ~land_pixels).any():
        bad(f"MAP cities.bmp has {int((city_mask & ~land_pixels).sum())} city pixels outside land")

trees_img = Image.open(MAP / "trees.bmp")
if trees_img.size != (max(64, W * 1650 // 5632), max(64, H * 600 // 2048)) or trees_img.mode not in ("P", "L"):
    bad(f"MAP trees.bmp has unexpected format or dimensions: {trees_img.mode} {trees_img.size}")
else:
    trees_raster = np.asarray(trees_img.convert("P"), dtype=np.uint8)
    if not set(np.unique(trees_raster).tolist()).issubset({0, 3, 4, 7, 10}):
        bad("MAP trees.bmp uses unsupported tree indices")
    tree_mask = trees_raster != 0
    if int(tree_mask.sum()) < 1000:
        bad("MAP trees.bmp has fewer than 1000 forest pixels")
    map_x = np.minimum(W - 1, ((np.arange(trees_img.width) + 0.5) * W / trees_img.width).astype(int))
    map_y = np.minimum(H - 1, ((np.arange(trees_img.height) + 0.5) * H / trees_img.height).astype(int))
    tree_land = land_pixels[np.ix_(map_y, map_x)]
    if (tree_mask & ~tree_land).any():
        bad(f"MAP trees.bmp has {int((tree_mask & ~tree_land).sum())} forest pixels outside land")

height_img = Image.open(MAP / "heightmap.bmp")
if height_img.size != (W, H):
    bad(f"MAP heightmap.bmp expected {W}x{H}, got {height_img.size}")
else:
    height_raster = np.asarray(height_img.convert("L"), dtype=np.uint8)
    if land_pixels.any() and int(height_raster[land_pixels].max()) - int(height_raster[land_pixels].min()) < 80:
        bad("MAP heightmap.bmp has insufficient relief variation on land")

normal_img = Image.open(MAP / "world_normal.bmp")
if normal_img.size != (W // 2, H // 2) or normal_img.mode != "RGB":
    bad(f"MAP world_normal.bmp expected RGB {W // 2}x{H // 2}, got {normal_img.mode} {normal_img.size}")
elif len(np.unique(np.asarray(normal_img).reshape(-1, 3), axis=0)) < 20:
    bad("MAP world_normal.bmp is nearly flat")

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
naval_base_provinces: set[int] = set()
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
        if "naval_base" in _inner:
            naval_base_provinces.add(int(pr))
            if defs.get(int(pr), {}).get("coastal") != "true":
                bad(f"STATE {sid} naval_base on non-coastal {pr}")
for sid, n in state_ids.items():
    if n > 1:
        bad(f"STATE id {sid} defined {n} times")
if state_ids and sorted(state_ids) != list(range(1, max(state_ids) + 1)):
    bad("STATE ids not contiguous 1..N")
for pid, d in defs.items():
    if pid and d["type"] == "land" and pid not in state_of:
        bad(f"STATE land province {pid} not in any state")
coastal_provinces = {
    pid for pid, d in defs.items()
    if pid and d["type"] == "land" and d["coastal"] == "true"
}
if naval_base_provinces != coastal_provinces:
    missing = sorted(coastal_provinces - naval_base_provinces)
    extra = sorted(naval_base_provinces - coastal_provinces)
    bad(f"STATE naval bases do not match coastal provinces (missing={missing}, extra={extra})")

# ---------- strategic regions ----------
sr_of: dict[int, int] = {}
strategic_region_ids = set()
for p in sorted((MAP / "strategicregions").glob("*.txt")):
    brace_balance(p)
    t = strip_comments(read(p))
    rid = int(re.search(r"\bid\s*=\s*(\d+)", t).group(1))
    if rid in strategic_region_ids:
        bad(f"SR id {rid} is defined more than once")
    strategic_region_ids.add(rid)
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

# ---------- strategic-region weather positions ----------
weather_region_ids = set()
for ln, line in enumerate(read(MAP / "weatherpositions.txt").splitlines(), 1):
    if not line.strip():
        continue
    fields = line.split(";")
    if len(fields) != 5:
        bad(f"WEATHER line {ln}: expected 'region_id;x;height;y;size'")
        continue
    try:
        rid = int(fields[0])
        x, _height, y = map(float, fields[1:4])
    except ValueError:
        bad(f"WEATHER line {ln}: invalid numeric field")
        continue
    if rid not in strategic_region_ids:
        bad(f"WEATHER line {ln}: unknown strategic region {rid}")
    if rid in weather_region_ids:
        bad(f"WEATHER line {ln}: duplicate position for region {rid}")
    weather_region_ids.add(rid)
    if not 0 <= x < W or not 0 <= y < H:
        bad(f"WEATHER line {ln}: position ({x}, {y}) outside {W}x{H} map")
    else:
        pid = int(idmap[min(H - 1, int(H - y)), int(x)])
        if sr_of.get(pid) != rid:
            bad(f"WEATHER line {ln}: position resolves to province {pid}, not strategic region {rid}")
    if not fields[4]:
        bad(f"WEATHER line {ln}: missing size")
if weather_region_ids != strategic_region_ids:
    missing = sorted(strategic_region_ids - weather_region_ids)
    extra = sorted(weather_region_ids - strategic_region_ids)
    bad(f"WEATHER regions do not match strategic regions (missing={missing}, extra={extra})")

# ---------- buildings.txt ----------
port_spawn_count = 0
for ln, line in enumerate(read(MAP / "buildings.txt").splitlines(), 1):
    f = line.split(";")
    if len(f) < 7:
        continue
    sid, btype = int(f[0]), f[1]
    if sid not in state_ids:
        bad(f"BUILDINGS line {ln}: state {sid} unknown")
    try:
        x, y = float(f[2]), float(f[4])
    except ValueError:
        bad(f"BUILDINGS line {ln}: invalid coordinates")
        continue
    if not 0 <= x < W or not 0 <= y < H:
        bad(f"BUILDINGS line {ln}: position ({x}, {y}) outside {W}x{H} map")
    else:
        province = int(idmap[min(H - 1, int(H - y)), int(x)])
        if state_of.get(province) != sid:
            bad(
                f"BUILDINGS line {ln}: position resolves to province {province} "
                f"in state {state_of.get(province)}, not state {sid}"
            )
    if btype == "infrastructure":
        bad(f"BUILDINGS line {ln}: infrastructure has no map building mesh")
    if btype == "naval_base_spawn":
        port_spawn_count += 1
        sea = int(f[6])
        if sea and defs.get(sea, {}).get("type") != "sea":
            bad(f"BUILDINGS line {ln}: naval_base adjacent {sea} is not sea")
coastal_province_count = sum(
    1 for pid, d in defs.items() if pid and d["type"] == "land" and d["coastal"] == "true"
)
if port_spawn_count != coastal_province_count:
    bad(
        f"BUILDINGS has {port_spawn_count} naval-base spawn points for "
        f"{coastal_province_count} coastal provinces"
    )

# ---------- unitstacks ----------
unitstack_slots: dict[int, set[int]] = defaultdict(set)
for ln, line in enumerate(read(MAP / "unitstacks.txt").splitlines(), 1):
    fields = line.split(";")
    if len(fields) != 7:
        bad(f"UNITSTACKS line {ln}: expected 7 fields")
        continue
    try:
        pid, slot = int(fields[0]), int(fields[1])
        x, y = float(fields[2]), float(fields[4])
    except ValueError:
        bad(f"UNITSTACKS line {ln}: invalid province, slot, or position")
        continue
    if pid not in defs or pid == 0:
        bad(f"UNITSTACKS province {pid} undefined")
        continue
    if slot in unitstack_slots[pid]:
        bad(f"UNITSTACKS province {pid} has duplicate slot {slot}")
    unitstack_slots[pid].add(slot)
    if not 0 <= x < W or not 0 <= y < H:
        bad(f"UNITSTACKS line {ln}: position ({x}, {y}) outside {W}x{H} map")
    else:
        map_province = int(idmap[min(H - 1, int(H - y)), int(x)])
        if map_province != pid:
            bad(f"UNITSTACKS line {ln}: position resolves to province {map_province}, not {pid}")
expected_slots = {0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 21, 22, 23, 24, 25, 26, 27, 28, 38}
for pid in ids:
    if pid == 0:
        continue
    slots = unitstack_slots.get(pid, set())
    expected_province_slots = expected_slots | (
        {19, 20} if defs[pid]["type"] == "land" and defs[pid]["coastal"] == "true" else set()
    )
    if slots != expected_province_slots:
        bad(
            f"UNITSTACKS province {pid} has {len(slots)} slots, "
            f"expected {len(expected_province_slots)}"
        )

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
    technology = block(t, "set_technology")
    if technology and re.search(r"^\s*artillery\s*=", technology, re.M):
        bad(f"COUNTRY {tag} has invalid technology id 'artillery' in set_technology")
    for oob in re.findall(r'\boob\s*=\s*"?([\w]+)"?', t):
        if oob not in oob_names:
            bad(f"COUNTRY {tag} oob {oob} missing")
    m = re.search(r"\bcapital\s*=\s*(\d+)", t)
    if m and int(m.group(1)) not in state_ids:
        bad(f"COUNTRY {tag} capital {m.group(1)} not an existing state")

# ---------- national focus trees ----------
focus_tree_counts: dict[str, int] = {}
for tag, baseline in FOCUS_BASELINES.items():
    p = ROOT / f"common/national_focus/mk_{tag}.txt"
    if not p.is_file():
        bad(f"FOCUS {tag} missing tree file")
        continue
    tree_text = strip_comments(read(p))
    tree = block(tree_text, "focus_tree")
    if tree is None:
        bad(f"FOCUS {tag} missing focus_tree block")
        continue
    focuses = script_blocks(tree, "focus")
    count = len(focuses)
    focus_tree_counts[tag] = count
    minimum = baseline * 3
    if count < minimum:
        bad(f"FOCUS {tag} has {count}, below 3x baseline {baseline} ({minimum})")
    if not 250 <= count <= 290:
        bad(f"FOCUS {tag} has {count}, outside approved 250..290 range")
    ids_seen: set[str] = set()
    for index, focus in enumerate(focuses, 1):
        id_match = re.search(r"^\s*id\s*=\s*(\S+)", focus, re.M)
        focus_id = id_match.group(1) if id_match else f"focus #{index}"
        if not id_match:
            bad(f"FOCUS {tag} {focus_id} missing ID")
        elif focus_id in ids_seen:
            bad(f"FOCUS {tag} duplicate ID {focus_id}")
        else:
            ids_seen.add(focus_id)
        cost_match = re.search(r"^\s*cost\s*=\s*(\S+)", focus, re.M)
        if not cost_match or cost_match.group(1) != "3":
            bad(f"FOCUS {tag} {focus_id} cost is not 3")

# Focus-unlocked characters can only be offered for capture if the defeated
# country completed the matching focus; the on-action records that eligibility
# on the victor for the post-capitulation recruitment events.
capture_actions = read(ROOT / "common/on_actions/mk_on_actions.txt")
ruler_events = read(ROOT / "events/mk_ruler_events.txt")
capture_event_blocks = {
    match.group(1): event
    for event in script_blocks(ruler_events, "country_event")
    if (match := re.search(r"^\s*id\s*=\s*(mk_ruler\.\d+)", event, re.M))
}
for tag, characters in FOCUS_UNLOCKED_CHARACTERS.items():
    focus_path = ROOT / f"common/national_focus/mk_{tag}.txt"
    focus_tree = block(strip_comments(read(focus_path)), "focus_tree") or ""
    focus_by_id = {}
    for focus in script_blocks(focus_tree, "focus"):
        match = re.search(r"^\s*id\s*=\s*(\S+)", focus, re.M)
        if match:
            focus_by_id[match.group(1)] = focus
    for character_id, focus_id in characters.items():
        unlock_flag = f"mk_unlocked_character_{character_id.lower()}"
        captured_flag = f"mk_captured_character_{character_id.lower()}"
        focus = focus_by_id.get(focus_id, "")
        if not focus:
            bad(f"CHARACTER {character_id} unlock focus {focus_id} missing")
        elif (f"recruit_character = {character_id}" in focus
              or f"set_country_flag = {unlock_flag}" not in focus):
            bad(f"CHARACTER {character_id} focus {focus_id} must set {unlock_flag} without recruit_character")
        matching_hooks = [
            hook for hook in script_blocks(capture_actions, "if")
            if f"original_tag = {tag}" in hook
            and f"has_country_flag = {unlock_flag}" in hook
            and f"set_country_flag = {captured_flag}" in hook
        ]
        if not matching_hooks:
            bad(f"CHARACTER {character_id} capture hook must gate on {unlock_flag} and record {captured_flag}")
            continue
        for hook in matching_hooks:
            event_match = re.search(r"\bcountry_event\s*=\s*\{\s*id\s*=\s*(mk_ruler\.\d+)", hook)
            event = capture_event_blocks.get(event_match.group(1), "") if event_match else ""
            character_source = read(ROOT / f"common/characters/{tag}.txt")
            character = block(strip_comments(character_source), character_id) or ""
            advisor = block(character, "advisor")
            field_marshal = block(character, "field_marshal")
            corps_commander = block(character, "corps_commander")
            role_blocks = [role for role in (advisor, field_marshal, corps_commander) if role]
            if not any(
                f"has_country_flag = {unlock_flag}" in (block(role, "available") or "")
                for role in role_blocks
            ):
                bad(f"CHARACTER {character_id} role must be gated by {unlock_flag}")
            if not event:
                bad(f"CHARACTER {character_id} capture hook must reference an existing ruler event")
            elif "generate_character = {" not in event:
                bad(f"CHARACTER {character_id} capture event must generate a recruitable copy")
            elif advisor:
                slot_match = re.search(r"\bslot\s*=\s*(\w+)", advisor)
                advisor_token = "political" if slot_match and slot_match.group(1) == "political_advisor" else "army"
                if f"activate_advisor = mk_capture_{character_id.lower()}_{advisor_token}" not in event:
                    bad(f"CHARACTER {character_id} capture event must activate its advisor copy")
            elif field_marshal and "add_field_marshal_role = {" not in event:
                bad(f"CHARACTER {character_id} capture event must assign its field-marshal role")
            elif corps_commander and "add_corps_commander_role = {" not in event:
                bad(f"CHARACTER {character_id} capture event must assign its commander role")
            elif not (advisor or field_marshal or corps_commander):
                bad(f"CHARACTER {character_id} has no supported role to validate")

# ---------- characters ----------
ideologies = set()
for p in Path(sys.argv[1] if len(sys.argv) > 1 else "").glob("common/ideologies/*.txt") if len(sys.argv) > 1 else []:
    pass
for p in (ROOT / "common/characters").glob("*.txt"):
    brace_balance(p)

# ---------- every mod script file ----------
decision_category_ids = {
    category
    for p in (ROOT / "common/decisions/categories").glob("*.txt")
    for category in re.findall(r"^([A-Za-z0-9_]+)\s*=\s*\{", strip_comments(read(p)), re.M)
}
for p in (ROOT / "common/decisions").glob("*.txt"):
    for category in re.findall(r"^([A-Za-z0-9_]+)\s*=\s*\{", strip_comments(read(p)), re.M):
        if category not in decision_category_ids:
            bad(f"DECISION {p.name} uses undefined category {category}")

for sub in ("common", "events", "history/units", "map/strategicregions"):
    for p in (ROOT / sub).rglob("*.txt"):
        if "characters" in p.parts or p.parent.name in ("states",):
            continue
        brace_balance(p)

print(f"provinces={len(ids)-1} land={sum(1 for pid, d in defs.items() if pid and d['type']=='land')} "
      f"states={len(state_ids)} SR-provinces={len(sr_of)} tags={len(tags)} owners={len(owners)}")
print("focus_trees:", ", ".join(f"{tag}={focus_tree_counts[tag]}" for tag in sorted(focus_tree_counts)))
cnt = Counter(m.split()[0] for m in problems)
print("summary:", dict(cnt))
for m in problems[:200]:
    print(" -", m)
if len(problems) > 200:
    print(f" ... {len(problems)-200} more")
sys.exit(1 if problems else 0)
