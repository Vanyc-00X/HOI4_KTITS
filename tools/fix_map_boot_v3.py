# -*- coding: utf-8 -*-
"""Fix X-crossing, rivers palette, BOM, and coastal ports (all sea-touching)."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV\map")
WIDTH, HEIGHT, CELL = 2048, 1024, 32


def load_definition():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(line.split(";"))
    return rows


def save_definition(rows):
    (ROOT / "map" / "definition.csv").write_text(
        "\n".join(";".join(p) for p in rows) + "\n", encoding="utf-8"
    )


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


def fix_x_crossings():
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    fixed = 0
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            a, b = px[x, y], px[x + 1, y]
            c, d = px[x, y + 1], px[x + 1, y + 1]
            if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                px[x + 1, y + 1] = c
                fixed += 1
    write_bmp_bgr(ROOT / "map" / "provinces.bmp", im)
    im2 = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px2 = im2.load()
    left = sum(
        1
        for y in range(HEIGHT - 1)
        for x in range(WIDTH - 1)
        if len({px2[x, y], px2[x + 1, y], px2[x, y + 1], px2[x + 1, y + 1]}) == 4
    )
    print(f"x_cross fixed={fixed} remaining_4color={left}")
    return im2


def province_maps(im: Image.Image, rows):
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows[1:]}
    px = im.load()
    sums = defaultdict(lambda: [0.0, 0.0, 0])
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            pid = color_to_pid.get(px[x, y])
            if pid is None:
                continue
            s = sums[pid]
            s[0] += x
            s[1] += y
            s[2] += 1
    centers = {pid: (sx / n, sy / n) for pid, (sx, sy, n) in sums.items() if n}
    return centers, color_to_pid


def province_to_state():
    p2s = {}
    for sf in (ROOT / "history" / "states").glob("*.txt"):
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        for p in re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S).group(1).split():
            p2s[int(p)] = sid
    return p2s


def find_pixel_in_province(px, color_to_pid, pid, ix, iy):
    for r in range(0, CELL + 2):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = int(ix) + dx, int(iy) + dy
                if 0 <= x < WIDTH and 0 <= y < HEIGHT and color_to_pid.get(px[x, y]) == pid:
                    return x + 0.5, y + 0.5
    return float(ix), float(iy)


def fix_coastal_ports(im, rows, centers, color_to_pid):
    sea = {int(p[0]) for p in rows[1:] if p[4] == "sea"}
    px = im.load()
    touches_sea = set()
    for y in range(0, HEIGHT, 1):
        for x in range(0, WIDTH, 1):
            pid = color_to_pid.get(px[x, y])
            if pid is None or pid in sea:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and color_to_pid.get(px[nx, ny]) in sea:
                    touches_sea.add(pid)
                    break

    p2s = province_to_state()
    # Every sea-touching land province MUST be coastal + have naval_base_spawn
    ports = {}
    for pid in sorted(touches_sea):
        sid = p2s.get(pid)
        if sid is None:
            continue
        ports[pid] = sid

    for parts in rows[1:]:
        if parts[4] == "land":
            parts[5] = "true" if int(parts[0]) in ports else "false"
    save_definition(rows)

    lines = []
    for pid, sid in sorted(ports.items()):
        cx, cy = centers.get(pid, (WIDTH / 2, HEIGHT / 2))
        x, y_pil = find_pixel_in_province(px, color_to_pid, pid, cx, cy)
        # buildings.txt uses Y from bottom of the map
        y_game = (HEIGHT - 1) - y_pil
        lines.append(f"{sid};naval_base_spawn;{x:.2f};10.00;{y_game:.2f};0.00;{pid}")
    (ROOT / "map" / "buildings.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # history: naval_base on each port province
    ports_by_state = defaultdict(list)
    for pid, sid in ports.items():
        ports_by_state[sid].append(pid)

    for sf in (ROOT / "history" / "states").glob("*.txt"):
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        # strip old naval_base lines
        text2 = re.sub(r"\n?\t\t\t\d+\s*=\s*\{\s*naval_base\s*=\s*\d+\s*\}", "", text)
        insert = "".join(f"\n\t\t\t{pid} = {{ naval_base = 1 }}" for pid in sorted(ports_by_state.get(sid, [])))
        if insert:
            text2 = text2.replace("buildings = {", "buildings = {" + insert, 1)
        sf.write_text(text2, encoding="utf-8")

    print(f"ports={len(ports)} touches_sea={len(touches_sea)}")
    return ports


def fix_rivers():
    van = (VANILLA_MAP / "rivers.bmp").read_bytes()
    pal = van[54 : 54 + 1024]
    w, h = WIDTH, HEIGHT
    row_stride = (w + 3) & ~3
    body = bytearray()
    row = bytes([254] * w) + b"\x00" * (row_stride - w)
    for _ in range(h):
        body.extend(row)
    header = bytearray(54)
    header[0:2] = b"BM"
    struct.pack_into("<I", header, 2, 54 + 1024 + len(body))
    struct.pack_into("<I", header, 10, 54 + 1024)
    struct.pack_into("<I", header, 14, 40)
    struct.pack_into("<i", header, 18, w)
    struct.pack_into("<i", header, 22, h)
    struct.pack_into("<H", header, 26, 1)
    struct.pack_into("<H", header, 28, 8)
    struct.pack_into("<I", header, 34, len(body))
    struct.pack_into("<i", header, 38, 2835)
    struct.pack_into("<i", header, 42, 2835)
    struct.pack_into("<I", header, 46, 0)  # biClrUsed=0
    struct.pack_into("<I", header, 50, 0)
    (ROOT / "map" / "rivers.bmp").write_bytes(bytes(header) + pal + body)
    print("rivers ok")


def strip_bom_countries():
    n = 0
    for f in (ROOT / "common" / "countries").glob("*.txt"):
        data = f.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            f.write_bytes(data[3:])
            n += 1
        else:
            text = data.decode("utf-8-sig")
            new = text.encode("utf-8")
            if new != data:
                f.write_bytes(new)
                n += 1
    print(f"bom stripped files={n}")


def fix_unitstacks_and_positions(centers, rows):
    """unitstacks.txt: province;x;y;z;rot;... — use inverted Y like buildings."""
    # Peek existing unitstacks
    us = ROOT / "map" / "unitstacks.txt"
    sample = us.read_text(encoding="utf-8", errors="replace")[:300] if us.exists() else ""
    print("unitstacks sample", repr(sample[:120]))

    # Common format: id;x;y;z;rotation;...
    # Also positions.txt can be empty in some installs — regenerate unitstacks densely
    lines = []
    for parts in rows[1:]:
        pid = int(parts[0])
        cx, cy = centers.get(pid, (WIDTH / 2.0, HEIGHT / 2.0))
        y_game = (HEIGHT - 1) - cy
        # 20 stack slots roughly — write one line pattern used by many TCs
        # Actually HOI4 unitstacks: each line is one stack type position
        # Format from wiki: ProvinceID;Xpos;Ypos;Zpos;Rotation;Anim;type?...
        # Keep simple: regenerate from a known working pattern if sample has semicolons
        if ";" in sample:
            # replicate field count from first line
            nfields = len(sample.splitlines()[0].split(";"))
            base = [f"{pid}", f"{cx:.2f}", "0.00", f"{y_game:.2f}", "0.00"]
            while len(base) < nfields:
                base.append("0")
            lines.append(";".join(base[:nfields]))
        else:
            lines.append(f"{pid};{cx:.2f};0.00;{y_game:.2f};0.00")
    us.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"unitstacks n={len(lines)}")

    # positions.txt — leave empty file (vanilla was empty here) or minimal
    # Many 1.14+ maps use only unitstacks; write empty positions to avoid bad parse
    (ROOT / "map" / "positions.txt").write_text("", encoding="utf-8")
    print("positions cleared")


def bump_register():
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
        for a, b in (("0.3.7", "0.3.8"), ("0.3.6", "0.3.8")):
            t = t.replace(a, b)
        p.write_text(t, encoding="utf-8")


def verify(ports):
    rows = load_definition()
    coastal = {int(p[0]) for p in rows[1:] if p[4] == "land" and p[5] == "true"}
    bld_ports = set()
    for l in (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines():
        if "naval_base_spawn" in l:
            bld_ports.add(int(l.split(";")[-1]))
    print("verify coastal==ports", coastal == bld_ports == set(ports), len(ports))
    # spot-check inverted Y for first port
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()
    color_to_pid = {(int(p[1]), int(p[2]), int(p[3])): int(p[0]) for p in rows[1:]}
    p2s = province_to_state()
    line = (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8").splitlines()[0]
    parts = line.split(";")
    sid, x, y_game, pid = int(parts[0]), float(parts[2]), float(parts[4]), int(parts[6])
    y_pil = (HEIGHT - 1) - y_game
    pid_at = color_to_pid.get(px[int(x), int(y_pil)])
    print(
        f"spot {line} -> pil y={y_pil:.1f} pid_at={pid_at} state_at={p2s.get(pid_at)} expect_pid={pid} expect_state={sid}"
    )


def main():
    strip_bom_countries()
    fix_rivers()
    im = fix_x_crossings()
    rows = load_definition()
    centers, color_to_pid = province_maps(im, rows)
    ports = fix_coastal_ports(im, rows, centers, color_to_pid)
    fix_unitstacks_and_positions(centers, rows)
    bump_register()
    verify(ports)
    print("DONE v0.3.8")


if __name__ == "__main__":
    main()
