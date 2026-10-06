# -*- coding: utf-8 -*-
"""
HOI4 Map Generator v2 — «Казуалия»
Organic coastline, varied heightmap, rivers, biomes, interesting country layout.
Preserves: 24 tags, capital state IDs 1-24, ~127 states, no X-crossings.
"""
from __future__ import annotations

import math
import random
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from build_resources import resources_block

ROOT = Path(__file__).resolve().parents[1]
# Fallback if vanilla path missing (palette only)
VANILLA_MAP = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map")
if not VANILLA_MAP.exists():
    VANILLA_MAP = Path("/tmp/vanilla_map_stub")  # will use hardcoded palettes

WIDTH, HEIGHT = 2048, 1024
NORMAL_W, NORMAL_H = WIDTH // 2, HEIGHT // 2
CELL = 18  # more detailed provinces while keeping capital and state IDs stable
RNG = random.Random(42)
np.random.seed(42)

# ─── Countries (tag, capital_state_id, size, russian name) ───────────────────
COUNTRIES = [
    ("VCI", 1, "large", "Великая Казуальная Империя"),
    ("SOY", 2, "medium", "Соевая Республика"),
    ("BTR", 3, "medium", "Чёрная Тартария"),
    ("KRZ", 4, "large", "Красная Земля"),
    ("KZS", 5, "small", "Казачьи штаты"),
    ("MUS", 6, "medium", "Королевство Муси"),
    ("TRF", 7, "medium", "Травинная Федерация"),
    ("ZLD", 8, "medium", "Демократический Зеленодольск"),
    ("ISL", 9, "medium", "Исламская Республика"),
    ("CLB", 10, "medium", "Челяба"),
    ("ADL", 11, "small", "Айдалия"),
    ("DMK", 12, "medium", "Дмитро-Княжество"),
    ("FDP", 13, "medium", "Федерация Депутатов"),
    ("CRE", 14, "medium", "Чёрная Республика"),
    ("SVA", 15, "medium", "Северная Ассамблея"),
    ("ART", 16, "medium", "Айратская Республика"),
    ("KMS", 17, "medium", "Камильское Содружество"),
    ("ZNS", 18, "medium", "Зайнутдиновский Союз"),
    ("ZKR", 19, "medium", "Республика Закария"),
    ("ZML", 20, "small", "Земля Замалия"),
    ("NBL", 21, "medium", "Новая Булатия"),
    ("ISG", 22, "small", "Республика Исмагил"),
    ("HRL", 23, "medium", "Харитоновская Лига"),
    ("SHF", 24, "large", "Шарафутдиновская Федерация"),
]

SIZE_STATES = {"large": 10, "medium": 5, "small": 3}

# Macro layout (col 0..9, row 0..6) — more interesting, not pure rectangle
# North = high row
BOARD = {
    # North coast / scientific
    (2, 6): "SVA", (3, 6): "SVA", (4, 6): "CLB", (5, 6): "CLB", (6, 6): "ART", (7, 6): "ART",
    # Northwest
    (0, 5): "KMS", (1, 5): "KMS", (2, 5): "ZLD", (3, 5): "ZLD",
    # Center-north / imperial core
    (4, 5): "VCI", (5, 5): "VCI", (6, 5): "NBL", (7, 5): "ZNS", (8, 5): "ZNS",
    # West
    (0, 4): "MUS", (1, 4): "MUS", (2, 4): "SOY", (3, 4): "SOY",
    (4, 4): "VCI", (5, 4): "FDP", (6, 4): "DMK", (7, 4): "DMK", (8, 4): "KRZ",
    # Southwest / green
    (0, 3): "ISL", (1, 3): "TRF", (2, 3): "TRF", (3, 3): "ZML",
    (4, 3): "ISG", (5, 3): "HRL", (6, 3): "HRL", (7, 3): "KRZ", (8, 3): "KRZ",
    # South-central
    (1, 2): "ADL", (2, 2): "ADL", (3, 2): "SHF", (4, 2): "SHF",
    (5, 2): "CRE", (6, 2): "CRE", (7, 2): "BTR", (8, 2): "BTR",
    # Far south
    (2, 1): "ZKR", (3, 1): "ZKR", (4, 1): "SHF", (5, 1): "SHF",
    (6, 1): "KZS", (7, 1): "KZS", (8, 1): "BTR",
    # Southeast peninsula
    (8, 0): "KZS", (7, 0): "KZS",
}

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


