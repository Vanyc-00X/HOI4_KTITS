# -*- coding: utf-8 -*-
"""Write tutorial/tutorial.txt with state/province/tag ids remapped onto the Kazualia map.

Vanilla tutorial.txt points at state 550 (Eritrea), provinces 5091/12856/... and ETH; the
engine resolves them on game start and dereferences null on a custom map (native crash)."""
import re
from pathlib import Path

GAME = Path(r"E:/SteamLibrary/steamapps/common/Hearts of Iron IV")
ROOT = Path(__file__).resolve().parents[1]
HOME_TAG, TARGET_TAG = "VCI", "SOY"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig", errors="replace")


def block(text: str, key: str) -> str:
    m = re.search(r"\b" + key + r"\s*=\s*\{", text)
    i, depth = m.end(), 1
    while depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[m.end(): i - 1]


def capital_state(tag: str) -> int:
    hist = next((ROOT / "history/countries").glob(f"{tag} - *.txt"))
    return int(re.search(r"\bcapital\s*=\s*(\d+)", read(hist)).group(1))


def state_provinces(sid: int) -> list[int]:
    for p in (ROOT / "history/states").glob("*.txt"):
        t = read(p)
        if int(re.search(r"\bid\s*=\s*(\d+)", t).group(1)) == sid:
            return [int(x) for x in block(t, "provinces").split()]
    raise SystemExit(f"state {sid} not found")


coastal = {int(l.split(";")[0]) for l in read(ROOT / "map/definition.csv").splitlines()
           if l.count(";") >= 7 and l.split(";")[5] == "true"}
home_state = capital_state(HOME_TAG)
home = state_provinces(home_state)
target = state_provinces(capital_state(TARGET_TAG))
port = next((p for p in home if p in coastal), home[0])

src = read(GAME / "tutorial/tutorial.txt")
remap: dict[int, int] = {}


def prov(n: int) -> int:
    if n == 12766:
        return port
    if n not in remap:
        remap[n] = home[len(remap) % len(home)]
    return remap[n]


out = re.sub(r"\bstate\s*=\s*\d+", f"state = {home_state}", src)
out = re.sub(r"(highlight_states_trigger\s*=\s*\{)[^}]*\}", rf"\1 {home_state} }}", out)
out = re.sub(r"(direction_pointer\s*=\s*)(\d+)", lambda m: m.group(1) + str(prov(int(m.group(2)))), out)
out = re.sub(r"(highlight_provinces\s*=\s*\{)([^}]*)\}",
             lambda m: m.group(1) + " " + " ".join(str(prov(int(x))) for x in m.group(2).split()) + " }", out)
out = re.sub(r"(target\s*=\s*)(\d+)", lambda m: m.group(1) + str(target[0]), out)
out = re.sub(r'(target\s*=\s*)"?ETH"?', rf'\1"{TARGET_TAG}"', out)

dst = ROOT / "tutorial/tutorial.txt"
dst.parent.mkdir(exist_ok=True)
dst.write_text(out, encoding="utf-8")
left = re.findall(r"\b(?:state|target|direction_pointer)\s*=\s*\d{3,}|\b(?:ETH)\b", re.sub(r"#[^\n]*", "", out))
print("home state", home_state, "provinces", home[:5], "port", port, "target prov", target[0])
print("leftover vanilla ids:", left)
