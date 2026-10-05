# -*- coding: utf-8 -*-
"""Cross-reference check for mod scripts: ideas, events, focuses, scripted effects/triggers, loc keys."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r"E:/SteamLibrary/steamapps/common/Hearts of Iron IV")
problems = []


def read(p):
    return re.sub(r"#[^\n]*", "", p.read_text(encoding="utf-8-sig", errors="replace"))


def top_keys(text, inside=None):
    """Keys defined at brace depth `depth_wanted` (0 = file root)."""
    keys, depth, i = [], 0, 0
    for m in re.finditer(r"([A-Za-z0-9_.\-]+)\s*=\s*\{|\{|\}", text):
        tok = m.group(0)
        if tok == "}":
            depth -= 1
        elif tok == "{":
            depth += 1
        else:
            keys.append((depth, m.group(1)))
            depth += 1
    return keys


mod_files = {sub: list((ROOT / sub).rglob("*.txt")) for sub in ("common", "events")}
all_mod = mod_files["common"] + mod_files["events"]
texts = {p: read(p) for p in all_mod}

ideas = set()
for p in (ROOT / "common/ideas").glob("*.txt"):
    ideas |= {k for d, k in top_keys(texts[p]) if d == 2}
for p in (GAME / "common/ideas").glob("*.txt"):
    ideas |= {k for d, k in top_keys(read(p)) if d == 2}

events = set()
for p in (ROOT / "events").glob("*.txt"):
    events |= set(re.findall(r"\bid\s*=\s*([a-z_]+\.\d+)", texts[p]))

effects, triggers = set(), set()
for base, store in (("scripted_effects", effects), ("scripted_triggers", triggers)):
    for root in (ROOT, GAME):
        for p in (root / "common" / base).glob("*.txt"):
            store |= {k for d, k in top_keys(read(p)) if d == 0}

focuses = set()
for p in (ROOT / "common/national_focus").glob("*.txt"):
    focuses |= {f for f in re.findall(r"\bid\s*=\s*(\w+)\b(?!\.)", texts[p]) if not f.endswith("_focus")}

loc = set()
for p in (ROOT / "localisation").rglob("*.yml"):
    loc |= set(re.findall(r"^\s*([\w.\-]+):\d*\s", p.read_text(encoding="utf-8-sig"), re.M))

for p, t in texts.items():
    rel = p.relative_to(ROOT).as_posix()
    for k in re.findall(r"\b(?:add_ideas|remove_ideas|has_idea|add_idea|remove_idea|idea)\s*=\s*(\w+)", t):
        if k not in ideas and k not in ("yes", "no"):
            problems.append(f"{rel}: unknown idea {k}")
    for k in re.findall(r"\b(?:country_event|news_event)\s*=\s*\{[^}]*?\bid\s*=\s*([\w.]+)", t):
        if k not in events:
            problems.append(f"{rel}: unknown event {k}")
    for k in re.findall(r"\bfocus\s*=\s*(\w+)", t):
        if k not in focuses:
            problems.append(f"{rel}: unknown focus {k}")
    for k in re.findall(r"\b(mk_\w+)\s*=\s*yes", t):
        if k not in effects and k not in triggers:
            problems.append(f"{rel}: unknown scripted effect/trigger {k}")

# loc: focuses, mod ideas, decisions, event titles
for f in focuses:
    for suffix in ("", "_desc"):
        if f + suffix not in loc and not f.startswith(("italian", "soviet", "mk_generic")):
            problems.append(f"loc missing {f}{suffix}")
for p in (ROOT / "common/ideas").glob("*.txt"):
    for d, k in top_keys(texts[p]):
        if d == 2 and k not in loc:
            problems.append(f"loc missing idea {k}")
for p in (ROOT / "common/decisions").glob("*.txt"):
    for d, k in top_keys(texts[p]):
        if d == 1 and k not in loc:
            problems.append(f"loc missing decision {k}")
for e in events:
    if e + ".t" not in loc:
        problems.append(f"loc missing event {e}.t")
for p in (ROOT / "events").glob("*.txt"):
    for k in re.findall(r"option\s*=\s*\{\s*name\s*=\s*([\w.]+)", texts[p]):
        if k not in loc:
            problems.append(f"loc missing option {k}")
for p, t in texts.items():
    for k in re.findall(r"(?:add_tech_bonus|add_doctrine_cost_reduction)\s*=\s*\{\s*name\s*=\s*(\w+)", t):
        if k not in loc:
            problems.append(f"loc missing bonus {k} ({p.name})")

print(f"ideas={len(ideas)} events={len(events)} focuses={len(focuses)} loc={len(loc)}")
for m in problems[:80]:
    print(" -", m)
print("problems:", len(problems))
sys.exit(1 if problems else 0)
