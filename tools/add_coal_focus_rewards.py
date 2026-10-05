# -*- coding: utf-8 -*-
"""Give national-focus steel rewards a matching coal grant (HOI4 1.19 energy).

Coal is a base-game resource since HOI4 1.19 (free update shipped with
"No Compromise, No Surrender"). All MK states already carry coal; focuses that
hand out steel now also hand out coal, so a country can fuel the factories and
industry those same focuses unlock.

Idempotent: a steel reward already followed by a coal grant is left untouched.

Usage:
  python tools/add_coal_focus_rewards.py [--dry-run]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOCUS = ROOT / "common" / "national_focus"

STEEL_RE = re.compile(
    r"^(?P<indent>\s*)add_resource = \{ type = steel amount = (?P<amount>\d+) \}\s*$"
)
COAL_RE = re.compile(r"^\s*add_resource = \{ type = coal amount = \d+ \}\s*$")


def coal_for(amount: int) -> int:
    """Bulk energy resource: ~1.5x the steel grant, never below 4."""
    return max(4, int(amount * 1.5 + 0.5))


def convert(text: str) -> tuple[str, int]:
    out: list[str] = []
    added = 0
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        m = STEEL_RE.match(stripped)
        if m and not (out and COAL_RE.match(out[-1].rstrip("\r\n"))):
            indent = m.group("indent")
            amount = coal_for(int(m.group("amount")))
            out.append(f"{indent}add_resource = {{ type = coal amount = {amount} }}\n")
            added += 1
        out.append(line)
    return "".join(out), added


def main() -> None:
    dry = "--dry-run" in sys.argv
    files = 0
    total = 0
    for path in sorted(FOCUS.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        new, added = convert(text)
        if not added:
            continue
        files += 1
        total += added
        print(f"{path.relative_to(ROOT)}: +{added}")
        if not dry:
            path.write_text(new, encoding="utf-8")
    verb = "would add" if dry else "added"
    print(f"{verb} {total} coal reward(s) in {files} file(s)")


if __name__ == "__main__":
    main()
