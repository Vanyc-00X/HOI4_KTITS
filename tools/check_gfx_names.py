# -*- coding: utf-8 -*-
"""Check that sprite names exist in vanilla interface/*.gfx.

Usage: python check_gfx_names.py NAME...      exact check
       python check_gfx_names.py --list PREFIX list names starting with PREFIX
"""
import re
import sys
from pathlib import Path

VANILLA = Path(r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV")
names = set()
for f in (VANILLA / "interface").rglob("*.gfx"):
    names.update(re.findall(r'name\s*=\s*"?([A-Za-z0-9_]+)"?', f.read_text(encoding="utf-8", errors="ignore")))
if sys.argv[1:2] == ["--list"]:
    for n in sorted(x for x in names if x.startswith(sys.argv[2])):
        print(n)
else:
    for n in sys.argv[1:]:
        print(("OK   " if n in names else "MISS ") + n)
