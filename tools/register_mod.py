# -*- coding: utf-8 -*-
"""Register Mir Kazualnosti with the HOI4 launcher (Documents/mod)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
DOCS_MOD = DOCS / "mod"
MOD_VERSION = "0.14.0"
GAME_VERSION = "1.19.*"
# Prefer Documents junction layout
MOD_PATH = "mod/Mir_Kazualnosti"

# Do NOT replace MIO / peace_conference — blank stubs crash boot.
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

DESCRIPTOR_BODY = (
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
POINTER = DESCRIPTOR_BODY + f'path="{MOD_PATH}"\n'


def main():
    (ROOT / "descriptor.mod").write_text(DESCRIPTOR_BODY, encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(POINTER, encoding="utf-8")
    DOCS_MOD.mkdir(parents=True, exist_ok=True)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS_MOD / name).write_text(POINTER, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )
    print("registered OK", MOD_VERSION, "path=", MOD_PATH)


if __name__ == "__main__":
    main()
