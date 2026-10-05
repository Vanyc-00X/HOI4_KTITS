# -*- coding: utf-8 -*-
"""
v0.3.16 — immediate boot crash after v0.3.15:
HOI4 definition.csv MUST start with province 0 (vanilla does).
Removing it offsets all province properties → native crash while loading states.
Also put province 0 into a strategic region (wiki: missing SR can crash before launch).
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
MOD_VERSION = "0.3.16"
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


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def restore_province_zero():
    path = ROOT / "map" / "definition.csv"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if any(l.startswith("0;") for l in lines):
        print("province 0 already present")
        return
    # vanilla placeholder: unused RGB black, no pixels on bmp
    lines.insert(0, "0;0;0;0;land;false;unknown;0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("restored province 0 at top of definition.csv")


def ensure_prov0_in_strategic_region():
    """Province without SR can crash before launch (wiki)."""
    sr_dir = ROOT / "map" / "strategicregions"
    for f in sr_dir.glob("*.txt"):
        t = f.read_text(encoding="utf-8")
        if re.search(r"\bid\s*=\s*1\b", t):
            if re.search(r"\b0\b", t.split("provinces")[-1] if "provinces" in t else ""):
                # crude: check provinces block contains 0 as token
                m = re.search(r"provinces\s*=\s*\{([^}]*)\}", t, re.S)
                if m and re.search(r"(?<!\d)0(?!\d)", m.group(1)):
                    print("SR1 already has province 0")
                    return
            def add0(match: re.Match) -> str:
                body = match.group(1)
                if re.search(r"(?<!\d)0(?!\d)", body):
                    return match.group(0)
                # prepend 0
                return "provinces = {\n\t\t0 " + body.lstrip()

            new_t, n = re.subn(r"provinces\s*=\s*\{([^}]*)\}", add0, t, count=1, flags=re.S)
            if n:
                f.write_text(new_t, encoding="utf-8")
                print("added province 0 to", f.name)
                return
    print("WARN: could not find SR id=1 to add province 0")


def clear_user_map_overrides():
    user_map = DOCS / "map"
    if not user_map.exists():
        return
    removed = 0
    for f in list(user_map.rglob("*")):
        if f.is_file() and (
            "definition" in f.name.lower()
            or f.suffix.lower() in {".fixed", ".csv", ".txt", ".bmp"}
        ):
            # only delete definition* and nudger leftovers that shadow mod
            if "definition" in f.name.lower() or f.name.endswith(".fixed"):
                f.unlink()
                removed += 1
    print(f"cleared user map definition overrides: {removed}")


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
    restore_province_zero()
    ensure_prov0_in_strategic_region()
    clear_user_map_overrides()

    # keep scripted_effects absent from mod (vanilla)
    se = ROOT / "common" / "scripted_effects"
    if se.exists() and any(se.glob("*.txt")):
        shutil.rmtree(se)
        se.mkdir(parents=True, exist_ok=True)
        write(se / ".gitkeep", "")
        print("cleared mod scripted_effects txt overrides")

    path_line = install_into_documents()
    pointer = write_descriptor(path_line)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    first = (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("0;"), first
    print("path=", path_line)
    print("DONE v0.3.16")
    print(pointer)


if __name__ == "__main__":
    main()
