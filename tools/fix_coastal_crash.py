# -*- coding: utf-8 -*-
"""Fix coastal-without-port crash + weatherpositions + portraits + rivers + sea SRs."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map")
WIDTH, HEIGHT = 2048, 1024
CELL = 32


def load_definition():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(";")
        rows.append(parts)
    return rows


def save_definition(rows):
    (ROOT / "map" / "definition.csv").write_text(
        "\n".join(";".join(p) for p in rows) + "\n", encoding="utf-8"
    )


def fix_coastal_and_ports():
    """Only provinces with naval_base_spawn may be coastal=true."""
    rows = load_definition()
    # parse states for owner capitals / coastal candidates from history
    state_files = list((ROOT / "history" / "states").glob("*.txt"))
    province_to_state = {}
    state_center = {}
    coastal_history_ports = set()  # provinces that history wants naval_base on

    for sf in state_files:
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        provs = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S).group(1).split()]
        for p in provs:
            province_to_state[p] = sid
        # naval_base in history: "123 = { naval_base = 2 }"
        for m in re.finditer(r"(\d+)\s*=\s*\{\s*naval_base", text):
            coastal_history_ports.add(int(m.group(1)))
        # fallback: first listed province as port candidate if any coastal later
        if provs:
            state_center[sid] = provs[0]

    # Mark ALL land as non-coastal first
    land_pids = []
    for parts in rows[1:]:
        if parts[4] == "land":
            parts[5] = "false"
            land_pids.append(int(parts[0]))

    # Choose port provinces: those referenced in history, else none
    port_provinces = set(coastal_history_ports)

    # If history has no ports, add one port per country capital state (edge province)
    # Find edge land provinces (adjacent to sea in definition after we know sea set)
    sea = {int(p[0]) for p in rows[1:] if p[4] == "sea"}
    # Build color->pid and paint map adjacency via cell grid from definition centers? 
    # Simpler: use provinces.bmp
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    color_to_pid = {}
    for parts in rows[1:]:
        color_to_pid[(int(parts[1]), int(parts[2]), int(parts[3]))] = int(parts[0])

    # map each land pid to whether it touches sea
    touches_sea = set()
    for y in range(0, HEIGHT, 4):
        for x in range(0, WIDTH, 4):
            pid = color_to_pid.get(px[x, y])
            if pid is None or pid in sea:
                continue
            for dx, dy in ((CELL, 0), (-CELL, 0), (0, CELL), (0, -CELL)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    npid = color_to_pid.get(px[nx, ny])
                    if npid in sea:
                        touches_sea.add(pid)
                        break

    # Ensure at least one port per state that has a touches_sea province
    states_needing = defaultdict(list)
    for pid in touches_sea:
        sid = province_to_state.get(pid)
        if sid is not None:
            states_needing[sid].append(pid)

    if not port_provinces:
        for sid, plist in states_needing.items():
            port_provinces.add(plist[0])

    # Also keep history-specified ports even if not detected
    port_provinces |= coastal_history_ports

    # Set coastal=true only for port provinces
    for parts in rows[1:]:
        pid = int(parts[0])
        if parts[4] == "land":
            parts[5] = "true" if pid in port_provinces else "false"

    save_definition(rows)

    # Rebuild buildings.txt: keep existing non-naval lines, add naval_base_spawn for ports
    bpath = ROOT / "map" / "buildings.txt"
    old_lines = []
    if bpath.exists():
        old_lines = [l for l in bpath.read_text(encoding="utf-8").splitlines() if l.strip() and "naval_base" not in l]

    # province centers
    centers = {}
    for parts in rows[1:]:
        pid = int(parts[0])
        # approximate from color scan
    # compute centers
    sums = defaultdict(lambda: [0, 0, 0])
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            pid = color_to_pid.get(px[x, y])
            if pid is None:
                continue
            s = sums[pid]
            s[0] += x
            s[1] += y
            s[2] += 1
    for pid, (sx, sy, n) in sums.items():
        if n:
            centers[pid] = (sx / n, sy / n)

    naval_lines = []
    for pid in sorted(port_provinces):
        sid = province_to_state.get(pid, 1)
        cx, cy = centers.get(pid, (WIDTH / 2, HEIGHT / 2))
        # state;naval_base_spawn;x;height;y;rot;province
        naval_lines.append(f"{sid};naval_base_spawn;{cx:.2f};10.00;{cy:.2f};0.00;{pid}")

    bpath.write_text("\n".join(old_lines + naval_lines) + "\n", encoding="utf-8")

    # Strip naval_base from history for provinces that are not ports; keep only port_provinces
    for sf in state_files:
        text = sf.read_text(encoding="utf-8")
        def repl(m):
            pid = int(m.group(1))
            if pid in port_provinces:
                return m.group(0)
            return ""  # remove naval_base block for non-port

        new = re.sub(
            r"\n?\t\t\t(\d+)\s*=\s*\{\s*naval_base\s*=\s*\d+\s*\}",
            repl,
            text,
        )
        # ensure each port province used by this state still has naval_base in history
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        provs = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S).group(1).split()]
        for pid in provs:
            if pid in port_provinces and f"{pid} =" not in new and f"{pid}=" not in new:
                new = new.replace(
                    "buildings = {",
                    f"buildings = {{\n\t\t\t{pid} = {{ naval_base = 2 }}",
                    1,
                )
        sf.write_text(new, encoding="utf-8")

    print(f"ports={len(port_provinces)} coastal_true={sum(1 for p in rows[1:] if p[4]=='land' and p[5]=='true')} touches_sea={len(touches_sea)}")


def fix_weatherpositions():
    """Format: strategic_region_id;x;height;y;size"""
    sr_dir = ROOT / "map" / "strategicregions"
    lines = []
    for f in sorted(sr_dir.glob("*.txt"), key=lambda p: p.name):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"id\s*=\s*(\d+)", text)
        pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
        if not m or not pm:
            continue
        srid = int(m.group(1))
        provs = [int(x) for x in pm.group(1).split() if x.strip().isdigit()]
        if not provs:
            continue
        # place weather at map center-ish using first province id as seed offset
        pid = provs[0]
        # rough position from pid hash
        x = 200 + (pid * 37) % (WIDTH - 400)
        y = 100 + (pid * 53) % (HEIGHT - 200)
        lines.append(f"{srid};{x:.2f};10.00;{y:.2f};small")
    (ROOT / "map" / "weatherpositions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"weatherpositions lines={len(lines)}")


def fix_portraits():
    p = ROOT / "portraits" / "mk_portraits.txt"
    if p.exists():
        p.unlink()
        print("removed broken mk_portraits.txt")


def fix_rivers():
    """Resize vanilla rivers.bmp with NEAREST to keep palette indices meaningful; fill unused with 254."""
    src = Image.open(VANILLA_MAP / "rivers.bmp")
    # Extract raw palette from file
    raw = (VANILLA_MAP / "rivers.bmp").read_bytes()
    pal = raw[54 : 54 + 1024]
    img = Image.new("P", (WIDTH, HEIGHT), 254)
    img.putpalette(src.getpalette())
    # write indexed bmp
    data = [254] * (WIDTH * HEIGHT)
    w, h = WIDTH, HEIGHT
    row_stride = (w + 3) & ~3
    body = bytearray()
    pad = b"\x00" * (row_stride - w)
    row = bytes([254] * w)
    for _ in range(h):
        body.extend(row)
        body.extend(pad)
    header = struct.pack(
        "<2sIHHIIiiHHIIiiii",
        b"BM",
        54 + 1024 + len(body),
        0,
        0,
        54 + 1024,
        40,
        w,
        h,
        1,
        8,
        0,
        len(body),
        2835,
        2835,
        256,
        256,
    )
    (ROOT / "map" / "rivers.bmp").write_bytes(header + pal + body)
    print("rivers rewritten")


def fix_sea_strategic_regions():
    """One strategic region per sea province → never fractioned."""
    sr_dir = ROOT / "map" / "strategicregions"
    # delete old sea SRs
    for f in sr_dir.glob("*-Sea*.txt"):
        f.unlink()
    # find max land SR id
    max_id = 0
    sea_provs = []
    for parts in load_definition()[1:]:
        if parts[4] == "sea":
            sea_provs.append(int(parts[0]))
    for f in sr_dir.glob("*.txt"):
        m = re.search(r"id\s*=\s*(\d+)", f.read_text(encoding="utf-8"))
        if m:
            max_id = max(max_id, int(m.group(1)))

    weather = """\tweather={
\t\tperiod={ between={ 0.0 30.0 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.1 27.1 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.2 30.2 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.3 29.3 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.4 30.4 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.5 29.5 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.6 30.6 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.7 30.7 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.8 29.8 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.9 30.9 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.10 29.10 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t\tperiod={ between={ 0.11 30.11 } temperature={ 5.0 20.0 } no_phenomenon=0.6 rain_light=0.2 rain_heavy=0.1 snow=0.0 blizzard=0.0 arctic_water=0.0 mud=0.1 sandstorm=0.0 min_snow_level=0.0 }
\t}
"""
    # Too many SRs if one per sea (1000+) — group into contiguous 4x4 cell blocks instead
    # Reload sea province positions from definition colors / bmp
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    rows = load_definition()
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows[1:]}
    sea_set = {int(p[0]) for p in rows[1:] if p[4] == "sea"}
    # map sea pid -> cell (fx,fy)
    sea_cell = {}
    for fy in range(HEIGHT // CELL):
        for fx in range(WIDTH // CELL):
            x, y = fx * CELL + CELL // 2, fy * CELL + CELL // 2
            pid = color_to_pid.get(px[x, y])
            if pid in sea_set:
                sea_cell[pid] = (fx, fy)

    blocks = defaultdict(list)
    for pid, (fx, fy) in sea_cell.items():
        blocks[(fx // 4, fy // 4)].append(pid)

    srid = max_id
    loc = ["l_russian:"]
    # keep existing land SR loc file; rewrite sea loc entries
    for (bx, by), provs in sorted(blocks.items()):
        srid += 1
        loc.append(f' STRATEGICREGION_{srid}:0 "Sea {bx}_{by}"')
        (sr_dir / f"{srid}-Sea-{bx}-{by}.txt").write_text(
            f"strategic_region={{\n\tid={srid}\n\tname=\"STRATEGICREGION_{srid}\"\n\tprovinces={{\n\t\t{' '.join(map(str, provs))}\n\t}}\n{weather}}}\n",
            encoding="utf-8",
        )
    # append loc
    loc_path = ROOT / "localisation" / "russian" / "mk_strategic_regions_l_russian.yml"
    # rewrite full loc from all SR files
    loc_lines = ["l_russian:"]
    for f in sorted(sr_dir.glob("*.txt"), key=lambda p: int(re.search(r"id\s*=\s*(\d+)", p.read_text(encoding='utf-8')).group(1))):
        text = f.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        name = f.stem
        loc_lines.append(f' STRATEGICREGION_{sid}:0 "{name}"')
    loc_path.write_bytes(b"\xef\xbb\xbf" + ("\n".join(loc_lines) + "\n").encode("utf-8"))
    print(f"sea strategic regions blocks={len(blocks)} total_sr_id_max={srid}")


def fix_descriptor_ai():
    """Replace vanilla ai_strategy that references missing state IDs."""
    desc = ROOT / "descriptor.mod"
    text = desc.read_text(encoding="utf-8")
    if 'replace_path="common/ai_strategy"' not in text:
        text = text.replace(
            'replace_path="common/ai_strategy_plans"',
            'replace_path="common/ai_strategy_plans"\nreplace_path="common/ai_strategy"\nreplace_path="common/ai_areas"',
        )
        desc.write_text(text, encoding="utf-8")
    # empty dirs
    for d in ("common/ai_strategy", "common/ai_areas"):
        path = ROOT / d
        path.mkdir(parents=True, exist_ok=True)
        for f in path.glob("*.txt"):
            f.unlink()
        (path / "mk_empty.txt").write_text("# intentionally empty for total conversion\n", encoding="utf-8")
    # update pointer
    docs = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV" / "mod" / "mir_kazualnosti.mod"
    body = desc.read_text(encoding="utf-8")
    docs.write_text(body + 'path="D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"\n', encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(body + 'path="D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"\n', encoding="utf-8")
    # bump version
    for p in (desc, ROOT / "mir_kazualnosti.mod", docs):
        t = p.read_text(encoding="utf-8").replace('version="0.3.4"', 'version="0.3.5"')
        p.write_text(t, encoding="utf-8")
    print("descriptor ai_strategy/ai_areas replaced")


def main():
    fix_portraits()
    fix_coastal_and_ports()
    fix_weatherpositions()
    fix_rivers()
    fix_sea_strategic_regions()
    fix_weatherpositions()  # regenerate after new SRs
    fix_descriptor_ai()
    print("DONE coastal crash fixes")


if __name__ == "__main__":
    main()
