# -*- coding: utf-8 -*-
"""
v0.3.12 — campaign start crash:
- restore vanilla scripted_triggers/effects (MIO was broken)
- replace_path history/general (spain/china advisors → missing focuses)
- replace_path MIO organizations
- rebuild unitstacks with all stack slots
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MOD_VERSION = "0.3.12"
GAME_VERSION = "1.19.*"
MOD_PATH = "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"
WIDTH, HEIGHT = 2048, 1024

# Vanilla stack type indices commonly present per province
STACK_TYPES = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 21, 22, 23, 24, 25, 26, 27, 28, 38]

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
    "common/military_industrial_organization",
    "common/peace_conference",
    "common/special_projects",
    # do NOT replace scripted_triggers/effects — that broke MIO (is_literally_china etc.)
]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clear_txt(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*"):
        if f.is_file():
            f.unlink()


def ensure_focus_onactions_events():
    # keep previous stubs
    write(
        ROOT / "common" / "national_focus" / "mk_generic.txt",
        "focus_tree = {\n\tid = mk_generic_focus\n\tcountry = { factor = 0 }\n\tdefault = yes\n\treset_on_civilwar = no\n}\n",
    )
    write(ROOT / "common" / "on_actions" / "mk_on_actions.txt", "on_actions = {\n}\n")
    write(ROOT / "events" / "mk_empty.txt", "# empty\n")
    # decisions
    d = ROOT / "common" / "decisions"
    for f in d.rglob("*"):
        if f.is_file():
            f.unlink()
    write(d / "mk_empty.txt", "# empty\n")
    write(d / "categories" / "mk_empty.txt", "# empty\n")
    print("focus/on_actions/events/decisions ok")


def stub_history_general():
    d = ROOT / "history" / "general"
    clear_txt(d)
    write(d / "mk_empty.txt", "# total conversion: no vanilla shared advisors\n")
    print("history/general ok")


def stub_mio():
    d = ROOT / "common" / "military_industrial_organization"
    # clear tree
    if d.exists():
        for f in d.rglob("*"):
            if f.is_file():
                f.unlink()
    write(d / "organizations" / "mk_empty.txt", "# empty\n")
    write(d / "policies" / "mk_empty.txt", "# empty\n")
    write(d / "ai_strategies" / "mk_empty.txt", "# empty\n")
    print("MIO ok")


def remove_broken_scripted_stubs():
    """Delete our empty scripted_* stubs so if any leftover replace is gone, vanilla loads cleanly."""
    for folder in ("scripted_effects", "scripted_triggers"):
        d = ROOT / "common" / folder
        if not d.exists():
            continue
        for f in d.glob("mk_empty.txt"):
            f.unlink()
        # if folder only had our stub, remove folder files; don't leave empty replace bait
    print("removed mk scripted stubs")


def rebuild_unitstacks():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(line.split(";"))
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows if p[0].isdigit() and int(p[0]) > 0}
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    from collections import defaultdict

    sums = defaultdict(lambda: [0.0, 0.0, 0])
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            pid = color_to_pid.get(px[x, y])
            if pid is None:
                continue
            s = sums[pid]
            s[0] += x
            s[1] += y
            s[2] += 1
    centers = {pid: (sx / n, sy / n) for pid, (sx, sy, n) in sums.items() if n}

    lines = []
    offsets = {
        0: (0.0, 0.0),
        1: (0.5, -2.5),
        2: (3.0, -2.5),
        3: (-2.0, 0.0),
        4: (4.0, -0.5),
        5: (-3.0, 2.0),
        6: (2.5, 2.0),
        7: (0.0, 3.0),
        9: (-1.5, -3.0),
        10: (1.5, -3.5),
        21: (5.0, 1.0),
        22: (-5.0, 1.0),
        23: (3.5, 3.5),
        24: (-3.5, 3.5),
        25: (0.5, 5.0),
        26: (-0.5, -5.0),
        27: (6.0, -1.0),
        28: (-6.0, -1.0),
        38: (0.0, -1.0),
    }
    for pid in sorted(centers):
        cx, cy = centers[pid]
        y_game = (HEIGHT - 1) - cy
        for st in STACK_TYPES:
            dx, dy = offsets.get(st, (0.0, 0.0))
            lines.append(
                f"{pid};{st};{cx + dx:.2f};12.00;{y_game + dy:.2f};0.00;0.50"
            )
    # no trailing empty line issues for unitstacks — final newline ok
    (ROOT / "map" / "unitstacks.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"unitstacks lines={len(lines)} provs={len(centers)}")


def write_descriptor():
    # unique replace paths
    seen = []
    for p in REPLACE_PATHS:
        if p not in seen:
            seen.append(p)
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
        + "".join(f'replace_path="{p}"\n' for p in seen)
    )
    pointer = body + f'path="{MOD_PATH}"\n'
    (ROOT / "descriptor.mod").write_text(body, encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    docs = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
    (docs / "mod").mkdir(parents=True, exist_ok=True)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (docs / "mod" / name).write_text(pointer, encoding="utf-8")
    (docs / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )
    # sync register_mod constants lightly
    print("descriptor ok")
    print("replace_paths:", ", ".join(seen))


def main():
    ensure_focus_onactions_events()
    stub_history_general()
    stub_mio()
    remove_broken_scripted_stubs()
    rebuild_unitstacks()
    write_descriptor()
    print("DONE v0.3.12")


if __name__ == "__main__":
    main()
