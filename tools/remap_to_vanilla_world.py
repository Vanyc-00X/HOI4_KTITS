# -*- coding: utf-8 -*-
"""Remap Mir Kazualnosti custom tags onto the vanilla HOI4 world map.

Option A: every land state is owned by one of the 24 MK tags.
CRE <- German Reich (GER/AUS/CZE)
KRZ <- USSR (SOV)
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")

# continent.txt order → 1-based index in definition.csv last field
CONTINENT_ID = {
    "europe": 1,
    "north_america": 2,
    "south_america": 3,
    "australia": 4,
    "africa": 5,
    "asia": 6,
    "middle_east": 7,
}

# Vanilla 1936 owner TAG -> MK TAG (homelands / primary)
OWNER_MAP: dict[str, str] = {
    "GER": "CRE",
    "AUS": "CRE",
    "CZE": "CRE",
    "SOV": "KRZ",
    "ITA": "BTR",
    "ETH": "BTR",
    "ALB": "BTR",
    "AFA": "BTR",
    "JAP": "DMK",
    "MAN": "DMK",
    "MEN": "DMK",
    "USA": "SOY",
    "PHI": "SOY",
    "LIB": "SOY",
    "ENG": "MUS",
    "IRE": "MUS",
    "FRA": "ZLD",
    "HOL": "ADL",
    "BEL": "ADL",
    "LUX": "ADL",
    "SWE": "SVA",
    "NOR": "SVA",
    "DEN": "SVA",
    "FIN": "SVA",
    "ICE": "SVA",
    "RAJ": "KMS",
    "BRM": "KMS",
    "NEP": "KMS",
    "BHU": "KMS",
    "AST": "ZKR",
    "NZL": "ZKR",
    "SPR": "HRL",
    "POR": "HRL",
    "CHI": "VCI",
    "PRC": "VCI",
    "GXC": "VCI",
    "YUN": "VCI",
    "SHX": "VCI",
    "XSM": "VCI",
    "SIK": "VCI",
    "TIB": "VCI",
    "POL": "KZS",
    "LIT": "KZS",
    "LAT": "KZS",
    "EST": "KZS",
    "ROM": "KZS",
    "HUN": "KZS",
    "TUR": "ISL",
    "PER": "ISL",
    "AFG": "ISL",
    "IRQ": "ISL",
    "SAU": "ISL",
    "YEM": "ISL",
    "OMA": "ISL",
    "PAL": "ISL",
    "JOR": "ISL",
    "LEB": "ISL",
    "SYR": "ISL",
    "KUW": "ISL",
    "CAN": "CLB",
    "YUG": "FDP",
    "GRE": "FDP",
    "BUL": "FDP",
    "SWI": "FDP",
    "ARG": "ART",
    "CHL": "ART",
    "URG": "ART",
    "PAR": "ART",
    "BRA": "NBL",
    "BOL": "NBL",
    "PRU": "NBL",
    "ECU": "NBL",
    "COL": "NBL",
    "VEN": "NBL",
    "MEX": "TRF",
    "COS": "TRF",
    "CUB": "TRF",
    "DOM": "TRF",
    "ELS": "TRF",
    "GUA": "TRF",
    "HAI": "TRF",
    "HON": "TRF",
    "NIC": "TRF",
    "PAN": "TRF",
    "MON": "ZML",
    "TAN": "ZML",
    "SIA": "ISG",
    "MAL": "ISG",
    "INS": "SHF",
    "SAF": "ZNS",
}

# Maghreb → ISL (Islamic Republic belt)
MAGHREB_STATES = {
    458,  # Tunisia
    459,  # Western Algeria
    460,  # Eastern Algeria
    461,  # Northern Morocco
    462,  # Southern Morocco
    513,  # Southern Algeria
    290,  # Spanish Africa / Sahara variants
    699,  # Rio de Oro
    783,  # Ifni / Spanish Africa
}

CAPITALS: dict[str, int] = {
    "KRZ": 219,
    "CRE": 64,
    "BTR": 2,
    "DMK": 282,
    "SOY": 361,
    "MUS": 126,
    "ZLD": 16,
    "ADL": 7,
    "SVA": 141,
    "KMS": 439,
    "ZKR": 285,
    "HRL": 41,
    "VCI": 608,
    "KZS": 10,
    "ISL": 49,
    "CLB": 276,
    "FDP": 107,
    "ART": 278,
    "ZNS": 275,
    "TRF": 277,
    "ZML": 330,
    "NBL": 500,
    "ISG": 1076,
    "SHF": 335,
}

COUNTRY_FILES = {
    "VCI": "VCI - Velikaya Kazualnaya Imperiya.txt",
    "SOY": "SOY - Soevaya Respublika.txt",
    "BTR": "BTR - Chyornaya Tartariya.txt",
    "KRZ": "KRZ - Krasnaya Zemlya.txt",
    "KZS": "KZS - Kazachi Shtaty.txt",
    "MUS": "MUS - Korolevstvo Musi.txt",
    "TRF": "TRF - Travinnaya Federatsiya.txt",
    "ZLD": "ZLD - Demokraticheskiy Zelenodolsk.txt",
    "ISL": "ISL - Islamskaya Respublika.txt",
    "CLB": "CLB - Chelyaba.txt",
    "ADL": "ADL - Aydaliya.txt",
    "DMK": "DMK - Dmitro Knyazhestvo.txt",
    "FDP": "FDP - Federatsiya Deputatov.txt",
    "CRE": "CRE - Chyornaya Respublika.txt",
    "SVA": "SVA - Severnaya Assambleya.txt",
    "ART": "ART - Ayratskaya Respublika.txt",
    "KMS": "KMS - Kamilskoe Sodruzhestvo.txt",
    "ZNS": "ZNS - Zaynutdinovskiy Soyuz.txt",
    "ZKR": "ZKR - Respublika Zakariya.txt",
    "ZML": "ZML - Zemlya Zamaliya.txt",
    "NBL": "NBL - Novaya Bulatiya.txt",
    "ISG": "ISG - Respublika Ismagil.txt",
    "HRL": "HRL - Kharitonovskaya Liga.txt",
    "SHF": "SHF - Sharafutdinovskaya Federatsiya.txt",
}

OWNER_RE = re.compile(r"^(\s*owner\s*=\s*)(\w+)", re.M)
CONTROLLER_RE = re.compile(r"^(\s*controller\s*=\s*)(\w+)", re.M)
CORE_RE = re.compile(r"^(\s*add_core_of\s*=\s*)(\w+)", re.M)
CLAIM_RE = re.compile(r"^(\s*add_claim_by\s*=\s*)(\w+)", re.M)
CAPITAL_RE = re.compile(r"^capital\s*=\s*\d+", re.M)
STATE_ID_RE = re.compile(r"^\s*id\s*=\s*(\d+)", re.M)
PROVINCES_RE = re.compile(r"provinces\s*=\s*\{([^}]*)\}", re.S)
TRANSFER_RE = re.compile(r"^\s*transfer_state_to\s*=\s*\w+\s*$", re.M)

MK_TAGS = set(CAPITALS)

# Colonial MK tags whose overseas Africa/Asia holdings get redistributed
COLONIAL = {"MUS", "ZLD", "ADL", "HRL"}


def load_province_continents() -> dict[int, int]:
    path = VANILLA / "map" / "definition.csv"
    out: dict[int, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split(";")
        if len(parts) < 8:
            continue
        try:
            pid = int(parts[0])
            cont = int(parts[7])
        except ValueError:
            continue
        out[pid] = cont
    return out


def state_continent(text: str, prov_cont: dict[int, int]) -> int | None:
    m = PROVINCES_RE.search(text)
    if not m:
        return None
    ids = [int(x) for x in m.group(1).split() if x.isdigit()]
    counts: dict[int, int] = {}
    for pid in ids:
        c = prov_cont.get(pid, 0)
        if c <= 0:
            continue
        counts[c] = counts.get(c, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def resolve_owner(vanilla_owner: str, state_id: int, continent: int | None) -> str:
    base = OWNER_MAP.get(vanilla_owner, vanilla_owner)
    africa = CONTINENT_ID["africa"]
    asia = CONTINENT_ID["asia"]
    me = CONTINENT_ID["middle_east"]

    # Maghreb → Islamic Republic
    if state_id in MAGHREB_STATES or (
        continent == africa and vanilla_owner in {"FRA", "SPR"} and state_id in MAGHREB_STATES
    ):
        if state_id in MAGHREB_STATES:
            return "ISL"

    # British / French / Belgian / Portuguese Africa → ZNS (pan-African)
    # Keep Italian/Ethiopian Africa with BTR
    if continent == africa and base in COLONIAL:
        return "ZNS"
    if continent == africa and base == "MUS":
        return "ZNS"

    # Middle East mandates (ENG etc.) → ISL
    if continent == me and base in {"MUS", "ZLD", "HRL"}:
        return "ISL"

    # French / British Indochina & SE Asia mainland → ISG
    if continent == asia and vanilla_owner == "FRA":
        return "ISG"
    if continent == asia and vanilla_owner == "ENG" and base == "MUS":
        # residual ENG Asia (Hong Kong, Singapore leftovers if any) → ISG or VCI
        # Hong Kong often asia ENG → VCI neighborhood; give coastal Asia ENG to ISG
        return "ISG"

    return base


def clean_state_text(text: str) -> str:
    # Remove DLC releasable transfers that would create stub owners
    text = TRANSFER_RE.sub("", text)
    return text


def remap_state_text(text: str, new_owner: str) -> str:
    text = clean_state_text(text)

    def repl_owner(m: re.Match[str]) -> str:
        return m.group(1) + new_owner

    text = OWNER_RE.sub(repl_owner, text, count=1)
    # controllers → same owner
    text = CONTROLLER_RE.sub(repl_owner, text)

    # Remap cores/claims to MK where possible; drop others
    def repl_core(m: re.Match[str]) -> str:
        old = m.group(2)
        mapped = OWNER_MAP.get(old, old)
        if mapped in MK_TAGS:
            return m.group(1) + mapped
        return ""  # drop

    text = CORE_RE.sub(lambda m: repl_core(m) or "", text)
    text = CLAIM_RE.sub(lambda m: repl_core(m) or "", text)

    # Remove empty leftovers from dropped cores
    lines = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(add_core_of|add_claim_by)\s*=\s*$", line):
            continue
        if re.match(r"^\s*(add_core_of|add_claim_by)\s*=\s*\w+\s*$", line):
            tag = line.split("=")[1].strip()
            if tag not in MK_TAGS:
                continue
        lines.append(line)
    text = "".join(lines)

    if f"add_core_of = {new_owner}" not in text:
        text = OWNER_RE.sub(
            lambda m: m.group(0) + f"\n\t\tadd_core_of = {new_owner}",
            text,
            count=1,
        )
    return text


def copy_and_remap_states(prov_cont: dict[int, int]) -> dict[str, int]:
    src = VANILLA / "history" / "states"
    dst = ROOT / "history" / "states"
    if not src.is_dir():
        raise SystemExit(f"Vanilla states not found: {src}")

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    counts: dict[str, int] = {t: 0 for t in CAPITALS}
    unmapped: dict[str, int] = {}

    for path in sorted(src.glob("*.txt")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        sid_m = STATE_ID_RE.search(raw)
        state_id = int(sid_m.group(1)) if sid_m else -1
        own_m = OWNER_RE.search(raw)
        if not own_m:
            # sea / empty — copy as-is
            (dst / path.name).write_text(raw, encoding="utf-8")
            continue
        vanilla_owner = own_m.group(2)
        if vanilla_owner not in OWNER_MAP:
            unmapped[vanilla_owner] = unmapped.get(vanilla_owner, 0) + 1
        cont = state_continent(raw, prov_cont)
        new_owner = resolve_owner(vanilla_owner, state_id, cont)
        if new_owner not in MK_TAGS:
            # fallback: force ZNS for safety on Option A
            print(f"Fallback owner for state {state_id} ({vanilla_owner}) -> ZNS")
            new_owner = "ZNS"
        new = remap_state_text(raw, new_owner)
        counts[new_owner] = counts.get(new_owner, 0) + 1
        (dst / path.name).write_text(new, encoding="utf-8")

    if unmapped:
        print("WARNING unmapped vanilla owners:")
        for k, v in sorted(unmapped.items()):
            print(f"  {k}: {v}")
    return counts


def update_capitals() -> None:
    cdir = ROOT / "history" / "countries"
    for tag, fname in COUNTRY_FILES.items():
        path = cdir / fname
        if not path.exists():
            print(f"MISSING country file: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        cap = CAPITALS[tag]
        if CAPITAL_RE.search(text):
            text = CAPITAL_RE.sub(f"capital = {cap}", text, count=1)
        else:
            text = f"capital = {cap}\n" + text
        # bump research/convoys a bit for majors
        path.write_text(text, encoding="utf-8")


def archive_custom_map() -> None:
    map_dir = ROOT / "map"
    archive = ROOT / "_archive_custom_map"
    if map_dir.exists():
        if archive.exists():
            shutil.rmtree(archive)
        shutil.move(str(map_dir), str(archive))
        print(f"Archived custom map -> {archive}")


def patch_descriptor() -> None:
    for name in ("descriptor.mod", "Mir_Kazualnosti.mod"):
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = [
            line
            for line in text.splitlines()
            if "map/strategicregions" not in line
        ]
        text2 = "\n".join(lines)
        text2 = re.sub(r'version="[^"]*"', 'version="0.13.0-vanilla-map"', text2, count=1)
        if not text2.endswith("\n"):
            text2 += "\n"
        path.write_text(text2, encoding="utf-8")
        print(f"Patched {name}")


def write_mapping_doc(counts: dict[str, int]) -> None:
    rows = [
        ("KRZ", "communism", "USSR (SOV)", "219 Moscow"),
        ("CRE", "fascism", "GER+AUS+CZE (Black Republic)", "64 Berlin"),
        ("BTR", "fascism", "Italy+Ethiopia+Albania+Libya", "2 Rome"),
        ("DMK", "fascism", "Japan+Manchukuo+Mengkukuo", "282 Tokyo"),
        ("SOY", "democratic", "USA+Philippines+Liberia", "361 Washington"),
        ("MUS", "democratic", "Britain+Ireland (homelands)", "126 London"),
        ("ZLD", "democratic", "France (homeland)", "16 Paris"),
        ("ADL", "democratic", "Benelux (homeland)", "7 Amsterdam"),
        ("SVA", "democratic", "Scandinavia", "141 Stockholm"),
        ("KMS", "democratic", "British Raj+Burma", "439 Delhi"),
        ("ZKR", "democratic", "Australia+NZ", "285 NSW"),
        ("HRL", "democratic", "Spain+Portugal (homelands)", "41 Madrid"),
        ("VCI", "neutrality", "China+warlords+Tibet", "608 Beijing"),
        ("KZS", "neutrality", "Poland+Baltics+Romania+Hungary", "10 Warsaw"),
        ("ISL", "neutrality", "Islamic belt+Maghreb+ME mandates", "49 Ankara"),
        ("CLB", "neutrality", "Canada", "276 Ottawa"),
        ("FDP", "neutrality", "Balkans+Switzerland", "107 Belgrade"),
        ("ART", "neutrality", "Southern Cone", "278 Buenos Aires"),
        ("NBL", "neutrality", "Brazil+Andes north", "500 Rio"),
        ("TRF", "communism", "Mexico+Central America+Caribbean", "277 Mexico"),
        ("ZML", "communism", "Mongolia+Tannu Tuva", "330 Mongolia"),
        ("ISG", "communism", "Siam+Malaya+Indochina", "1076 Bangkok"),
        ("SHF", "neutrality", "Dutch East Indies", "335 Java"),
        ("ZNS", "neutrality", "Sub-Saharan Africa (ex-colonies+SAF)", "275 Transvaal"),
    ]
    lines = [
        "# Vanilla world remap (v0.13)",
        "",
        "Custom Kazualia map archived to `_archive_custom_map/`.",
        "Option A: all land states owned by the 24 MK tags.",
        "Focus trees / characters / ideas kept on original MK tags.",
        "",
        "| TAG | Ideology | Territory | Capital | States |",
        "|-----|----------|-----------|---------|--------|",
    ]
    for tag, ideo, terr, cap in rows:
        lines.append(f"| {tag} | {ideo} | {terr} | {cap} | {counts.get(tag, 0)} |")
    path = ROOT / "docs" / "VANILLA_WORLD_REMAP.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    if not VANILLA.is_dir():
        raise SystemExit(f"HOI4 install not found: {VANILLA}")
    print("Loading province continents...")
    prov_cont = load_province_continents()
    print(f"  {len(prov_cont)} provinces")
    print("Copying & remapping states...")
    counts = copy_and_remap_states(prov_cont)
    print("State counts by MK tag:")
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    missing = [t for t in CAPITALS if counts.get(t, 0) == 0]
    if missing:
        print("ERROR tags with 0 states:", missing)
    print("Updating capitals...")
    update_capitals()
    print("Archiving custom map...")
    archive_custom_map()
    print("Patching descriptors...")
    patch_descriptor()
    write_mapping_doc(counts)
    print("DONE")


if __name__ == "__main__":
    main()
