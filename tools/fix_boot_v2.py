# -*- coding: utf-8 -*-
"""Second-pass boot fixes: buildings-only-ports, contiguous sea SRs, theaters, flags."""
from __future__ import annotations

import re
import struct
from collections import defaultdict, deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, CELL = 2048, 1024, 32
DOCS_MOD = (
    Path.home()
    / "Documents"
    / "Paradox Interactive"
    / "Hearts of Iron IV"
    / "mod"
    / "mir_kazualnosti.mod"
)
PATH_LINE = 'path="D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"\n'


def load_definition():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(line.split(";"))
    return rows


def strip_buildings_to_ports_only():
    bpath = ROOT / "map" / "buildings.txt"
    lines = [l for l in bpath.read_text(encoding="utf-8").splitlines() if "naval_base_spawn" in l]
    bpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"buildings naval_only={len(lines)}")


def flood_fill_sea_srs():
    """Contiguous sea strategic regions via flood-fill on the cell grid."""
    rows = load_definition()
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows[1:]}
    sea_set = {int(p[0]) for p in rows[1:] if p[4] == "sea"}
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    cols, rows_n = WIDTH // CELL, HEIGHT // CELL
    grid = [[None] * cols for _ in range(rows_n)]
    for fy in range(rows_n):
        for fx in range(cols):
            x, y = fx * CELL + CELL // 2, fy * CELL + CELL // 2
            pid = color_to_pid.get(px[x, y])
            if pid in sea_set:
                grid[fy][fx] = pid

    visited = [[False] * cols for _ in range(rows_n)]
    components = []
    for fy in range(rows_n):
        for fx in range(cols):
            if grid[fy][fx] is None or visited[fy][fx]:
                continue
            q = deque([(fx, fy)])
            visited[fy][fx] = True
            provs = []
            while q:
                x, y = q.popleft()
                pid = grid[y][x]
                if pid is not None:
                    provs.append(pid)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < cols and 0 <= ny < rows_n and not visited[ny][nx] and grid[ny][nx] is not None:
                        visited[ny][nx] = True
                        q.append((nx, ny))
            # unique keep order
            seen = set()
            uniq = []
            for p in provs:
                if p not in seen:
                    seen.add(p)
                    uniq.append(p)
            if uniq:
                components.append(uniq)

    sr_dir = ROOT / "map" / "strategicregions"
    for f in sr_dir.glob("*-Sea*.txt"):
        f.unlink()

    max_id = 0
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
    srid = max_id
    # Keep each flood-fill component intact (contiguous). Split oversized ones by
    # taking BFS subsets so each chunk stays contiguous.
    MAX_CHUNK = 64

    def split_contiguous(provs):
        if len(provs) <= MAX_CHUNK:
            return [provs]
        # rebuild adjacency from cell grid
        pid_cells = defaultdict(list)
        for fy in range(rows_n):
            for fx in range(cols):
                pid = grid[fy][fx]
                if pid in set(provs):
                    pid_cells[pid].append((fx, fy))
        cell_pid = {}
        for pid, cells in pid_cells.items():
            for c in cells:
                cell_pid[c] = pid
        remaining = set(provs)
        out = []
        while remaining:
            start = next(iter(remaining))
            q = deque(pid_cells[start][:1])
            seen_cells = set(q)
            got = []
            got_set = set()
            while q and len(got) < MAX_CHUNK:
                x, y = q.popleft()
                pid = cell_pid.get((x, y))
                if pid in remaining and pid not in got_set:
                    got.append(pid)
                    got_set.add(pid)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in seen_cells and (nx, ny) in cell_pid and cell_pid[(nx, ny)] in remaining:
                        seen_cells.add((nx, ny))
                        q.append((nx, ny))
            if not got:
                # fallback: take one
                got = [remaining.pop()]
                got_set = set(got)
            remaining -= got_set
            out.append(got)
        return out

    chunks = []
    for comp in components:
        chunks.extend(split_contiguous(comp))

    for i, provs in enumerate(chunks):
        srid += 1
        (sr_dir / f"{srid}-Sea-{i}.txt").write_text(
            f"strategic_region={{\n\tid={srid}\n\tname=\"STRATEGICREGION_{srid}\"\n\tprovinces={{\n\t\t{' '.join(map(str, provs))}\n\t}}\n{weather}}}\n",
            encoding="utf-8",
        )

    loc_lines = ["l_russian:"]
    for f in sorted(sr_dir.glob("*.txt"), key=lambda p: int(re.search(r"(\d+)", p.name).group(1))):
        text = f.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        loc_lines.append(f' STRATEGICREGION_{sid}:0 "{f.stem}"')
    loc_path = ROOT / "localisation" / "russian" / "mk_strategic_regions_l_russian.yml"
    loc_path.write_bytes(b"\xef\xbb\xbf" + ("\n".join(loc_lines) + "\n").encode("utf-8"))
    print(f"sea components={len(components)} chunks={len(chunks)} max_sr={srid}")
    return srid


