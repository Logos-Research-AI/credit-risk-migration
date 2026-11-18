"""Explanation of the fz_hl differences (rejected chunks of def:hosmer_lemeshow), task of 2026-11-17.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_hl_explain.py [out.txt]

Reads diffeval/work/fz_hl.json (cases, seeds) and the Lean outputs (default diffeval/work/fz_hl.out.txt, or the
re-evaluation given as argument). Writes nothing.

1. Re-runs the real port (sc.hosmer_lemeshow, chi2 stubbed as in the generator) on every seed of every case and
   checks the stored expected chunk digests.
2. For every seed, says which clause of def:hosmer_lemeshow_precond fails (Python rendering of the generator,
   split by clause).
3. Builds the Lean's semantics in Python: the port's own source with exactly two changes, the R-F2I narrowing of
   the Lean: `o1 = int(..sum())` -> `o1 = float(..sum())` (o1, and o0 = size - o1, stay floats) and the two
   observed columns Float64 instead of Int64 (the Lean's `.f64` columns; the generator compares them cast to
   Float64 anyway). pow2 = the pack's lookup table (as the Lean input), x*x elsewhere. If the chunk digests of
   this model equal the Lean's output on every chunk, the int() truncation accounts for the whole difference.
"""
from __future__ import annotations

import inspect
import json
import math
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz_hl_gen as g  # noqa: E402

sc = g.sc
WORK = HERE.parent / "work"

# ---------------------------------------------------------------- the Lean's semantics (R-F2I) from the port's source
src = textwrap.dedent(inspect.getsource(sc.hosmer_lemeshow))
CHANGES = [
    ("o1 = int(yy[start : start + size].sum())", "o1 = float(yy[start : start + size].sum())"),
    ("cols[2]: pl.Int64,", "cols[2]: pl.Float64,"),
    ("cols[4]: pl.Int64,", "cols[4]: pl.Float64,"),
    ("(o1 - e1) ** 2", "_POW2(o1 - e1)"),
    ("(o0 - e0) ** 2", "_POW2(o0 - e0)"),
]
for a, b in CHANGES:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
src = src.replace("def hosmer_lemeshow(", "def hl_lean_model(", 1)
ns = dict(vars(sc))
exec(compile(src, "hl_lean_model", "exec"), ns)  # noqa: S102
hl_lean_model = ns["hl_lean_model"]


def clauses(y, pd) -> list[str]:
    """The clauses of def:hosmer_lemeshow_precond that fail (generator's rendering, split)."""
    import numpy as np
    import polars as pl
    d = pl.DataFrame({"y": y.cast(pl.Float64), "p": pd.cast(pl.Float64)}).drop_nulls()
    if d.height == 0:
        return []
    p0 = np.asarray(d.get_column("p").to_numpy(), dtype=np.float64)
    y0 = np.asarray(d.get_column("y").to_numpy(), dtype=np.float64)
    o = np.argsort(p0, kind="stable")
    p, yy = p0[o], y0[o]
    n = len(p)
    bad = set()
    if n > 2**52:
        bad.add("(2) n")
    blocks, i = [], 0
    while i < n:
        j = int(p.searchsorted(float(p[i]) + 1e-6, side="right"))
        blocks.append(j - i)
        i = j
    starts = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64)
    p = np.repeat(p[starts], blocks)
    sizes = sc._hl_groups(blocks, n, 10)
    start = 0
    for size in sizes:
        if size == 0:
            bad.add("(6) size")
        o1 = float(yy[start:start + size].sum())
        e1 = size * min(max(float(p[start:start + size].sum()) / size, 1e-6), 0.999999)
        start += size
        o0, e0 = size - o1, size - e1
        if not math.isfinite(o1):
            bad.add("(3) finite")
        elif math.floor(o1) != o1:
            bad.add("(3) integral")
        if math.isfinite(o1) and abs(o1) > 4503599627370496.0:
            bad.add("(5) bound")
        for x in (o1 - e1, o0 - e0):
            if math.isfinite(x):
                try:
                    if not math.isfinite(x ** 2):
                        bad.add("(4) overflow")
                except OverflowError:
                    bad.add("(4) overflow")
    return sorted(bad)


def model_digest(y, pd, pt: dict[int, int]) -> int:
    import polars as pl

    def pow2(x: float) -> float:
        b = g.fb(x)
        return g.struct.unpack("<d", g.struct.pack("<Q", pt[b]))[0] if b in pt else x * x

    ns["_POW2"] = pow2
    ns["chi2_sf"] = g.stub_chi2
    table, chisq, dof, pv = hl_lean_model(y, pd)
    if table.height > 0:
        table = table.with_columns(pl.col("EventsObserved").cast(pl.Float64), pl.col("NoneventsObserved").cast(pl.Float64))
    return g.w(g.frame_tok(table) + g.otok(chisq) + [dof] + g.otok(pv))


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else WORK / "fz_hl.out.txt"
    suite = json.loads((WORK / "fz_hl.json").read_text())
    lean_lines = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    cases = suite["cases"]
    # pass 1: python digests and the pow2 table of each eval input (as the generator builds it)
    pts: dict[int, dict[int, int]] = {}
    per_case = []
    for c in cases:
        dgs = []
        for k in c["seeds"]:
            y, pd = g.build(g.params(k))
            dg, pt = g.run_py(y, pd)
            pts.setdefault(c["input"], {}).update(pt)
            dgs.append((k, y, pd, dg))
        per_case.append(dgs)
    stats = {"kept": [0, 0, 0, 0, 0], "rejected": [0, 0, 0, 0, 0]}  # chunks, py=exp, lean=exp, lean=model, seeds
    clause_count: dict[str, int] = {}
    seed_diff = {"kept": 0, "rejected": 0}
    for c, dgs in zip(cases, per_case, strict=True):
        kind = c["fz"]
        s = stats[kind]
        s[0] += 1
        s[4] += len(dgs)
        py_chunk = g.w([d[3] for d in dgs])
        lean = lean_lines[c["input"]][c["pos"]]
        s[1] += py_chunk == c["expected"]
        s[2] += lean == c["expected"]
        model = []
        for k, y, pd, dg in dgs:
            m = model_digest(y, pd, pts[c["input"]])
            model.append(m)
            seed_diff[kind] += m != dg
            cl = clauses(y, pd)
            key = kind + ": " + (", ".join(cl) if cl else "none")
            clause_count[key] = clause_count.get(key, 0) + 1
        s[3] += g.w(model) == lean
    for kind, s in stats.items():
        print(f"{kind}: chunks {s[0]} (seeds {s[4]}); python chunk digest = stored expected: {s[1]}; "
              f"lean = expected: {s[2]}; lean = R-F2I model of the port: {s[3]}; seeds where the model differs from the port: {seed_diff[kind]}")
    print("failing precondition clauses per seed:", json.dumps(clause_count, sort_keys=True))


if __name__ == "__main__":
    main()
