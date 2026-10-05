# -*- coding: utf-8 -*-
"""Scatter strategic resources across MK states by owner tag.

HOI4 format (state root):
  resources={
    steel=12
    oil=4
    ...
    coal=18
  }

Coal is a base-game resource since HOI4 1.19 (free update shipped with
"No Compromise, No Surrender"): it powers factories/energy. Vanilla defines it
in `common/resources/00_resources.txt` (icon frame 7), but the mod replaces
`history/states` via replace_path, so vanilla coal never reaches our map and
must be authored here. No extra files (resources/gfx/interface) are needed.

Usage: python tools/build_resources.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "history" / "states"

# Base profile per tag (steel, oil, aluminium, rubber, tungsten, chromium, coal)
PROFILE = {
    "VCI": (28, 10, 8, 4, 6, 6, 44),
    "SOY": (10, 6, 6, 18, 4, 4, 20),
    "BTR": (16, 22, 4, 2, 8, 10, 30),
    "KRZ": (20, 8, 6, 4, 10, 8, 34),
    "KZS": (12, 14, 4, 6, 6, 4, 24),
    "MUS": (8, 6, 10, 8, 4, 4, 16),
    "TRF": (6, 4, 8, 16, 2, 2, 14),
    "ZLD": (10, 6, 8, 8, 4, 4, 20),
    "ISL": (8, 12, 4, 6, 4, 6, 18),
    "CLB": (24, 8, 12, 2, 10, 8, 40),
    "ADL": (8, 6, 6, 6, 4, 4, 16),
    "DMK": (14, 8, 6, 4, 8, 8, 26),
    "FDP": (10, 6, 8, 6, 4, 4, 18),
    "CRE": (18, 16, 4, 2, 10, 12, 32),
    "SVA": (8, 6, 14, 4, 6, 4, 16),
    "ART": (12, 8, 6, 6, 8, 6, 22),
    "KMS": (10, 10, 6, 8, 4, 4, 18),
    "ZNS": (14, 8, 6, 4, 8, 6, 24),
    "ZKR": (12, 8, 10, 4, 6, 6, 22),
    "ZML": (8, 6, 4, 10, 4, 4, 16),
    "NBL": (16, 10, 6, 4, 8, 8, 28),
    "ISG": (10, 6, 8, 8, 4, 4, 18),
    "HRL": (12, 8, 8, 6, 6, 6, 22),
    "SHF": (18, 10, 8, 6, 8, 8, 32),
}
DEFAULT_PROFILE = (10, 6, 6, 4, 4, 4, 18)
# Keep KEYS at six entries: existing resource amounts stay byte-identical,
# coal is computed separately and appended last.
KEYS = ("steel", "oil", "aluminium", "rubber", "tungsten", "chromium")
COAL = "coal"
CAPITAL_STATES = 24  # states 1..24 are the 24 capital states


def profile(owner: str) -> tuple[int, ...]:
    return PROFILE.get(owner, DEFAULT_PROFILE)


def owner_of(text: str) -> str | None:
    m = re.search(r"owner\s*=\s*([A-Z]{3})", text)
    return m.group(1) if m else None


def state_id(text: str) -> int:
    m = re.search(r"id\s*=\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def coal_amount(owner: str, sid: int) -> int:
    """Coal from owner profile + per-state variance; capitals get a bonus."""
    base = profile(owner)[6]
    mult = 0.62 + (sid % 5) * 0.14  # 0.62 .. 1.18
    amt = int(round(base * mult))
    if sid <= CAPITAL_STATES:
        amt += 6
    return max(amt, 6)


def resources_block(owner: str, sid: int) -> str:
    base = profile(owner)
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
    parts.append(f"\t\t{COAL}={coal_amount(owner, sid)}")
    return "\tresources={\n" + "\n".join(parts) + "\n\t}\n"


def strip_resources(text: str) -> str:
    """Remove the whole resources={...} block (with its indentation) if present."""
    return re.sub(r"\n[ \t]*resources=\{[^}]*\}", "", text, count=1)


def main() -> None:
    n = 0
    coal_total = 0
    coal_values: list[int] = []
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
        coal = coal_amount(owner, sid)
        coal_total += coal
        coal_values.append(coal)
    print(
        f"resources written for {n} states "
        f"(coal: total {coal_total}, per state {min(coal_values)}..{max(coal_values)})"
    )


if __name__ == "__main__":
    main()
