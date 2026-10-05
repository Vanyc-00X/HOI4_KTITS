# -*- coding: utf-8 -*-
"""Fix remaining boot errors: continents, seas grid, rivers, flags, weatherpositions, descriptor."""
from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
VANILLA_MAP = VANILLA / "map"
DOCS_MOD = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV" / "mod"

WIDTH, HEIGHT = 2048, 1024
LAND_X0, LAND_Y0 = 288, 160
LAND_X1, LAND_Y1 = 1760, 864
CELL = 32

OUR = [
    ("VCI", (180, 140, 60)),
    ("SOY", (120, 200, 140)),
    ("BTR", (40, 40, 40)),
    ("KRZ", (180, 30, 30)),
    ("KZS", (90, 70, 40)),
    ("MUS", (200, 120, 160)),
    ("TRF", (80, 160, 60)),
    ("ZLD", (40, 140, 80)),
    ("ISL", (20, 120, 80)),
    ("CLB", (70, 90, 120)),
    ("ADL", (160, 160, 180)),
    ("DMK", (120, 80, 40)),
    ("FDP", (100, 100, 140)),
    ("CRE", (90, 20, 20)),
    ("SVA", (100, 160, 200)),
    ("ART", (160, 100, 40)),
    ("KMS", (80, 140, 180)),
    ("ZNS", (140, 100, 60)),
    ("ZKR", (60, 100, 140)),
    ("ZML", (120, 160, 80)),
    ("NBL", (180, 80, 40)),
    ("ISG", (160, 40, 60)),
    ("HRL", (200, 160, 40)),
    ("SHF", (80, 100, 80)),
]
OUR_TAGS = {t for t, _ in OUR}

BOARD = {
    (1, 5): "SVA", (2, 5): "SVA", (3, 5): "CLB", (4, 5): "CLB", (5, 5): "ART", (6, 5): "ART",
    (0, 4): "KMS", (1, 4): "KMS", (2, 4): "ZLD", (3, 4): "VCI", (4, 4): "VCI", (5, 4): "NBL", (6, 4): "ZNS", (7, 4): "ZNS",
    (0, 3): "MUS", (1, 3): "MUS", (2, 3): "SOY", (3, 3): "VCI", (4, 3): "FDP", (5, 3): "DMK", (6, 3): "DMK", (7, 3): "KRZ",
    (0, 2): "ISL", (1, 2): "TRF", (2, 2): "TRF", (3, 2): "ZML", (4, 2): "ISG", (5, 2): "HRL", (6, 2): "KRZ", (7, 2): "KRZ",
    (0, 1): "ADL", (1, 1): "ADL", (2, 1): "SHF", (3, 1): "SHF", (4, 1): "SHF", (5, 1): "CRE", (6, 1): "CRE", (7, 1): "BTR",
    (0, 0): "ZKR", (1, 0): "ZKR", (2, 0): "SHF", (3, 0): "SHF", (4, 0): "KZS", (5, 0): "KZS", (6, 0): "BTR", (7, 0): "BTR",
}
SIZE_STATES = {"large": 10, "medium": 5, "small": 3}
SIZE_OF = {
    "VCI": "large", "SOY": "medium", "BTR": "medium", "KRZ": "large", "KZS": "small", "MUS": "medium",
    "TRF": "medium", "ZLD": "medium", "ISL": "medium", "CLB": "medium", "ADL": "small", "DMK": "medium",
    "FDP": "medium", "CRE": "medium", "SVA": "medium", "ART": "medium", "KMS": "medium", "ZNS": "medium",
    "ZKR": "medium", "ZML": "small", "NBL": "medium", "ISG": "small", "HRL": "medium", "SHF": "large",
}
CAPITAL = {t: i for i, (t, _) in enumerate(OUR, 1)}
NAME = {
    "VCI": "Velikaya Kazualnaya Imperiya", "SOY": "Soevaya Respublika", "BTR": "Chyornaya Tartariya",
    "KRZ": "Krasnaya Zemlya", "KZS": "Kazachi Shtaty", "MUS": "Korolevstvo Musi", "TRF": "Travinnaya Federatsiya",
    "ZLD": "Demokraticheskiy Zelenodolsk", "ISL": "Islamskaya Respublika", "CLB": "Chelyaba", "ADL": "Aydaliya",
    "DMK": "Dmitro-Knyazhestvo", "FDP": "Federatsiya Deputatov", "CRE": "Chyornaya Respublika",
    "SVA": "Severnaya Assambleya", "ART": "Ayratskaya Respublika", "KMS": "Kamilskoe Sodruzhestvo",
    "ZNS": "Zaynutdinovskiy Soyuz", "ZKR": "Respublika Zakariya", "ZML": "Zemlya Zamaliya",
    "NBL": "Novaya Bulatiya", "ISG": "Respublika Ismagil", "HRL": "Kharitonovskaya Liga",
    "SHF": "Sharafutdinovskaya Federatsiya",
}

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