def fix_weatherpositions():
    lines = []
    for f in (ROOT / "map" / "strategicregions").glob("*.txt"):
        text = f.read_text(encoding="utf-8")
        m = re.search(r"id\s*=\s*(\d+)", text)
        pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
        if not m or not pm:
            continue
        srid = int(m.group(1))
        provs = [int(x) for x in pm.group(1).split() if x.strip().isdigit()]
        if not provs:
            continue
        pid = provs[0]
        x = 200 + (pid * 37) % (WIDTH - 400)
        y = 100 + (pid * 53) % (HEIGHT - 200)
        lines.append(f"{srid};{x:.2f};10.00;{y:.2f};small")
    lines.sort(key=lambda l: int(l.split(";")[0]))
    (ROOT / "map" / "weatherpositions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"weatherpositions={len(lines)}")


def write_empty_theaters():
    d = ROOT / "common" / "ai_faction_theaters"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.txt"):
        f.unlink()
    (d / "mk_empty.txt").write_text("# total conversion: no vanilla theaters\n", encoding="utf-8")
    print("ai_faction_theaters emptied")


def write_stub_flags():
    """Ensure every history country + common stub tags have 32bpp TGA flags."""
    flags_dir = ROOT / "gfx" / "flags"
    flags_dir.mkdir(parents=True, exist_ok=True)
    tags = set()
    for f in (ROOT / "history" / "countries").glob("*.txt"):
        # VCI - Name.txt or TAG.txt
        m = re.match(r"^([A-Z]{3})", f.name)
        if m:
            tags.add(m.group(1))
    # also from common/country_tags if present
    tags_dir = ROOT / "common" / "country_tags"
    if tags_dir.exists():
        for f in tags_dir.glob("*.txt"):
            for m in re.finditer(r"^([A-Z]{3})\s*=", f.read_text(encoding="utf-8"), re.M):
                tags.add(m.group(1))
    # known stubs that appeared in log
    tags |= {"SCO", "CSA", "ENG", "GER", "FRA", "USA", "SOV", "ITA", "JAP", "CHI"}

    def solid_tga(path: Path, rgb=(40, 40, 80)):
        w, h = 82, 52
        r, g, b = rgb
        # 32bpp BGRA TGA
        header = struct.pack(
            "<BBBHHBHHHHBB",
            0,  # id length
            0,  # no colormap
            2,  # uncompressed truecolor
            0, 0, 0,  # colormap spec
            0, 0,  # x,y origin
            w, h,
            32,  # bpp
            8,  # alpha in descriptor (bits 0-3 = 8)
        )
        # bottom-up rows
        row = bytes([b, g, r, 255]) * w
        body = row * h
        path.write_bytes(header + body)

    ideologies = ["", "_communism", "_democratic", "_fascism", "_neutrality"]
    made = 0
    for tag in sorted(tags):
        color = (hash(tag) % 200 + 30, hash(tag + "g") % 200 + 30, hash(tag + "b") % 200 + 30)
        for suf in ideologies:
            p = flags_dir / f"{tag}{suf}.tga"
            if not p.exists() or p.stat().st_size < 100:
                solid_tga(p, color)
                made += 1
            else:
                # convert 24bpp to 32bpp if needed
                data = p.read_bytes()
                if len(data) >= 18 and data[16] == 24:
                    solid_tga(p, color)
                    made += 1
    print(f"flags ensured tags={len(tags)} rewritten={made}")


def bump_descriptor():
    # Never regex-replace bare path= — it matches inside replace_path="..."
    import runpy

    runpy.run_path(str(Path(__file__).with_name("register_mod.py")), run_name="__main__")
    print("descriptor re-registered via register_mod")


def main():
    strip_buildings_to_ports_only()
    flood_fill_sea_srs()
    fix_weatherpositions()
    write_empty_theaters()
    write_stub_flags()
    bump_descriptor()
    print("DONE boot v2")


if __name__ == "__main__":
    main()
