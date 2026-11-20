"""Fidelity pass 2026-11-20 (label train-b): def:_kept (sas_compat.py:772-787, port HEAD 4a757fb).

No carrier item exists on the blueprint and none may be added, so the sweep runs INSIDE the `solve` argument of one
eval_decl call on item def:_solve_sas (def:_kept is a dependency of it, so `_kept` is in scope there):
`_solve_sas solve0 dot0 (.d2 [[1.0]]) (.d1 [0.0])` keeps index 0 and calls solve0 once on the plain path; solve0
ignores its arguments, runs `_kept solve dot (.d2 (mk s))` for every seed of the input and returns, per chunk of
10 seeds, 0.0 when the chunk digest equals the Python one embedded in the input, else the Lean digest mod 2^52.

Cases (seed s, built inside Lean from hsh and mirrored here; matrix builder `mk` and pools from fz5_kept_gen.py,
loaded unchanged): a square n x n matrix, n = 0..5, mode 0..6 (0 symmetric from edge pools: 0, -0, NaN, +-inf,
5e-324, 1e-9, 1e300 ...; 1 X'X of a small integer matrix with duplicated columns (exactly singular, the X28 shape);
2 the same with scaled columns; 3 the second pivot on the threshold 1e-9 * a[1,1], +-3 ulp; 4 asymmetric; 5 rank one;
6 diagonal d, off-diagonal d * r with r one ulp to 1e-8 below 1).
Hand edge matrices (fz5_kept_hand.CASES: the empty matrix, 1 x 1 of 0, -0, NaN, inf, 5e-324, 1e-9, singular 2 x 2,
...) are the seeds 100000 + k of the same sweep (`--hand`).

Routines (explicit parameters of the Lean, RULEBOOK section 3), written identically on both sides:
  solve  Gaussian elimination with partial pivoting (first strict max of |.|), no raise: the Lean text is
         fz5_kept_gen.SOLVE, the Python mirror fz3_s03_gen.solve_sa (same algorithm and operation order)
  dot    sequential sum from 0.0 (Python: `c @ x` through an ndarray subclass whose 1-D @ 1-D is that sum)
Python runs the REAL sas_compat._kept with np.linalg.solve patched. Class `zero_pivot`: the stand-in met an exactly
zero pivot, where the real np.linalg.solve would raise LinAlgError (outside the model, RULEBOOK 3); such seeds are
still compared (the Lean takes the same stand-in) and counted apart.
Precondition def:_kept_precond (a 2-D array, every row as long as the number of rows) holds by construction:
every generated input is kept.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_kept_gen.py
      writes work/fz10_kept.inputs.json (seeds 0..2399 in 2 inputs, hand cases in a third); --show K; --cmp
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz3_s03_gen as f3  # noqa: E402
import fz5_kept_gen as k5  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

W = HERE.parent / "work"
# fz5_kept_hand.py runs its CLI at import: take its CASES list only (source up to `def run`), unchanged
_HS = (HERE / "fz5_kept_hand.py").read_text()
_hns: dict = {}
exec(_HS[_HS.index("NAN, INF"):_HS.index("def run")], {"math": __import__("math")}, _hns)  # noqa: S102


class kh:  # noqa: N801
    CASES = _hns["CASES"]

M64 = (1 << 64) - 1
OFF = 14695981039346656037
RANGES = [(0, 1200), (1200, 1200)]
HAND0 = 100000


def mx(h, x):
    g = ((h ^ x) * 1099511628211) & M64
    return g ^ (g >> 32)


def matrix(s):
    return kh.CASES[s - HAND0] if s >= HAND0 else k5.mk(s)


def py_kept(m):
    n = len(m)
    arr = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            arr[i, j] = m[i][j]
    f3.FLAG["zero_pivot"] = False
    o = np.linalg.solve
    np.linalg.solve = f3.solve_sa
    try:
        with np.errstate(all="ignore"):
            k = sc._kept(arr.view(f3.NA))  # pyright: ignore[reportPrivateUsage]
    finally:
        np.linalg.solve = o
    return [int(x) for x in k], f3.FLAG["zero_pivot"]


def seed_dg(s):
    k, _ = py_kept(matrix(s))
    h = OFF
    for t in [len(k)] + k:
        h = mx(h, t & M64)
    return h


def chunks(seeds):
    out = []
    for c in range(0, len(seeds), 10):
        h = OFF
        for s in seeds[c:c + 10]:
            h = mx(h, seed_dg(s))
        out.append(h)
    return out


def hand_lean():
    rows = ", ".join("[" + ", ".join("[" + ", ".join(k5.lit(v) for v in r) + "]" for r in m) + "]" for m in kh.CASES)
    return f"let HAND : List (List (List Float)) := [{rows}]; "


def lean_input(lo, n, exp, hand=False):
    mat = (f"(HAND.getD (s - {HAND0}) [])" if hand else "(mk s)")
    body = (k5.PRE + (hand_lean() if hand else "")
            + "let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
            + f"let EXP : List UInt64 := [{', '.join(str(x) for x in exp)}]; "
            + f"let sd := fun (s : Nat) => let k := _kept solve dot (Np.NDArray.d2 {mat}); "
            + "((k.length : Int) :: k).foldl (fun (h : UInt64) (t : Int) => mx h (UInt64.ofInt t)) 14695981039346656037; "
            + f"let NS : Nat := {n}; "
            + f"(List.range ((NS + 9) / 10)).map (fun (c : Nat) => let h : UInt64 := (((List.range 10).filter (fun (i : Nat) => c * 10 + i < NS)).map (fun (i : Nat) => sd ({lo} + c * 10 + i))).foldl mx 14695981039346656037; "
            + "if h == EXP.getD c 0 then 0.0 else Float.ofNat (h.toNat % 4503599627370496))")
    return "(α := Float) (fun (_ : List (List Float)) (_ : List Float) => " + body + ") (fun (_ _ : List Float) => 0.0) (Np.NDArray.d2 [[1.0]]) (Np.NDArray.d1 [0.0])"


def stats(seeds):
    st = Counter()
    for s in seeds:
        m = matrix(s)
        k, zp = py_kept(m)
        st["n=%d" % len(m)] += 1
        st["all kept" if len(k) == len(m) else ("none kept" if not k else "partial")] += 1
        st["zero_pivot"] += zp
        if s < HAND0:
            st["mode%d" % (k5.hsh(s, 1) % 7)] += 1
    return dict(st)


def main():
    if sys.argv[1:2] == ["--show"]:
        print(json.loads((W / "fz10_kept.inputs.json").read_text())[int(sys.argv[2])]["input"])
        return
    if sys.argv[1:2] == ["--cmp"]:
        ins = json.loads((W / "fz10_kept.inputs.json").read_text())
        outs = (W / "fz10_kept.out.txt").read_text().splitlines()
        tot = bad = 0
        for c, o in zip(ins, outs):
            vals = [float(x) for x in o.replace("[", " ").replace("]", " ").replace(",", " ").split()]
            assert len(vals) == len(c["expected_chunks"]), (len(vals), len(c["expected_chunks"]))
            tot += c["count"]
            for j, v in enumerate(vals):
                if v != 0.0:
                    bad += 1
                    print("DIFF chunk seeds from", c["start"] + 10 * j, "lean digest", v)
        print(json.dumps({"cases": tot, "differing_chunks": bad, "inputs": len(ins), "outputs": len(outs)}))
        return
    out = []
    for lo, n in RANGES:
        seeds = list(range(lo, lo + n))
        exp = chunks(seeds)
        out.append({"item": "def:_solve_sas", "decl": "_solve_sas", "start": lo, "count": n, "expected_chunks": exp,
                    "input": lean_input(lo, n, exp), "stats": stats(seeds)})
    hs = list(range(HAND0, HAND0 + len(kh.CASES)))
    exp = chunks(hs)
    out.append({"item": "def:_solve_sas", "decl": "_solve_sas", "start": HAND0, "count": len(hs), "expected_chunks": exp,
                "input": lean_input(HAND0, len(hs), exp, hand=True), "stats": stats(hs)})
    for o in out:
        print(o["start"], o["count"], len(o["input"]), o["stats"])
    (W / "fz10_kept.inputs.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
