# -*- coding: utf-8 -*-
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r"D:/Dowland/Mod/Games/HOI4/mir_kazualnosti")
docs = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV" / "mod" / "Mir_Kazualnosti.mod"
for p in [ROOT / "descriptor.mod", ROOT / "mir_kazualnosti.mod", docs]:
    t = re.sub(r'version="[^"]+"', 'version="0.3.9"', p.read_text(encoding="utf-8"))
    p.write_text(t, encoding="utf-8")
    print(p.name, re.search(r'version="([^"]+)"', t).group(1))

reg = ROOT / "tools" / "register_mod.py"
if not reg.exists():
    reg = Path(__file__).with_name("register_mod.py")
t = reg.read_text(encoding="utf-8")
t = re.sub(r'version="[^"]+"', 'version="0.3.9"', t)
reg.write_text(t, encoding="utf-8")

b = (ROOT / "map" / "buildings.txt").read_bytes()
print("double nl", b.endswith(b"\n\n"))
print("lines", len(b.decode().splitlines()), "empty", sum(1 for l in b.decode().splitlines() if not l.strip()))
print(Counter(l.split(";")[1] for l in b.decode().splitlines() if ";" in l))
print("names", (ROOT / "common" / "names" / "mk_names.txt").exists())
