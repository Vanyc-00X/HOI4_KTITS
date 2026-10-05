# -*- coding: utf-8 -*-
from pathlib import Path
from collections import Counter, defaultdict

p = Path(r"c:\Users\Admin\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log")
print("LastWrite", p.stat().st_mtime)
print("Size", p.stat().st_size)
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
print("lines", len(lines))
recent = lines[-8000:] if len(lines) > 8000 else lines
print("recent", len(recent), "from", recent[0][:80], "to", recent[-1][:80])

c = Counter()
examples = defaultdict(list)
for l in recent:
    if "invalid X crossing" in l:
        k = "x_cross"
    elif "TOO LARGE BOX" in l:
        k = "large_box"
    elif "pixels around" in l:
        k = "tiny"
    elif "Duplicate Country" in l:
        k = "dup"
    elif "not in the tag list" in l:
        k = "missing_tag"
    elif "Unknown trigger" in l:
        k = "unk_trigger"
    elif "Palette" in l:
        k = "palette"
    elif "MAP_ERROR" in l:
        k = "map_error"
    elif "Error:" in l or "[ERROR]" in l:
        k = "error"
    elif "Failed" in l or "failed" in l:
        k = "failed"
    elif "Assert" in l or "Crash" in l or "fatal" in l.lower():
        k = "fatal"
    else:
        k = "other"
    c[k] += 1
    limit = 8 if k in ("unk_trigger", "missing_tag", "other") else 15
    if k != "x_cross" and len(examples[k]) < limit:
        examples[k].append(l[:280])

print("COUNTS", dict(c))
for k in sorted(examples.keys()):
    if k == "other":
        continue
    print("====", k)
    for e in examples[k]:
        print(e)

print("==== interesting other ====")
for e in examples["other"]:
    if any(x in e for x in ("province", "state", "history", "bookmark", "capital", "oob", "Character", "idea", "focus")):
        print(e[:280])

files = Counter()
for l in recent:
    if "in file:" in l:
        f = l.split("in file:")[1].split("near")[0].strip().strip('"').strip()
        files[f] += 1
print("TOP FILES")
for f, n in files.most_common(25):
    print(n, f)

# Non map unique messages
print("==== UNIQUE MSG HEADS ====")
seen = set()
for l in recent:
    if "invalid X crossing" in l or "coastal" in l or "not in the tag list" in l or "Unknown trigger" in l:
        continue
    msg = l.split("]:", 1)[-1][:140] if "]:" in l else l[:140]
    if msg in seen:
        continue
    seen.add(msg)
    print(l[:260])
    if len(seen) > 60:
        break
