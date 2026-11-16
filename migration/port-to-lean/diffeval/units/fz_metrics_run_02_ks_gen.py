"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-11 (reviewer of T13):
  def:metrics_run_02_ks   credit_risk/metrics_calculation.py:156-196

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_metrics_run_02_ks_gen.py
  (eval_decl each input of diffeval/work/fz_ks.inputs.json on def:zz_carrier_m / zz_carrier_m)
  python3 diffeval/fuzz_collect.py 11 fz_ks
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/fz_ks.json diffeval/work/fz_ks.out.txt
  python3 diffeval/fuzz_receipt.py fz_ks

One case = one seed s. The frame is built INSIDE Lean from s (kit.GEN) and mirrored here (kit.gF):
  rows      n = NS[hsh(s, 7) % 9], NS = 0, 1, 2, 3, 5, 8, 13, 24, 40
  default_flag (Float64) = gF(2 s, n, FPE[fm], 2, FE[fm]),  fm = hsh(s, 9) % 8:
      0, 4, 7 general pool (null, NaN, 0, 1, -0.0, 2, 0.5, inf; mostly 0 / 1), 1 all 0 (no defaulter),
      2 all 1 (no non-defaulter), 3, 5, 6 clean 0 / 1
  pd_logistic (Float64) = gF(2 s + 1, n, PPE[pm], 2, PE[pm]),  pm = hsh(s, 8) % 3:
      0 edge pool at 70 % (null, NaN, +-inf, +-0.0, 0.5 and one ulp either side, 0.25, 0.75, 1,
        1e300, 1e-300, the smallest subnormal, 0.1, 0.2, 0.3), 1 four values only (heavy ties, null),
      2 random values with the edge pool at 20 %
The result compared is ONE digest per seed of (sorted logit_scored_valid, ks_statistic).
Expected: the source lines 156-196 of the port executed verbatim with the module's globals.

Explicit parameters. The step calls sas_best(k, 8) only on the two Int64 totals, 0 <= k <= 40, or on
None. Instead of a typed table the Lean side uses  sb x = "" for none, the decimal text of the
integer otherwise;  pf s = the integer of the text as a float.  Asserted below against the real
sas_compat.sas_best and float() for every k in 0..40 (as int and as float) and None.

Precondition def:metrics_run_02_ks_precond, clause by clause:
  distinct column names                     always true (two names)
  columns of one common length              always true (both columns have n values)
  0 < height                                n >= 1  (the only clause a generated input can fail)
  Float64 default_flag and pd_logistic      always true (both are built Float64)
So n = 0 is "rejected" (Python returns one row of two nulls; sent to Lean, a narrowing if equal).
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_m", "zz_carrier_m")

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

U = "metrics_run_02_ks"
nan, inf = float("nan"), float("inf")
NS = [0, 1, 2, 3, 5, 8, 13, 24, 40]
GEN_ = [None, nan, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, -0.0, 2.0, 0.5, inf]
FE = [GEN_, [0.0], [1.0], [0.0, 1.0], GEN_, [0.0, 1.0], [0.0, 1.0], GEN_]
FPE = [97, 100, 100, 100, 97, 100, 100, 97]
EDGE = [None, nan, inf, -inf, 0.0, -0.0, 0.5, lt.from_bits(lt.bits(0.5) - 1), lt.from_bits(lt.bits(0.5) + 1), 0.25, 0.75, 1.0,
        1e300, 1e-300, 5e-324, 0.1, 0.2, 0.3]
PE = [EDGE, [0.25, 0.5, 0.75, None], EDGE]
PPE = [70, 100, 20]
BASE, PER_CALL, CALLS = 1000, 500, 5

SRC = textwrap.dedent("".join(Path(mc.__file__).read_text().splitlines(keepends=True)[155:196]))
assert "ne_missing" in SRC and SRC.lstrip().startswith("# metrics_calculation.sas:124-126") and "KS_Cutoff" in SRC

for k in range(0, 41):
    assert sc.sas_best(k, 8) == str(k) == sc.sas_best(float(k), 8) and float(str(k)) == k
assert sc.sas_best(None, 8) == ""


def frame(s: int) -> pl.DataFrame:
    n = NS[kit.hsh(s, 7) % 9]
    fm, pm = kit.hsh(s, 9) % 8, kit.hsh(s, 8) % 3
    return pl.DataFrame({"default_flag": pl.Series(kit.gF(2 * s, n, FPE[fm], 2, FE[fm]), dtype=pl.Float64),
                         "pd_logistic": pl.Series(kit.gF(2 * s + 1, n, PPE[pm], 2, PE[pm]), dtype=pl.Float64)})