def value_noise(w: int, h: int, scale: float, octaves: int = 4) -> np.ndarray:
    """Simple multi-octave value noise."""
    result = np.zeros((h, w), dtype=np.float32)
    amp = 1.0
    freq = 1.0
    for _ in range(octaves):
        gw = max(2, int(w / (scale * freq)) + 2)
        gh = max(2, int(h / (scale * freq)) + 2)
        grid = np.random.rand(gh, gw).astype(np.float32)
        # bilinear upsample
        ys = np.linspace(0, gh - 1, h)
        xs = np.linspace(0, gw - 1, w)
        y0 = np.floor(ys).astype(int)
        x0 = np.floor(xs).astype(int)
        y1 = np.minimum(y0 + 1, gh - 1)
        x1 = np.minimum(x0 + 1, gw - 1)
        fy = (ys - y0)[:, None]
        fx = (xs - x0)[None, :]
        n00 = grid[y0[:, None], x0[None, :]]
        n10 = grid[y1[:, None], x0[None, :]]
        n01 = grid[y0[:, None], x1[None, :]]
        n11 = grid[y1[:, None], x1[None, :]]
        layer = (n00 * (1 - fx) + n01 * fx) * (1 - fy) + (n10 * (1 - fx) + n11 * fx) * fy
        result += layer * amp
        amp *= 0.5
        freq *= 2.0
    result = (result - result.min()) / (result.max() - result.min() + 1e-6)
    return result


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
        0, 0, 54, 40, w, h, 1, 24, 0, len(pixel_data), 2835, 2835, 0, 0,
    )
    path.write_bytes(header + pixel_data)


def save_bmp_indexed(
    path: Path,
    index_img: Image.Image,
    palette_rgb: list[int],
    colors_used: int = 256,
    colors_important: int | None = None,
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
        0, 0, off, 40, w, h, 1, 8, 0, len(pixel_bytes), 2835, 2835, 256, 256,
    )
    if colors_important is None:
        colors_important = colors_used
    header = header[:46] + struct.pack("<II", colors_used, colors_important) + header[54:]
    path.write_bytes(header + pal_bytes + pixel_bytes)


