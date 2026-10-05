# -*- coding: utf-8 -*-
"""Scatter strategic resources across MK states by owner tag.

HOI4 format (state root):
  resources={
    steel=12
    oil=4
    ...
  }

Usage: python tools/build_resources.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "history" / "states"

# Base profile per tag (steel, oil, aluminium, rubber, tungsten, chromium)
PROFILE = {
    "VCI": (28, 10, 8, 4, 6, 6),
    "SOY": (10, 6, 6, 18, 4, 4),
    "BTR": (16, 22, 4, 2, 8, 10),
    "KRZ": (20, 8, 6, 4, 10, 8),
    "KZS": (12, 14, 4, 6, 6, 4),
    "MUS": (8, 6, 10, 8, 4, 4),
    "TRF": (6, 4, 8, 16, 2, 2),
    "ZLD": (10, 6, 8, 8, 4, 4),
    "ISL": (8, 12, 4, 6, 4, 6),
    "CLB": (24, 8, 12, 2, 10, 8),
    "ADL": (8, 6, 6, 6, 4, 4),
    "DMK": (14, 8, 6, 4, 8, 8),
    "FDP": (10, 6, 8, 6, 4, 4),
    "CRE": (18, 16, 4, 2, 10, 12),
    "SVA": (8, 6, 14, 4, 6, 4),
    "ART": (12, 8, 6, 6, 8, 6),
    "KMS": (10, 10, 6, 8, 4, 4),
    "ZNS": (14, 8, 6, 4, 8, 6),
    "ZKR": (12, 8, 10, 4, 6, 6),
    "ZML": (8, 6, 4, 10, 4, 4),
    "NBL": (16, 10, 6, 4, 8, 8),
    "ISG": (10, 6, 8, 8, 4, 4),
    "HRL": (12, 8, 8, 6, 6, 6),
    "SHF": (18, 10, 8, 6, 8, 8),
}
KEYS = ("steel", "oil", "aluminium", "rubber", "tungsten", "chromium")


def owner_of(text: str) -> str | None:
    m = re.search(r"owner\s*=\s*([A-Z]{3})", text)
    return m.group(1) if m else None


def state_id(text: str) -> int:
    m = re.search(r"id\s*=\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def resources_block(owner: str, sid: int) -> str:
    base = PROFILE.get(owner, (10, 6, 6, 4, 4, 4))
    # Spread unevenly: capital-ish low ids get more; vary by id
    mult = 0.55 + (sid % 7) * 0.12
    bias = sid % len(KEYS)
    parts = []
    for i, key in enumerate(KEYS):
        amt = int(base[i] * mult)
        if i == bias:
            amt += 4
        if amt < 1:
            amt = 1
        parts.append(f"\t\t{key}={amt}")
    return "\tresources={\n" + "\n".join(parts) + "\n\t}\n"


def strip_resources(text: str) -> str:
    return re.sub(r"\n?\tresources=\{[^}]*\}\n?", "\n", text, count=1)


def main() -> None:
    n = 0
    for path in sorted(STATES.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        owner = owner_of(text)
        if not owner:
            continue
        sid = state_id(text)
        text = strip_resources(text)
        block = resources_block(owner, sid)
        # Insert before history={ or after state_category line
        if "history={" in text:
            text = text.replace("history={", block + "\thistory={", 1)
        else:
            text = text.replace("state={", "state={\n" + block, 1)
        path.write_text(text, encoding="utf-8")
        n += 1
    print(f"resources written for {n} states")


if __name__ == "__main__":
    main()
