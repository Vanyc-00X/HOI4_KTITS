# -*- coding: utf-8 -*-
"""
v0.3.15 — post-VCI-launch crash:
- restore vanilla scripted_effects (blanking broke special_projects/techs)
- remove phantom province 0 from definition.csv
- strip rocket_site_spawn from buildings
- give landless stubs unique capitals (not all capital=1)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
DOCS_MOD_DIR = DOCS / "mod" / "Mir_Kazualnosti"
MOD_VERSION = "0.3.15"
GAME_VERSION = "1.19.*"

PLAYABLE = {
    "VCI", "SOY", "BTR", "KRZ", "KZS", "MUS", "TRF", "ZLD", "ISL", "CLB",
    "ADL", "DMK", "FDP", "CRE", "SVA", "ART", "KMS", "ZNS", "ZKR", "ZML",
    "NBL", "ISG", "HRL", "SHF",
}

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


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def remove_province_zero():
    path = ROOT / "map" / "definition.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    kept = [l for l in lines if not l.startswith("0;")]
    removed = len(lines) - len(kept)
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    print(f"definition.csv: removed province 0 lines={removed}, kept={len(kept)}")


def strip_rocket_sites():
    path = ROOT / "map" / "buildings.txt"
    lines = [
        l
        for l in path.read_text(encoding="utf-8").splitlines()
        if l.strip() and "rocket_site" not in l
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"buildings without rocket_site: {len(lines)}")


def restore_scripted_effects():
    se = ROOT / "common" / "scripted_effects"
    if se.exists():
        shutil.rmtree(se)
        print("removed mod scripted_effects (use vanilla)")
    se.mkdir(parents=True, exist_ok=True)
    write(se / ".gitkeep", "")


def ensure_core_stubs():
    write(
        ROOT / "common" / "national_focus" / "mk_generic.txt",
        "focus_tree = {\n\tid = mk_generic_focus\n\tcountry = { factor = 0 }\n"
        "\tdefault = yes\n\treset_on_civilwar = no\n}\n\n"
        "focus_tree = {\n\tid = italian_focus\n\tcountry = { factor = 0 }\n"
        "\tdefault = no\n\treset_on_civilwar = no\n}\n\n"
        "focus_tree = {\n\tid = soviet_focus\n\tcountry = { factor = 0 }\n"
        "\tdefault = no\n\treset_on_civilwar = no\n}\n",
    )
    write(ROOT / "common" / "on_actions" / "mk_on_actions.txt", "on_actions = {\n}\n")
    write(ROOT / "events" / "mk_empty.txt", "# empty\n")
    write(ROOT / "history" / "general" / "mk_empty.txt", "# empty\n")
    write(ROOT / "common" / "decisions" / "mk_empty.txt", "# empty\n")
    write(ROOT / "common" / "decisions" / "categories" / "mk_empty.txt", "# empty\n")


def fix_stub_capitals():
    """Landless vanilla stubs all had capital=1 → redistribute across 1..127."""
    state_ids = sorted(
        int(m.group(1))
        for f in (ROOT / "history" / "states").glob("*.txt")
        for m in [re.search(r"id\s*=\s*(\d+)", f.read_text(encoding="utf-8"))]
        if m
    )
    if not state_ids:
        print("no states for capital fix")
        return
    n = 0
    for f in sorted((ROOT / "history" / "countries").glob("*.txt")):
        tag = f.name.split(" ")[0].split("-")[0].strip()
        if tag in PLAYABLE:
            continue
        text = f.read_text(encoding="utf-8")
        # stable pick from tag chars
        idx = sum(ord(c) for c in tag) % len(state_ids)
        cap = state_ids[idx]
        new_text, count = re.subn(
            r"capital\s*=\s*\d+", f"capital = {cap}", text, count=1
        )
        if count:
            f.write_text(new_text, encoding="utf-8")
            n += 1
    print(f"stub capitals redistributed: {n}")


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
    return pointer


def install_into_documents():
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
    # peace/MIO must stay absent (vanilla)
    for rel in (
        "common/peace_conference",
        "common/military_industrial_organization",
    ):
        p = ROOT / rel
        if p.exists():
            shutil.rmtree(p)
            print("removed", rel)

    restore_scripted_effects()
    remove_province_zero()
    strip_rocket_sites()
    ensure_core_stubs()
    fix_stub_capitals()

    path_line = install_into_documents()
    pointer = write_descriptor(path_line)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    defs = (ROOT / "map" / "definition.csv").read_text(encoding="utf-8")
    assert not any(l.startswith("0;") for l in defs.splitlines())
    assert "scripted_effects" not in pointer
    assert "rocket_site" not in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8")
    print("path=", path_line)
    print("DONE v0.3.15")
    print(pointer)


if __name__ == "__main__":
    main()
