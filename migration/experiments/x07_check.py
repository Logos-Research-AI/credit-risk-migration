"""Compare x07_roc_ties.log with candidate tie rules. Usage: python3 x07_check.py"""

import json
import math
import re
import struct
from itertools import product
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
EPS = math.sqrt(2.0**-53)


def unhex(h: str) -> float:
    return struct.unpack(">d", bytes.fromhex(h))[0]


def hx(x: float) -> str:
    return struct.pack(">d", x).hex().upper()


def groups_top(vals, eps, strict=False, form="diff"):
    """Greedy grouping from the largest down; returns {value: group index}, larger index = higher."""
    out, top, gi = {}, None, 0
    for v in sorted(set(vals), reverse=True):
        if top is None:
            top = v
        else:
            if form == "diff":
                d = top - v
                same = d < eps if strict else d <= eps
            elif form == "sub":
                same = v > top - eps if strict else v >= top - eps
            else:
                same = v + eps > top if strict else v + eps >= top
            if not same:
                top, gi = v, gi - 1
        out[v] = gi
    return out


def groups_bottom(vals, eps):
    out, bot, gi = {}, None, 0
    for v in sorted(set(vals)):
        if bot is None:
            bot = v
        elif v - bot > eps:
            bot, gi = v, gi + 1
        out[v] = gi
    return out


def counts_grouped(rows, gmap):
    nc = nd = nt = 0
    ev = [gmap[p] for p, y in rows if y == 1]
    ne = [gmap[p] for p, y in rows if y == 0]
    for a, b in product(ev, ne):
        nc += a > b
        nd += a < b
        nt += a == b
    return nc, nd, nt


def counts_pairwise(rows, eps):
    nc = nd = nt = 0
    for a, b in product([p for p, y in rows if y == 1], [p for p, y in rows if y == 0]):
        if abs(a - b) <= eps:
            nt += 1
        elif a > b:
            nc += 1
        else:
            nd += 1
    return nc, nd, nt


RULES = {
    "top ROCEPS <= (diff)": lambda r: counts_grouped(r, groups_top([p for p, _ in r], EPS)),
    "top ROCEPS <  (diff)": lambda r: counts_grouped(r, groups_top([p for p, _ in r], EPS, strict=True)),
    "top ROCEPS <= (v >= top-eps)": lambda r: counts_grouped(r, groups_top([p for p, _ in r], EPS, form="sub")),
    "top ROCEPS <= (v+eps >= top)": lambda r: counts_grouped(r, groups_top([p for p, _ in r], EPS, form="add")),
    "top 1e-8": lambda r: counts_grouped(r, groups_top([p for p, _ in r], 1e-8)),
    "bottom ROCEPS": lambda r: counts_grouped(r, groups_bottom([p for p, _ in r], EPS)),
    "pairwise ROCEPS": lambda r: counts_pairwise(r, EPS),
    "pairwise 1e-8 (port before P1)": lambda r: counts_pairwise(r, 1e-8),
}

log = (HERE / "x07_roc_ties.log").read_text()
text = re.sub(r"\n(?=(StdErr|LowerArea|UpperArea|SomersD|Gamma|TauA|Label2|nValue\d)=)", " ", log)
roc = {}
for ln in text.splitlines():
    if ln.startswith("X07 roc "):
        kv = dict(re.findall(r"(\w+)=(\S+)", ln))
        roc[int(kv["g"])] = kv
groups = json.loads((HERE / "x07_groups.json").read_text())
print(f"groups {len(groups)}, SAS rows {len(roc)}")

# --- A: which tie rule gives SAS's Area, group by group
fails = {k: [] for k in RULES}
for g in groups:
    if g["part"] != "A":
        continue
    rows = [(unhex(p), y) for p, y in g["rows"]]
    n1 = sum(y for _, y in rows)
    n0 = len(rows) - n1
    sas = unhex(roc[g["g"]]["Area"])
    for name, rule in RULES.items():
        nc, nd, nt = rule(rows)
        if (nc + 0.5 * nt) / (n1 * n0) != sas:
            fails[name].append(g["tag"])
print("\nA. groups whose SAS Area a rule does NOT reproduce (of", sum(g["part"] == "A" for g in groups), ")")
for name, f in fails.items():
    print(f"  {name:34s} {len(f):3d}  {', '.join(f[:6])}{' ...' if len(f) > 6 else ''}")
for tag in ("exact_0_eps_evtop", "above_0_eps_evtop", "below_0_eps_evtop", "exact_eps_2eps_evtop",
            "exact_pow2_evtop", "exact_0_eps_netop", "p1_step_witness", "p1_stage_witness",
            "chain_ev_bottom", "chain_ev_top", "chain_ev_mid"):
    g = next(x for x in groups if x["tag"] == tag)
    print(f"  {tag:24s} SAS Area = {unhex(roc[g['g']]['Area'])!r}")
for base in ("0.5", "0.3", "0.123456"):
    for k in range(-2, 4):
        g = next(x for x in groups if x["tag"] == f"scan_{base}_k{k}_evtop")
        lo, hi = unhex(g["rows"][0][0]), unhex(g["rows"][1][0])
        print(f"  scan base {base} k={k:2d} top-base {'<=' if hi - lo <= EPS else '> '} ROCEPS (diff {hx(hi - lo)})"
              f"  SAS Area {unhex(roc[g['g']]['Area'])}")


