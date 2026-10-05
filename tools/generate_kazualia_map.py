# -*- coding: utf-8 -*-
"""Generate the fictional Kazualia map with varied biomes and a shaped coastline."""
from __future__ import annotations

import struct
from collections import defaultdict
from math import cos, exp, floor, sin
from pathlib import Path

from PIL import Image

from build_resources import resources_block

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map")

WIDTH, HEIGHT = 2048, 1024
NORMAL_W, NORMAL_H = WIDTH // 2, HEIGHT // 2
LAND_X0, LAND_Y0 = 192, 96
LAND_X1, LAND_Y1 = 1856, 928
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
TERRAIN_BMP_INDEX = {
    "plains": 0,
    "forest": 1,
    "hills": 2,
    "desert": 3,
    "marsh": 9,
    "mountain": 11,
    "urban": 13,
    "jungle": 22,
}
TREE_BIOME_INDEX = {
    "forest": (3, 4),
    "jungle": (7, 10),
}
UNIT_STACK_OFFSETS = (
    (0, 0.0, 0.0),
    (1, 0.5, -2.5),
    (2, 3.0, -2.5),
    (3, -2.0, 0.0),
    (4, 4.0, -0.5),
    (5, -3.0, 2.0),
    (6, 2.5, 2.0),
    (7, 0.0, 3.0),
    (9, -1.5, -3.0),
    (10, 1.5, -3.5),
    (21, 5.0, 1.0),
    (22, -5.0, 1.0),
    (23, 3.5, 3.5),
    (24, -3.5, 3.5),
    (25, 0.5, 5.0),
    (26, -0.5, -5.0),
    (27, 6.0, -1.0),
    (28, -6.0, -1.0),
    (38, 0.0, -1.0),
)

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


def save_bmp_indexed(
    path: Path,
    index_img: Image.Image,
    palette_rgb: list[int],
    colors_used: int = 256,
    colors_important: int = 256,
) -> None:
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
        colors_used,
        colors_important,
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
            if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                n += 1
    return n


def repair_province_junctions(img: Image.Image) -> None:
    px = img.load()
    w, h = img.size
    for _ in range(4):
        fixed = 0
        for y in range(h - 1):
            for x in range(w - 1):
                a, b = px[x, y], px[x + 1, y]
                c, d = px[x, y + 1], px[x + 1, y + 1]
                if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                    px[x + 1, y + 1] = c
                    fixed += 1
        for y in range(h - 1):
            a, b = px[w - 1, y], px[0, y]
            c, d = px[w - 1, y + 1], px[0, y + 1]
            if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                px[0, y + 1] = b
                fixed += 1
        if not fixed:
            break


def nearest_board_tag(col: int, row: int) -> str:
    best, best_d = "VCI", 999
    for (bc, br), tag in BOARD.items():
        d = abs(bc - col) + abs(br - row)
        if d < best_d:
            best, best_d = tag, d
    return best


def land_shape(gx: float, gy: float, grid_cols: int, grid_rows: int) -> bool:
    nx = (gx / grid_cols) * 2 - 1
    ny = (gy / grid_rows) * 2 - 1
    coast = (
        1.24
        + 0.075 * sin(nx * 7.1 + ny * 3.8)
        + 0.045 * cos(ny * 8.3 - nx * 2.7)
        + 0.025 * sin(nx * 14.0 + ny * 10.5)
    )
    return abs(nx) ** 4 + abs(ny) ** 4 <= coast


def cell_at_pixel(x: int, y: int) -> tuple[int, int]:
    local_x, local_y = x - LAND_X0, y - LAND_Y0
    bend_x = 2.6 * sin(local_y * 0.017 + local_x * 0.003) + 1.0 * cos(local_y * 0.043)
    bend_y = 2.2 * sin(local_x * 0.015 + local_y * 0.004) + 0.9 * cos(local_x * 0.039)
    return floor((local_x + bend_x) / CELL), floor((local_y + bend_y) / CELL)


