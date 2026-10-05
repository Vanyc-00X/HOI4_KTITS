# -*- coding: utf-8 -*-
"""HOI4-valid rectangular map: 1 grid cell = 1 province (no X-cross / no scatter)."""
from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map")

WIDTH, HEIGHT = 2048, 1024
NORMAL_W, NORMAL_H = WIDTH // 2, HEIGHT // 2
LAND_X0, LAND_Y0 = 288, 160
LAND_X1, LAND_Y1 = 1760, 864
CELL = 32

COUNTRIES = [
    ("VCI", 1, "large", "Velikaya Kazualnaya Imperiya"),
    ("SOY", 2, "medium", "Soevaya Respublika"),
    ("BTR", 3, "medium", "Chyornaya Tartariya"),
    ("KRZ", 4, "large", "Krasnaya Zemlya"),
    ("KZS", 5, "small", "Kazachi Shtaty"),
    ("MUS", 6, "medium", "Korolevstvo Musi"),
    ("TRF", 7, "medium", "Travinnaya Federatsiya"),
    ("ZLD", 8, "medium", "Demokraticheskiy Zelenodolsk"),
    ("ISL", 9, "medium", "Islamskaya Respublika"),
    ("CLB", 10, "medium", "Chelyaba"),
    ("ADL", 11, "small", "Aydaliya"),
    ("DMK", 12, "medium", "Dmitro-Knyazhestvo"),
    ("FDP", 13, "medium", "Federatsiya Deputatov"),
    ("CRE", 14, "medium", "Chyornaya Respublika"),
    ("SVA", 15, "medium", "Severnaya Assambleya"),
    ("ART", 16, "medium", "Ayratskaya Respublika"),
    ("KMS", 17, "medium", "Kamilskoe Sodruzhestvo"),
    ("ZNS", 18, "medium", "Zaynutdinovskiy Soyuz"),
    ("ZKR", 19, "medium", "Respublika Zakariya"),
    ("ZML", 20, "small", "Zemlya Zamaliya"),
    ("NBL", 21, "medium", "Novaya Bulatiya"),
    ("ISG", 22, "small", "Respublika Ismagil"),
    ("HRL", 23, "medium", "Kharitonovskaya Liga"),
    ("SHF", 24, "large", "Sharafutdinovskaya Federatsiya"),
]

BOARD = {
    (1, 5): "SVA", (2, 5): "SVA", (3, 5): "CLB", (4, 5): "CLB", (5, 5): "ART", (6, 5): "ART",
    (0, 4): "KMS", (1, 4): "KMS", (2, 4): "ZLD", (3, 4): "VCI", (4, 4): "VCI", (5, 4): "NBL", (6, 4): "ZNS", (7, 4): "ZNS",
    (0, 3): "MUS", (1, 3): "MUS", (2, 3): "SOY", (3, 3): "VCI", (4, 3): "FDP", (5, 3): "DMK", (6, 3): "DMK", (7, 3): "KRZ",
    (0, 2): "ISL", (1, 2): "TRF", (2, 2): "TRF", (3, 2): "ZML", (4, 2): "ISG", (5, 2): "HRL", (6, 2): "KRZ", (7, 2): "KRZ",
    (0, 1): "ADL", (1, 1): "ADL", (2, 1): "SHF", (3, 1): "SHF", (4, 1): "SHF", (5, 1): "CRE", (6, 1): "CRE", (7, 1): "BTR",
    (0, 0): "ZKR", (1, 0): "ZKR", (2, 0): "SHF", (3, 0): "SHF", (4, 0): "KZS", (5, 0): "KZS", (6, 0): "BTR", (7, 0): "BTR",
}

SIZE_STATES = {"large": 10, "medium": 5, "small": 3}

