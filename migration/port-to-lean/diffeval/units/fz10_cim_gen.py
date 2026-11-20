"""Fidelity fuzz 2026-11-20 (label train-c) of def:classification_is_made on its precondition
def:classification_is_made_precond, against port/credit_risk/sas_compat.py:1653-1665 at port HEAD.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_cim_gen.py gen
      -> diffeval/work/fz10_cim.inputs.json   (the eval_decl inputs: item def:classification_is_made, decl
                                               classification_is_made, one input per block of BLOCK seeds)
         diffeval/work/fz10_cim.json           (blocks: seeds, expected per seed, class of each seed)
  ... cmp <outputs file>   (one Lean output per line, in input order) -> diffeval/work/fz10_cim.result.json

Inputs are built INSIDE Lean from the seed with the generator of fz4_cim_gen.py (imported unchanged: kit.hsh,
eight design modes with the edge pools NaN, +-inf, +-0, 1 +- ulp, 1e-300, 5e-324, 1e300; exact multiples / ties /
duplicate columns; the pivot threshold of _kept (1e-9 relative) approached to 1..3 ulps; 0..8 rows (empty x
included), 0..5 columns, fit.names longer / shorter than x.shape[1], a duplicate name, cov larger than names,
diagonal patterns 0 / -0.0 / NaN / 1e-300 / 5e-324 / inf). Routines (explicit parameters of the unit, RULEBOOK §3):
solve = Gaussian elimination with partial pivoting, matmul / dot = sequential sums from 0.0, written identically
in Lean and Python (fz4_cim_gen.solve_sa / NA.__matmul__).
Expected = the REAL sas_compat.classification_is_made (with _kept, _left_out) executed with those routines.

Precondition (def:classification_is_made_precond) rendered on the Python side: (1) x 2-D, ncols = x.shape[1] >= 0,
every row of length ncols: true by construction (x = np.array(rows).reshape(n, k)); (2) _kept_precond on matmul xT
rows: the stand-in returns a k x k list: square, true by construction; (3) _left_out_precond: cov square, side
>= len(names): true by construction. So every generated input is admitted.
Seeds on which the stand-in solve meets an exactly zero pivot are those where REAL np.linalg.solve raises
LinAlgError: outside the model by RULEBOOK §3 ("the inputs on which the routine raises ... are outside the model",
OPEN in the unit's trailer). They are NOT counted as kept; they are still compared (stand-in vs Lean) in blocks of
their own, as information.

Lean side, one Bool per block (the fz4 device): classification_is_made is evaluated on a fixed dummy (fit with
names ["Intercept"], cov [[0.0]], no row, routines returning zeros) whose result is `0 < ncols`; ncols is the term
`if every seed of the block that is compared gives the Python value (packed in E) then 1 else 0`. `true` = all
cases of the block equal. A planted block (one expected bit flipped) must return `false`.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_cim_gen as g  # noqa: E402

WORK = HERE.parent / "work"
LO, N, BLOCK = 2_000_000, 2600, 650
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"


def lean_block(seeds, exp, flip=None):
    """one input: the dummy call with ncols = the check of `seeds` (list) against exp (dict seed -> bool)."""
    E = 0
    for t, s in enumerate(seeds):
        if exp[s] ^ (flip == s):
            E |= 1 << t
    if seeds == list(range(seeds[0], seeds[0] + len(seeds))):  # consecutive: the list is built in Lean
        sl = f"((List.range {len(seeds)}).map (fun (t : Nat) => t + {seeds[0]}))"
    else:
        sl = "[" + ", ".join(str(s) for s in seeds) + "]"
    return (g.DUMMY + " (" + g.LEAN.rstrip() + f" let E : Nat := {hex(E)}; let SL : List Nat := {sl}; "
            f"if (List.range SL.length).all (fun (t : Nat) => one (SL.getD t 0) == Nat.testBit E t) then (1 : Int) else 0)")


def classify(inp, r):
    k, n, mode, rows, names, cov, zm = inp
    t = [f"mode{mode}", f"zm{zm}", "true" if r else "false"]
    if n == 0:
        t.append("no row")
    if k == 0:
        t.append("no column")
    if len(names) > k:
        t.append("names longer than x.shape[1]")
    if len(names) < k:
        t.append("names shorter")
    if len(set(names)) < len(names):
        t.append("duplicate name")
    if any(v != v for rw in rows for v in rw):
        t.append("NaN in x")
    if any(abs(v) == float("inf") for rw in rows for v in rw):
        t.append("inf in x")
    if any(cov[i][i] == 0.0 for i in range(len(names))):
        t.append("left-out non-empty")
    return t


def gen():
    exp, kept, outside, cnt = {}, [], [], Counter()
    for s in range(LO, LO + N):
        inp = g.seed_input(s)
        r, err = g.run(inp, False)
        if err and err.startswith("zero pivot"):
            # same stand-in call without the flag: the value the Lean must compute too
            g.FLAG["zero_pivot"] = False
            o = g.np.linalg.solve
            g.np.linalg.solve = g.solve_sa
            try:
                with g.np.errstate(all="ignore"):
                    k, n, mode, rows, names, cov, zm = inp
                    fit = g.sc.LogisticFit(names=names, beta=g.np.zeros(0),
                                           cov=g.np.array(cov, dtype=g.np.float64).reshape(len(cov), len(cov)),
                                           loglik=0.0, n_iter=0, converged=True)
                    r = bool(g.sc.classification_is_made(fit, g.na(g.np.array(rows, dtype=g.np.float64).reshape(n, k))))
            finally:
                g.np.linalg.solve = o
            exp[s] = r
            outside.append(s)
            cnt["outside (zero pivot: real solve raises LinAlgError)"] += 1
            continue
        if err:
            cnt["python raises: " + err.split(":")[0]] += 1
            continue
        exp[s] = r
        kept.append(s)
        for t in classify(inp, r):
            cnt[t] += 1
    blocks = []
    for cls, seeds in (("kept", kept), ("outside", outside)):
        for i in range(0, len(seeds), BLOCK):
            blocks.append({"class": cls, "seeds": seeds[i:i + BLOCK]})
    # planted: the first kept block with one bit flipped (must come back false)
    planted = {"class": "planted", "seeds": kept[:BLOCK], "flip": kept[0]}
    blocks.append(planted)
    inputs = [lean_block(b["seeds"], exp, b.get("flip")) for b in blocks]
    (WORK / "fz10_cim.json").write_text(json.dumps({
        "blueprint": BLUEPRINT, "item": "def:classification_is_made", "decl": "classification_is_made",
        "seeds": f"{LO}..{LO + N - 1}", "generated": N, "kept": len(kept), "outside": len(outside),
        "expected": {str(s): v for s, v in exp.items()}, "blocks": blocks, "reached": dict(cnt)}))
    (WORK / "fz10_cim.inputs.json").write_text(json.dumps(
        [{"item": "def:classification_is_made", "decl": "classification_is_made", "inputs": [t]} for t in inputs], indent=0))
    print("generated", N, "kept", len(kept), "outside", len(outside), "blocks", len(blocks),
          "max chars", max(len(t) for t in inputs))
    print(sorted(cnt.items()))


def cmp(path):
    s = json.loads((WORK / "fz10_cim.json").read_text())
    outs = [ln.strip() for ln in Path(path).read_text().splitlines()]
    assert len(outs) == len(s["blocks"]), (len(outs), len(s["blocks"]))
    res = []
    for b, o in zip(s["blocks"], outs):
        want = "false" if b["class"] == "planted" else "true"
        res.append({"class": b["class"], "covers": len(b["seeds"]), "first": b["seeds"][0], "got": o,
                    "status": "PASS" if o == want else ("ERROR" if o.startswith("ERROR") else "FAIL")})
    (WORK / "fz10_cim.result.json").write_text(json.dumps(res))
    c = Counter((r["class"], r["status"]) for r in res)
    cases = Counter()
    for r in res:
        cases[(r["class"], r["status"])] += r["covers"]
    print(dict(c))
    print("cases", dict(cases))


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen()
    else:
        cmp(sys.argv[2])
