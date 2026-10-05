# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter, defaultdict

p = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
print("mtime", p.stat().st_mtime, "size", p.stat().st_size)
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
print("total lines", len(lines))
if not lines:
    raise SystemExit("empty")

# detect newest session by last timestamp prefix hour
last_ts = lines[-1][1:9] if lines[-1].startswith("[") else ""
print("last ts", last_ts, lines[-1][:120])
# find start of last minute-ish session: walk back for big gap or first of same minute prefix
prefix = lines[-1][:7]  # [20:16
idx = 0
for i in range(len(lines) - 1, -1, -1):
    if not lines[i].startswith(prefix[:4]):  # [20:
        idx = i + 1
        break
# better: find first line with same [HH:MM
mm = lines[-1][1:6]  # 20:16
starts = [i for i, l in enumerate(lines) if l.startswith(f"[{mm}")]
session = lines[starts[0]:] if starts else lines[-15000:]
print("session lines", len(session), "from", session[0][:80])

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
    elif "Unable to find focus" in l:
        k = "no_focus"
    elif "Invalid focus" in l:
        k = "bad_focus"
    elif "Trigger failed" in l:
        k = "trig_fail"
    elif "not in the tag list" in l:
        k = "missing_tag"
    elif "Duplicate Country" in l:
        k = "dup_tag"
    elif "MAP_ERROR" in l:
        k = "map_error"
    elif "weatherpositions" in l:
        k = "weatherpos"
    elif "Error:" in l:
        k = "error"
    elif "invalid on_" in l:
        k = "border_war"
    elif "Failed" in l or "failed" in l:
        k = "failed"
    else:
        k = "other"
    c[k] += 1
    if k not in ("x_cross", "bad_focus", "trig_fail") and len(ex[k]) < 12:
        ex[k].append(l[:260])

print("COUNTS", dict(c))
for k in sorted(ex):
    if k == "other":
        continue
    print("====", k)
    for e in ex[k]:
        print(e)

print("==== OTHER interesting ====")
seen = set()
for l in session:
    if any(x in l for x in ("invalid X", "has_completed_focus", "Trigger failed", "Invalid focus")):
        continue
    msg = l.split("]:", 1)[-1][:100]
    if msg in seen:
        continue
    seen.add(msg)
    print(l[:260])
    if len(seen) >= 50:
        break

print("==== LAST 30 ====")
for l in session[-30:]:
    print(l[:260])