def unique_color(pid: int) -> tuple[int, int, int]:
    v = pid + 1
    return v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF


def save_bmp_rgb(path: Path, img: Image.Image) -> None:
    img = img.convert("RGB").transpose(Image.FLIP_TOP_BOTTOM)
    w, h = img.size
    row_stride = (w * 3 + 3) & ~3
    raw = img.tobytes()
    out = bytearray()
    pad = b"\x00" * (row_stride - w * 3)
    for y in range(h):
        row = raw[y * w * 3 : (y + 1) * w * 3]
        bgr = bytearray(w * 3)
        for i in range(0, w * 3, 3):
            bgr[i], bgr[i + 1], bgr[i + 2] = row[i + 2], row[i + 1], row[i]
        out.extend(bgr)
        out.extend(pad)
    header = struct.pack("<2sIHHIIiiHHIIiiii", b"BM", 54 + len(out), 0, 0, 54, 40, w, h, 1, 24, 0, len(out), 2835, 2835, 0, 0)
    path.write_bytes(header + out)


def save_bmp_indexed_from_palette_bytes(path: Path, indices: Image.Image, pal_bgrx: bytes) -> None:
    w, h = indices.size
    data = list(indices.convert("L").getdata())
    row_stride = (w + 3) & ~3
    body = bytearray()
    pad = b"\x00" * (row_stride - w)
    for y in range(h - 1, -1, -1):
        body.extend(bytes(data[y * w : (y + 1) * w]))
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
    path.write_bytes(header + pal_bgrx + body)


def write_tga32(path: Path, img: Image.Image) -> None:
    img = img.convert("RGBA")
    w, h = img.size
    # TGA bottom-up BGRA
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    raw = img.tobytes("raw", "BGRA")
    header = bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]) + struct.pack("<HHBB", w, h, 32, 8)
    path.write_bytes(header + raw)


