"""Fuzz pass 2026-11-16, port-translator-2: def:metrics_run_06_psi (metrics_calculation.py:325-401),
a unit I reviewed and did not write.

  from migration/port-to-lean:
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_psi_gen.py
      -> diffeval/work/fz_psi.json, .inputs.json, .fuzz.json, fz_psi.in<k>.txt
  eval_decl each input on def:zz_carrier_m / zz_carrier_m (text exactly as in work/fz_psi.inputs.json)
  python3 diffeval/fuzz_collect.py 2 fz_psi; compare.py; python3 diffeval/fuzz_receipt.py fz_psi

One generated input = one seed s: two one-column frames (credit_risk_score), training and validation,
built INSIDE Lean from s with kit.GEN and mirrored here with kit.gF / kit.gI / kit.hsh:
  rows     SZ[hsh(s, 9001) % 10] training rows, SZ[hsh(s, 9002) % 10] validation rows,
           SZ = 0, 1, 2, 3, 5, 9, 10, 11, 20, 37
  column   a mode per frame from hsh(s, 9003) % 8 (training), hsh(s, 9004) % 8 (validation):
           0-2  gF: 60 % from the edge pool E (null, NaN, +-inf, +-0.0, +-1e300, 1e-300, the smallest
                subnormal, 700 and one ulp either side, 650, 2^53, 1, 4), else a random float of
                either sign with exponent in [-3, 3]
           3-4  six levels 600, 610, .. 650, each exactly or one ulp below / above (so a validation
                score sits on a training cut, or one ulp either side), 10 % nulls: ties on every cut
           5-6  forty levels 500 + 7k, 5 % nulls
           7    an Int64 column (values -3 .. 8, 10 % nulls): outside the precondition
           the validation column uses the seed s + 500000.
Expected: lines 325-401 of the source, executed verbatim on the two frames (as t15_gen.py does).
One generated input gives one digest of (psi_calculation, psi_summary). A block of seeds returns
three integers, each the fold W of the digests of one class of seeds, in seed order (the class is
computed in Lean from the same hashes):
  kept      the precondition admits the input (fz "kept")
  rows      rejected only by the clause "at least one row in each frame" (fz "rejected")
  dtype     rejected by the clause "credit_risk_score is Float64" (an Int64 column) (fz "rejected")
def:metrics_run_06_psi_precond rendered in Python: distinct column names and equal column lengths
hold by construction (one column per frame); `0 < height` of each frame is `height > 0`; the
Float64 clause is `schema["credit_risk_score"] == pl.Float64` for each frame.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402

U = "metrics_run_06_psi"
WORK = HERE.parent / "work"
S0, BLOCK, NBLOCK = 20000, 500, 7
SZ = [0, 1, 2, 3, 5, 9, 10, 11, 20, 37]
nan, inf = float("nan"), float("inf")
E = [None, nan, inf, -inf, 0.0, -0.0, 1e300, -1e300, 1e-300, 5e-324, 700.0, math.nextafter(700.0, inf),
     math.nextafter(700.0, -inf), 650.0, 2.0**53, 1.0, 4.0]

lines = Path(mc.__file__).read_text().splitlines(keepends=True)
assert "psi_cuts: the nine nearest-rank deciles" in lines[324] and lines[400].strip() == ")" and lines[401].strip() == ""
assert "train_scores_sorted = " in lines[327] and "otherwise(pl.lit(\"Significant change\"))" in lines[399]
SLICE = compile(textwrap.dedent("".join(lines[324:401])), "metrics_calculation.py:325-401", "exec")


def run_slice(t: pl.DataFrame, v: pl.DataFrame):
    ns = dict(vars(mc))
    ns.update(logit_scored_train=t, logit_scored_valid=v)
    exec(SLICE, ns)
    return ns["psi_calculation"], ns["psi_summary"]


def md(h: int) -> int:
    return 0 if h < 3 else 1 if h < 5 else 2 if h < 7 else 3


def fb(bits: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


def column(s: int, n: int, m: int) -> pl.Series:
    if m == 0:
        return pl.Series("credit_risk_score", kit.gF(s, n, 60, 3, E), dtype=pl.Float64, nan_to_null=False)
    if m == 1:
        a, b = kit.gI(s, n, 10, 6, 0), kit.gI(s + 1, n, 0, 3, 0)
        vals = [None if x is None else fb(b4.raw(float(600 + 10 * x)) + y - 1) for x, y in zip(a, b, strict=True)]
        return pl.Series("credit_risk_score", vals, dtype=pl.Float64)
    if m == 2:
        return pl.Series("credit_risk_score", [None if x is None else float(500 + 7 * x) for x in kit.gI(s, n, 5, 40, 0)], dtype=pl.Float64)
    return pl.Series("credit_risk_score", kit.gI(s, n, 10, 12, 3), dtype=pl.Int64)


def frames(s: int):
    nt, nv = SZ[kit.hsh(s, 9001) % 10], SZ[kit.hsh(s, 9002) % 10]
    mt, mv = md(kit.hsh(s, 9003) % 8), md(kit.hsh(s, 9004) % 8)
    return pl.DataFrame([column(s, nt, mt)]), pl.DataFrame([column(s + 500000, nv, mv)]), (nt, nv, mt, mv)


def one(s: int):
    """(class, digest or None when Python raises, message)"""
    t, v, (nt, nv, mt, mv) = frames(s)
    # the precondition, clause by clause
    f64 = t.schema["credit_risk_score"] == pl.Float64 and v.schema["credit_risk_score"] == pl.Float64
    rows = t.height > 0 and v.height > 0
    cls = 2 if not f64 else (0 if rows else 1)
    assert (mt == 3 or mv == 3) == (not f64) and (nt > 0 and nv > 0) == rows
    try:
        pc, ps = run_slice(t, v)
    except Exception as ex:  # noqa: BLE001
        return cls, None, f"{type(ex).__name__}: {ex}"
    return cls, cmp.digest(cmp.tokens(cmp.canon_frame(pc)) + cmp.tokens(cmp.canon_frame(ps))), ""


EL = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in E) + "]"
LETS = (b4.W
        + f"let SZ : List Nat := {SZ}; let E : List (Option Float) := {EL}; "
        + "let MD := fun (h : Nat) => if h < 3 then (0 : Nat) else if h < 5 then 1 else if h < 7 then 2 else 3; "
        + "let COL := fun (s n m : Nat) => (if m == 0 then Pl.Col.f64 (gF s n 60 3 E) "
          "else if m == 1 then Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => "
          "some (Float.ofBits ((Float.ofInt (600 + 10 * a)).toBits + b.toNat.toUInt64 - 1)) | _, _ => none : Option Float)) (gI s n 10 6 0) (gI (s + 1) n 0 3 0)) "
          "else if m == 2 then Pl.Col.f64 ((gI s n 5 40 0).map (fun (o : Option Int) => o.map (fun (a : Int) => Float.ofInt (500 + 7 * a)))) "
          "else Pl.Col.int (gI s n 10 12 3) : Pl.Col Float); "
        + "let ONE := fun (s : Nat) => let nt := SZ.getD ((hsh s 9001).toNat % 10) 0; let nv := SZ.getD ((hsh s 9002).toNat % 10) 0; "
          "let mt := MD ((hsh s 9003).toNat % 8); let mv := MD ((hsh s 9004).toNat % 8); "
          "let t : Pl.Frame Float := [(\"credit_risk_score\", COL s nt mt)]; let v : Pl.Frame Float := [(\"credit_risk_score\", COL (s + 500000) nv mv)]; "
          "let r := metrics_run_06_psi t v; "
          "((if mt == 3 || mv == 3 then 2 else if nt > 0 && nv > 0 then 0 else 1 : Nat), dg (tR r.1 ++ tR r.2)); ")


def main():
    st = Suite("fz_psi")
    st.item, st.decl = "def:zz_carrier_m", "zz_carrier_m"
    gen = kept = 0
    raises_inside, dropped, narrow_n = [], [], [0, 0]
    for b in range(NBLOCK):
        s0 = S0 + b * BLOCK
        dig = {0: [], 1: [], 2: []}
        for s in range(s0, s0 + BLOCK):
            cls, d, msg = one(s)
            gen += 1
            if d is None:
                (raises_inside if cls == 0 else dropped).append((s, msg))
                continue
            dig[cls].append(d)
        # a seed on which Python raises would have to be left out of the Lean range
        assert not raises_inside and not dropped, (raises_inside[:3], dropped[:3])
        kept += len(dig[0])
        narrow_n[0] += len(dig[1])
        narrow_n[1] += len(dig[2])
        body = (f"(let RS := (List.range {BLOCK}).map (fun (i : Nat) => ONE ({s0} + i)); "
                "[0, 1, 2].map (fun (c : Nat) => W ((RS.filter (fun (p : Nat × Int) => p.1 == c)).map (fun (p : Nat × Int) => p.2))))")
        rng = f"seeds {s0}..{s0 + BLOCK - 1}"
        st.ints(LETS, body, [
            (f"{rng}: kept ({len(dig[0])} inputs)", U, b4.w(dig[0]), {"fz": "kept", "covers": len(dig[0])}),
            (f"{rng}: rejected, a frame without rows ({len(dig[1])} inputs)", U, b4.w(dig[1]), {"fz": "rejected", "covers": len(dig[1])}),
            (f"{rng}: rejected, an Int64 column ({len(dig[2])} inputs)", U, b4.w(dig[2]), {"fz": "rejected", "covers": len(dig[2])}),
        ], gen=True)
    st.write()
    for i, inp in enumerate(st.inputs):
        (WORK / f"fz_psi.in{i}.txt").write_text(inp["text"])
    (WORK / "fz_psi.fuzz.json").write_text(json.dumps({
        "fuzzer": "port-translator-2", "generator": "diffeval/units/fz_psi_gen.py",
        "units": {U: {"seeds": f"{S0}..{S0 + NBLOCK * BLOCK - 1}", "generated": gen, "kept": kept,
                      "python_raises_inside_precondition": [s for s, _ in raises_inside],
                      "note": ("one case = the fold of the digests of (psi_calculation, psi_summary) over the seeds of one class in a block of "
                               f"{BLOCK} seeds; pools: 0-37 rows per frame; edge pool (null, NaN, +-inf, +-0.0, +-1e300, 1e-300, subnormal, 700 +-1 ulp, 2^53) at 60 %, "
                               "six levels each +-1 ulp with nulls (ties on every cut), forty levels, Int64 column; "
                               f"rejected inputs on which Python returns: {narrow_n[0]} with a frame without rows, {narrow_n[1]} with an Int64 column. "
                               "EXPLAINED difference, kept block 20500..20999: seed 20912 only (37 training rows, 2 validation rows; bin 7 has shares 7/37 and 1/2): "
                               "psi_component of that bin is 1 ulp apart because the Lean evaluator's Float.log(0.3783783783783784) is 1 ulp above the log of polars / libm "
                               "(checked first-hand on that one value); every other column and PSI are equal. RULEBOOK section 6: the last bit of log is outside the model. "
                               "Int64 class: 3 of 7 blocks differ, one input each (seeds 20163, 21413, 22258), each with the same shares 7/37 and 1/2: "
                               "the Python frames with the Lean log on that bin give the Lean digest exactly (diffeval/work/fz_psi_int.py), so 780 of 783 Int64 inputs "
                               "equal Python and the other 3 differ by this log bit only"),
                      "all_differences_are_recorded_limit": (
                          "the last bit of log (RULEBOOK section 6, outside the model): seed 20912, bin with shares 7/37 and 1/2; Float.log(0.3783783783783784) "
                          "in the Lean evaluator is bits 13830300998319222871, polars and math.log give ...870 (evaluated first-hand); the Python result with that one "
                          "log value replaced has the Lean digest exactly (diffeval/work/fz_psi_int.py)")}}}))
    print(f"generated {gen}, kept {kept} ({kept / gen:.3f}); rejected rows {narrow_n[0]}, dtype {narrow_n[1]}; input sizes {[len(i['text']) for i in st.inputs]}")


if __name__ == "__main__":
    main()
