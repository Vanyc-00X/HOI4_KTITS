# -*- coding: utf-8 -*-
"""
v0.3.13 — hard neutralize vanilla MIO/peace (file overrides),
strip special_project spawns, install mod under Documents/mod/Mir_Kazualnosti.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
DOCS_MOD_DIR = DOCS / "mod" / "Mir_Kazualnosti"
MOD_VERSION = "0.3.13"
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
    # subfolder replaces — parent-only sometimes ignored for these trees
    "common/military_industrial_organization",
    "common/military_industrial_organization/organizations",
    "common/military_industrial_organization/policies",
    "common/military_industrial_organization/ai_strategies",
    "common/peace_conference",
    "common/peace_conference/ai_peace",
    "common/peace_conference/cost_modifiers",
    "common/peace_conference/categories",
    "common/peace_conference/facet_costs",
]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def blank_overrides(vanilla_subdir: str, mod_subdir: str):
    """Create empty same-named files so overrides win even if replace_path fails."""
    src = VANILLA / vanilla_subdir
    dst = ROOT / mod_subdir
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    if not src.exists():
        print("missing vanilla", src)
        return
    for f in src.rglob("*.txt"):
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        # truly empty content — disables the scripted block
        out.write_text(f"# neutralized for total conversion ({rel.as_posix()})\n", encoding="utf-8")
        n += 1
    print(f"blanked {mod_subdir}: {n} files")


def strip_special_project_spawns():
    bpath = ROOT / "map" / "buildings.txt"
    lines = [
        l
        for l in bpath.read_text(encoding="utf-8").splitlines()
        if l.strip() and "special_project" not in l
    ]
    # no trailing blank line
    bpath.write_text("\n".join(lines), encoding="utf-8")
    print(f"buildings without special_project: {len(lines)}")


def ensure_core_stubs():
    write(
        ROOT / "common" / "national_focus" / "mk_generic.txt",
        "focus_tree = {\n\tid = mk_generic_focus\n\tcountry = { factor = 0 }\n"
        "\tdefault = yes\n\treset_on_civilwar = no\n}\n",
    )
    write(ROOT / "common" / "on_actions" / "mk_on_actions.txt", "on_actions = {\n}\n")
    write(ROOT / "events" / "mk_empty.txt", "# empty\n")
    write(ROOT / "history" / "general" / "mk_empty.txt", "# empty\n")
    # decisions only ours
    d = ROOT / "common" / "decisions"
    for f in list(d.rglob("*.txt")):
        if f.name != "mk_empty.txt" and "categories" not in f.parts:
            # keep only mk_empty
            pass
    write(d / "mk_empty.txt", "# empty\n")
    write(d / "categories" / "mk_empty.txt", "# empty\n")
    # remove special_projects replace bait — delete our empty tree so vanilla can load if we don't replace
    sp = ROOT / "common" / "special_projects"
    if sp.exists():
        shutil.rmtree(sp, ignore_errors=True)
        print("removed mod special_projects (use vanilla)")


def write_descriptor(path_line: str):
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
    return body, pointer


def install_into_documents():
    """
    Junction Documents/mod/Mir_Kazualnosti -> ROOT and point launcher path to mod/Mir_Kazualnosti.
    This is the most reliable layout for replace_path on Windows.
    """
    DOCS_MOD_DIR.parent.mkdir(parents=True, exist_ok=True)
    # remove old dir/junction/file
    if DOCS_MOD_DIR.exists() or DOCS_MOD_DIR.is_symlink():
        # directory junction
        subprocess.run(["cmd", "/c", "rmdir", str(DOCS_MOD_DIR)], check=False)
        if DOCS_MOD_DIR.exists():
            shutil.rmtree(DOCS_MOD_DIR, ignore_errors=True)
    # also clear OLD_no_map if present — leave it
    cmd = ["cmd", "/c", "mklink", "/J", str(DOCS_MOD_DIR), str(ROOT)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("junction:", r.stdout.strip() or r.stderr.strip(), "code", r.returncode)
    if r.returncode != 0 or not DOCS_MOD_DIR.exists():
        # fallback: copy essential? too heavy. use absolute path
        print("junction failed, keeping absolute path")
        return "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"
    return "mod/Mir_Kazualnosti"


def main():
    ensure_core_stubs()
    blank_overrides(
        "common/military_industrial_organization",
        "common/military_industrial_organization",
    )
    blank_overrides("common/peace_conference", "common/peace_conference")
    strip_special_project_spawns()

    path_line = install_into_documents()
    body, pointer = write_descriptor(path_line)

    # launcher files
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    # sanity
    assert (ROOT / "map" / "provinces.bmp").exists()
    assert "military_industrial_organization/organizations" in pointer
    assert "special_project" not in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8")
    print("path=", path_line)
    print("DONE v0.3.13")
    print(pointer)


if __name__ == "__main__":
    main()