def make_flag(color: tuple[int, int, int], size: tuple[int, int]) -> Image.Image:
    img = Image.new("RGBA", size, color + (255,))
    d = ImageDraw.Draw(img)
    # simple mark so flags differ
    margin = max(1, size[0] // 8)
    d.rectangle([margin, margin, size[0] - margin - 1, size[1] - margin - 1], outline=(255, 255, 255, 255))
    return img


def nearest_tag(col: int, row: int) -> str:
    best, bd = "VCI", 999
    for (bc, br), tag in BOARD.items():
        d = abs(bc - col) + abs(br - row)
        if d < bd:
            best, bd = tag, d
    return best


def rebuild_map() -> None:
    map_dir = ROOT / "map"
    states_dir = ROOT / "history" / "states"
    sr_dir = map_dir / "strategicregions"
    for d in (map_dir, states_dir, sr_dir):
        d.mkdir(parents=True, exist_ok=True)
    for p in list(states_dir.glob("*.txt")) + list(sr_dir.glob("*.txt")):
        p.unlink()

    # Continents MUST include vanilla names (portraits/definition)
    (map_dir / "continent.txt").write_text(
        "continents = {\n\teurope\n\tnorth_america\n\tsouth_america\n\taustralia\n\tafrica\n\tasia\n\tmiddle_east\n\tkazualia\n}\n",
        encoding="utf-8",
    )

    grid_cols = (LAND_X1 - LAND_X0) // CELL
    grid_rows = (LAND_Y1 - LAND_Y0) // CELL
    land_x1 = LAND_X0 + grid_cols * CELL
    land_y1 = LAND_Y0 + grid_rows * CELL

    # Full-map cell grid for BOTH land and sea (small provinces → no TOO LARGE BOX)
    full_cols = WIDTH // CELL
    full_rows = HEIGHT // CELL
    # trim map paint area to multiples
    map_w = full_cols * CELL
    map_h = full_rows * CELL

    tag_states = {}
    next_extra = 25
    for tag, _ in OUR:
        n = SIZE_STATES[SIZE_OF[tag]]
        ids = [CAPITAL[tag]]
        while len(ids) < n:
            ids.append(next_extra)
            next_extra += 1
        tag_states[tag] = ids

    # Assign every land cell to tag
    land_cells = defaultdict(list)
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            bcol = min(7, int(gx / grid_cols * 8))
            brow = 5 - min(5, int(gy / grid_rows * 6))
            tag = BOARD.get((bcol, brow)) or nearest_tag(bcol, brow)
            # store in full-grid coords
            fx = (LAND_X0 // CELL) + gx
            fy = (LAND_Y0 // CELL) + gy
            land_cells[tag].append((fx, fy))

    provinces = {}
    cell_pid = {}
    state_provinces = defaultdict(list)
    state_owner = {}
    state_names = {}
    capital_province = {}
    next_pid = 1

    for tag, _col in OUR:
        cells = sorted(land_cells[tag], key=lambda c: (c[0], c[1]))
        states = tag_states[tag]
        n_states = len(states)
        xs = sorted({c[0] for c in cells})
        chunks = [[] for _ in range(n_states)]
        if len(xs) >= n_states:
            strip = max(1, (len(xs) + n_states - 1) // n_states)
            xmap = {x: min(n_states - 1, i // strip) for i, x in enumerate(xs)}
            for cell in cells:
                chunks[xmap[cell[0]]].append(cell)
        else:
            n = len(cells)
            for i in range(n_states):
                chunks[i] = cells[i * n // n_states : (i + 1) * n // n_states]
        for i in range(n_states):
            if not chunks[i]:
                donor = max(range(n_states), key=lambda j: len(chunks[j]))
                if chunks[donor]:
                    chunks[i].append(chunks[donor].pop())

        for si, sid in enumerate(states):
            state_owner[sid] = tag
            is_cap = sid == CAPITAL[tag]
            state_names[sid] = f"{NAME[tag]} Capital" if is_cap else f"{NAME[tag]} Region {si}"
            created = []
            for fx, fy in sorted(chunks[si], key=lambda c: (c[1], c[0])):
                pid = next_pid
                next_pid += 1
                color = unique_color(pid)
                cx = fx * CELL + CELL / 2
                cy = fy * CELL + CELL / 2
                # coastal if touches sea cell
                coastal = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = fx + dx, fy + dy
                    lx0, ly0 = LAND_X0 // CELL, LAND_Y0 // CELL
                    lx1, ly1 = lx0 + grid_cols, ly0 + grid_rows
                    if not (lx0 <= nx < lx1 and ly0 <= ny < ly1):
                        coastal = True
                        break
                provinces[pid] = {"color": color, "cx": cx, "cy": cy, "type": "land", "coastal": coastal, "fx": fx, "fy": fy}
                cell_pid[(fx, fy)] = pid
                state_provinces[sid].append(pid)
                created.append(pid)
            if is_cap and created:
                capital_province[tag] = created[len(created) // 2]

    # Sea: every non-land full-grid cell is its own province
    sea_ids = []
    lx0, ly0 = LAND_X0 // CELL, LAND_Y0 // CELL
    lx1, ly1 = lx0 + grid_cols, ly0 + grid_rows
    for fy in range(full_rows):
        for fx in range(full_cols):
            if lx0 <= fx < lx1 and ly0 <= fy < ly1:
                continue
            pid = next_pid
            next_pid += 1
            color = unique_color(pid)
            provinces[pid] = {
                "color": color,
                "cx": fx * CELL + CELL / 2,
                "cy": fy * CELL + CELL / 2,
                "type": "sea",
                "coastal": False,
                "fx": fx,
                "fy": fy,
            }
            cell_pid[(fx, fy)] = pid
            sea_ids.append(pid)

    # Paint
    img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    px = img.load()
    for (fx, fy), pid in cell_pid.items():
        color = provinces[pid]["color"]
        x0, y0 = fx * CELL, fy * CELL
        for y in range(y0, y0 + CELL):
            for x in range(x0, x0 + CELL):
                if x < WIDTH and y < HEIGHT:
                    px[x, y] = color
    # fill any remainder edge strips (if WIDTH not multiple — should be exact)
    # verify no black
    black = sum(1 for y in range(HEIGHT) for x in range(WIDTH) if px[x, y] == (0, 0, 0))
    if black:
        # paint leftover to nearest sea
        fill = provinces[sea_ids[0]]["color"]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if px[x, y] == (0, 0, 0):
                    px[x, y] = fill
        print("filled leftover black", black)

    save_bmp_rgb(map_dir / "provinces.bmp", img)

    # definition — continent index 1 = europe (vanilla-compatible)
    lines = ["0;0;0;0;land;false;unknown;0"]
    for pid in sorted(provinces):
        p = provinces[pid]
        r, g, b = p["color"]
        if p["type"] == "sea":
            lines.append(f"{pid};{r};{g};{b};sea;false;ocean;0")
        else:
            coastal = "true" if p["coastal"] else "false"
            terr = "urban" if pid in capital_province.values() else "plains"
            lines.append(f"{pid};{r};{g};{b};land;{coastal};{terr};1")
    (map_dir / "definition.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # terrain/height/cities/rivers — raw BGRX palette from vanilla BMP
    riv_data = (VANILLA_MAP / "rivers.bmp").read_bytes()
    riv_pal = riv_data[54 : 54 + 1024]
    def pal_bgrx_from_image(name: str) -> bytes:
        lst = list(Image.open(VANILLA_MAP / name).getpalette() or [])
        lst = (lst + [0] * 768)[:768]
        out = bytearray()
        for i in range(256):
            r, g, b = lst[i * 3], lst[i * 3 + 1], lst[i * 3 + 2]
            out.extend(bytes((b, g, r, 0)))
        return bytes(out)

    cities_pal = pal_bgrx_from_image("cities.bmp")
    terr_pal_b = pal_bgrx_from_image("terrain.bmp")

    terrain = Image.new("L", (WIDTH, HEIGHT), 15)
    height = Image.new("L", (WIDTH, HEIGHT), 40)
    rivers = Image.new("L", (WIDTH, HEIGHT), 254)
    cities = Image.new("L", (WIDTH, HEIGHT), 0)
    tpx, hpx, cpx = terrain.load(), height.load(), cities.load()
    for fy in range(ly0, ly1):
        for fx in range(lx0, lx1):
            for y in range(fy * CELL, fy * CELL + CELL):
                for x in range(fx * CELL, fx * CELL + CELL):
                    tpx[x, y] = 0
                    hpx[x, y] = 120
    for tag, pid in capital_province.items():
        cx, cy = int(provinces[pid]["cx"]), int(provinces[pid]["cy"])
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = cx + dx, cy + dy
                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    tpx[x, y] = 7
                    cpx[x, y] = 15

    save_bmp_indexed_from_palette_bytes(map_dir / "terrain.bmp", terrain, terr_pal_b)
    save_bmp_indexed_from_palette_bytes(map_dir / "rivers.bmp", rivers, riv_pal)
    gray = bytearray()
    for i in range(256):
        gray.extend(bytes((i, i, i, 0)))
    save_bmp_indexed_from_palette_bytes(map_dir / "heightmap.bmp", height, bytes(gray))
    save_bmp_indexed_from_palette_bytes(map_dir / "cities.bmp", cities, cities_pal)
    save_bmp_rgb(map_dir / "world_normal.bmp", Image.new("RGB", (WIDTH // 2, HEIGHT // 2), (128, 128, 255)))
    trees_pal = pal_bgrx_from_image("trees.bmp")
    tw, th = max(64, WIDTH * 1650 // 5632), max(64, HEIGHT * 600 // 2048)
    save_bmp_indexed_from_palette_bytes(map_dir / "trees.bmp", Image.new("L", (tw, th), 0), trees_pal)

    (map_dir / "default.map").write_text(
        '''definitions = "definition.csv"
provinces = "provinces.bmp"
positions = "positions.txt"
terrain = "terrain.bmp"
rivers = "rivers.bmp"
heightmap = "heightmap.bmp"
tree_definition = "trees.bmp"
continent = "continent.txt"
adjacency_rules = "adjacency_rules.txt"
adjacencies = "adjacencies.csv"
ambient_object = "ambient_object.txt"
seasons = "seasons.txt"
tree = { 3 4 7 10 }
''',
        encoding="utf-8",
    )
    (map_dir / "positions.txt").write_text("", encoding="utf-8")
    (map_dir / "adjacencies.csv").write_text(
        "From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment\n", encoding="utf-8"
    )
    for fname in ("seasons.txt", "adjacency_rules.txt", "cities.txt"):
        (map_dir / fname).write_bytes((VANILLA_MAP / fname).read_bytes())
    (map_dir / "ambient_object.txt").write_text(
        'type={\n\ttype="ambient_wind_entity"\n\tuse_animation=no\n\talways_visible=yes\n\tobject={\n\t\tname="ambient_wind"\n\t\tposition={ 0 0 0 }\n\t\trotation={ 0 0 0 }\n\t}\n}\n',
        encoding="utf-8",
    )

    # unitstacks / buildings / supply / weatherpositions
    ustack, buildings, supply, weather = [], [], [], []
    for pid, p in provinces.items():
        if p["type"] != "land":
            continue
        ustack.append(f"{pid};0;{p['cx']:.2f};12.00;{p['cy']:.2f};0.00;0.50")
    for sid, provs in state_provinces.items():
        tag = state_owner[sid]
        pid = capital_province.get(tag, provs[0]) if sid == CAPITAL[tag] else provs[0]
        p = provinces[pid]
        for btype, n in (("industrial_complex", 2), ("arms_factory", 1), ("infrastructure", 3)):
            for i in range(n):
                buildings.append(f"{sid};{btype};{p['cx']+i*0.3:.2f};12.00;{p['cy']+i*0.2:.2f};{i*0.4:.2f};0")
        if sid == CAPITAL[tag]:
            supply.append(f"1 {pid} ")
            weather.append(f"{pid};{p['cx']:.2f};12.00;{p['cy']:.2f}")
    (map_dir / "unitstacks.txt").write_text("\n".join(ustack) + "\n", encoding="utf-8")
    (map_dir / "buildings.txt").write_text("\n".join(buildings) + "\n", encoding="utf-8")
    (map_dir / "supply_nodes.txt").write_text("\n".join(supply) + "\n", encoding="utf-8")
    (map_dir / "railways.txt").write_text("", encoding="utf-8")
    (map_dir / "weatherpositions.txt").write_text("\n".join(weather) + "\n", encoding="utf-8")

    # states
    loc_states = ["l_russian:"]
    for sid in sorted(state_provinces):
        provs = state_provinces[sid]
        tag = state_owner[sid]
        size = SIZE_OF[tag]
        is_cap = sid == CAPITAL[tag]
        cat = {
            ("large", True): "metropolis", ("large", False): "large_town",
            ("medium", True): "large_city", ("medium", False): "town",
            ("small", True): "city", ("small", False): "rural",
        }[(size, is_cap)]
        manpower = {"large": 1500000, "medium": 750000, "small": 400000}[size]
        if is_cap:
            manpower = int(manpower * 1.3)
        infra = {"large": 4, "medium": 3, "small": 2}[size]
        civ = {"large": 2, "medium": 1, "small": 1}[size] + (1 if is_cap else 0)
        mil = {"large": 1, "medium": 1, "small": 0}[size] + (1 if is_cap else 0)
        vp = capital_province.get(tag, provs[0]) if is_cap else provs[0]
        vp_val = ({"large": 30, "medium": 20, "small": 12}[size] if is_cap else 3)
        loc_states.append(f' STATE_{sid}:0 "{state_names[sid]}"')
        coastal = ""
        if any(provinces[p]["coastal"] for p in provs):
            cp = next(p for p in provs if provinces[p]["coastal"])
            coastal = f"\n\t\t\t{cp} = {{ naval_base = 2 }}"
        air = "\n\t\t\tair_base = 1" if is_cap else ""
        (states_dir / f"{sid}-{tag}.txt").write_text(
            f'''state={{
\tid={sid}
\tname="STATE_{sid}"
\tmanpower = {manpower}
\tstate_category = {cat}
\thistory={{
\t\towner = {tag}
\t\tvictory_points = {{ {vp} {vp_val} }}
\t\tbuildings = {{
\t\t\tinfrastructure = {infra}
\t\t\tindustrial_complex = {civ}
\t\t\tarms_factory = {mil}{air}{coastal}
\t\t}}
\t\tadd_core_of = {tag}
\t}}
\tprovinces={{
\t\t{" ".join(map(str, provs))}
\t}}
\tlocal_supplies=0.0
}}
''',
            encoding="utf-8",
        )

    # strategic regions: one per country + chunk seas into ~16 regions of contiguous rows
    loc_sr = ["l_russian:"]
    sr_id = 1
    for tag, _ in OUR:
        provs = []
        for sid in tag_states[tag]:
            provs.extend(state_provinces[sid])
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "{NAME[tag]}"')
        (sr_dir / f"{sr_id}-{tag}.txt").write_text(
            f"strategic_region={{\n\tid={sr_id}\n\tname=\"STRATEGICREGION_{sr_id}\"\n\tprovinces={{\n\t\t{' '.join(map(str, provs))}\n\t}}\n{WEATHER}}}\n",
            encoding="utf-8",
        )
        sr_id += 1
    # sea SRs by rows of 4
    chunk = max(1, len(sea_ids) // 16)
    for i in range(0, len(sea_ids), chunk):
        group = sea_ids[i : i + chunk]
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "Sea {sr_id}"')
        (sr_dir / f"{sr_id}-Sea.txt").write_text(
            f"strategic_region={{\n\tid={sr_id}\n\tname=\"STRATEGICREGION_{sr_id}\"\n\tprovinces={{\n\t\t{' '.join(map(str, group))}\n\t}}\n{WEATHER}}}\n",
            encoding="utf-8",
        )
        sr_id += 1

    (ROOT / "localisation" / "russian" / "mk_states_l_russian.yml").write_bytes(
        b"\xef\xbb\xbf" + ("\n".join(loc_states) + "\n").encode("utf-8")
    )
    (ROOT / "localisation" / "russian" / "mk_strategic_regions_l_russian.yml").write_bytes(
        b"\xef\xbb\xbf" + ("\n".join(loc_sr) + "\n").encode("utf-8")
    )
    print(f"map ok provinces={len(provinces)} land={sum(1 for p in provinces.values() if p['type']=='land')} sea={len(sea_ids)} states={len(state_provinces)} sr={sr_id-1}")


def make_flags() -> None:
    base = ROOT / "gfx" / "flags"
    med = base / "medium"
    small = base / "small"
    for d in (base, med, small):
        d.mkdir(parents=True, exist_ok=True)
    ideo = {
        "VCI": "neutrality", "SOY": "democratic", "BTR": "fascism", "KRZ": "communism",
        "KZS": "neutrality", "MUS": "democratic", "TRF": "communism", "ZLD": "democratic",
        "ISL": "neutrality", "CLB": "neutrality", "ADL": "democratic", "DMK": "fascism",
        "FDP": "neutrality", "CRE": "fascism", "SVA": "democratic", "ART": "neutrality",
        "KMS": "democratic", "ZNS": "neutrality", "ZKR": "democratic", "ZML": "communism",
        "NBL": "neutrality", "ISG": "communism", "HRL": "democratic", "SHF": "neutrality",
    }
    for tag, color in OUR:
        for path, size in (
            (base / f"{tag}.tga", (82, 52)),
            (med / f"{tag}.tga", (41, 26)),
            (small / f"{tag}.tga", (10, 7)),
        ):
            write_tga32(path, make_flag(color, size))
        # ideology variants commonly requested
        for suf in ("neutrality", "democratic", "fascism", "communism"):
            write_tga32(base / f"{tag}_{suf}.tga", make_flag(color, (82, 52)))
            write_tga32(med / f"{tag}_{suf}.tga", make_flag(color, (41, 26)))
            write_tga32(small / f"{tag}_{suf}.tga", make_flag(color, (10, 7)))
    print("flags generated for 24 tags + ideology variants")


def write_portraits_stub() -> None:
    """Minimal portraits file so vanilla 00_portraits parse errors don't cascade from bad continent."""
    pdir = ROOT / "portraits"
    pdir.mkdir(parents=True, exist_ok=True)
    # Do not replace vanilla portraits — additive empty/default for our tags only
    text = "default = {\n"
    for tag, _ in OUR:
        text += f"""\t{tag} = {{
\t\tarmy = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\tnavy = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\tpolitical = {{
\t\t\tcommunism = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\t\tdemocratic = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\t\tfascism = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\t\tneutrality = {{ male = {{ \"gfx/leaders/leader_unknown.dds\" }} }}
\t\t}}
\t}}
"""
    text += "}\n"
    (pdir / "mk_portraits.txt").write_text(text, encoding="utf-8")
    print("portraits stub written")


def write_descriptor() -> None:
    body = '''version="0.3.4"
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
    path = "D:/Dowland/Mod/Games/HOI4/mir_kazualnosti"
    pointer = body + f'path="{path}"\n'
    (ROOT / "descriptor.mod").write_text(body, encoding="utf-8")
    (ROOT / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    DOCS_MOD.mkdir(parents=True, exist_ok=True)
    (DOCS_MOD / "mir_kazualnosti.mod").write_text(pointer, encoding="utf-8")
    print("descriptor v0.3.4")


def ensure_stubs() -> None:
    tags = []
    for p in (VANILLA / "common" / "country_tags").glob("*.txt"):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                tag = s.split("=")[0].strip().upper()
                if len(tag) == 3 and tag.isalpha():
                    tags.append(tag)
    hist = ROOT / "history" / "countries"
    hist.mkdir(parents=True, exist_ok=True)
    for p in hist.glob("*- Stub.txt"):
        p.unlink()
    n = 0
    for tag in dict.fromkeys(tags):
        if tag in OUR_TAGS:
            continue
        (hist / f"{tag} - Stub.txt").write_text(
            "capital = 1\nset_research_slots = 2\nset_technology = { infantry_weapons = 1 }\n"
            "set_politics = { ruling_party = neutrality last_election = \"1935.1.1\" election_frequency = 48 elections_allowed = no }\n"
            "set_popularities = { democratic = 0 communism = 0 fascism = 0 neutrality = 100 }\n",
            encoding="utf-8",
        )
        n += 1
    print("stubs", n)


def main() -> None:
    write_descriptor()
    rebuild_map()
    make_flags()
    write_portraits_stub()
    ensure_stubs()
    print("ALL BOOT FIXES DONE")


if __name__ == "__main__":
    main()
