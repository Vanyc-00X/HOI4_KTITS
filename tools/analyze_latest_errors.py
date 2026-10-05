# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter, defaultdict

p = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
print("mtime", p.stat().st_mtime, "size", p.stat().st_size)
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
print("lines", len(lines))
if not lines:
    raise SystemExit("empty")
print("LAST", lines[-1][:200])
mm = lines[-1][1:6] if lines[-1].startswith("[") else ""
starts = [i for i, l in enumerate(lines) if l.startswith(f"[{mm}")]
session = lines[starts[0]:] if starts else lines[-20000:]
print("session", len(session), "prefix", mm, "from", session[0][:90])

c = Counter()
ex = defaultdict(list)
for l in session:
    if "invalid X crossing" in l:
        k = "x_cross"
    elif "TOO LARGE BOX" in l:
        k = "large_box"
    elif "pixels around" in l:
        k = "tiny"
    elif "Palette" in l:
        k = "palette"
    elif "fractioned" in l:
        k = "fractioned"
    elif "Unable to find focus" in l:
        k = "no_focus"
    elif "Invalid focus" in l or "has_completed_focus" in l:
        k = "focus"
    elif "not in the tag list" in l:
        k = "missing_tag"
    elif "Duplicate Country" in l:
        k = "dup"
    elif "Error loading flag" in l:
        k = "flag"
    elif "unknown continent" in l:
        k = "continent"
    elif "portraits" in l and ("Error" in l or "unknown" in l):
        k = "portraits"
    elif "weatherpositions" in l:
        k = "weather"
    elif "MAP_ERROR" in l:
        k = "map"
    elif "Error:" in l or "Error " in l:
        k = "error"
    elif "Failed" in l or "failed" in l:
        k = "failed"
    else:
        k = "other"
    c[k] += 1
    if k not in ("x_cross", "focus", "flag") and len(ex[k]) < 15:
        ex[k].append(l[:280])
    if k == "flag" and len(ex[k]) < 5:
        ex[k].append(l[:280])
    if k == "x_cross" and len(ex[k]) < 3:
        ex[k].append(l[:280])

print("COUNTS", dict(c))
for k in sorted(ex):
    print("====", k)
    for e in ex[k]:
        print(e)

print("==== UNIQUE non-spam ====")
seen = set()
for l in session:
    if any(x in l for x in ("invalid X crossing", "Error loading flag", "has_completed_focus", "Trigger failed", "Invalid focus")):
        continue
    msg = l.split("]:", 1)[-1][:120]
    if msg in seen:
        continue
    seen.add(msg)
    print(l[:280])
    if len(seen) >= 40:
        break

print("==== LAST 25 ====")
for l in session[-25:]:
    print(l[:280])

g = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\game.log")
print("==== GAME TAIL ====")
print(g.read_text(encoding="utf-8", errors="replace")[-1500:])
