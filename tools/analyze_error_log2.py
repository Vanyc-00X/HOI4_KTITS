# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter

p = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

# Find session start around 20:13
starts = [i for i, l in enumerate(lines) if l.startswith("[20:13:")]
print("session lines with 20:13:", len(starts), "first idx", starts[0] if starts else None)
if starts:
    session = lines[starts[0]:]
else:
    session = lines[-10000:]

c = Counter()
for l in session:
    if "invalid X" in l:
        c["x_cross"] += 1
    elif "TOO LARGE" in l:
        c["large_box"] += 1
    elif "Palette" in l:
        c["palette"] += 1
    elif "Unable to find focus" in l:
        c["no_focus_tree"] += 1
    elif "Invalid focus" in l:
        c["invalid_focus"] += 1
    elif "Trigger failed" in l:
        c["trigger_fail"] += 1
    elif "MAP_ERROR" in l:
        c["map_error"] += 1
    elif "Error:" in l:
        c["error"] += 1
    elif "not in the tag list" in l:
        c["missing_tag"] += 1
print("SESSION COUNTS", dict(c))

print("==== FIRST 40 non-focus lines ====")
n = 0
for l in session:
    if "has_completed_focus" in l or "Invalid focus" in l or "Trigger failed" in l:
        continue
    print(l[:250])
    n += 1
    if n >= 40:
        break

print("==== LAST 40 lines ====")
for l in session[-40:]:
    print(l[:250])

print("==== Unable to find focus tree samples ====")
n = 0
for l in session:
    if "Unable to find focus" in l or "focus tree" in l.lower():
        print(l[:250])
        n += 1
        if n >= 20:
            break