WEATHER = """\tweather={
\t\tperiod={
\t\t\tbetween={ 0.0 30.0 }
\t\t\ttemperature={ -2.0 18.0 }
\t\t\tno_phenomenon=0.550
\t\t\train_light=0.250
\t\t\train_heavy=0.100
\t\t\tsnow=0.050
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.200
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.1 27.1 }
\t\t\ttemperature={ -4.0 16.0 }
\t\t\tno_phenomenon=0.500
\t\t\train_light=0.250
\t\t\train_heavy=0.100
\t\t\tsnow=0.100
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.250
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.2 30.2 }
\t\t\ttemperature={ 2.0 20.0 }
\t\t\tno_phenomenon=0.550
\t\t\train_light=0.250
\t\t\train_heavy=0.100
\t\t\tsnow=0.020
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.200
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.3 29.3 }
\t\t\ttemperature={ 6.0 24.0 }
\t\t\tno_phenomenon=0.600
\t\t\train_light=0.220
\t\t\train_heavy=0.080
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.150
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.4 30.4 }
\t\t\ttemperature={ 10.0 28.0 }
\t\t\tno_phenomenon=0.650
\t\t\train_light=0.200
\t\t\train_heavy=0.080
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.100
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.5 29.5 }
\t\t\ttemperature={ 14.0 30.0 }
\t\t\tno_phenomenon=0.700
\t\t\train_light=0.180
\t\t\train_heavy=0.060
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.080
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.6 30.6 }
\t\t\ttemperature={ 16.0 32.0 }
\t\t\tno_phenomenon=0.700
\t\t\train_light=0.160
\t\t\train_heavy=0.060
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.050
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.7 30.7 }
\t\t\ttemperature={ 14.0 30.0 }
\t\t\tno_phenomenon=0.650
\t\t\train_light=0.180
\t\t\train_heavy=0.070
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.080
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.8 29.8 }
\t\t\ttemperature={ 10.0 26.0 }
\t\t\tno_phenomenon=0.600
\t\t\train_light=0.200
\t\t\train_heavy=0.080
\t\t\tsnow=0.000
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.120
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.9 30.9 }
\t\t\ttemperature={ 6.0 22.0 }
\t\t\tno_phenomenon=0.550
\t\t\train_light=0.220
\t\t\train_heavy=0.090
\t\t\tsnow=0.010
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.150
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.10 29.10 }
\t\t\ttemperature={ 2.0 18.0 }
\t\t\tno_phenomenon=0.520
\t\t\train_light=0.230
\t\t\train_heavy=0.100
\t\t\tsnow=0.040
\t\t\tblizzard=0.000
\t\t\tarctic_water=0.000
\t\t\tmud=0.180
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
\t\tperiod={
\t\t\tbetween={ 0.11 30.11 }
\t\t\ttemperature={ -1.0 16.0 }
\t\t\tno_phenomenon=0.500
\t\t\train_light=0.240
\t\t\train_heavy=0.100
\t\t\tsnow=0.080
\t\t\tblizzard=0.010
\t\t\tarctic_water=0.000
\t\t\tmud=0.200
\t\t\tsandstorm=0.000
\t\t\tmin_snow_level=0.000
\t\t}
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
    pixel_data = bytearray()
    pad = b"\x00" * (row_stride - w * 3)
    for y in range(h):
        row = raw[y * w * 3 : (y + 1) * w * 3]
        bgr = bytearray(w * 3)
        for i in range(0, w * 3, 3):
            bgr[i] = row[i + 2]
            bgr[i + 1] = row[i + 1]
            bgr[i + 2] = row[i]
        pixel_data.extend(bgr)
        pixel_data.extend(pad)
    header = struct.pack(
        "<2sIHHIIiiHHIIiiii",
        b"BM",
        54 + len(pixel_data),
        0,
        0,
        54,
        40,
        w,
        h,
        1,
        24,
        0,
        len(pixel_data),
        2835,
        2835,
        0,
        0,
    )
    path.write_bytes(header + pixel_data)


def save_bmp_indexed(path: Path, index_img: Image.Image, palette_rgb: list[int]) -> None:
    full_pal = (list(palette_rgb) + [0] * 768)[:768]
    data = list(index_img.convert("L").getdata())
    w, h = index_img.size
    rows = bytearray()
    pad_n = (4 - (w % 4)) % 4
    for y in range(h - 1, -1, -1):
        rows.extend(data[y * w : (y + 1) * w])
        if pad_n:
            rows.extend(b"\x00" * pad_n)
    pixel_bytes = bytes(rows)
    pal_bytes = bytearray()
    for i in range(256):
        r, g, b = full_pal[i * 3], full_pal[i * 3 + 1], full_pal[i * 3 + 2]
        pal_bytes.extend(bytes((b, g, r, 0)))
    off = 14 + 40 + 1024
    header = struct.pack(
        "<2sIHHIIiiHHIIiiii",
        b"BM",
        off + len(pixel_bytes),
        0,
        0,
        off,
        40,
        w,
        h,
        1,
        8,
        0,
        len(pixel_bytes),
        2835,
        2835,
        256,
        256,
    )
    path.write_bytes(header + pal_bytes + pixel_bytes)


def load_vanilla_palette(name: str) -> list[int]:
    im = Image.open(VANILLA_MAP / name)
    return (list(im.getpalette() or []) + [0] * 768)[:768]


def count_x_crossings(img: Image.Image) -> int:
    px = img.load()
    w, h = img.size
    n = 0
    for y in range(h - 1):
        for x in range(w - 1):
            a, b = px[x, y], px[x + 1, y]
            c, d = px[x, y + 1], px[x + 1, y + 1]
            if a != b and a != c and a == d and b == c:
                n += 1
    return n


def nearest_board_tag(col: int, row: int) -> str:
    best, best_d = "VCI", 999
    for (bc, br), tag in BOARD.items():
        d = abs(bc - col) + abs(br - row)
        if d < best_d:
            best, best_d = tag, d
    return best


def terrain_for_cell(gx: int, gy: int) -> str:
    ridge_x = 12 + gy // 2
    ridge_distance = abs(gx - ridge_x)
    if 4 <= gy <= 18 and ridge_distance <= 1:
        return "mountain"
    if ridge_distance <= 4:
        return "hills"
    if (gx <= 11 and gy <= 8) or (gx >= 34 and gy <= 14):
        return "forest"
    if 18 <= gx <= 25 and 10 <= gy <= 16:
        return "marsh"
    if gx >= 39 and gy >= 16:
        return "desert"
    return "plains"


TERRAIN_HEIGHT = {
    "mountain": 205,
    "hills": 155,
    "forest": 112,
    "marsh": 76,
    "desert": 92,
    "plains": 100,
}


def main() -> None:
    map_dir = ROOT / "map"
    states_dir = ROOT / "history" / "states"
    sr_dir = map_dir / "strategicregions"
    for d in (map_dir, states_dir, sr_dir):
        d.mkdir(parents=True, exist_ok=True)
    for p in states_dir.glob("*.txt"):
        p.unlink()
    for p in sr_dir.glob("*.txt"):
        p.unlink()

    tag_meta = {t[0]: t for t in COUNTRIES}
    next_extra = 25
    tag_states: dict[str, list[int]] = {}
    for tag, cap, size, _ in COUNTRIES:
        ids = [cap]
        while len(ids) < SIZE_STATES[size]:
            ids.append(next_extra)
            next_extra += 1
        tag_states[tag] = ids

    grid_cols = (LAND_X1 - LAND_X0) // CELL
    grid_rows = (LAND_Y1 - LAND_Y0) // CELL
    land_x1 = LAND_X0 + grid_cols * CELL
    land_y1 = LAND_Y0 + grid_rows * CELL
    print(f"Land grid {grid_cols}x{grid_rows} (1 cell = 1 province)")

    tag_cells: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            bcol = min(7, int(gx / grid_cols * 8))
            brow = 5 - min(5, int(gy / grid_rows * 6))
            tag = BOARD.get((bcol, brow)) or nearest_board_tag(bcol, brow)
            tag_cells[tag].append((gx, gy))

    provinces: dict[int, dict] = {}
    cell_pid: dict[tuple[int, int], int] = {}
    state_provinces: dict[int, list[int]] = defaultdict(list)
    state_owner: dict[int, str] = {}
    state_names: dict[int, str] = {}
    capital_province: dict[str, int] = {}
    next_pid = 1

    # Each cell is its own province; cells distributed into states by contiguous strips
    for tag, cap, size, ru_name in COUNTRIES:
        cells = sorted(tag_cells[tag], key=lambda c: (c[0], c[1]))
        if not cells:
            raise RuntimeError(f"No cells for {tag}")
        states = tag_states[tag]
        n_states = len(states)
        xs = sorted({c[0] for c in cells})
        chunks: list[list[tuple[int, int]]] = [[] for _ in range(n_states)]
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
            is_cap = sid == cap
            state_names[sid] = f"{ru_name} Capital" if is_cap else f"{ru_name} Region {si}"
            created = []
            for gx, gy in sorted(chunks[si], key=lambda c: (c[1], c[0])):
                pid = next_pid
                next_pid += 1
                color = unique_color(pid)
                cx = LAND_X0 + gx * CELL + CELL / 2
                cy = LAND_Y0 + gy * CELL + CELL / 2
                coastal = gx == 0 or gy == 0 or gx == grid_cols - 1 or gy == grid_rows - 1
                provinces[pid] = {
                    "id": pid,
                    "color": color,
                    "cx": cx,
                    "cy": cy,
                    "type": "land",
                    "terrain": terrain_for_cell(gx, gy),
                    "coastal": coastal,
                    "gx": gx,
                    "gy": gy,
                }
                cell_pid[(gx, gy)] = pid
                state_provinces[sid].append(pid)
                created.append(pid)
            if is_cap and created:
                # center-most cell as capital VP
                capital_province[tag] = min(
                    created,
                    key=lambda p: (provinces[p]["cx"] - (LAND_X0 + land_x1) / 2) ** 2
                    + (provinces[p]["cy"] - (LAND_Y0 + land_y1) / 2) ** 2,
                )

    # Paint land
    prov_img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    px = prov_img.load()
    for (gx, gy), pid in cell_pid.items():
        color = provinces[pid]["color"]
        x0 = LAND_X0 + gx * CELL
        y0 = LAND_Y0 + gy * CELL
        for y in range(y0, y0 + CELL):
            for x in range(x0, x0 + CELL):
                px[x, y] = color

    # Seas: never span both left and right map edges (avoids TOO LARGE BOX)
    print("Building seas...")
    mid_x = WIDTH // 2
    sea_defs = {
        "nw": lambda x, y: y < LAND_Y0 and x < mid_x,
        "ne": lambda x, y: y < LAND_Y0 and x >= mid_x,
        "sw": lambda x, y: y >= land_y1 and x < mid_x,
        "se": lambda x, y: y >= land_y1 and x >= mid_x,
        "west": lambda x, y: LAND_Y0 <= y < land_y1 and x < LAND_X0,
        "east": lambda x, y: LAND_Y0 <= y < land_y1 and x >= land_x1,
    }
    # mid belt between land and map sides already covered; gaps above/below handled by n/s
    sea_ids = []
    for key, pred in sea_defs.items():
        pixels = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if LAND_X0 <= x < land_x1 and LAND_Y0 <= y < land_y1:
                    continue
                if pred(x, y):
                    pixels.append((x, y))
        if not pixels:
            continue
        pid = next_pid
        next_pid += 1
        color = unique_color(pid)
        for x, y in pixels:
            px[x, y] = color
        provinces[pid] = {
            "id": pid,
            "color": color,
            "cx": sum(a for a, _ in pixels) / len(pixels),
            "cy": sum(b for _, b in pixels) / len(pixels),
            "type": "sea",
            "coastal": False,
        }
        sea_ids.append(pid)
        print(f"  sea {key}: pid={pid} pixels={len(pixels)}")

    # Fill any leftover sea pixels (shouldn't happen) into nearest sea
    leftovers = [(x, y) for y in range(HEIGHT) for x in range(WIDTH) if px[x, y] == (0, 0, 0)]
    if leftovers:
        print(f"WARNING leftover pixels {len(leftovers)} — assigning to first sea")
        fill = provinces[sea_ids[0]]["color"]
        for x, y in leftovers:
            px[x, y] = fill

    xc = count_x_crossings(prov_img)
    print(f"X-crossings: {xc}")
    if xc:
        raise RuntimeError(f"X-crossings remain: {xc}")

    # Terrain layers
    terrain_pal = load_vanilla_palette("terrain.bmp")
    rivers_pal = load_vanilla_palette("rivers.bmp")
    cities_pal = load_vanilla_palette("cities.bmp")
    terrain_idx = Image.new("L", (WIDTH, HEIGHT), 15)
    height_idx = Image.new("L", (WIDTH, HEIGHT), 40)
    rivers_idx = Image.new("L", (WIDTH, HEIGHT), 254)
    cities_idx = Image.new("L", (WIDTH, HEIGHT), 0)
    tpx, hpx, cpx = terrain_idx.load(), height_idx.load(), cities_idx.load()
    for y in range(LAND_Y0, land_y1):
        for x in range(LAND_X0, land_x1):
            tpx[x, y] = 0
            gx, gy = (x - LAND_X0) // CELL, (y - LAND_Y0) // CELL
            hpx[x, y] = TERRAIN_HEIGHT[terrain_for_cell(gx, gy)]

    # Preserve the game's indexed river segments rather than drawing arbitrary colors.
    vanilla_rivers = Image.open(VANILLA_MAP / "rivers.bmp").convert("P")
    if vanilla_rivers.width < land_x1 - LAND_X0 or vanilla_rivers.height < land_y1 - LAND_Y0:
        raise RuntimeError("Vanilla rivers.bmp is too small to provide a river network")
    river_indices = Image.frombytes("L", vanilla_rivers.size, vanilla_rivers.tobytes())
    river_patch = river_indices.crop((0, 0, land_x1 - LAND_X0, land_y1 - LAND_Y0))
    rivers_idx.paste(river_patch, (LAND_X0, LAND_Y0))

    for tag, pid in capital_province.items():
        cx, cy = int(provinces[pid]["cx"]), int(provinces[pid]["cy"])
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = cx + dx, cy + dy
                if LAND_X0 <= x < land_x1 and LAND_Y0 <= y < land_y1:
                    tpx[x, y] = 7
                    cpx[x, y] = 15

    print("Writing BMPs...")
    save_bmp_rgb(map_dir / "provinces.bmp", prov_img)
    save_bmp_indexed(map_dir / "terrain.bmp", terrain_idx, terrain_pal)
    save_bmp_indexed(map_dir / "rivers.bmp", rivers_idx, rivers_pal)
    gray_pal = [v for i in range(256) for v in (i, i, i)]
    save_bmp_indexed(map_dir / "heightmap.bmp", height_idx, gray_pal)
    save_bmp_indexed(map_dir / "cities.bmp", cities_idx, cities_pal)
    save_bmp_rgb(map_dir / "world_normal.bmp", Image.new("RGB", (NORMAL_W, NORMAL_H), (128, 128, 255)))
    tw, th = max(64, WIDTH * 1650 // 5632), max(64, HEIGHT * 600 // 2048)
    save_bmp_indexed(map_dir / "trees.bmp", Image.new("L", (tw, th), 0), load_vanilla_palette("trees.bmp"))

    lines = ["0;0;0;0;land;false;unknown;0"]
    for pid in sorted(provinces):
        p = provinces[pid]
        r, g, b = p["color"]
        if p["type"] == "sea":
            lines.append(f"{pid};{r};{g};{b};sea;false;ocean;0")
        else:
            coastal = "true" if p["coastal"] else "false"
            terr = "urban" if pid in capital_province.values() else p["terrain"]
            lines.append(f"{pid};{r};{g};{b};land;{coastal};{terr};1")
    (map_dir / "definition.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
    (map_dir / "continent.txt").write_text("continents = {\n\tkazualia\n}\n", encoding="utf-8")
    (map_dir / "positions.txt").write_text("", encoding="utf-8")
    (map_dir / "adjacencies.csv").write_text(
        "From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment\n",
        encoding="utf-8",
    )
    for fname in ("seasons.txt", "adjacency_rules.txt", "cities.txt"):
        src = VANILLA_MAP / fname
        if src.exists():
            (map_dir / fname).write_bytes(src.read_bytes())
    (map_dir / "ambient_object.txt").write_text(
        'type={\n\ttype="ambient_wind_entity"\n\tuse_animation=no\n\talways_visible=yes\n\tobject={\n\t\tname="ambient_wind"\n\t\tposition={ 0 0 0 }\n\t\trotation={ 0 0 0 }\n\t}\n}\n',
        encoding="utf-8",
    )
    # weatherpositions: leave EMPTY file (valid) — non-empty wrong arity errors
    (map_dir / "weatherpositions.txt").write_text("", encoding="utf-8")

    ustack, buildings, supply = [], [], []
    for pid, p in provinces.items():
        if p["type"] != "land":
            continue
        ustack.append(f"{pid};0;{p['cx']:.2f};12.00;{p['cy']:.2f};0.00;0.50")
    (map_dir / "unitstacks.txt").write_text("\n".join(ustack) + "\n", encoding="utf-8")
    for sid, provs in state_provinces.items():
        tag = state_owner[sid]
        cap = tag_meta[tag][1]
        pid = capital_province.get(tag, provs[0]) if sid == cap else provs[0]
        p = provinces[pid]
        x, y = p["cx"], p["cy"]
        for btype, n in (("industrial_complex", 2), ("arms_factory", 1), ("infrastructure", 4)):
            for i in range(n):
                buildings.append(f"{sid};{btype};{x+i*0.3:.2f};12.00;{y+i*0.2:.2f};{i*0.4:.2f};0")
        if sid == cap:
            supply.append(f"1 {pid} ")
    (map_dir / "buildings.txt").write_text("\n".join(buildings) + "\n", encoding="utf-8")
    (map_dir / "supply_nodes.txt").write_text("\n".join(supply) + "\n", encoding="utf-8")
    (map_dir / "railways.txt").write_text("", encoding="utf-8")

    loc_states = ["l_russian:"]
    for sid in sorted(state_provinces):
        provs = state_provinces[sid]
        tag = state_owner[sid]
        _, cap, size, ru_name = tag_meta[tag]
        is_cap = sid == cap
        cat = {
            ("large", True): "metropolis",
            ("large", False): "large_town",
            ("medium", True): "large_city",
            ("medium", False): "town",
            ("small", True): "city",
            ("small", False): "rural",
        }[(size, is_cap)]
        manpower = {"large": 1600000, "medium": 800000, "small": 400000}[size]
        if is_cap:
            manpower = int(manpower * 1.3)
        infra = {"large": 4, "medium": 3, "small": 2}[size]
        civ = {"large": 2, "medium": 1, "small": 1}[size] + (1 if is_cap else 0)
        mil = {"large": 1, "medium": 1, "small": 0}[size] + (1 if is_cap else 0)
        vp_prov = capital_province.get(tag, provs[0]) if is_cap else provs[0]
        vp_val = ({"large": 30, "medium": 20, "small": 12}[size] if is_cap else 3)
        name_key = f"STATE_{sid}"
        loc_states.append(f' {name_key}:0 "{state_names[sid]}"')
        coastal_buildings = ""
        if any(provinces[p]["coastal"] for p in provs):
            cprov = next(p for p in provs if provinces[p]["coastal"])
            coastal_buildings = f"\n\t\t\t{cprov} = {{\n\t\t\t\tnaval_base = 2\n\t\t\t}}"
        air = "\n\t\t\tair_base = 1" if is_cap else ""
        content = f'''state={{
\tid={sid}
\tname="{name_key}"
\tmanpower = {manpower}
\tstate_category = {cat}
\thistory={{
\t\towner = {tag}
\t\tvictory_points = {{ {vp_prov} {vp_val} }}
\t\tbuildings = {{
\t\t\tinfrastructure = {infra}
\t\t\tindustrial_complex = {civ}
\t\t\tarms_factory = {mil}{air}{coastal_buildings}
\t\t}}
\t\tadd_core_of = {tag}
\t}}
\tprovinces={{
\t\t{" ".join(str(p) for p in provs)}
\t}}
\tlocal_supplies=0.0
}}
'''
        (states_dir / f"{sid}-{tag}-{'Capital' if is_cap else 'Region'+str(sid)}.txt").write_text(content, encoding="utf-8")

    loc_sr = ["l_russian:"]
    sr_id = 1
    for tag, cap, size, ru_name in COUNTRIES:
        provs = []
        for sid in tag_states[tag]:
            provs.extend(state_provinces[sid])
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "{ru_name}"')
        (sr_dir / f"{sr_id}-{tag}.txt").write_text(
            f'strategic_region={{\n\tid={sr_id}\n\tname="STRATEGICREGION_{sr_id}"\n\tprovinces={{\n\t\t{" ".join(map(str, provs))}\n\t}}\n{WEATHER}}}\n',
            encoding="utf-8",
        )
        sr_id += 1
    for i, pid in enumerate(sea_ids, 1):
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "Sea {i}"')
        (sr_dir / f"{sr_id}-Sea-{i}.txt").write_text(
            f'strategic_region={{\n\tid={sr_id}\n\tname="STRATEGICREGION_{sr_id}"\n\tprovinces={{\n\t\t{pid}\n\t}}\n{WEATHER}}}\n',
            encoding="utf-8",
        )
        sr_id += 1

    def write_yml(path: Path, rows: list[str]) -> None:
        path.write_bytes(b"\xef\xbb\xbf" + ("\n".join(rows) + "\n").encode("utf-8"))

    write_yml(ROOT / "localisation" / "russian" / "mk_states_l_russian.yml", loc_states)
    write_yml(ROOT / "localisation" / "russian" / "mk_strategic_regions_l_russian.yml", loc_sr)

    check = Image.open(map_dir / "provinces.bmp").convert("RGB")
    print(f"Verified X-crossings: {count_x_crossings(check)}")
    print(f"provinces={len(provinces)} land={sum(1 for p in provinces.values() if p['type']=='land')} sea={len(sea_ids)}")
    print(f"states={len(state_provinces)} sr={sr_id-1}")
    print("DONE")


if __name__ == "__main__":
    main()
