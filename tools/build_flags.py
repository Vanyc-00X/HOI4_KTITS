# -*- coding: utf-8 -*-
"""Generate simple TGA flags for tags and cosmetic ideology tags.

HOI4 expects TGA BGRA, top-left origin typically for flags:
  gfx/flags/TAG.tga          82x52
  gfx/flags/medium/TAG.tga   41x26
  gfx/flags/small/TAG.tga    10x7

Usage: python tools/build_flags.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_cosmetics import CHARS, COSMETICS, IDEOLOGY_TINT, TAG_RGB, blend_rgb, cosmetic_tag

ROOT = Path(__file__).resolve().parents[1]
SIZES = {
    "": (82, 52),
    "medium": (41, 26),
    "small": (10, 7),
}


def write_tga(path: Path, w: int, h: int, rgb: tuple[int, int, int], stripe: tuple[int, int, int] | None = None) -> None:
    """Uncompressed 24-bit TGA, bottom-up BGR."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = bytearray()
    for y in range(h):
        for x in range(w):
            if stripe and x >= w // 2:
                r, g, b = stripe
            else:
                r, g, b = rgb
            # simple emblem: lighter square in center
            if w > 20 and abs(x - w // 2) < w // 8 and abs(y - h // 2) < h // 6:
                r = min(255, r + 60)
                g = min(255, g + 60)
                b = min(255, b + 60)
            pixels += bytes((b, g, r))
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0, 0, 2, 0, 0, 0, 0, 0, w, h, 24, 0,
    )
    path.write_bytes(header + pixels)


def _clean_foreign_flags(allowed: set[str]) -> int:
    """Remove leftover vanilla / non-MK TGA so only our tags remain."""
    removed = 0
    flags_root = ROOT / "gfx" / "flags"
    if not flags_root.is_dir():
        return 0
    for folder in ("", "medium", "small"):
        d = flags_root / folder if folder else flags_root
        if not d.is_dir():
            continue
        for p in d.glob("*.tga"):
            stem = p.stem
            tag = stem.split("_", 1)[0]
            if tag not in allowed:
                p.unlink()
                removed += 1
    return removed


def main() -> None:
    tags = list(CHARS)
    ideologies = list(IDEOLOGY_TINT)
    removed = _clean_foreign_flags(set(tags))
    count = 0
    for tag in tags:
        base = TAG_RGB[tag]
        for folder, (w, h) in SIZES.items():
            rel = Path("gfx/flags") / folder / f"{tag}.tga" if folder else Path("gfx/flags") / f"{tag}.tga"
            write_tga(ROOT / rel, w, h, base)
            count += 1
        for ideo in ideologies:
            ctag = cosmetic_tag(tag, ideo)
            rgb = blend_rgb(tag, ideo)
            stripe = IDEOLOGY_TINT[ideo]
            for folder, (w, h) in SIZES.items():
                rel = Path("gfx/flags") / folder / f"{ctag}.tga" if folder else Path("gfx/flags") / f"{ctag}.tga"
                write_tga(ROOT / rel, w, h, rgb, stripe)
                count += 1
    print(f"wrote {count} flag files for {len(tags)} tags x (1+{len(ideologies)}) cosmetics"
          + (f"; removed {removed} foreign" if removed else ""))


if __name__ == "__main__":
    main()