def elevation_at(gx: float, gy: float) -> float:
    main_ridge = 12.5 + gy * 0.48 + 1.5 * sin(gy * 0.31)
    east_ridge = 35.5 - gy * 0.18 + 1.4 * cos(gy * 0.36)
    main_peak = exp(-((gx - main_ridge) / 2.05) ** 2)
    east_peak = exp(-((gx - east_ridge) / 1.8) ** 2)
    broad_upland = 0.5 * exp(-((gx - (main_ridge - 4.2)) / 5.0) ** 2)
    texture = 7 * sin(gx * 0.71 + gy * 0.42) + 4 * cos(gx * 0.37 - gy * 0.83)
    basin = 12 * exp(-(((gx - 27) / 5.5) ** 2 + ((gy - 13) / 4.5) ** 2))
    return max(34, min(238, 66 + 132 * main_peak + 76 * east_peak + 30 * broad_upland + texture - basin))


def moisture_at(gx: float, gy: float, grid_cols: int, grid_rows: int) -> float:
    main_ridge = 12.5 + gy * 0.48 + 1.5 * sin(gy * 0.31)
    windward = 0.17 if gx < main_ridge else -0.14
    broad_rain = 0.12 * cos((gy - 10) * 0.22) + 0.10 * sin(gx * 0.19 + gy * 0.13)
    coastal = 0.12 * (
        min(gx, grid_cols - 1 - gx, gy, grid_rows - 1 - gy) / 8
    )
    drought = 0.35 * exp(-(((gx - 40) / 6.0) ** 2 + ((gy - 18) / 5.0) ** 2))
    rain_shadow = 0.16 * exp(-(((gx - (main_ridge + 5)) / 4.5) ** 2))
    return max(0, min(1, 0.48 + windward + broad_rain + coastal - drought - rain_shadow))