# --- B: operation order of Area and the other columns (grouping: top, ROCEPS, <=)
def stats(rows):
    gm = groups_top([p for p, _ in rows], EPS)
    ev = np.sort(np.array([gm[p] for p, y in rows if y == 1], dtype=np.float64))
    ne = np.sort(np.array([gm[p] for p, y in rows if y == 0], dtype=np.float64))
    n1, n0 = len(ev), len(ne)
    lo_ne, le_ne = np.searchsorted(ne, ev, "left"), np.searchsorted(ne, ev, "right")
    lo_ev, le_ev = np.searchsorted(ev, ne, "left"), np.searchsorted(ev, ne, "right")
    nc, nt = int(lo_ne.sum()), int((le_ne - lo_ne).sum())
    nd = n1 * n0 - nc - nt
    v10 = (lo_ne + 0.5 * (le_ne - lo_ne)) / n0
    v01 = ((n1 - le_ev) + 0.5 * (le_ev - lo_ev)) / n1
    t, n = n1 * n0, n1 + n0
    area = (nc + 0.5 * nt) / t
    se = math.sqrt(float(np.var(v10, ddof=1)) / n1 + float(np.var(v01, ddof=1)) / n0) if n1 > 1 and n0 > 1 else None
    return {
        "Area": {"(nc+0.5nt)/t": area, "nc/t+0.5*(nt/t)": nc / t + 0.5 * (nt / t),
                 "(nc+0.5nt)/n1/n0": (nc + 0.5 * nt) / n1 / n0, "mean(v10)": float(np.sum(v10)) / n1,
                 "mean(v01)": float(np.sum(v01)) / n0, "0.5*(1+(nc-nd)/t)": 0.5 * (1 + (nc - nd) / t)},
        "StdErr": {"DeLong (port)": se},
        "LowerArea": {"port": None if se is None else area - 1.959963984540054 * se},
        "UpperArea": {"port": None if se is None else area + 1.959963984540054 * se},
        "SomersD": {"(nc-nd)/t (port)": (nc - nd) / t, "2*Area-1": 2 * area - 1, "nc/t-nd/t": nc / t - nd / t},
        "Gamma": {"(nc-nd)/(nc+nd) (port)": (nc - nd) / (nc + nd) if nc + nd else None},
        "TauA": {"(nc-nd)/(n(n-1)/2) (port)": (nc - nd) / (n * (n - 1) / 2),
                 "(nc-nd)/(0.5*n*(n-1))": (nc - nd) / (0.5 * n * (n - 1))},
    }


def sasval(s):
    return None if set(s) <= {"."} else unhex(s)


tally: dict = {}
worst: dict = {}
nB = 0
for g in groups:
    rows = [(unhex(p), y) for p, y in g["rows"]]
    st = stats(rows)
    nB += 1
    for col, cands in st.items():
        sas = sasval(roc[g["g"]].get(col, "."))
        for name, v in cands.items():
            key = (col, name)
            exact = v == sas
            if col in ("LowerArea", "UpperArea") and v is not None and sas is not None:
                exact = max(0.0, min(1.0, v)) == sas or exact
            tally[key] = tally.get(key, 0) + exact
            if v is not None and sas is not None and not exact:
                worst[key] = max(worst.get(key, 0.0), abs(v - sas))
print(f"\nB. bit-exact matches over all {nB} groups (A and B), per column and formula; max abs error of the rest")
for (col, name), k in tally.items():
    print(f"  {col:10s} {name:28s} {k:3d}/{nB}   {worst.get((col, name), 0.0):.3g}")

# --- C: Association table of a fitted model
print("\nC. fitted-model Association table: tied pairs by rule against SAS (Percent Tied * Pairs / 100)")
for seed in (1, 2, 3, 4):
    rows, assoc = [], {}
    for ln in text.splitlines():
        if ln.startswith(f"X07 C{seed} row "):
            kv = dict(re.findall(r"(\w+)=(\S+)", ln))
            rows.append((unhex(kv["p"]), int(kv["y"])))
        elif ln.startswith(f"X07 C{seed} assoc "):
            m = re.match(r"X07 C\d assoc Label1=(.+?) nValue1=(\S+) nValue1=\S+ Label2=(.+?) nValue2=(\S+)", ln)
            assert m, ln
            assoc[m.group(1)], assoc[m.group(3)] = unhex(m.group(2)), unhex(m.group(4))
    pairs = assoc["Pairs"]
    sas = tuple(round(assoc[k] * pairs / 100) for k in ("Percent Concordant", "Percent Discordant", "Percent Tied"))
    print(f"  seed {seed}: n={len(rows)} pairs={pairs:.0f} SAS (nc, nd, nt) = {sas}")
    for name, rule in RULES.items():
        c = rule(rows)
        print(f"     {name:34s} {c}  {'MATCH' if c == sas else ''}")
    nc, nd, nt = sas
    n = len(rows)
    for lab, cands in {
        "c": {"(nc+0.5nt)/t": (nc + 0.5 * nt) / pairs},
        "Somers' D": {"(nc-nd)/t": (nc - nd) / pairs, "nc/t-nd/t": nc / pairs - nd / pairs},
        "Gamma": {"(nc-nd)/(nc+nd)": (nc - nd) / (nc + nd)},
        "Tau-a": {"(nc-nd)/(n(n-1)/2)": (nc - nd) / (n * (n - 1) / 2)},
        "Percent Tied": {"100*nt/t": 100.0 * nt / pairs},
        "Percent Concordant": {"100*nc/t": 100.0 * nc / pairs},
    }.items():
        print("     ", lab, {k: ("exact" if v == assoc[lab] else f"off {v - assoc[lab]:.2g}") for k, v in cands.items()})
