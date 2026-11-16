"""Fuzz pass, def:fe_run_02b_medians_all (port-translator-6): smallest MonthlyIncome lists on which
polars' Series.median returns a zero of another sign than the model "stable sort (-0.0 and 0.0
equal, input order kept), middle value, or the lower of the two middle values when they are equal".
  PYTHONPATH=../../port uv run --project ../../port python experiments/fz_t4_zero_median_min.py"""
import itertools, struct
import polars as pl
b = lambda x: struct.unpack("<Q", struct.pack("<d", x))[0]
def model(v):
    s = sorted(v)  # stable; -0.0 == 0.0 compare equal
    n = len(s)
    if n % 2: return s[n // 2]
    a, c = s[n // 2 - 1], s[n // 2]
    return a if a == c else 0.5 * (c - a) + a
found = 0
for n in range(1, 8):
    for v in itertools.product([-1.0, -0.0, 0.0, 1.0], repeat=n):
        m = pl.Series(list(v), dtype=pl.Float64).drop_nulls().median()
        g = pl.DataFrame({"g": [1] * n, "x": list(v)}).group_by("g", maintain_order=True).agg(pl.col("x").median())["x"][0]
        if b(m) != b(model(v)):
            found += 1
            if found <= 12: print(n, list(v), "polars Series", repr(m), "model", repr(model(v)), "group_by median", repr(g))
    if found: print("length", n, "differing lists so far", found); 
    if found > 12: break

# reduction of the two lists the fuzz found (seeds 11164 and 11214 of diffeval/units/fz_t4_gen.py)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diffeval" / "units"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diffeval"))
import fz_t4_gen as g
pm = lambda v: pl.Series(v, dtype=pl.Float64).drop_nulls().median()
differs = lambda v: len(v) > 0 and b(pm(v)) != b(model(v))
for seed in (11164, 11214):
    v = [x for x in g.mk02(seed)[1]["MonthlyIncome"].to_list() if x is not None]
    assert differs(v), seed
    changed = True
    while changed:
        changed = False
        for i in range(len(v)):
            w = v[:i] + v[i + 1:]
            if differs(w):
                v, changed = w, True
                break
        if not changed:  # simplify values: replace each non-zero by +-1.0
            for i, x in enumerate(v):
                if x != 0 and abs(x) != 1.0:
                    w = v[:i] + [1.0 if x > 0 else -1.0] + v[i + 1:]
                    if differs(w):
                        v, changed = w, True
                        break
    print("seed", seed, "reduced to", len(v), "values:", [repr(x) for x in v], "polars", repr(pm(v)), "model", repr(model(v)))
# shortest pattern search: k times -1.0, zeros, k times 1.0 in fixed arrangements
for n in range(8, 40):
    hit = None
    for z in ([0.0, -0.0], [-0.0, 0.0]):
        for pos in range(n - 1):
            k = (n - 2) // 2
            rest = [-1.0] * k + [1.0] * (n - 2 - k)
            v = rest[:pos] + [z[0]] + rest[pos:]
            for pos2 in range(pos + 1, n):
                w = v[:pos2] + [z[1]] + v[pos2:]
                if differs(w):
                    hit = w
                    break
            if hit: break
        if hit: break
    if hit:
        print("shortest two-zero list found: length", n, [repr(x) for x in hit], "polars", repr(pm(hit)), "model", repr(model(hit)))
        break
