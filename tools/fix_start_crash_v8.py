# -*- coding: utf-8 -*-
"""
v0.3.18 — CTD after Launching SINGLEPLAYER:
ALL naval_base_spawn lines had adjacent-sea field = LAND province id.
HOI4 needs a real SEA province there; wrong sea adj → native crash on start/navy.
Also copy map/colors.txt from vanilla.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
DOCS_MOD_DIR = DOCS / "mod" / "Mir_Kazualnosti"
MOD_VERSION = "0.3.18"
GAME_VERSION = "1.19.*"

REPLACE_PATHS = [
    "history/countries",
    "history/states",
    "history/units",
    "history/diplomacy",
    "history/general",
    "common/bookmarks",
    "map/strategicregions",
    "common/ai_strategy_plans",
    "common/ai_strategy",
    "common/ai_areas",
    "common/ai_faction_theaters",
    "common/national_focus",
    "common/on_actions",
    "events",
    "common/decisions",
]


def load_definition():
    id2type = {}
    color2id = {}
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        p = line.split(";")
        if len(p) < 5:
            continue
        try:
            pid = int(p[0])
        except ValueError:
            continue
        rgb = (int(p[1]), int(p[2]), int(p[3]))
        id2type[pid] = p[4].strip()
        color2id[rgb] = pid
    return id2type, color2id


def build_land_to_sea(id2type, color2id):
    """Pixel-neighbour adjacency: land province -> set of adjacent sea provinces."""
    img = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = img.load()
    w, h = img.size
    land_to_sea: dict[int, set[int]] = defaultdict(set)
    # sample every pixel edge to neighbour (right + down) — enough for adjacency
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            pid = color2id.get(c)
            if pid is None:
                continue
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if nx >= w or ny >= h:
                    continue
                nid = color2id.get(px[nx, ny])
                if nid is None or nid == pid:
                    continue
                t1, t2 = id2type.get(pid), id2type.get(nid)
                if t1 == "land" and t2 == "sea":
                    land_to_sea[pid].add(nid)
                elif t1 == "sea" and t2 == "land":
                    land_to_sea[nid].add(pid)
    print(f"coastal land provinces with sea neighbour: {len(land_to_sea)}")
    return land_to_sea


def province_at(color2id, x_game: float, y_game: float, height: int):
    """buildings use game coords: X east, Z south; BMP Y is top-down → invert."""
    img_x = int(round(x_game))
    img_y = int(round(height - 1 - y_game))
    img = getattr(province_at, "_img", None)
    if img is None:
        province_at._img = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
        img = province_at._img
    w, h = img.size
    img_x = max(0, min(w - 1, img_x))
    img_y = max(0, min(h - 1, img_y))
    return color2id.get(img.load()[img_x, img_y])


def fix_naval_bases(id2type, color2id, land_to_sea):
    bpath = ROOT / "map" / "buildings.txt"
    lines = [l for l in bpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    h = Image.open(ROOT / "map" / "provinces.bmp").size[1]
    fixed = 0
    dropped = 0
    out = []
    for line in lines:
        parts = line.split(";")
        if len(parts) < 7 or parts[1] != "naval_base_spawn":
            out.append(line)
            continue
        x, z = float(parts[2]), float(parts[4])
        old_adj = int(parts[6])
        # prefer province under the building marker
        land_id = province_at(color2id, x, z, h)
        if land_id is None or id2type.get(land_id) != "land":
            # fallback: old field was wrongly the land province
            if id2type.get(old_adj) == "land":
                land_id = old_adj
            else:
                dropped += 1
                continue
        seas = land_to_sea.get(land_id)
        if not seas:
            dropped += 1
            continue
        sea_id = sorted(seas)[0]
        parts[6] = str(sea_id)
        out.append(";".join(parts))
        if sea_id != old_adj:
            fixed += 1
    bpath.write_text("\n".join(out), encoding="utf-8")
    print(f"naval_base_spawn fixed={fixed} dropped={dropped} total_kept={sum(1 for l in out if 'naval_base_spawn' in l)}")


def add_special_project_spawns():
    """Vanilla has special_project_facility_spawn per state; restore near air_base."""
    bpath = ROOT / "map" / "buildings.txt"
    lines = [l for l in bpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    lines = [l for l in lines if "special_project" not in l]
    air = {}
    for l in lines:
        p = l.split(";")
        if len(p) >= 5 and p[1] == "air_base":
            air[int(p[0])] = (float(p[2]), float(p[4]))
    state_ids = []
    for f in (ROOT / "history" / "states").glob("*.txt"):
        m = re.search(r"id\s*=\s*(\d+)", f.read_text(encoding="utf-8"))
        if m:
            state_ids.append(int(m.group(1)))
    extra = []
    for sid in sorted(set(state_ids)):
        if sid in air:
            x, z = air[sid]
        else:
            x, z = 100.0 + sid, 100.0 + sid
        extra.append(
            f"{sid};special_project_facility_spawn;{x - 2.0:.2f};10.00;{z - 2.0:.2f};0.00;0"
        )
    bpath.write_text("\n".join(lines + extra), encoding="utf-8")
    print(f"added special_project_facility_spawn: {len(extra)}")


def copy_colors():
    src = VANILLA / "map" / "colors.txt"
    dst = ROOT / "map" / "colors.txt"
    if src.exists():
        shutil.copy2(src, dst)
        print("copied colors.txt")


def write_descriptor(path_line: str) -> str:
    body = (
        f'version="{MOD_VERSION}"\n'
        "tags={\n"
        '\t"Alternative History"\n'
        '\t"Total Conversion"\n'
        '\t"Map"\n'
        '\t"National Focuses"\n'
        '\t"Gameplay"\n'
        "}\n"
        'name="Mir Kazualnosti: Epokha Skhodyashchikh s Uma Pravitely"\n'
        f'supported_version="{GAME_VERSION}"\n'
        + "".join(f'replace_path="{p}"\n' for p in REPLACE_PATHS)
    )
    pointer = body + f'path="{path_line}"\n'
    (ROOT / "descriptor.mod").write_text(body, encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    return pointer


def install_into_documents() -> str:
    DOCS_MOD_DIR.parent.mkdir(parents=True, exist_ok=True)
    if DOCS_MOD_DIR.exists() or DOCS_MOD_DIR.is_symlink():
        subprocess.run(["cmd", "/c", "rmdir", str(DOCS_MOD_DIR)], check=False)
        if DOCS_MOD_DIR.exists():
            shutil.rmtree(DOCS_MOD_DIR, ignore_errors=True)
    r = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(DOCS_MOD_DIR), str(ROOT)],
        capture_output=True,
        text=True,
    )
    print("junction:", (r.stdout or r.stderr).strip(), "code", r.returncode)
    if r.returncode != 0 or not DOCS_MOD_DIR.exists():
        return "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"
    return "mod/Mir_Kazualnosti"


def main():
    id2type, color2id = load_definition()
    land_to_sea = build_land_to_sea(id2type, color2id)
    fix_naval_bases(id2type, color2id, land_to_sea)
    add_special_project_spawns()
    copy_colors()

    # sanity: no naval adj to land
    bad = 0
    for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines():
        if "naval_base_spawn" not in l:
            continue
        adj = int(l.split(";")[6])
        if id2type.get(adj) != "sea":
            bad += 1
    assert bad == 0, f"still {bad} naval with non-sea adj"

    path_line = install_into_documents()
    pointer = write_descriptor(path_line)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )
    print("path=", path_line)
    print("DONE v0.3.18")
    print(pointer)


if __name__ == "__main__":
    main()
