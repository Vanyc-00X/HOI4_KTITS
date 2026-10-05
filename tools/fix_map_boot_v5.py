# -*- coding: utf-8 -*-
"""
v0.3.10 crash fix:
- Restore wrap edge (undo left=right paint that caused TOO LARGE BOX)
- Fix wrap X-crossings without sharing colors across the seam
- Rewrite buildings.txt with NO trailing empty line
"""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, CELL = 2048, 1024, 32


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


def load_definition():
    rows = []
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(line.split(";"))
    return rows


def fix_provinces_wrap():
    im = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px = im.load()

    # 1) Restore rightmost column from its western neighbor (undo wrap-merge)
    for y in range(HEIGHT):
        px[WIDTH - 1, y] = px[WIDTH - 2, y]

    # 2) Interior X-cross → T-junction (SE := SW), never copies across wrap
    for y in range(HEIGHT - 1):
        for x in range(WIDTH - 1):
            a, b = px[x, y], px[x + 1, y]
            c, d = px[x, y + 1], px[x + 1, y + 1]
            if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
                px[x + 1, y + 1] = c

    # 3) Wrap X-cross: only mutate LEFT column pixels (x=0), never copy right→left color
    #    A=right[y], B=left[y], C=right[y+1], D=left[y+1]
    wrap_fixed = 0
    for y in range(HEIGHT - 1):
        a, b = px[WIDTH - 1, y], px[0, y]
        c, d = px[WIDTH - 1, y + 1], px[0, y + 1]
        if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
            px[0, y + 1] = b  # D := B (left side only)
            wrap_fixed += 1

    write_bmp_bgr(ROOT / "map" / "provinces.bmp", im)

    # verify
    im2 = Image.open(ROOT / "map" / "provinces.bmp").convert("RGB")
    px2 = im2.load()
    color_to_pid = {}
    rows = load_definition()
    for p in rows[1:]:
        color_to_pid[(int(p[1]), int(p[2]), int(p[3]))] = int(p[0])

    # bbox width check
    mins = {}
    maxs = {}
    for y in range(0, HEIGHT, 1):
        for x in range(0, WIDTH, 1):
            pid = color_to_pid.get(px2[x, y])
            if pid is None:
                continue
            if pid not in mins:
                mins[pid] = x
                maxs[pid] = x
            else:
                mins[pid] = min(mins[pid], x)
                maxs[pid] = max(maxs[pid], x)
    huge = [pid for pid in mins if maxs[pid] - mins[pid] > WIDTH // 2]
    wrap_xc = 0
    for y in range(HEIGHT - 1):
        a, b = px2[WIDTH - 1, y], px2[0, y]
        c, d = px2[WIDTH - 1, y + 1], px2[0, y + 1]
        if len({a, b, c, d}) == 4 or (a == d and b == c and a != b):
            wrap_xc += 1
    interior = sum(
        1
        for y in range(HEIGHT - 1)
        for x in range(WIDTH - 1)
        if len({px2[x, y], px2[x + 1, y], px2[x, y + 1], px2[x + 1, y + 1]}) == 4
    )
    print(f"wrap_fixed={wrap_fixed} wrap_xc={wrap_xc} interior_4c={interior} huge_bbox={len(huge)} {huge[:10]}")
    return im2, color_to_pid, rows


def province_to_state():
    p2s = {}
    for sf in (ROOT / "history" / "states").glob("*.txt"):
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        for p in re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S).group(1).split():
            p2s[int(p)] = sid
    return p2s


