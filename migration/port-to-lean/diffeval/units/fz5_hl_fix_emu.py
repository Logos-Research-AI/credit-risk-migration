"""Float emulation (revision af2ffda1: non-finite read back as +-big) of def:_hl_groups as corrected on 2026-11-18 (exact integer read-back of the three
floor values, comparisons in Int) and of the Lean before the change, on the random cases
(fz5_hl_groups.cases.json) and the targeted cases (fz5_hl_groups.tcases.json). Python floats stand in for
Lean's Float: ofInt = correctly rounded float(n) (inf on overflow), /, *, +, floor exact.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_hl_fix_emu.py
"""
import json, math, sys
from pathlib import Path
W = Path(__file__).resolve().parent.parent / "work"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "port"))
from credit_risk import sas_compat as sc

def ofInt(n):
    try: return float(n)
    except OverflowError: return math.inf if n > 0 else -math.inf
def floor(x): return float(math.floor(x)) if math.isfinite(x) else x
def toInt(x, fuel, big):
    neg = x < 0.0
    if not math.isfinite(x): return -big if neg else big
    ax = -x if neg else x
    acc, pw = 0, 1
    for _ in range(fuel):
        q = floor(ax / 2.0); r = ax - 2.0 * q
        acc += pw * (1 if 1.0 <= r else 0); pw *= 2; ax = q
    return -acc if neg else acc
def new(blocks, n, g):
    mx = max([abs(n), abs(g)] + [abs(b) for b in blocks])
    fuel = (mx.bit_length() - 1 if mx > 0 else 0) + 3   # Nat.log2 mx + 3
    big = sum(abs(b) for b in blocks) + 2 ** fuel
    m = toInt(floor(ofInt(n) / ofInt(g) + 0.5), fuel, big)
    groups, c = [], 0
    for nj in blocks:
        if c == 0 or (c < m and c + toInt(floor(0.5 * ofInt(nj)), fuel, big) <= m): c += nj
        else: groups.append(c); c = nj
    groups.append(c)
    if len(groups) > 1 and groups[-1] <= toInt(floor(0.05 * ofInt(n)), fuel, big):
        last = groups.pop(); groups[-1] += last
    return groups
def old(blocks, n, g):
    m = floor(ofInt(n) / ofInt(g) + 0.5)
    groups, c = [], 0
    for nj in blocks:
        if c == 0 or (ofInt(c) < m and ofInt(c) + floor(0.5 * ofInt(nj)) <= m): c += nj
        else: groups.append(c); c = nj
    groups.append(c)
    if len(groups) > 1 and ofInt(groups[-1]) <= floor(0.05 * ofInt(n)):
        last = groups.pop(); groups[-1] += last
    return groups
for name in ["cases", "tcases"]:
    cs = json.load(open(W / f"fz5_hl_groups.{name}.json"))
    on = nn = 0; left = []
    for c in cs:
        py = sc._hl_groups(list(c["blocks"]), c["n"], c["g"])
        assert py == c["py"]
        on += old(c["blocks"], c["n"], c["g"]) != py
        if new(c["blocks"], c["n"], c["g"]) != py: nn += 1; left.append(c["input"])
    print(name, len(cs), "old-differs", on, "new-differs", nn, left[:5])
