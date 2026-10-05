# -*- coding: utf-8 -*-
"""Summarise the newest HOI4 crash dumps and the mod-relevant lines of error.log."""
import re
import sys
from pathlib import Path

DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
NOISE = re.compile(r"Invalid focus|Trigger failed to validate|Invalid [Dd]ecision|has_completed_focus"
                   r"|equipment_graphic_database|has_game_rule|loc key collisions")

n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
for d in sorted((DOCS / "crashes").glob("hoi4_*"))[-n:]:
    t = (d / "exception.txt").read_text(errors="replace") if (d / "exception.txt").exists() else ""
    frames = re.findall(r"\d+\s+hoi4.exe\s+(\S+ \(\+ \d+\))", t)[:4]
    print(d.name, "|", " | ".join(frames))

for name in ("error.log", "game.log"):
    p = DOCS / "logs" / name
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    keep = [l for l in lines if not NOISE.search(l)]
    print(f"===== {name}: {len(lines)} lines, {len(keep)} non-noise (last 40)")
    print("\n".join(keep[-40:]))