def rebuild_buildings(im, color_to_pid, rows):
    p2s = province_to_state()
    px = im.load()
    sea = {int(p[0]) for p in rows[1:] if p[4] == "sea"}

    # touches sea
    touches = set()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            pid = color_to_pid.get(px[x, y])
            if pid is None or pid in sea:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and color_to_pid.get(px[nx, ny]) in sea:
                    touches.add(pid)
                    break
            # wrap neighbors
            if x == 0 and color_to_pid.get(px[WIDTH - 1, y]) in sea:
                touches.add(pid)
            if x == WIDTH - 1 and color_to_pid.get(px[0, y]) in sea:
                touches.add(pid)

    # province centers
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

    # coastal flags
    ports = {pid: p2s[pid] for pid in touches if pid in p2s}
    for parts in rows[1:]:
        if parts[4] == "land":
            parts[5] = "true" if int(parts[0]) in ports else "false"
    (ROOT / "map" / "definition.csv").write_text(
        "\n".join(";".join(p) for p in rows) + "\n", encoding="utf-8"
    )

    naval = []
    for pid, sid in sorted(ports.items()):
        cx, cy = centers.get(pid, (WIDTH / 2, HEIGHT / 2))
        # snap to real pixel of this province
        found = None
        for r in range(0, CELL + 4):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = int(cx) + dx, int(cy) + dy
                    if 0 <= x < WIDTH and 0 <= y < HEIGHT and color_to_pid.get(px[x, y]) == pid:
                        found = (x + 0.5, y + 0.5)
                        break
                if found:
                    break
            if found:
                break
        if not found:
            continue
        x, y_pil = found
        y_game = (HEIGHT - 1) - y_pil
        naval.append(f"{sid};naval_base_spawn;{x:.2f};10.00;{y_game:.2f};0.00;{pid}")

    # state centers for sites
    state_sum = defaultdict(lambda: [0.0, 0.0, 0])
    for pid, (cx, cy) in centers.items():
        sid = p2s.get(pid)
        if sid is None:
            continue
        s = state_sum[sid]
        s[0] += cx
        s[1] += cy
        s[2] += 1
    state_c = {sid: (sx / n, sy / n) for sid, (sx, sy, n) in state_sum.items() if n}

    site = []
    for sid in sorted(state_c):
        cx, cy = state_c[sid]
        y_game = (HEIGHT - 1) - cy
        site.append(f"{sid};air_base;{cx:.2f};12.00;{y_game:.2f};0.00;0")
        site.append(f"{sid};rocket_site_spawn;{cx + 2:.2f};10.00;{y_game + 2:.2f};0.00;0")
        site.append(f"{sid};special_project_facility_spawn;{cx - 2:.2f};10.00;{y_game - 2:.2f};0.00;0")

    lines = naval + site
    # CRITICAL: no trailing newline after last line (HOI4 counts empty line as invalid)
    (ROOT / "map" / "buildings.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"buildings lines={len(lines)} ports={len(ports)} (no trailing nl)")

    # history naval_base sync
    by_state = defaultdict(list)
    for pid, sid in ports.items():
        by_state[sid].append(pid)
    for sf in (ROOT / "history" / "states").glob("*.txt"):
        text = sf.read_text(encoding="utf-8")
        sid = int(re.search(r"id\s*=\s*(\d+)", text).group(1))
        text2 = re.sub(r"\n?\t\t\t\d+\s*=\s*\{\s*naval_base\s*=\s*\d+\s*\}", "", text)
        insert = "".join(f"\n\t\t\t{pid} = {{ naval_base = 1 }}" for pid in sorted(by_state.get(sid, [])))
        if insert:
            text2 = text2.replace("buildings = {", "buildings = {" + insert, 1)
        sf.write_text(text2, encoding="utf-8")


def bump():
    import runpy

    # register_mod owns version strings — never blind-replace "version="
    runpy.run_path(str(Path(__file__).with_name("register_mod.py")), run_name="__main__")


def main():
    im, color_to_pid, rows = fix_provinces_wrap()
    rebuild_buildings(im, color_to_pid, rows)
    bump()
    # final verify buildings
    raw = (ROOT / "map" / "buildings.txt").read_bytes()
    print("ends_with_nl", raw.endswith(b"\n"), "line_count", len(raw.splitlines()))
    print("DONE v0.3.10")


if __name__ == "__main__":
    main()
