# -*- coding: utf-8 -*-
"""v0.3.11 — neutralize vanilla focus/on_actions/events that crash on campaign start."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_VERSION = "0.3.11"
GAME_VERSION = "1.19.*"
MOD_PATH = "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"

REPLACE_PATHS = [
    "history/countries",
    "history/states",
    "history/units",
    "history/diplomacy",
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
    "common/scripted_effects",
    "common/scripted_triggers",
]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clear_txt(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*.txt"):
        f.unlink()


def stub_focus():
    d = ROOT / "common" / "national_focus"
    clear_txt(d)
    for f in d.glob(".gitkeep"):
        f.unlink()
    write(
        d / "mk_generic.txt",
        "focus_tree = {\n"
        "\tid = mk_generic_focus\n"
        "\tcountry = { factor = 0 }\n"
        "\tdefault = yes\n"
        "\treset_on_civilwar = no\n"
        "}\n",
    )
    print("national_focus ok")


def stub_on_actions():
    d = ROOT / "common" / "on_actions"
    clear_txt(d)
    write(d / "mk_on_actions.txt", "on_actions = {\n}\n")
    print("on_actions ok")


def stub_events():
    d = ROOT / "events"
    clear_txt(d)
    write(d / "mk_empty.txt", "# empty\n")
    print("events ok")


def stub_decisions():
    d = ROOT / "common" / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.rglob("*"):
        if f.is_file():
            f.unlink()
    write(d / "mk_empty.txt", "# empty\n")
    write(d / "categories" / "mk_empty.txt", "# empty\n")
    print("decisions ok")


def stub_scripted():
    for folder in ("scripted_effects", "scripted_triggers"):
        d = ROOT / "common" / folder
        clear_txt(d)
        write(d / "mk_empty.txt", "# empty\n")
    print("scripted ok")


def ensure_leader_portrait():
    src = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\gfx\leaders\leader_unknown.dds")
    dst = ROOT / "gfx" / "leaders" / "leader_unknown.dds"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        dst.write_bytes(src.read_bytes())
        print("portrait ok")


def clean_stubs():
    n = 0
    for f in (ROOT / "history" / "countries").glob("*Stub*.txt"):
        t = f.read_text(encoding="utf-8")
        t2 = re.sub(r"^\s*oob\s*=.*$", "", t, flags=re.M)
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    print("stubs cleaned", n)


def write_descriptor():
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
    print("descriptor ok")
    print(pointer)


def main():
    stub_focus()
    stub_on_actions()
    stub_events()
    stub_decisions()
    stub_scripted()
    ensure_leader_portrait()
    clean_stubs()
    write_descriptor()
    print("DONE v0.3.11")


if __name__ == "__main__":
    main()