def terrain_for_cell(gx: int, gy: int, grid_cols: int, grid_rows: int) -> str:
    center_x, center_y = gx + 0.5, gy + 0.5
    elevation = elevation_at(center_x, center_y)
    moisture = moisture_at(center_x, center_y, grid_cols, grid_rows)
    main_ridge = 12.5 + center_y * 0.48 + 1.5 * sin(center_y * 0.31)
    east_ridge = 35.5 - center_y * 0.18 + 1.4 * cos(center_y * 0.36)
    if elevation >= 184:
        return "mountain"
    if elevation >= 132:
        return "hills"
    if gx >= 37 and gy >= 15 and moisture < 0.49:
        return "desert"
    if gx <= 9 and gy >= 16 and moisture < 0.43:
        return "desert"
    if 23 <= gx <= 30 and 10 <= gy <= 16 and elevation < 105 and moisture > 0.47:
        return "marsh"
    if gy >= 16 and gx <= main_ridge and moisture > 0.59:
        return "jungle"
    if moisture >= 0.57:
        return "forest"
    if abs(gx + 0.5 - east_ridge) < 4 and elevation >= 105:
        return "hills"
    return "plains"


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
            if not land_shape(gx + 0.5, gy + 0.5, grid_cols, grid_rows):
                continue
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
    land_cells = {cell for cells in tag_cells.values() for cell in cells}

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
                coastal = (
                    gx == 0 or gy == 0 or gx == grid_cols - 1 or gy == grid_rows - 1
                    or (gx - 1, gy) not in land_cells or (gx + 1, gy) not in land_cells
                    or (gx, gy - 1) not in land_cells or (gx, gy + 1) not in land_cells
                )
                provinces[pid] = {
                    "id": pid,
                    "color": color,
                    "cx": cx,
                    "cy": cy,
                    "type": "land",
                    "terrain": terrain_for_cell(gx, gy, grid_cols, grid_rows),
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

    # Paint the warped province grid through an irregular coast mask.
    prov_img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    px = prov_img.load()
    for y in range(LAND_Y0, land_y1):
        for x in range(LAND_X0, land_x1):
            gx, gy = cell_at_pixel(x, y)
            if (gx, gy) in cell_pid and land_shape(
                (x - LAND_X0 + 0.5) / CELL,
                (y - LAND_Y0 + 0.5) / CELL,
                grid_cols,
                grid_rows,
            ):
                px[x, y] = provinces[cell_pid[(gx, gy)]]["color"]

    # Keep the existing 32-pixel naval province grid and group it into 19 regions.
    print("Building seas...")
    world_cols, world_rows = WIDTH // CELL, HEIGHT // CELL
    origin_x, origin_y = LAND_X0 // CELL, LAND_Y0 // CELL
    sea_cell_ids: dict[tuple[int, int], int] = {}
    sea_region_provinces: list[list[int]] = [[] for _ in range(19)]

    def sea_region_index(world_x: int, world_y: int) -> int:
        local_x, local_y = world_x - origin_x, world_y - origin_y

        def segment(position: int, count: int, length: int) -> int:
            return min(count - 1, max(0, position * count // length))

        if world_y < origin_y:
            return segment(world_x, 6, world_cols)
        if world_y >= origin_y + grid_rows:
            return 6 + segment(world_x, 6, world_cols)
        if world_x < origin_x:
            return 12 + segment(local_y, 4, grid_rows)
        if world_x >= origin_x + grid_cols:
            return 16 + segment(local_y, 3, grid_rows)
        distances = {
            "north": local_y,
            "south": grid_rows - 1 - local_y,
            "west": local_x,
            "east": grid_cols - 1 - local_x,
        }
        side = min(distances, key=distances.get)
        if side == "north":
            return segment(world_x, 6, world_cols)
        if side == "south":
            return 6 + segment(world_x, 6, world_cols)
        if side == "west":
            return 12 + segment(local_y, 4, grid_rows)
        return 16 + segment(local_y, 3, grid_rows)

    for world_y in range(world_rows):
        for world_x in range(world_cols):
            local_cell = (world_x - origin_x, world_y - origin_y)
            if local_cell in land_cells:
                continue
            pid = next_pid
            next_pid += 1
            color = unique_color(pid)
            provinces[pid] = {
                "id": pid,
                "color": color,
                "cx": world_x * CELL + CELL / 2,
                "cy": world_y * CELL + CELL / 2,
                "type": "sea",
                "coastal": False,
            }
            sea_cell_ids[(world_x, world_y)] = pid
            sea_region_provinces[sea_region_index(world_x, world_y)].append(pid)

    if next_pid != world_cols * world_rows + 1:
        raise RuntimeError(
            f"Expected one province per 32px map cell, got {next_pid - 1} provinces"
        )

    sea_pixel_totals: dict[int, list[float]] = {
        pid: [0.0, 0.0, 0.0] for pid in sea_cell_ids.values()
    }
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if px[x, y] != (0, 0, 0):
                continue
            key = (x // CELL, y // CELL)
            pid = sea_cell_ids.get(key)
            if pid is None:
                for radius in (1, 2):
                    candidates = [
                        sea_cell_ids.get((key[0] + dx, key[1] + dy))
                        for dx in range(-radius, radius + 1)
                        for dy in range(-radius, radius + 1)
                        if max(abs(dx), abs(dy)) == radius
                    ]
                    candidates = [candidate for candidate in candidates if candidate is not None]
                    if candidates:
                        pid = candidates[0]
                        break
            if pid is None:
                raise RuntimeError(f"Could not assign sea pixel at {x},{y}")
            px[x, y] = provinces[pid]["color"]
            totals = sea_pixel_totals[pid]
            totals[0] += x
            totals[1] += y
            totals[2] += 1

    sea_ids = list(sea_cell_ids.values())
    for pid, (sum_x, sum_y, count) in sea_pixel_totals.items():
        if not count:
            raise RuntimeError(f"Sea province {pid} has no raster pixels")
        provinces[pid]["cx"] = sum_x / count
        provinces[pid]["cy"] = sum_y / count
    print(f"  sea provinces: {len(sea_ids)} across {len(sea_region_provinces)} regions")

    repair_province_junctions(prov_img)
    all_color_to_id = {p["color"]: pid for pid, p in provinces.items()}
    sea_ids_set = set(sea_ids)
    for pid, province in provinces.items():
        if province["type"] == "land":
            province["coastal"] = False
    coastal_sea_neighbor: dict[int, int] = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pid = all_color_to_id.get(px[x, y])
            if pid is None:
                raise RuntimeError(f"Unassigned province pixel at {x},{y}")
            if provinces[pid]["type"] != "land":
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    neighbor = all_color_to_id[px[nx, ny]]
                    if neighbor in sea_ids_set:
                        provinces[pid]["coastal"] = True
                        coastal_sea_neighbor.setdefault(pid, neighbor)
                        break

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
    land_color_to_id = {
        p["color"]: pid for pid, p in provinces.items() if p["type"] == "land"
    }
    capital_ids = set(capital_province.values())
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pid = land_color_to_id.get(px[x, y])
            if pid is None:
                continue
            province = provinces[pid]
            terrain_name = "urban" if pid in capital_ids else province["terrain"]
            tpx[x, y] = TERRAIN_BMP_INDEX[terrain_name]
            geographic_x = (x - LAND_X0 + 0.5) / CELL
            geographic_y = (y - LAND_Y0 + 0.5) / CELL
            hpx[x, y] = int(elevation_at(geographic_x, geographic_y))

    # Preserve the game's indexed river segments rather than drawing arbitrary colors.
    vanilla_rivers = Image.open(VANILLA_MAP / "rivers.bmp").convert("P")
    if vanilla_rivers.width < land_x1 - LAND_X0 or vanilla_rivers.height < land_y1 - LAND_Y0:
        raise RuntimeError("Vanilla rivers.bmp is too small to provide a river network")
    river_indices = Image.frombytes("L", vanilla_rivers.size, vanilla_rivers.tobytes())
    river_patch = river_indices.crop((0, 0, land_x1 - LAND_X0, land_y1 - LAND_Y0))
    rivers_idx.paste(river_patch, (LAND_X0, LAND_Y0))
    rpx = rivers_idx.load()
    river_pixels = 0
    for y in range(LAND_Y0, land_y1):
        for x in range(LAND_X0, land_x1):
            if px[x, y] not in land_color_to_id:
                rpx[x, y] = 254
            elif rpx[x, y] not in (254, 255):
                river_pixels += 1
    if river_pixels < 1000:
        raise RuntimeError(f"River raster contains too few mapped river pixels: {river_pixels}")

    city_centers: dict[int, tuple[int, int, int]] = {}
    for sid, provs in state_provinces.items():
        tag = state_owner[sid]
        _, cap, size, _ = tag_meta[tag]
        if sid == cap:
            pid = capital_province[tag]
            radius = {"large": 3, "medium": 2, "small": 1}[size]
        else:
            center_x = sum(provinces[province_id]["cx"] for province_id in provs) / len(provs)
            center_y = sum(provinces[province_id]["cy"] for province_id in provs) / len(provs)
            pid = min(
                provs,
                key=lambda candidate: (provinces[candidate]["cx"] - center_x) ** 2
                + (provinces[candidate]["cy"] - center_y) ** 2,
            )
            radius = 1
        city_centers[pid] = (
            int(provinces[pid]["cx"]),
            int(provinces[pid]["cy"]),
            radius,
        )
    for cx, cy, radius in city_centers.values():
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x, y = cx + dx, cy + dy
                if 0 <= x < WIDTH and 0 <= y < HEIGHT and px[x, y] in land_color_to_id:
                    cpx[x, y] = 15

    print("Writing BMPs...")
    save_bmp_rgb(map_dir / "provinces.bmp", prov_img)
    save_bmp_indexed(map_dir / "terrain.bmp", terrain_idx, terrain_pal)
    save_bmp_indexed(map_dir / "rivers.bmp", rivers_idx, rivers_pal, 0, 0)
    gray_pal = [v for i in range(256) for v in (i, i, i)]
    save_bmp_indexed(map_dir / "heightmap.bmp", height_idx, gray_pal)
    save_bmp_indexed(map_dir / "cities.bmp", cities_idx, cities_pal)
    normal_map = Image.new("RGB", (NORMAL_W, NORMAL_H))
    normal_pixels = normal_map.load()
    for y in range(NORMAL_H):
        y0, y1 = max(0, y * 2 - 2), min(HEIGHT - 1, y * 2 + 2)
        for x in range(NORMAL_W):
            x0, x1 = max(0, x * 2 - 2), min(WIDTH - 1, x * 2 + 2)
            nx = -(hpx[x1, y * 2] - hpx[x0, y * 2]) * 0.06
            ny = -(hpx[x * 2, y1] - hpx[x * 2, y0]) * 0.06
            length = (nx * nx + ny * ny + 1) ** 0.5
            normal_pixels[x, y] = (
                int((nx / length + 1) * 127.5),
                int((ny / length + 1) * 127.5),
                int((1 / length + 1) * 127.5),
            )
    save_bmp_rgb(map_dir / "world_normal.bmp", normal_map)
    trees_w, trees_h = max(64, WIDTH * 1650 // 5632), max(64, HEIGHT * 600 // 2048)
    trees_idx = Image.new("L", (trees_w, trees_h), 0)
    tree_pixels = trees_idx.load()
    for y in range(trees_h):
        for x in range(trees_w):
            map_x = min(WIDTH - 1, int((x + 0.5) * WIDTH / trees_w))
            map_y = min(HEIGHT - 1, int((y + 0.5) * HEIGHT / trees_h))
            pid = land_color_to_id.get(px[map_x, map_y])
            if pid is None:
                continue
            biome = provinces[pid]["terrain"]
            tree_types = TREE_BIOME_INDEX.get(biome)
            if not tree_types:
                continue
            canopy = (
                sin(x * 0.071 + y * 0.037)
                + cos(y * 0.089 - x * 0.021)
                + 0.5 * sin((x + y) * 0.13)
            )
            if canopy > -0.28:
                tree_pixels[x, y] = tree_types[(x + 3 * y) % len(tree_types)]
    save_bmp_indexed(map_dir / "trees.bmp", trees_idx, load_vanilla_palette("trees.bmp"))

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
        if src.exists() and not (map_dir / fname).exists():
            (map_dir / fname).write_bytes(src.read_bytes())
    (map_dir / "ambient_object.txt").write_text(
        'type={\n\ttype="ambient_wind_entity"\n\tuse_animation=no\n\talways_visible=yes\n\tobject={\n\t\tname="ambient_wind"\n\t\tposition={ 0 0 0 }\n\t\trotation={ 0 0 0 }\n\t}\n}\n',
        encoding="utf-8",
    )
    ustack, buildings, supply = [], [], []
    for pid, p in provinces.items():
        for slot, dx, dy in UNIT_STACK_OFFSETS:
            ustack.append(
                f"{pid};{slot};{p['cx'] + dx:.2f};12.00;{p['cy'] + dy:.2f};0.00;0.50"
            )
    (map_dir / "unitstacks.txt").write_text("\n".join(ustack) + "\n", encoding="utf-8")
    province_to_state = {
        pid: sid for sid, provs in state_provinces.items() for pid in provs
    }
    for sid, provs in state_provinces.items():
        tag = state_owner[sid]
        cap = tag_meta[tag][1]
        pid = capital_province.get(tag, provs[0]) if sid == cap else provs[0]
        p = provinces[pid]
        x, y = p["cx"], p["cy"]
        for btype, n in (("industrial_complex", 2), ("arms_factory", 1)):
            for i in range(n):
                buildings.append(f"{sid};{btype};{x+i*0.3:.2f};12.00;{y+i*0.2:.2f};{i*0.4:.2f};0")
        if sid == cap:
            level = {"large": 3, "medium": 2, "small": 1}[size]
            supply.append(f"{level} {pid}")
    for pid, sea_pid in sorted(coastal_sea_neighbor.items()):
        province = provinces[pid]
        sid = province_to_state[pid]
        buildings.append(
            f"{sid};naval_base_spawn;{province['cx']:.2f};10.00;"
            f"{province['cy']:.2f};0.00;{sea_pid}"
        )
    (map_dir / "buildings.txt").write_text("\n".join(buildings) + "\n", encoding="utf-8")
    (map_dir / "supply_nodes.txt").write_text("\n".join(supply) + "\n", encoding="utf-8")

    land_neighbors: dict[int, set[int]] = defaultdict(set)
    state_by_province = {
        pid: sid for sid, provs in state_provinces.items() for pid in provs
    }
    country_by_province = {
        pid: state_owner[sid] for pid, sid in state_by_province.items()
    }
    country_borders: set[tuple[str, str]] = set()
    for (gx, gy), pid in cell_pid.items():
        for neighbor_cell in ((gx + 1, gy), (gx, gy + 1)):
            neighbor_pid = cell_pid.get(neighbor_cell)
            if neighbor_pid is None:
                continue
            land_neighbors[pid].add(neighbor_pid)
            land_neighbors[neighbor_pid].add(pid)
            tag, neighbor_tag = country_by_province[pid], country_by_province[neighbor_pid]
            if neighbor_tag is not None and neighbor_tag != tag:
                country_borders.add(tuple(sorted((tag, neighbor_tag))))

    capital_by_country = {
        tag: capital_province[tag] for tag, _, _, _ in COUNTRIES
    }
    railways = []
    for left, right in sorted(country_borders):
        start, goal = capital_by_country[left], capital_by_country[right]
        queue = [start]
        previous = {start: None}
        for current in queue:
            if current == goal:
                break
            for neighbor in sorted(land_neighbors[current]):
                if neighbor not in previous:
                    previous[neighbor] = current
                    queue.append(neighbor)
        if goal not in previous:
            raise RuntimeError(f"No land railway route between {left} and {right}")
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        level = 3 if left in {"VCI", "KRZ", "SHF"} or right in {"VCI", "KRZ", "SHF"} else 2
        railways.append(f"{level} {len(path)} " + " ".join(map(str, path)))
    (map_dir / "railways.txt").write_text("\n\n".join(railways) + "\n", encoding="utf-8")

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
        coastal_buildings = "".join(
            f"\n\t\t\t{province_id} = {{\n\t\t\t\tnaval_base = 1\n\t\t\t}}"
            for province_id in provs
            if provinces[province_id]["coastal"]
        )
        air = "\n\t\t\tair_base = 1" if is_cap else ""
        content = f'''state={{
\tid={sid}
\tname="{name_key}"
{resources_block(tag, sid)}
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
        (states_dir / f"{sid}-{tag}.txt").write_text(content, encoding="utf-8")

    loc_sr = ["l_russian:"]
    strategic_region_provinces = []
    sr_id = 1
    for tag, cap, size, ru_name in COUNTRIES:
        provs = []
        for sid in tag_states[tag]:
            provs.extend(state_provinces[sid])
        strategic_region_provinces.append(provs)
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "{ru_name}"')
        (sr_dir / f"{sr_id}-{tag}.txt").write_text(
            f'strategic_region={{\n\tid={sr_id}\n\tname="STRATEGICREGION_{sr_id}"\n\tprovinces={{\n\t\t{" ".join(map(str, provs))}\n\t}}\n{WEATHER}}}\n',
            encoding="utf-8",
        )
        sr_id += 1
    for i, region_provinces in enumerate(sea_region_provinces):
        strategic_region_provinces.append(region_provinces)
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "Sea {i + 1}"')
        (sr_dir / f"{sr_id}-Sea-{i}.txt").write_text(
            f'strategic_region={{\n\tid={sr_id}\n\tname="STRATEGICREGION_{sr_id}"\n\tprovinces={{\n\t\t{" ".join(map(str, region_provinces))}\n\t}}\n{WEATHER}}}\n',
            encoding="utf-8",
        )
        sr_id += 1

    weather_positions = []
    for region_id, region_provinces in enumerate(strategic_region_provinces, 1):
        x = sum(provinces[pid]["cx"] for pid in region_provinces) / len(region_provinces)
        y = sum(provinces[pid]["cy"] for pid in region_provinces) / len(region_provinces)
        weather_positions.append(f"{region_id};{x:.2f};10.00;{y:.2f};small")
    (map_dir / "weatherpositions.txt").write_text(
        "\n".join(weather_positions) + "\n", encoding="utf-8"
    )

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
