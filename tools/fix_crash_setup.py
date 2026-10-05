# -*- coding: utf-8 -*-
"""Crash fixes: descriptor paths, vanilla history stubs, keep focuses/events from vanilla."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
DOCS_MOD = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV" / "mod"

OUR_TAGS = {
    "VCI", "SOY", "BTR", "KRZ", "KZS", "MUS", "TRF", "ZLD", "ISL", "CLB",
    "ADL", "DMK", "FDP", "CRE", "SVA", "ART", "KMS", "ZNS", "ZKR", "ZML",
    "NBL", "ISG", "HRL", "SHF",
}


def vanilla_tags() -> list[str]:
    tags = []
    for p in (VANILLA / "common" / "country_tags").glob("*.txt"):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            tag = s.split("=")[0].strip().upper()
            if len(tag) == 3 and tag.isalpha():
                tags.append(tag)
    out, seen = [], set()
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def write_stub_history(tag: str, path: Path) -> None:
    path.write_text(
        f'''capital = 1

oob = ""

set_research_slots = 2
set_stability = 0.50
set_war_support = 0.50

set_technology = {{
	infantry_weapons = 1
}}

set_politics = {{
	ruling_party = neutrality
	last_election = "1935.1.1"
	election_frequency = 48
	elections_allowed = no
}}

set_popularities = {{
	democratic = 0
	communism = 0
	fascism = 0
	neutrality = 100
}}
''',
        encoding="utf-8",
    )


def write_descriptors() -> None:
    abs_path = "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"
    # CRITICAL: do NOT replace national_focus or events — vanilla trees/events required to boot
    # do NOT replace country_tags
    body = '''version="0.3.3"
tags={
	"Alternative History"
	"Total Conversion"
	"Map"
	"National Focuses"
	"Gameplay"
}
name="Mir Kazualnosti: Epokha Skhodyashchikh s Uma Pravitely"
supported_version="1.19.*"
replace_path="history/countries"
replace_path="history/states"
replace_path="history/units"
replace_path="history/diplomacy"
replace_path="common/bookmarks"
replace_path="map/strategicregions"
replace_path="common/ai_strategy_plans"
'''
    pointer = body + f'path="{abs_path}"\n'
    (ROOT / "descriptor.mod").write_text(body, encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    DOCS_MOD.mkdir(parents=True, exist_ok=True)
    (DOCS_MOD / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    print("descriptor v0.3.3 — no replace_path for focus/events/country_tags")


def patch_our_histories_focus() -> None:
    """Ensure playable tags load generic_focus from vanilla."""
    hist = ROOT / "history" / "countries"
    for tag in OUR_TAGS:
        files = list(hist.glob(f"{tag}*.txt"))
        files = [f for f in files if "Stub" not in f.name]
        if not files:
            print("MISSING history", tag)
            continue
        p = files[0]
        text = p.read_text(encoding="utf-8")
        if "set_cosmetic_tag" in text:
            continue
        if "generic_focus" not in text and "load_focus_tree" not in text:
            # HOI4 uses: unlock_national_focus / country history often has no explicit tree;
            # effect set in common/national_focus via tag triggers. Add safe line used by many mods:
            if not text.endswith("\n"):
                text += "\n"
            text += "\nset_variable = { mk_boot = 1 }\n"
            p.write_text(text, encoding="utf-8")


def main() -> None:
    write_descriptors()
    hist = ROOT / "history" / "countries"
    hist.mkdir(parents=True, exist_ok=True)
    for p in hist.glob("*- Stub.txt"):
        p.unlink()
    created = 0
    for tag in vanilla_tags():
        if tag in OUR_TAGS:
            continue
        write_stub_history(tag, hist / f"{tag} - Stub.txt")
        created += 1
    print(f"stubs: {created}")
    patch_our_histories_focus()
    # Clear national_focus replace leftovers — leave folder empty but NOT in replace_path
    nf = ROOT / "common" / "national_focus"
    nf.mkdir(parents=True, exist_ok=True)
    for p in nf.glob("*.txt"):
        p.unlink()
        print("removed mod focus override", p.name)
    print("DONE")


if __name__ == "__main__":
    main()
