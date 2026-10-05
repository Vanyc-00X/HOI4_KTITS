# -*- coding: utf-8 -*-
"""v0.3.9: wrap X-cross, state sites, empty adj rules, names, clean buildings."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 2048, 1024
MK_TAGS = [
    "VCI", "SOY", "BTR", "KRZ", "KZS", "MUS", "TRF", "ZLD", "ISL", "CLB",
    "ADL", "DMK", "FDP", "CRE", "SVA", "ART", "KMS", "ZNS", "ZKR", "ZML",
    "NBL", "ISG", "HRL", "SHF",
]


def write_bmp_bgr(path: Path, rgb_img: Image.Image):
    img = rgb_img.convert("RGB")
    w, h = img.size
    raw = img.tobytes()
    row_stride = (w * 3 + 3) & ~3
    pad = b"\x00" * (row_stride - w * 3)
    body = bytearray()
    for y in range(h - 1, -1, -1):
        row = bytearray()
        base = y * w * 3
        for x in range(w):
            i = base + x * 3
            r, g, b = raw[i], raw[i + 1], raw[i + 2]
            row.extend((b, g, r))
        body.extend(row)
        body.extend(pad)
    header = struct.pack(
        "<2sIHHIIiiHHIIiiii",
        b"BM",
        54 + len(body),
        0,
        0,
        54,
        40,
        w,
        h,
        1,
        24,
        0,
        len(body),
        2835,
        2835,
        0,
        0,
    )
    path.write_bytes(header + body)


def fix_wrap_x():
    """Eliminate wrap-around X-crossings by making x=0 and x=W-1 the same color per row."""
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    for y in range(HEIGHT):
        px[WIDTH - 1, y] = px[0, y]
    # also break any remaining 4-color corners
    fixed = 0
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            a, b = px[x, y], px[x + 1, y]
            c, d = px[x, y + 1], px[x + 1, y + 1]
            if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                px[x + 1, y + 1] = c
                fixed += 1
    write_bmp_bgr(ROOT / "map" / "provinces.bmp", im)
    # verify wrap
    im2 = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px2 = im2.load()
    wrap = 0
    for y in range(HEIGHT - 1):
        cols = {px2[WIDTH - 1, y], px2[0, y], px2[WIDTH - 1, y + 1], px2[0, y + 1]}
        a, b = px2[WIDTH - 1, y], px2[0, y]
        c, d = px2[WIDTH - 1, y + 1], px2[0, y + 1]
        if len(cols) == 4 or (a == d and b == c and a != b):
            wrap += 1
    left = sum(
        1
        for y in range(HEIGHT - 1)
        for x in range(WIDTH - 1)
        if len({px2[x, y], px2[x + 1, y], px2[x, y + 1], px2[x + 1, y + 1]}) == 4
    )
    print(f"wrap_x remaining={wrap} interior_4color={left} extra_fixed={fixed}")
    return im2


def load_definition():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(line.split(";"))
    return rows


def province_to_state():
    p2s = {}
    for sf in (ROOT / "history" / "states").glob("*.txt"):
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        for p in re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S).group(1).split():
            p2s[int(p)] = sid
    return p2s


def state_centers(im, rows):
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows[1:]}
    p2s = province_to_state()
    px = im.load()
    sums = defaultdict(lambda: [0.0, 0.0, 0])
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            pid = color_to_pid.get(px[x, y])
            if pid is None:
                continue
            sid = p2s.get(pid)
            if sid is None:
                continue
            s = sums[sid]
            s[0] += x
            s[1] += y
            s[2] += 1
    return {sid: (sx / n, sy / n) for sid, (sx, sy, n) in sums.items() if n}, color_to_pid, p2s


def rebuild_buildings(im, rows):
    """Keep naval ports; add air_base + rocket_site_spawn per state; no trailing blank line."""
    centers, color_to_pid, p2s = state_centers(im, rows)
    px = im.load()

    # existing naval lines — revalidate coords with inverted Y
    naval = []
    for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines():
        if "naval_base_spawn" not in l:
            continue
        parts = l.split(";")
        if len(parts) != 7:
            continue
        pid = int(parts[6])
        sid = p2s.get(pid)
        if sid is None:
            continue
        # find pixel in province
        found = None
        for y in range(0, HEIGHT, 2):
            for x in range(0, WIDTH, 2):
                if color_to_pid.get(px[x, y]) == pid:
                    found = (x + 0.5, y + 0.5)
                    break
            if found:
                break
        if not found:
            continue
        x, y_pil = found
        y_game = (HEIGHT - 1) - y_pil
        naval.append(f"{sid};naval_base_spawn;{x:.2f};10.00;{y_game:.2f};0.00;{pid}")

    state_ids = sorted({int(re.search(r"id\s*=\s*(\d+)", sf.read_text(encoding="utf-8")).group(1))
                        for sf in (ROOT / "history" / "states").glob("*.txt")})

    site_lines = []
    for sid in state_ids:
        cx, cy = centers.get(sid, (WIDTH / 2, HEIGHT / 2))
        y_game = (HEIGHT - 1) - cy
        # last field 0 for state buildings
        site_lines.append(f"{sid};air_base;{cx:.2f};12.00;{y_game:.2f};0.00;0")
        site_lines.append(f"{sid};rocket_site_spawn;{cx + 2:.2f};10.00;{y_game + 2:.2f};0.00;0")
        site_lines.append(f"{sid};special_project_facility_spawn;{cx - 2:.2f};10.00;{y_game - 2:.2f};0.00;0")

    # no trailing newline-only line: write with single final \n
    all_lines = naval + site_lines
    text = "\n".join(all_lines) + "\n"
    (ROOT / "map" / "buildings.txt").write_text(text, encoding="utf-8")
    print(f"buildings naval={len(naval)} sites={len(site_lines)} total={len(all_lines)}")


def empty_adjacency_rules():
    (ROOT / "map" / "adjacency_rules.txt").write_text(
        "# total conversion: no canal/strait rules\n", encoding="utf-8"
    )
    (ROOT / "map" / "adjacencies.csv").write_text(
        "From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment\n",
        encoding="utf-8",
    )
    print("adjacency rules cleared")


def write_names():
    d = ROOT / "common" / "names"
    d.mkdir(parents=True, exist_ok=True)
    male = " ".join(
        [
            "Ivan", "Petr", "Aleksei", "Dmitri", "Sergei", "Nikolai", "Andrei", "Mikhail",
            "Vladimir", "Yuri", "Oleg", "Roman", "Viktor", "Pavel", "Kirill", "Timur",
            "Ruslan", "Igor", "Boris", "Gleb", "Artem", "Lev", "Maksim", "Fedor",
        ]
    )
    female = " ".join(
        ["Anna", "Maria", "Elena", "Olga", "Natalia", "Irina", "Svetlana", "Tatiana", "Yulia", "Vera"]
    )
    surnames = " ".join(
        [
            "Ivanov", "Petrov", "Sidorov", "Kuznetsov", "Smirnov", "Popov", "Volkov",
            "Sokolov", "Lebedev", "Kozlov", "Novikov", "Morozov", "Pavlov", "Semenov",
            "Golubev", "Vinogradov", "Bogdanov", "Voronov", "Frolov", "Mikhailov",
        ]
    )
    blocks = [
        "default = {\n"
        f"\tmale = {{ names = {{ {male} }} }}\n"
        f"\tfemale = {{ names = {{ {female} }} }}\n"
        f"\tsurnames = {{ {surnames} }}\n"
        "\tcallsigns = { Falcon Bear Eagle Storm }\n"
        "\tprefix = o_operation\n"
        "\toperation = { 0 = { o_default_operation } }\n"
        "}\n"
    ]
    for tag in MK_TAGS:
        blocks.append(
            f"{tag} = {{\n"
            f"\tmale = {{ names = {{ {male} }} }}\n"
            f"\tfemale = {{ names = {{ {female} }} }}\n"
            f"\tsurnames = {{ {surnames} }}\n"
            "\tcallsigns = { Falcon Bear Eagle Storm }\n"
            "\tprefix = o_operation\n"
            "\toperation = { 0 = { o_default_operation } }\n"
            "}\n"
        )
    (d / "mk_names.txt").write_text("\n".join(blocks), encoding="utf-8")
    print(f"names for {len(MK_TAGS)} tags + default")


def bump():
    import runpy

    runpy.run_path(str(Path(__file__).with_name("register_mod.py")), run_name="__main__")
    for p in [
        ROOT / "descriptor.mod",
        ROOT / "mir_kazualnosti.mod",
        Path.home()
        / "Documents"
        / "Paradox Interactive"
        / "Hearts of Iron IV"
        / "mod"
        / "Mir_Kazualnosti.mod",
    ]:
        t = p.read_text(encoding="utf-8")
        for a in ("0.3.8", "0.3.7", "0.3.6"):
            t = t.replace(a, "0.3.9")
        p.write_text(t, encoding="utf-8")
    # also update register_mod source version
    reg = Path(__file__).with_name("register_mod.py")
    reg.write_text(reg.read_text(encoding="utf-8").replace("0.3.8", "0.3.9"), encoding="utf-8")


def main():
    im = fix_wrap_x()
    rows = load_definition()
    rebuild_buildings(im, rows)
    empty_adjacency_rules()
    write_names()
    bump()
    print("DONE v0.3.9")


if __name__ == "__main__":
    main()
