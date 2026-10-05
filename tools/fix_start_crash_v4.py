# -*- coding: utf-8 -*-
"""
v0.3.14 — stop blanking peace/MIO (restore vanilla), blank scripted_effects instead.
Hard crash was: Expected exactly one peace_action_category to be set as default.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
DOCS_MOD_DIR = DOCS / "mod" / "Mir_Kazualnosti"
MOD_VERSION = "0.3.14"
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
    # kill vanilla history side-effects that call missing focus trees / missions
    "common/scripted_effects",
]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def blank_overrides(vanilla_subdir: str, mod_subdir: str):
    src = VANILLA / vanilla_subdir
    dst = ROOT / mod_subdir
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in src.rglob("*.txt"):
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"# neutralized for total conversion ({rel.as_posix()})\n", encoding="utf-8")
        n += 1
    print(f"blanked {mod_subdir}: {n} files")


def remove_mod_tree(rel: str):
    p = ROOT / rel
    if p.exists():
        shutil.rmtree(p)
        print("removed", rel)


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
    d = ROOT / "common" / "decisions"
    write(d / "mk_empty.txt", "# empty\n")
    write(d / "categories" / "mk_empty.txt", "# empty\n")
    # keep a tiny scripted_effects stub in case replace needs a file
    write(ROOT / "common" / "scripted_effects" / "mk_empty.txt", "# empty\n")


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
    # HOI4 prefers forward-slash relative path under Documents
    return "mod/Mir_Kazualnosti"


def main():
    # 1) restore vanilla peace + MIO by deleting our blank overrides
    remove_mod_tree("common/peace_conference")
    remove_mod_tree("common/military_industrial_organization")

    ensure_core_stubs()
    # 2) blank ALL vanilla scripted_effects (same filenames) so history cannot
    #    call load_focus_tree italian_focus / soviet_focus or SWI missions
    blank_overrides("common/scripted_effects", "common/scripted_effects")
    write(ROOT / "common" / "scripted_effects" / "mk_empty.txt", "# empty\n")

    path_line = install_into_documents()
    body, pointer = write_descriptor(path_line)

    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    # sanity
    assert not (ROOT / "common" / "peace_conference").exists()
    assert not (ROOT / "common" / "military_industrial_organization").exists()
    assert "peace_conference" not in pointer
    assert "military_industrial_organization" not in pointer
    assert "scripted_effects" in pointer
    assert (ROOT / "map" / "provinces.bmp").exists()
    cats = VANILLA / "common/peace_conference/categories/00_peace_action_categories.txt"
    assert "default = yes" in cats.read_text(encoding="utf-8")
    print("path=", path_line)
    print("DONE v0.3.14")
    print(pointer)


if __name__ == "__main__":
    main()
