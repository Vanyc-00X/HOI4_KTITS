# -*- coding: utf-8 -*-
"""
v0.3.17 — crash after country select:
1) SR1 provinces block lost closing '}' when province 0 was inserted → malformed weather
2) MAP_ERROR no rocket site / gun emplacement → need rocket_site_spawn per state
   (mega_gun_emplacement and rocket_site both use spawn_point = rocket_site_spawn)
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
MOD_VERSION = "0.3.17"
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

WEATHER = """\tweather={
\t\tperiod={ between={ 0.0 30.0 } temperature={ -2.0 18.0 } no_phenomenon=0.550 rain_light=0.250 rain_heavy=0.100 snow=0.050 blizzard=0.000 arctic_water=0.000 mud=0.200 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.1 27.1 } temperature={ -4.0 16.0 } no_phenomenon=0.500 rain_light=0.250 rain_heavy=0.100 snow=0.100 blizzard=0.000 arctic_water=0.000 mud=0.250 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.2 30.2 } temperature={ 2.0 20.0 } no_phenomenon=0.550 rain_light=0.250 rain_heavy=0.100 snow=0.020 blizzard=0.000 arctic_water=0.000 mud=0.200 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.3 29.3 } temperature={ 6.0 24.0 } no_phenomenon=0.600 rain_light=0.220 rain_heavy=0.080 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.150 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.4 30.4 } temperature={ 10.0 28.0 } no_phenomenon=0.650 rain_light=0.200 rain_heavy=0.080 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.100 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.5 29.5 } temperature={ 14.0 30.0 } no_phenomenon=0.700 rain_light=0.180 rain_heavy=0.060 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.080 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.6 30.6 } temperature={ 16.0 32.0 } no_phenomenon=0.700 rain_light=0.160 rain_heavy=0.060 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.050 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.7 30.7 } temperature={ 14.0 30.0 } no_phenomenon=0.650 rain_light=0.180 rain_heavy=0.070 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.080 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.8 29.8 } temperature={ 10.0 26.0 } no_phenomenon=0.600 rain_light=0.200 rain_heavy=0.080 snow=0.000 blizzard=0.000 arctic_water=0.000 mud=0.120 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.9 30.9 } temperature={ 6.0 22.0 } no_phenomenon=0.550 rain_light=0.220 rain_heavy=0.090 snow=0.010 blizzard=0.000 arctic_water=0.000 mud=0.150 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.10 29.10 } temperature={ 2.0 18.0 } no_phenomenon=0.520 rain_light=0.230 rain_heavy=0.100 snow=0.040 blizzard=0.000 arctic_water=0.000 mud=0.180 sandstorm=0.000 min_snow_level=0.000 }
\t\tperiod={ between={ 0.11 30.11 } temperature={ -1.0 16.0 } no_phenomenon=0.500 rain_light=0.240 rain_heavy=0.100 snow=0.080 blizzard=0.000 arctic_water=0.000 mud=0.200 sandstorm=0.000 min_snow_level=0.000 }
\t}
"""


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


def fix_strategic_regions():
    """Rewrite any SR whose provinces={...} is not properly closed before weather."""
    sr_dir = ROOT / "map" / "strategicregions"
    fixed = 0
    for f in sorted(sr_dir.glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        mid = re.search(r"id\s*=\s*(\d+)", text)
        name_m = re.search(r'name\s*=\s*"([^"]+)"', text)
        prov_m = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
        # broken case: provinces = { ... weather={  (no closing before weather)
        broken = re.search(
            r"provinces\s*=\s*\{([^}]*)\n\s*weather\s*=", text, re.S
        )
        if not broken and prov_m:
            continue
        if broken:
            provs = broken.group(1)
        elif not prov_m:
            print("WARN no provinces", f.name)
            continue
        else:
            continue
        # ensure province 0 in SR1
        sid = int(mid.group(1)) if mid else 0
        tokens = [t for t in provs.replace("\n", " ").split() if t.isdigit()]
        if sid == 1 and "0" not in tokens:
            tokens = ["0"] + tokens
        # dedupe preserve order
        seen = set()
        ordered = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        name = name_m.group(1) if name_m else f"STRATEGICREGION_{sid}"
        body = (
            "strategic_region={\n"
            f"\tid={sid}\n"
            f'\tname="{name}"\n'
            "\tprovinces={\n"
            f"\t\t{' '.join(ordered)}\n"
            "\t}\n"
            f"{WEATHER}"
            "}\n"
        )
        f.write_text(body, encoding="utf-8")
        fixed += 1
        print("rewrote SR", f.name, "provs", len(ordered))
    # also ensure SR1 has 0 even if not broken
    sr1 = sr_dir / "1-VCI.txt"
    if sr1.exists():
        t = sr1.read_text(encoding="utf-8")
        m = re.search(r"provinces\s*=\s*\{([^}]*)\}", t, re.S)
        if m and not re.search(r"(?<!\d)0(?!\d)", m.group(1)):
            inner = "0 " + m.group(1).lstrip()
            t = t[: m.start(1)] + inner + t[m.end(1) :]
            sr1.write_text(t, encoding="utf-8")
            print("ensured province 0 in SR1")
            fixed += 1
    print("strategic regions fixed:", fixed)


def rebuild_rocket_spawns():
    """Keep naval/air lines; ensure every state has rocket_site_spawn near air_base."""
    bpath = ROOT / "map" / "buildings.txt"
    lines = [l for l in bpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept = [l for l in lines if "rocket_site" not in l]
    # parse air_base coords per state
    air = {}
    for l in kept:
        parts = l.split(";")
        if len(parts) < 6:
            continue
        if parts[1] != "air_base":
            continue
        sid = int(parts[0])
        air[sid] = (float(parts[2]), float(parts[3]), float(parts[4]))

    # all state ids from history
    state_ids = []
    for f in (ROOT / "history" / "states").glob("*.txt"):
        m = re.search(r"id\s*=\s*(\d+)", f.read_text(encoding="utf-8"))
        if m:
            state_ids.append(int(m.group(1)))
    state_ids = sorted(set(state_ids))

    rockets = []
    for sid in state_ids:
        if sid in air:
            x, y, z = air[sid]
            rockets.append(
                f"{sid};rocket_site_spawn;{x + 2.0:.2f};10.00;{z + 2.0:.2f};0.00;0"
            )
        else:
            # fallback centroid-ish from any naval line of that state
            found = None
            for l in kept:
                parts = l.split(";")
                if parts[0] == str(sid) and len(parts) >= 5:
                    found = (float(parts[2]), float(parts[4]))
                    break
            if found:
                x, z = found
            else:
                x, z = 100.0 + sid, 100.0 + sid
            rockets.append(
                f"{sid};rocket_site_spawn;{x + 2.0:.2f};10.00;{z + 2.0:.2f};0.00;0"
            )

    out = kept + rockets
    bpath.write_text("\n".join(out), encoding="utf-8")
    print(f"buildings: kept={len(kept)} rocket_site_spawn={len(rockets)} total={len(out)}")


def ensure_definition_has_zero():
    path = ROOT / "map" / "definition.csv"
    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(l.startswith("0;") for l in lines):
        lines.insert(0, "0;0;0;0;land;false;unknown;0")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("restored province 0")
    else:
        print("province 0 ok")


def main():
    ensure_definition_has_zero()
    fix_strategic_regions()
    rebuild_rocket_spawns()

    path_line = install_into_documents()
    pointer = write_descriptor(path_line)
    for name in ("Mir_Kazualnosti.mod", "mir_kazualnosti.mod"):
        (DOCS / "mod" / name).write_text(pointer, encoding="utf-8")
    (DOCS / "dlc_load.json").write_text(
        json.dumps({"enabled_mods": ["mod/Mir_Kazualnosti.mod"], "disabled_dlcs": []}),
        encoding="utf-8",
    )

    # sanity SR1
    sr1 = (ROOT / "map" / "strategicregions" / "1-VCI.txt").read_text(encoding="utf-8")
    assert "weather={" in sr1
    assert re.search(r"provinces\s*=\s*\{[^}]+\}", sr1, re.S), "SR1 provinces not closed"
    assert "rocket_site_spawn" in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8")
    print("path=", path_line)
    print("DONE v0.3.17")
    print(pointer)


if __name__ == "__main__":
    main()
