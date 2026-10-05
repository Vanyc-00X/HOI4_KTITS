# -*- coding: utf-8 -*-
"""
v0.3.19 — ACCESS_VIOLATION after Launching SINGLEPLAYER (UI init).
Crash dumps show C0000005 at same address; game reaches in-game GUI then dies.

Mitigations:
- nuclear_reactor_spawn per state (required spawn_point in 1.19 buildings)
- empty supply_nodes.txt / railways.txt (wiki: invalid supply crashes on SP start)
- province 0 -> sea (avoid land/continent 0 phantom)
- minimal ai_area covering all land (replace_path left empty before)
- keep naval sea-adj valid; keep rocket/air/naval; drop special_project_facility_spawn
  (user has no Gotterdammerung; SP facilities previously implicated)
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
MOD_VERSION = "0.3.19"
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
    rows = []
    id2type = {}
    color2id = {}
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        p = line.split(";")
        if len(p) < 8:
            continue
        pid = int(p[0])
        id2type[pid] = p[4]
        color2id[(int(p[1]), int(p[2]), int(p[3]))] = pid
        rows.append(p)
    return rows, id2type, color2id


def fix_province_zero(rows):
    for p in rows:
        if p[0] == "0":
            # unused black colour — mark as sea so no land/continent issues
            p[4] = "sea"
            p[5] = "false"
            p[6] = "ocean"
            p[7] = "0"
            print("province 0 set to sea/ocean")
            break
    (ROOT / "map" / "definition.csv").write_text(
        "\n".join(";".join(p) for p in rows) + "\n", encoding="utf-8"
    )


def rebuild_buildings(id2type, color2id):
    """Regenerate spawn points; naval with real sea adj; no special_project."""
    img = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = img.load()
    w, h = img.size
    land_to_sea = defaultdict(set)
    for y in range(h):
        for x in range(w):
            pid = color2id.get(px[x, y])
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

    # keep existing air/naval/rocket lines if valid; else rebuild from current file
    old = [
        l
        for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines()
        if l.strip() and "special_project" not in l
    ]
    naval = []
    air = {}
    rocket = {}
    for l in old:
        parts = l.split(";")
        if len(parts) < 7:
            continue
        typ = parts[1]
        sid = int(parts[0])
        if typ == "naval_base_spawn":
            x, z = float(parts[2]), float(parts[4])
            ix = max(0, min(w - 1, int(round(x))))
            iy = max(0, min(h - 1, int(round(h - 1 - z))))
            land = color2id.get(px[ix, iy])
            if land is None or id2type.get(land) != "land":
                continue
            seas = land_to_sea.get(land)
            if not seas:
                continue
            parts[6] = str(sorted(seas)[0])
            naval.append(";".join(parts))
        elif typ == "air_base":
            air[sid] = (float(parts[2]), float(parts[4]))
        elif typ == "rocket_site_spawn":
            rocket[sid] = l

    state_ids = sorted(
        {
            int(m.group(1))
            for f in (ROOT / "history" / "states").glob("*.txt")
            for m in [re.search(r"id\s*=\s*(\d+)", f.read_text(encoding="utf-8"))]
            if m
        }
    )
    out = list(naval)
    for sid in state_ids:
        if sid in air:
            x, z = air[sid]
        else:
            x, z = 200.0 + sid * 3, 200.0 + sid * 2
        out.append(f"{sid};air_base;{x:.2f};12.00;{z:.2f};0.00;0")
        out.append(f"{sid};rocket_site_spawn;{x + 2:.2f};10.00;{z + 2:.2f};0.00;0")
        out.append(f"{sid};nuclear_reactor_spawn;{x - 2:.2f};10.00;{z + 4:.2f};0.00;0")
    (ROOT / "map" / "buildings.txt").write_text("\n".join(out), encoding="utf-8")
    print(
        f"buildings: naval={len(naval)} states={len(state_ids)} "
        f"with air/rocket/nuclear (no special_project)"
    )


def empty_supply_files():
    (ROOT / "map" / "supply_nodes.txt").write_text("", encoding="utf-8")
    (ROOT / "map" / "railways.txt").write_text("", encoding="utf-8")
    print("emptied supply_nodes.txt and railways.txt")


def write_ai_area(id2type):
    land = sorted(pid for pid, t in id2type.items() if t == "land" and pid != 0)
    # chunk to keep lines readable
    chunks = []
    for i in range(0, len(land), 40):
        chunks.append(" ".join(str(x) for x in land[i : i + 40]))
    body = (
        "areas = {\n"
        "\tmk_all_land = {\n"
        "\t\tstrategic_regions = {\n"
        + "".join(f"\t\t\t{i}\n" for i in range(1, 44))
        + "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    # ai_areas use strategic_regions OR continents typically — use strategic_regions 1-43
    path = ROOT / "common" / "ai_areas" / "mk_empty.txt"
    # overwrite with real area
    path.write_text(body, encoding="utf-8")
    print("wrote minimal ai_area mk_all_land over", len(land), "land provinces via SRs")


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
    rows, id2type, color2id = load_definition()
    fix_province_zero(rows)
    # reload types after province 0 change
    _, id2type, color2id = load_definition()
    rebuild_buildings(id2type, color2id)
    empty_supply_files()
    write_ai_area(id2type)

    path_line = install_into_documents()
    pointer = write_descriptor(path_line)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    # sanity naval
    bad = 0
    for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines():
        if "naval_base_spawn" not in l:
            continue
        if id2type.get(int(l.split(";")[6])) != "sea":
            bad += 1
    assert bad == 0
    assert "nuclear_reactor_spawn" in (ROOT / "map" / "buildings.txt").read_text(
        encoding="utf-8"
    )
    assert "special_project" not in (ROOT / "map" / "buildings.txt").read_text(
        encoding="utf-8"
    )
    print("path=", path_line)
    print("DONE v0.3.19")
    print(pointer)


if __name__ == "__main__":
    main()
