"""Fuzz of def:_hl_groups / def:_hl_groups_precond (update 2026-11-18, fifth diff), by a non-author.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_hl_groups_gen.py

Precondition (def:_hl_groups_precond): g != 0 (blocks, n unconstrained). Rendered as `g != 0`.
Per seed s (hsh of diffeval/kit.py, mirrored here; all arithmetic on integers):
  blocks: L = (hsh(s,1)>>8) % 13 entries; mode = (hsh(s,2)>>8) % 10; entry i, u = hsh(s+1000,i):
     mode 0-7: (u>>20) % 31;  mode 8: BS[(u>>20) % 18];  mode 9: BS[12 + (u>>20) % 6]  (large values)
  n: if (hsh(s,3)>>8) % 10 < 6 then sum(blocks) else with k = (hsh(s,3)>>20) % 3: k<2 NP[(hsh(s,3)>>24) % len NP] else (hsh(s,3)>>24) % 201
  g: if (hsh(s,4)>>8) % 20 < 12 then 10 else GP[(hsh(s,4)>>20) % len GP]
Pools hold 0, +-1, the thresholds of the unit (n/10 + 0.5 at x.5: 5, 15, 25; floor(0.05 n) at 20, 60), 2^52, 2^53, 2^53+1,
2^62, 2^64+3, 1e20, 10^310 (Python raises: OverflowError).
Expected: sas_compat._hl_groups itself. Classes: g == 0 (rejected, Python raises: dropped); admitted and Python
raises (defect, not sent); admitted and returns (kept, sent). Lean gets seeds base..base+N-1 and a list of the
expected 32-bit digests (-1 = not sent); it returns [number evaluated, seeds whose digest differs].
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

BP = "5365851c-5549-44b7-9207-4bd4c422031d"
BS = [0, 1, 1, 2, 3, 5, 10, 15, 20, -1, -5, 7, 4503599627370496, 9007199254740992, 9007199254740993,
      4611686018427387904, 18446744073709551619, 10**20]
NP = [0, 1, 2, 5, 9, 10, 11, 14, 15, 16, 19, 20, 21, 25, 59, 60, 61, 100, -1, -10, 4503599627370496, 4503599627370497,
      9007199254740992, 9007199254740993, 1152921504606846976, 10**20, 10**310]
GP = [1, 2, 3, 4, 5, 7, 10, 20, 100, -1, -10, 0, 9007199254740993, 10**20, 8]
h = kit.hsh


def blocks_of(s):
    L = (h(s, 1) >> 8) % 13
    mode = (h(s, 2) >> 8) % 10
    out = []
    for i in range(L):
        u = h(s + 1000, i)
        if mode < 8:
            out.append((u >> 20) % 31)
        elif mode < 9:
            out.append(BS[(u >> 20) % len(BS)])
        else:
            out.append(BS[12 + (u >> 20) % 6])
    return out


def n_of(s, bl):
    if (h(s, 3) >> 8) % 10 < 8:
        return sum(bl)
    k = (h(s, 3) >> 20) % 3
    return NP[(h(s, 3) >> 24) % len(NP)] if k < 2 else (h(s, 3) >> 24) % 201


def g_of(s):
    return 10 if (h(s, 4) >> 8) % 20 < 14 else GP[(h(s, 4) >> 20) % len(GP)]


def toks(r):
    out = [len(r)]
    for n in r:
        out += [2 if n < 0 else 1, abs(n) % 2**64, (abs(n) >> 64) % 2**64]
    return out


def lit(x):
    return f"({x} : Int)" if x < 0 else (f"{x}" if x < 10**30 else f"((10 : Int) ^ {len(str(x)) - 1})")


def fmt_int(x):
    return str(x) if x >= 0 else f"({x})"


def main(base0=700000, total=2200, per=200):
    cnt = Counter()
    defects, cases = [], []
    for s in range(base0, base0 + total):
        bl = blocks_of(s); n = n_of(s, bl); g = g_of(s)
        if g == 0:
            cnt["rejected_raises"] += 1; continue
        try:
            r = sc._hl_groups(list(bl), n, g)
        except Exception as e:  # noqa: BLE001
            cnt["defect"] += 1; defects.append((s, len(str(n)), g, f"{type(e).__name__}")); continue
        cnt["kept"] += 1
        inp = f"(\u03b1 := Float) [{','.join(fmt_int(b) for b in bl)}] {fmt_int(n)} {fmt_int(g)}".replace("\\u03b1", "\u03b1")
        cases.append({"seed": s, "input": inp, "blocks": bl, "n": n, "g": g, "py": r})
    cases = cases[:2000] if len(cases) > 2000 else cases
    W = HERE.parent / "work"
    (W / "fz5_hl_groups.cases.json").write_text(json.dumps(cases))
    chunks = [cases[i:i + per] for i in range(0, len(cases), per)]
    for ci, ch in enumerate(chunks):
        (W / f"fz5_hl_groups.in{ci}.json").write_text(json.dumps([c["input"] for c in ch], ensure_ascii=False))
    (W / "fz5_hl_groups.fuzz.json").write_text(json.dumps({"generated": total, **cnt, "defects": [d[0] for d in defects]}, indent=1))
    print(dict(cnt), len(cases), len(chunks)); print("defects", defects[:8])
    print(sum(len(c["input"]) for c in cases), "input chars")


main()