def load_vanilla_palette(name: str) -> list[int]:
    p = VANILLA_MAP / name
    if p.exists():
        im = Image.open(p)
        return (list(im.getpalette() or []) + [0] * 768)[:768]
    # Hardcoded fallbacks (approximate vanilla)
    if "terrain" in name:
        # plains=0, forest=1, hills=2, mountain=3, urban=7, marsh=9, desert=10, ocean=15
        return [0] * 768
    if "rivers" in name:
        return [0] * 768
    if "cities" in name:
        return [0] * 768
    if "trees" in name:
        return [0] * 768
    return [i // 3 for i in range(768)]


def count_x_crossings(img: Image.Image) -> int:
    pixels = np.asarray(img.convert("RGB"))
    a, b = pixels[:-1, :-1], pixels[:-1, 1:]
    c, d = pixels[1:, :-1], pixels[1:, 1:]
    four_distinct = (
        np.any(a != b, axis=2) & np.any(a != c, axis=2) & np.any(a != d, axis=2)
        & np.any(b != c, axis=2) & np.any(b != d, axis=2) & np.any(c != d, axis=2)
    )
    diagonal_cross = np.all(a == d, axis=2) & np.all(b == c, axis=2) & np.any(a != b, axis=2)
    return int(np.count_nonzero(four_distinct | diagonal_cross))


def repair_province_junctions(img: Image.Image) -> None:
    pixels = np.asarray(img.convert("RGB")).copy()
    h, w, _ = pixels.shape
    for _ in range(8):
        a, b = pixels[:-1, :-1], pixels[:-1, 1:]
        c, d = pixels[1:, :-1], pixels[1:, 1:]
        four_distinct = (
            np.any(a != b, axis=2) & np.any(a != c, axis=2) & np.any(a != d, axis=2)
            & np.any(b != c, axis=2) & np.any(b != d, axis=2) & np.any(c != d, axis=2)
        )
        diagonal_cross = (
            np.all(a == d, axis=2) & np.all(b == c, axis=2) & np.any(a != b, axis=2)
        )
        positions = np.argwhere(four_distinct | diagonal_cross)
        if not len(positions):
            break
        for y, x in positions:
            pixels[y + 1, x + 1] = pixels[y + 1, x]
        # Also repair junctions that wrap across the map's horizontal seam.
        left, right = pixels[:-1, 0], pixels[:-1, -1]
        left_below, right_below = pixels[1:, 0], pixels[1:, -1]
        wrapped = (
            np.all(left == right_below, axis=1)
            & np.all(right == left_below, axis=1)
            & np.any(left != right, axis=1)
        )
        pixels[np.flatnonzero(wrapped) + 1, 0] = pixels[np.flatnonzero(wrapped), -1]
    img.paste(Image.fromarray(pixels, "RGB"))


def nearest_board_tag(col: int, row: int) -> str:
    best, best_d = "VCI", 999
    for (bc, br), tag in BOARD.items():
        d = abs(bc - col) + abs(br - row)
        if d < best_d:
            best, best_d = tag, d
    return best


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

    # ─── 1. Generate organic landmask with noise ─────────────────────────────
    print("Generating organic landmass...")
    base = value_noise(WIDTH, HEIGHT, scale=180, octaves=5)
    # Elliptical continent bias
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    cx, cy = WIDTH * 0.52, HEIGHT * 0.48
    rx, ry = WIDTH * 0.38, HEIGHT * 0.32
    dist = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    # Peninsulas / bays via secondary noise
    detail = value_noise(WIDTH, HEIGHT, scale=90, octaves=4)
    land_score = (1.0 - dist * 0.92) + (base - 0.5) * 0.28 + (detail - 0.5) * 0.12
    # Stronger ocean margins + bays
    land_score[yy > HEIGHT * 0.72] -= 0.45 * ((yy[yy > HEIGHT * 0.72] / HEIGHT - 0.72) / 0.28)
    land_score[yy < HEIGHT * 0.12] -= 0.35 * ((0.12 - yy[yy < HEIGHT * 0.12] / HEIGHT) / 0.12)
    land_score[xx < WIDTH * 0.12] -= 0.40
    land_score[xx > WIDTH * 0.88] -= 0.40
    # Extra bay on south-east
    land_score[(xx > WIDTH * 0.65) & (yy > HEIGHT * 0.55)] -= 0.18
    landmask = land_score > 0.20

    # Clean small islands / lakes
    from scipy import ndimage  # optional, fallback if missing
    try:
        labeled, num = ndimage.label(landmask)
        sizes = ndimage.sum(landmask, labeled, range(1, num + 1))
        mask_size = sizes >= 400  # keep large components
        if num:
            landmask = (labeled > 0) & mask_size[np.maximum(labeled - 1, 0)]
        # Fill small lakes inside land
        inv = ~landmask
        labeled_i, num_i = ndimage.label(inv)
        sizes_i = ndimage.sum(inv, labeled_i, range(1, num_i + 1))
        border_labels = np.unique(np.concatenate((
            labeled_i[0, :], labeled_i[-1, :], labeled_i[:, 0], labeled_i[:, -1],
        )))
        small_labels = np.flatnonzero(sizes_i < 800) + 1
        lake_labels = small_labels[~np.isin(small_labels, border_labels)]
        if len(lake_labels):
            landmask[np.isin(labeled_i, lake_labels)] = True
    except ImportError:
        print("scipy not available — skipping morphological clean")

    # ─── 2. Grid cells over land ─────────────────────────────────────────────
    # Find bounding box of land
    ys, xs = np.where(landmask)
    if len(xs) == 0:
        raise RuntimeError("No land generated")
    LAND_X0 = max(0, int(xs.min()) - 8)
    LAND_Y0 = max(0, int(ys.min()) - 8)
    LAND_X1 = min(WIDTH, int(xs.max()) + 9)
    LAND_Y1 = min(HEIGHT, int(ys.max()) + 9)
    # Snap to CELL
    LAND_X0 = (LAND_X0 // CELL) * CELL
    LAND_Y0 = (LAND_Y0 // CELL) * CELL
    LAND_X1 = ((LAND_X1 + CELL - 1) // CELL) * CELL
    LAND_Y1 = ((LAND_Y1 + CELL - 1) // CELL) * CELL

    grid_cols = (LAND_X1 - LAND_X0) // CELL
    grid_rows = (LAND_Y1 - LAND_Y0) // CELL
    print(f"Land bbox grid {grid_cols}x{grid_rows} cells, CELL={CELL}")

    # Assign each land cell to a board country
    tag_cells: dict[str, list[tuple[int, int]]] = defaultdict(list)
    cell_is_land: dict[tuple[int, int], bool] = {}
    for gy in range(grid_rows):
        for gx in range(grid_cols):
            # sample center of cell
            cx = LAND_X0 + gx * CELL + CELL // 2
            cy = LAND_Y0 + gy * CELL + CELL // 2
            # majority of cell is land?
            x0, y0 = LAND_X0 + gx * CELL, LAND_Y0 + gy * CELL
            patch = landmask[y0 : y0 + CELL, x0 : x0 + CELL]
            is_land = patch.mean() > 0.45 if patch.size else False
            cell_is_land[(gx, gy)] = is_land
            if not is_land:
                continue
            # map to board coordinates (0..9 , 0..6)
            bcol = min(9, int(gx / max(1, grid_cols - 1) * 9.0))
            brow = 6 - min(6, int(gy / max(1, grid_rows - 1) * 6.0))
            tag = BOARD.get((bcol, brow)) or nearest_board_tag(bcol, brow)
            tag_cells[tag].append((gx, gy))

    # Ensure every country has cells
    for tag, _, _, _ in COUNTRIES:
        if not tag_cells[tag]:
            # steal nearest
            print(f"WARNING: no cells for {tag}, stealing")
            for other in tag_cells:
                if tag_cells[other]:
                    tag_cells[tag].append(tag_cells[other].pop())
                    break

    provinces: dict[int, dict] = {}
    cell_pid: dict[tuple[int, int], int] = {}
    state_provinces: dict[int, list[int]] = defaultdict(list)
    state_owner: dict[int, str] = {}
    state_names: dict[int, str] = {}
    capital_province: dict[str, int] = {}
    next_pid = 1

    # ─── 3. Create provinces (1 cell = 1 province) and distribute to states ──
    for tag, cap, size, ru_name in COUNTRIES:
        cells = sorted(tag_cells[tag], key=lambda c: (c[0], c[1]))
        if not cells:
            raise RuntimeError(f"No cells for {tag}")
        states = tag_states[tag]
        n_states = len(states)
        xs_list = sorted({c[0] for c in cells})
        chunks: list[list[tuple[int, int]]] = [[] for _ in range(n_states)]
        if len(xs_list) >= n_states:
            strip = max(1, (len(xs_list) + n_states - 1) // n_states)
            xmap = {x: min(n_states - 1, i // strip) for i, x in enumerate(xs_list)}
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
            state_names[sid] = f"{ru_name} — Столица" if is_cap else f"{ru_name} — Регион {si}"
            created = []
            for gx, gy in sorted(chunks[si], key=lambda c: (c[1], c[0])):
                pid = next_pid
                next_pid += 1
                color = unique_color(pid)
                cx = LAND_X0 + gx * CELL + CELL / 2
                cy = LAND_Y0 + gy * CELL + CELL / 2
                # coastal if any edge of cell touches sea
                x0, y0 = LAND_X0 + gx * CELL, LAND_Y0 + gy * CELL
                coastal = False
                for edge in [
                    landmask[y0, x0 : x0 + CELL],
                    landmask[min(HEIGHT - 1, y0 + CELL - 1), x0 : x0 + CELL],
                    landmask[y0 : y0 + CELL, x0],
                    landmask[y0 : y0 + CELL, min(WIDTH - 1, x0 + CELL - 1)],
                ]:
                    if not edge.all():
                        coastal = True
                        break
                provinces[pid] = {
                    "id": pid,
                    "color": color,
                    "cx": cx,
                    "cy": cy,
                    "type": "land",
                    "coastal": coastal,
                    "gx": gx,
                    "gy": gy,
                }
                cell_pid[(gx, gy)] = pid
                state_provinces[sid].append(pid)
                created.append(pid)
            if is_cap and created:
                center_x = sum(provinces[p]["cx"] for p in created) / len(created)
                center_y = sum(provinces[p]["cy"] for p in created) / len(created)
                capital_province[tag] = min(
                    created,
                    key=lambda p: (provinces[p]["cx"] - center_x) ** 2
                    + (provinces[p]["cy"] - center_y) ** 2,
                )

    # ─── 4. Paint provinces.bmp ──────────────────────────────────────────────
    province_pixels = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    for (gx, gy), pid in cell_pid.items():
        color = provinces[pid]["color"]
        x0 = LAND_X0 + gx * CELL
        y0 = LAND_Y0 + gy * CELL
        x1, y1 = min(WIDTH, x0 + CELL), min(HEIGHT, y0 + CELL)
        patch = province_pixels[y0:y1, x0:x1]
        patch[landmask[y0:y1, x0:x1]] = color

    # ─── 5. Seas: any remaining black pixel becomes sea, split into 6 zones ──
    print("Building seas...")
    mid_x = WIDTH // 2
    mid_y = HEIGHT // 2
    # Collect all unpainted pixels
    sea_candidates = np.all(province_pixels == 0, axis=2)
    sea_y, sea_x = np.where(sea_candidates)
    print(f"  unpainted (sea candidates): {len(sea_x)}")
    zones = {
        "nw": (sea_y < mid_y) & (sea_x < mid_x),
        "ne": (sea_y < mid_y) & (sea_x >= mid_x),
        "sw": (sea_y >= mid_y) & (sea_x < WIDTH // 3),
        "mid_w": (sea_y >= mid_y) & (sea_x >= WIDTH // 3) & (sea_x < mid_x),
        "mid_e": (sea_y >= mid_y) & (sea_x >= mid_x) & (sea_x < 2 * WIDTH // 3),
        "se": (sea_y >= mid_y) & (sea_x >= 2 * WIDTH // 3),
    }
    sea_ids = []
    for key, mask in zones.items():
        coords = np.flatnonzero(mask)
        if not len(coords):
            continue
        parts = [coords]
        if len(coords) > 200000:
            midpoint = (int(sea_x[coords].min()) + int(sea_x[coords].max())) / 2
            left = coords[sea_x[coords] < midpoint]
            right = coords[sea_x[coords] >= midpoint]
            parts = [part for part in (left, right) if len(part)]
        for pi, part in enumerate(parts):
            pid = next_pid
            next_pid += 1
            color = unique_color(pid)
            indices = part
            ycoords, xcoords = sea_y[indices], sea_x[indices]
            province_pixels[ycoords, xcoords] = color
            provinces[pid] = {
                "id": pid, "color": color,
                "cx": float(xcoords.mean()),
                "cy": float(ycoords.mean()),
                "type": "sea", "coastal": False,
            }
            sea_ids.append(pid)
            print(f"  sea {key}{pi if len(parts)>1 else ''}: pid={pid} pixels={len(indices)}")

    leftovers = np.all(province_pixels == 0, axis=2)
    if leftovers.any():
        print(f"WARNING leftover pixels {int(leftovers.sum())}")
        if sea_ids:
            fill = provinces[sea_ids[0]]["color"]
            province_pixels[leftovers] = fill
        else:
            # create one emergency sea
            pid = next_pid
            next_pid += 1
            color = unique_color(pid)
            province_pixels[leftovers] = color
            provinces[pid] = {"id": pid, "color": color, "cx": WIDTH/2, "cy": HEIGHT/2, "type": "sea", "coastal": False}
            sea_ids.append(pid)
    prov_img = Image.fromarray(province_pixels, "RGB")
    px = prov_img.load()

    xc = count_x_crossings(prov_img)
    print(f"Initial X-crossings before junction repair: {xc}")

    # ─── 6. Heightmap + terrain + rivers ─────────────────────────────────────
    print("Generating heightmap & terrain...")
    height_noise = value_noise(WIDTH, HEIGHT, scale=120, octaves=5)
    mountain_noise = value_noise(WIDTH, HEIGHT, scale=60, octaves=3)
    # Mountain ranges: central spine + northern highlands
    spine = np.exp(-((xx - WIDTH * 0.55) / (WIDTH * 0.12)) ** 2) * np.exp(-((yy - HEIGHT * 0.45) / (HEIGHT * 0.25)) ** 2)
    north_high = np.clip((0.35 - dist) * 2.5, 0, 1) * (yy < HEIGHT * 0.4)

    height = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    height[landmask] = 95 + height_noise[landmask] * 70 + spine[landmask] * 60 + north_high[landmask] * 40
    height[landmask] += (mountain_noise[landmask] - 0.5) * 35
    height[~landmask] = 40  # underwater
    height = np.clip(height, 0, 255).astype(np.uint8)

    # Terrain indices (approximate vanilla: 0=plains, 1=forest, 2=hills, 3=mountain, 7=urban, 9=marsh, 10=desert, 15=ocean)
    terrain_idx = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)  # ocean
    rivers_idx = np.full((HEIGHT, WIDTH), 254, dtype=np.uint8)
    cities_idx = np.full((HEIGHT, WIDTH), 0, dtype=np.uint8)

    terrain_idx[landmask] = 0
    latitude = yy / HEIGHT
    forest = landmask & (height_noise > 0.56) & (height < 155)
    marsh = landmask & (height_noise < 0.25) & (latitude > 0.55)
    desert = landmask & (latitude < 0.36) & (height_noise > 0.5) & (height <= 145)
    jungle = landmask & (latitude > 0.62) & (height_noise > 0.56) & (height < 155)
    hills = landmask & (height > 145)
    mountains = landmask & (height > 180)
    terrain_idx[forest] = 1
    terrain_idx[marsh] = 9
    terrain_idx[desert] = 3
    terrain_idx[jungle] = 22
    terrain_idx[hills] = 2
    terrain_idx[mountains] = 11

    # Capitals → urban
    for tag, pid in capital_province.items():
        cx, cy = int(provinces[pid]["cx"]), int(provinces[pid]["cy"])
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                x, y = cx + dx, cy + dy
                if 0 <= x < WIDTH and 0 <= y < HEIGHT and landmask[y, x]:
                    terrain_idx[y, x] = 13
                    cities_idx[y, x] = 15

    # Simple rivers: from high points to sea
    print("Carving rivers...")
    river_seeds = np.argwhere(landmask & (height > 145))
    if len(river_seeds):
        coast_distance = ndimage.distance_transform_edt(landmask)
        for river_index in range(48):
            y, x = map(int, river_seeds[(river_index * 7919) % len(river_seeds)])
            path = []
            visited = {(x, y)}
            for _ in range(400):
                path.append((x, y))
                options = []
                for dy, dx in (
                    (-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (-1, 1), (1, -1), (1, 1),
                ):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < WIDTH and 0 <= ny < HEIGHT
                        and landmask[ny, nx] and (nx, ny) not in visited
                    ):
                        score = float(height[ny, nx]) + 0.2 * float(coast_distance[ny, nx])
                        options.append((score, float(coast_distance[ny, nx]), ny, nx))
                if not options:
                    break
                _, distance, y, x = min(options)
                visited.add((x, y))
                if distance <= 1:
                    path.append((x, y))
                    break
            for i, (rx, ry) in enumerate(path):
                rivers_idx[ry, rx] = 0 if i % 3 else 1
                if landmask[ry, rx]:
                    height[ry, rx] = min(height[ry, rx], 110)
    else:
        print("WARNING no highland river sources found")

    if not river_seeds.size:
        # A deterministic lowland fallback still draws channels to the coast.
        for start_y in range(HEIGHT // 3, HEIGHT * 2 // 3, 32):
            candidates = np.flatnonzero(landmask[start_y])
            if not len(candidates):
                continue
            x = int(candidates[len(candidates) // 2])
            y = start_y
            for step in range(200):
                if not landmask[y, x]:
                    break
                rivers_idx[y, x] = 0 if step % 3 else 1
                next_y = min(HEIGHT - 1, y + 1)
                while next_y < HEIGHT - 1 and landmask[next_y, x]:
                    next_y += 1
                if next_y == y:
                    break
                y = next_y
        if not np.any(~np.isin(rivers_idx, (254, 255)) & landmask):
            print("WARNING no river pixels were generated")

    # Keep one terrain index per province so definition.csv and terrain.bmp agree.
    capital_ids = set(capital_province.values())
    province_terrain = {}
    for pid, province in provinces.items():
        if province["type"] != "land":
            continue
        x0 = int(province["gx"]) * CELL + LAND_X0
        y0 = int(province["gy"]) * CELL + LAND_Y0
        x1, y1 = min(WIDTH, x0 + CELL), min(HEIGHT, y0 + CELL)
        land_patch = landmask[y0:y1, x0:x1]
        terrain_patch = terrain_idx[y0:y1, x0:x1][land_patch]
        indices, counts = np.unique(terrain_patch, return_counts=True)
        index = 13 if pid in capital_ids else int(indices[np.argmax(counts)])
        province_terrain[pid] = index
        terrain_idx[y0:y1, x0:x1][land_patch] = index

    repair_province_junctions(prov_img)
    px = prov_img.load()
    color_to_pid = {p["color"]: pid for pid, p in provinces.items()}
    province_array = np.asarray(prov_img)
    packed = (
        (province_array[:, :, 0].astype(np.uint32) << 16)
        | (province_array[:, :, 1].astype(np.uint32) << 8)
        | province_array[:, :, 2].astype(np.uint32)
    )
    packed_to_pid = {
        (color[0] << 16) | (color[1] << 8) | color[2]: pid
        for pid, color in ((pid, province["color"]) for pid, province in provinces.items())
    }
    unique_colors, inverse = np.unique(packed, return_inverse=True)
    terrain_by_color = np.full(len(unique_colors), 255, dtype=np.uint8)
    unique_index = {int(color): index for index, color in enumerate(unique_colors)}
    for packed_color, pid in packed_to_pid.items():
        if provinces[pid]["type"] == "land":
            terrain_by_color[unique_index[packed_color]] = province_terrain[pid]
    terrain_idx = terrain_by_color[inverse].reshape(HEIGHT, WIDTH)
    rivers_idx[terrain_idx == 255] = 254
    final_xc = count_x_crossings(prov_img)
    print(f"Verified X-crossings after junction repair: {final_xc}")
    if final_xc:
        raise RuntimeError(f"Province junction repair left {final_xc} X-crossings")

    for province in provinces.values():
        if province["type"] == "land":
            province["coastal"] = False
    sea_colors = np.asarray([
        (color[0] << 16) | (color[1] << 8) | color[2]
        for pid, color in ((pid, p["color"]) for pid, p in provinces.items())
        if provinces[pid]["type"] == "sea"
    ], dtype=np.uint32)
    coastal_spawn_by_pid: dict[int, tuple[float, float, int]] = {}
    for center, neighbor, x_offset, y_offset in (
        (packed[:, :-1], packed[:, 1:], 0, 0),
        (packed[:, 1:], packed[:, :-1], 1, 0),
        (packed[:-1, :], packed[1:, :], 0, 0),
        (packed[1:, :], packed[:-1, :], 0, 1),
    ):
        sea_adjacent = np.isin(neighbor, sea_colors)
        if not sea_adjacent.any():
            continue
        land_colors = center[sea_adjacent]
        adjacent_seas = neighbor[sea_adjacent]
        pairs = np.column_stack((land_colors, adjacent_seas))
        _, first_indices = np.unique(pairs, axis=0, return_index=True)
        adjacent_positions = np.argwhere(sea_adjacent)
        for index in first_indices:
            land_color, sea_color = map(int, pairs[index])
            pid = packed_to_pid.get(land_color)
            sea_pid = packed_to_pid.get(sea_color)
            if pid is None or sea_pid is None or provinces[pid]["type"] != "land":
                continue
            row, col = adjacent_positions[index]
            coastal_spawn_by_pid.setdefault(
                pid, (float(col + x_offset) + 0.5, float(row + y_offset) + 0.5, sea_pid)
            )
    for pid, province in provinces.items():
        if province["type"] == "land":
            province["coastal"] = pid in coastal_spawn_by_pid

    # ─── 7. Write BMPs ───────────────────────────────────────────────────────
    print("Writing BMPs...")
    save_bmp_rgb(map_dir / "provinces.bmp", prov_img)

    terrain_pal = load_vanilla_palette("terrain.bmp")
    rivers_pal = load_vanilla_palette("rivers.bmp")
    cities_pal = load_vanilla_palette("cities.bmp")
    gray_pal = [v for i in range(256) for v in (i, i, i)]

    save_bmp_indexed(map_dir / "terrain.bmp", Image.fromarray(terrain_idx, "L"), terrain_pal)
    save_bmp_indexed(map_dir / "heightmap.bmp", Image.fromarray(height, "L"), gray_pal)
    save_bmp_indexed(
        map_dir / "rivers.bmp",
        Image.fromarray(rivers_idx, "L"),
        rivers_pal,
        colors_used=0,
    )
    save_bmp_indexed(map_dir / "cities.bmp", Image.fromarray(cities_idx, "L"), cities_pal)
    grad_y, grad_x = np.gradient(height.astype(np.float32))
    nx = -grad_x[::2, ::2] * 0.08
    ny = -grad_y[::2, ::2] * 0.08
    nz = np.ones_like(nx)
    normal_len = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack(
        (
            (nx / normal_len + 1) * 127.5,
            (ny / normal_len + 1) * 127.5,
            (nz / normal_len + 1) * 127.5,
        ),
        axis=-1,
    ).clip(0, 255).astype(np.uint8)
    save_bmp_rgb(map_dir / "world_normal.bmp", Image.fromarray(normal, "RGB"))
    tw, th = max(64, WIDTH * 1650 // 5632), max(64, HEIGHT * 600 // 2048)
    trees = np.zeros((th, tw), dtype=np.uint8)
    for ty in range(th):
        my = min(HEIGHT - 1, int((ty + 0.5) * HEIGHT / th))
        for tx in range(tw):
            mx = min(WIDTH - 1, int((tx + 0.5) * WIDTH / tw))
            if terrain_idx[my, mx] == 1:
                trees[ty, tx] = 3 + (tx + ty) % 2
            elif terrain_idx[my, mx] == 22:
                trees[ty, tx] = 7 if (tx + ty) % 2 == 0 else 10
    save_bmp_indexed(map_dir / "trees.bmp", Image.fromarray(trees, "L"), load_vanilla_palette("trees.bmp"))

    # ─── 8. definition.csv + rest ────────────────────────────────────────────
    lines = ["0;0;0;0;land;false;unknown;0"]
    for pid in sorted(provinces):
        p = provinces[pid]
        r, g, b = p["color"]
        if p["type"] == "sea":
            lines.append(f"{pid};{r};{g};{b};sea;false;ocean;0")
        else:
            coastal = "true" if p["coastal"] else "false"
            # terrain type for definition
            terr = {
                0: "plains", 1: "forest", 2: "hills", 3: "desert",
                9: "marsh", 11: "mountain", 13: "urban", 22: "jungle",
            }[province_terrain[pid]]
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
            if fname == "adjacency_rules.txt":
                normalized = "\n".join(
                    line.rstrip() for line in src.read_text(encoding="utf-8").splitlines()
                )
                (map_dir / fname).write_text(normalized + "\n", encoding="utf-8")
            else:
                (map_dir / fname).write_bytes(src.read_bytes())
        else:
            (map_dir / fname).write_text("", encoding="utf-8")
    (map_dir / "ambient_object.txt").write_text(
        'type={\n\ttype="ambient_wind_entity"\n\tuse_animation=no\n\talways_visible=yes\n\tobject={\n\t\tname="ambient_wind"\n\t\tposition={ 0 0 0 }\n\t\trotation={ 0 0 0 }\n\t}\n}\n',
        encoding="utf-8",
    )
    weather_positions = []

    # unitstacks / buildings / supply
    ustack, buildings, supply = [], [], []
    unit_slots = (
        (0, 0.0, 0.0), (1, 0.5, -2.5), (2, 3.0, -2.5), (3, -2.0, 0.0),
        (4, 4.0, -0.5), (5, -3.0, 2.0), (6, 2.5, 2.0), (7, 0.0, 3.0),
        (9, -1.5, -3.0), (10, 1.5, -3.5), (21, 5.0, 1.0), (22, -5.0, 1.0),
        (23, 3.5, 3.5), (24, -3.5, 3.5), (25, 0.5, 5.0), (26, -0.5, -5.0),
        (27, 6.0, -1.0), (28, -6.0, -1.0), (38, 0.0, -1.0),
    )
    def position_in_province(pid: int, x: float, y: float) -> tuple[float, float]:
        color = provinces[pid]["color"]
        ix, iy = int(x), int(y)
        if 0 <= ix < WIDTH and 0 <= iy < HEIGHT and px[ix, iy] == color:
            return x, y
        for radius in range(1, CELL + 1):
            candidates = []
            for cy in range(max(0, iy - radius), min(HEIGHT, iy + radius + 1)):
                for cx in range(max(0, ix - radius), min(WIDTH, ix + radius + 1)):
                    if max(abs(cx - ix), abs(cy - iy)) == radius and px[cx, cy] == color:
                        candidates.append(((cx - x) ** 2 + (cy - y) ** 2, cx, cy))
            if candidates:
                _, cx, cy = min(candidates)
                return cx + 0.5, cy + 0.5
        raise RuntimeError(f"No map position found inside province {pid}")

    def stack_line(pid: int, slot: int, x: float, y: float) -> str:
        x, y = position_in_province(pid, x, y)
        return f"{pid};{slot};{x:.2f};12.00;{HEIGHT-y:.2f};0.00;0.50"

    for pid, p in provinces.items():
        for slot, dx, dy in unit_slots:
            ustack.append(stack_line(pid, slot, p["cx"] + dx, p["cy"] + dy))
        if p["type"] == "land" and p["coastal"]:
            for slot, dx in ((19, -1.0), (20, 1.0)):
                ustack.append(stack_line(pid, slot, p["cx"] + dx, p["cy"]))
    (map_dir / "unitstacks.txt").write_text("\n".join(ustack) + "\n", encoding="utf-8")
    for sid, provs in state_provinces.items():
        tag = state_owner[sid]
        cap = tag_meta[tag][1]
        pid = capital_province.get(tag, provs[0]) if sid == cap else provs[0]
        p = provinces[pid]
        x, y = p["cx"], p["cy"]
        for btype, n in (("industrial_complex", 2), ("arms_factory", 1)):
            for i in range(n):
                bx, by = position_in_province(pid, x + i * 0.3, y + i * 0.2)
                buildings.append(
                    f"{sid};{btype};{bx:.2f};12.00;{HEIGHT-by:.2f};{i*0.4:.2f};0"
                )
        if sid == cap:
            supply.append(f"1 {pid}")
        if any(provinces[p]["coastal"] for p in provs):
            for coast_pid in (p for p in provs if p in coastal_spawn_by_pid):
                bx, by, sea_pid = coastal_spawn_by_pid[coast_pid]
                buildings.append(
                    f"{sid};naval_base_spawn;{bx:.2f};10.00;{HEIGHT-by:.2f};0.00;{sea_pid}"
                )
    (map_dir / "buildings.txt").write_text("\n".join(buildings) + "\n", encoding="utf-8")
    (map_dir / "supply_nodes.txt").write_text("\n".join(supply) + "\n", encoding="utf-8")
    railways = []
    province_neighbors: dict[int, set[int]] = defaultdict(set)
    for (gx, gy), pid in cell_pid.items():
        for cell in ((gx + 1, gy), (gx, gy + 1)):
            neighbor = cell_pid.get(cell)
            if neighbor is not None:
                province_neighbors[pid].add(neighbor)
                province_neighbors[neighbor].add(pid)
    capital_ids = [capital_province[tag] for tag, _, _, _ in COUNTRIES]
    root_capital = capital_ids[0]
    for target in capital_ids[1:]:
        queue = [root_capital]
        previous = {root_capital: None}
        for current in queue:
            if current == target:
                break
            for neighbor in sorted(province_neighbors[current]):
                if neighbor not in previous:
                    previous[neighbor] = current
                    queue.append(neighbor)
        if target in previous:
            path = []
            current = target
            while current is not None:
                path.append(current)
                current = previous[current]
            path.reverse()
            railways.append(f"2 {len(path)} " + " ".join(map(str, path)))
    (map_dir / "railways.txt").write_text("\n".join(railways) + "\n", encoding="utf-8")

    # history/states
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
            coastal_buildings = "".join(
                f"\n\t\t\t{cprov} = {{\n\t\t\t\tnaval_base = 2\n\t\t\t}}"
                for cprov in provs if provinces[cprov]["coastal"]
            )
        air = "\n\t\t\tair_base = 1" if is_cap else ""
        content = f'''state={{
\tid={sid}
\tname="{name_key}"
\tmanpower = {manpower}
\tstate_category = {cat}
{resources_block(tag, sid).rstrip()}
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

    # strategic regions
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
        loc_sr.append(f' STRATEGICREGION_{sr_id}:0 "Море {i}"')
        (sr_dir / f"{sr_id}-Sea-{i}.txt").write_text(
            f'strategic_region={{\n\tid={sr_id}\n\tname="STRATEGICREGION_{sr_id}"\n\tprovinces={{\n\t\t{pid}\n\t}}\n{WEATHER}}}\n',
            encoding="utf-8",
        )
        weather_x, weather_y = position_in_province(pid, provinces[pid]["cx"], provinces[pid]["cy"])
        weather_positions.append(f"{sr_id};{weather_x:.2f};10.00;{HEIGHT-weather_y:.2f};small")
        sr_id += 1

    for rid, tag, _, _, _ in [
        (index + 1, *country) for index, country in enumerate(COUNTRIES)
    ]:
        land_ids = [pid for sid in tag_states[tag] for pid in state_provinces[sid]]
        representative = land_ids[len(land_ids) // 2]
        wx, wy = position_in_province(
            representative, provinces[representative]["cx"], provinces[representative]["cy"]
        )
        weather_positions.append(f"{rid};{wx:.2f};10.00;{HEIGHT-wy:.2f};small")
    (map_dir / "weatherpositions.txt").write_text(
        "\n".join(sorted(weather_positions, key=lambda row: int(row.split(";")[0]))) + "\n",
        encoding="utf-8",
    )

    def write_yml(path: Path, rows: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\xef\xbb\xbf" + ("\n".join(rows) + "\n").encode("utf-8"))

    write_yml(ROOT / "localisation" / "russian" / "mk_states_l_russian.yml", loc_states)
    write_yml(ROOT / "localisation" / "russian" / "mk_strategic_regions_l_russian.yml", loc_sr)

    check = Image.open(map_dir / "provinces.bmp").convert("RGB")
    print(f"Verified X-crossings: {count_x_crossings(check)}")
    print(f"provinces={len(provinces)} land={sum(1 for p in provinces.values() if p['type']=='land')} sea={len(sea_ids)}")
    print(f"states={len(state_provinces)} sr={sr_id-1}")
    print("DONE — map v2 generated")


if __name__ == "__main__":
    main()