def precond(df: pl.DataFrame) -> bool:
    return (len(set(df.columns)) == len(df.columns) and df.height > 0
            and df.schema["default_flag"] == pl.Float64 and df.schema["pd_logistic"] == pl.Float64)


def python(df: pl.DataFrame):
    ns = dict(vars(mc))
    ns["logit_scored_valid"] = df
    exec(compile(SRC, "metrics_calculation.py:156-196", "exec"), ns)  # noqa: S102
    return ns["logit_scored_valid"], ns["ks_statistic"]


def opts(xs) -> str:
    return "[" + ", ".join("none" if x is None else f"some {lt.lean_float(x)}" for x in xs) + "]"


LETS = (
    'let sb := fun (x : Option Float) (_ : Int) => (match x with | none => "" | some v => toString v.toUInt64.toNat); '
    "let pf := fun (s : String) => Float.ofNat s.toNat!; "
    f"let NS : List Nat := {NS}; "
    f"let G : List (Option Float) := {opts(GEN_)}; let C : List (Option Float) := {opts([0.0, 1.0])}; "
    f"let FE : List (List (Option Float)) := [G, {opts([0.0])}, {opts([1.0])}, C, G, C, C, G]; "
    f"let FPE : List UInt64 := {FPE}; "
    f"let ED : List (Option Float) := {opts(EDGE)}; "
    f"let PE : List (List (Option Float)) := [ED, {opts(PE[1])}, ED]; "
    f"let PPE : List UInt64 := {PPE}; "
    "let mk := fun (s : Nat) => (let n := NS.getD ((hsh s 7) % 9).toNat 0; let fm := ((hsh s 9) % 8).toNat; let pm := ((hsh s 8) % 3).toNat; "
    '([("default_flag", Pl.Col.f64 (gF (2 * s) n (FPE.getD fm 100) 2 (FE.getD fm []))), '
    '("pd_logistic", Pl.Col.f64 (gF (2 * s + 1) n (PPE.getD pm 100) 2 (PE.getD pm [])))] : Pl.Frame Float)); '
    "let one := fun (s : Nat) => (let r := metrics_run_02_ks sb pf (mk s); dg (tR r.1 ++ tR r.2)); "
)


def main():
    s = Suite("fz_ks")
    gen = kept = 0
    raises_in, dropped, stats = [], 0, {"null KS": 0, "rows0": 0}
    for c in range(CALLS):
        b = BASE + c * PER_CALL
        cases = []
        for seed in range(b, b + PER_CALL):
            gen += 1
            df = frame(seed)
            ok = precond(df)
            try:
                srt, ks = python(df)
            except Exception as e:  # noqa: BLE001
                if ok:
                    raises_in.append(seed)
                    print("RAISES inside precondition", seed, type(e).__name__, e)
                else:
                    dropped += 1
                cases.append((f"seed {seed}: Python raises", U, -1, {"fz": "rejected", "expect_diff": True, "note": "Python raises"}))
                continue
            kept += ok
            stats["null KS"] += ks["KS_Statistic"][0] is None
            stats["rows0"] += df.height == 0
            exp = cmp.digest(cmp.tokens(cmp.canon_frame(srt)) + cmp.tokens(cmp.canon_frame(ks)))
            cases.append((f"seed {seed} ({df.height} rows)", U, exp, {"fz": "kept" if ok else "rejected"}))
        s.ints(LETS, f"((List.range {PER_CALL}).map (fun (i : Nat) => one ({b} + i)))", cases, gen=True)
    s.write()
    note = ("one case = one seed: digest of (sorted frame, ks_statistic); rows 0..40 by seed; default_flag pools: general "
            "(null, NaN, 0, 1, -0.0, 2, 0.5, inf), all 0, all 1, clean 0/1; pd_logistic pools: edges (null, NaN, +-inf, +-0.0, "
            "0.5 +- 1 ulp, 1e300, 1e-300, subnormal) at 70 %, four tied values, random with edges at 20 %; "
            f"{stats['null KS']} cases with a null KS_Statistic; rejected = the {stats['rows0']} frames with no row")
    (HERE.parent / "work" / "fz_ks.fuzz.json").write_text(json.dumps({
        "fuzzer": "port-translator-11", "generator": "diffeval/units/fz_metrics_run_02_ks_gen.py",
        "units": {U: {"seeds": f"{BASE}..{BASE + CALLS * PER_CALL - 1}", "generated": gen, "kept": kept,
                      "python_raises_inside_precondition": raises_in, "note": note}}}))
    print(f"generated {gen} kept {kept} ({kept / gen:.3f}) raises inside {len(raises_in)} dropped {dropped} {stats}")


if __name__ == "__main__":
    main()
