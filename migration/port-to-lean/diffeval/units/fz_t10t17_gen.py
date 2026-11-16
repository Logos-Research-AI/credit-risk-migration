"""Fuzz pass 2026-11-16, port-translator-10 (reviewer of T10 / T17, not their author):
  def:predict_run_07_predictions, def:predict_run_08_outputs (suite fz_p0708, carrier def:zz_carrier_p)
  def:train_run_12_risk_scores (suite fz_train12, carrier def:zz_carrier_t)

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t10t17_gen.py
  eval_decl each input of work/<suite>.inputs.json; python3 diffeval/fuzz_collect.py 10 fz_p0708 fz_train12;
  compare.py; python3 diffeval/fuzz_receipt.py fz_p0708 fz_train12

Inputs are built inside Lean from the seed (kit.GEN: hsh, gF, gI) and mirrored here with kit.hsh /
kit.gF / kit.gI. Expected values: the step's own source lines, read from the file and executed with
the module's globals on the mirrored frame. One case is the digest of CH consecutive seeds
(`covers`); a differing case is reduced by per-seed digests afterwards.

Steps 07 and 12, frame of seed s: n = NS[hsh(s, 7777) % 8] rows (0, 1, 1, 2, 3, 5, 9, 24); for
s % 4 == 0 a column base_score (all 1.0) that the step replaces in place; row_id = 0..n-1;
pd_logistic = gF(s, n, 55, 4, E): 55 % from the edge pool E (null twice, NaN, +-inf, +-0.0, the cuts
0.10 0.15 0.25 0.35 0.50 and one ulp either side of each, 1.0 and its neighbours, 2.0, -1.0, 1e300,
1e-300, 5e-324, 600.0), else a random float with exponent in [-4, 4]. Step 12 takes the frames of
seeds s and s + 500000.
Precondition of 07 / 12 as a Python function (def:predict_run_07_predictions_precond,
def:train_run_12_risk_scores_precond): names distinct -> len(set(columns)) == len(columns); columns
of one height -> true of any DataFrame; pd_logistic present and Float64 -> dtype test.
Rejected class: pd_logistic an Int64 column gI(s, n, 25, 4, 1) (values -1..2, 25 % null).
Step 08, frame of seed s: the names of POOL (the 15 kept names, base_rate, x, AGE, default_flag)
rotated by hsh(s, 99) % 19, each kept with probability 85 % (hsh(s, 100 + i) % 100 < 85); n = s % 3
rows; risk_grade is a String column, the others Float64 (value 10 * i + row); age_name =
AN[hsh(s, 98) % 8] from age, age, AGE, Age, x, row_id, zz, base_rate.
Precondition of 08 (def:predict_run_08_outputs_precond): names distinct; "age" in columns; age_name
== "age" or age_name is not one of the kept names present in the frame. The Lean body filters the
seeds with the same test (`ok8`), so a disagreement of the filter shows as a differing digest.
Outside it Python raises (no age to rename, or a duplicate name) except: no age column and
age_name == "age" (the rename of an absent name to itself returns); those go to Lean as rejected
(filter `rj8`).
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import train as tr  # noqa: E402

U07, U08, U12 = "predict_run_07_predictions", "predict_run_08_outputs", "train_run_12_risk_scores"
CH = 50
NS = [0, 1, 1, 2, 3, 5, 9, 24]
inf, nan = float("inf"), float("nan")
up, dn = (lambda x: math.nextafter(x, inf)), (lambda x: math.nextafter(x, -inf))
EV = [nan, inf, -inf, 0.0, -0.0] + [f(c) for c in (0.10, 0.15, 0.25, 0.35, 0.50, 1.0) for f in (dn, float, up)] + [
    2.0, -1.0, 1e300, 1e-300, 5e-324, 600.0]
E = [None, None] + EV
KEEP = ["row_id", "pd_logistic", "pred_logistic", "credit_risk_score", "risk_grade", "recommendation",
        "interest_rate", "age", "monthly_income", "credit_utilization", "debt_ratio", "total_late_payments",
        "num_credit_lines", "financial_health", "total_risk_flags"]
POOL = KEEP + ["base_rate", "x", "AGE", "default_flag"]
AN = ["age", "age", "AGE", "Age", "x", "row_id", "zz", "base_rate"]
F = pl.Float64


def slice_fn(mod, a: int, b: int, first: str, last: str):
    lines = Path(mod.__file__).read_text().splitlines()[a - 1:b]
    assert lines[0].strip().startswith(first) and lines[-1].strip().startswith(last), (lines[0], lines[-1])
    code = compile(textwrap.dedent("\n".join(lines)), f"{Path(mod.__file__).name}:{a}-{b}", "exec")

    def run(env: dict) -> dict:
        ns = dict(vars(mod))
        ns.update(env)
        exec(code, ns)  # noqa: S102  the port's own lines
        return ns

    return run


S07 = slice_fn(pr, 398, 443, "test_predictions = test_scored.with_columns(", ")")
S08 = slice_fn(pr, 446, 469, "KEEP_KAGGLE", ").rename(")
S12 = slice_fn(tr, 584, 673, "risk_scores_train = logit_scored_train.with_columns(", ")")


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def n_of(s: int) -> int:
    return NS[kit.hsh(s, 7777) % 8]


def frame(s: int, integer: bool = False) -> pl.DataFrame:
    n = n_of(s)
    cols: dict = {}
    if s % 4 == 0:
        cols["base_score"] = pl.Series([1.0] * n, dtype=F)
    cols["row_id"] = pl.Series([float(i) for i in range(n)], dtype=F)
    if integer:
        cols["pd_logistic"] = pl.Series(kit.gI(s, n, 25, 4, 1), dtype=pl.Int64)
    else:
        cols["pd_logistic"] = pl.Series(kit.gF(s, n, 55, 4, E), dtype=F, nan_to_null=False)
    return pl.DataFrame(cols)


def pre_pd(df: pl.DataFrame) -> bool:
    return len(set(df.columns)) == len(df.columns) and "pd_logistic" in df.columns and df.schema["pd_logistic"] == F


def frame08(s: int) -> tuple[pl.DataFrame, str]:
    r = kit.hsh(s, 99) % len(POOL)
    n = s % 3
    cols: dict = {}
    for k in range(len(POOL)):
        i = (k + r) % len(POOL)
        if kit.hsh(s, 100 + i) % 100 < 85:
            name = POOL[i]
            if name == "risk_grade":
                cols[name] = pl.Series(["A"] * n, dtype=pl.String)
            else:
                cols[name] = pl.Series([float(10 * i + j) for j in range(n)], dtype=F)
    return pl.DataFrame(cols), AN[kit.hsh(s, 98) % len(AN)]


def pre08(df: pl.DataFrame, an: str) -> bool:
    return (len(set(df.columns)) == len(df.columns) and "age" in df.columns
            and (an == "age" or all(c != an for c in df.columns if c in KEEP)))


LE = ("let E : List (Option Float) := [none, none] ++ ([" + ", ".join(str(lt.bits(x)) for x in EV)
      + "] : List UInt64).map (fun (b : UInt64) => some (Float.ofBits b)); ")
LN = "let nOf := fun (s : Nat) => ([0, 1, 1, 2, 3, 5, 9, 24] : List Nat).getD ((hsh s 7777) % 8).toNat 0; "
LMK = ("let mkG := fun (s : Nat) (pd : Nat → Pl.Col Float) => (let n := nOf s; let f : Pl.Frame Float := "
       '(if s % 4 == 0 then [("base_score", Pl.Col.f64 (List.replicate n (some 1.0)))] else []) ++ '
       '[("row_id", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofNat i)))), ("pd_logistic", pd n)]; f); '
       "let mk := fun (s : Nat) => mkG s (fun (n : Nat) => Pl.Col.f64 (gF s n 55 4 E)); "
       "let mkI := fun (s : Nat) => mkG s (fun (n : Nat) => Pl.Col.int (gI s n 25 4 1)); ")
LCH = (f"let ch := fun (U : Nat → List UInt64) (ok : Nat → Bool) (b c : Nat) => dg (((List.range {CH}).map (fun (i : Nat) => b + c * {CH} + i)).filter ok |>.map "
       "(fun (s : Nat) => (dg (U s)).toNat.toUInt64)); let yes := fun (_ : Nat) => true; ")
L08 = ("let POOL : List String := [" + ", ".join(lt.lean_str(x) for x in POOL) + "]; let KEEP := POOL.take 15; "
       "let AN : List String := [" + ", ".join(lt.lean_str(x) for x in AN) + "]; "
       "let an := fun (s : Nat) => AN.getD ((hsh s 98) % 8).toNat \"\"; "
       "let mk8 := fun (s : Nat) => (let r := ((hsh s 99) % 19).toNat; let n := s % 3; let f : Pl.Frame Float := "
       "(List.range 19).filterMap (fun (k : Nat) => let i := (k + r) % 19; let nm := POOL.getD i \"\"; "
       "if (hsh s (100 + i)) % 100 < 85 then some (nm, (if nm == \"risk_grade\" then Pl.Col.str (List.replicate n (some \"A\")) "
       "else Pl.Col.f64 ((List.range n).map (fun (j : Nat) => some (Float.ofNat (10 * i + j)))) : Pl.Col Float)) else none); f); "
       "let ok8 := fun (s : Nat) => (let nm := (mk8 s).map (fun (p : String × Pl.Col Float) => p.1); "
       "nm.contains \"age\" && (an s == \"age\" || !((nm.filter (fun (x : String) => KEEP.contains x)).contains (an s)))); "
       "let rj8 := fun (s : Nat) => (!((mk8 s).map (fun (p : String × Pl.Col Float) => p.1)).contains \"age\") && an s == \"age\"; ")


def chunk_cases(unit: str, what: str, base: int, chunks: int, per_seed, fz: str) -> tuple[list, int, int]:
    """per_seed(s) -> digest or None (not part of the case). Returns the cases, generated, taken."""
    cases, gen, taken = [], 0, 0
    for c in range(chunks):
        ds = []
        for i in range(CH):
            gen += 1
            d = per_seed(base + c * CH + i)
            if d is not None:
                ds.append(d)
        taken += len(ds)
        cases.append((f"{what} seeds {base + c * CH}..{base + c * CH + CH - 1} ({len(ds)} inputs)", unit, cmp.digest(ds),
                      {"fz": fz, "covers": len(ds)}))
    return cases, gen, taken


def main() -> None:
    fuzz: dict = {}
    # ------------------------------------------------------------ predict 07 and 08
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_p", "zz_carrier_p")
    s = Suite("fz_p0708")

    def d07(seed: int, integer: bool = False):
        df = frame(seed, integer)
        assert pre_pd(df) == (not integer)
        return dgf(S07({"test_scored": df})["test_predictions"])

    for a in range(1):  # 48 chunks x 50 seeds = 2400 kept
        cs, g, k = chunk_cases(U07, "Float64 pd,", 1000, 48, d07, "kept")
        s.ints(LE + LN + LMK + LCH, "((List.range 48).map (ch (fun (s : Nat) => tR (predict_run_07_predictions (mk s))) yes 1000))",
               cs, gen=True)
    csr, gr, kr = chunk_cases(U07, "Int64 pd (outside the precondition),", 9000, 6, lambda z: d07(z, True), "rejected")
    s.ints(LE + LN + LMK + LCH, "((List.range 6).map (ch (fun (s : Nat) => tR (predict_run_07_predictions (mkI s))) yes 9000))", csr, gen=True)
    fuzz[U07] = {"seeds": "1000..3399 (Float64 pd), 9000..9299 (Int64 pd, rejected)", "generated": 2400 + gr, "kept": 2400,
                 "python_raises_inside_precondition": [],
                 "note": "frames of 0-24 rows; pd pool: null, NaN, +-inf, +-0.0, each cut and one ulp either side, 1.0, huge, tiny, subnormal; "
                         "a base_score column replaced in place every 4th seed; one case = digest of 50 seeds"}

    raises_in, rej_returns = [], []

    def d08(seed: int, want: bool = True):
        df, an = frame08(seed)
        ok = pre08(df, an)
        try:
            ns = S08({"test_predictions": df, "age_name": an})
        except Exception:  # noqa: BLE001
            if ok:
                raises_in.append(seed)
            return None
        if not ok:
            assert "age" not in df.columns and an == "age", seed  # the one rejected class that returns
            if want:
                rej_returns.append(seed)
        if ok != want:
            return None
        return cmp.digest(cmp.tokens(cmp.canon_frame(ns["kaggle_submission"])) + cmp.tokens(cmp.canon_frame(ns["test_predictions_full"])))

    tot_g = tot_k = 0
    for a in range(1):
        cs, g, k = chunk_cases(U08, "frame and age_name of", 20000, 80, d08, "kept")
        tot_g, tot_k = tot_g + g, tot_k + k
        s.ints(L08 + LCH, "((List.range 80).map (ch (fun (s : Nat) => (let r := predict_run_08_outputs (mk8 s) (an s); tR r.1 ++ tR r.2)) ok8 "
               "20000))", cs, gen=True)
    csr8, _, kr8 = chunk_cases(U08, "no age column and age_name = age (outside the precondition),", 20000, 20,
                               lambda z: d08(z, False), "rejected")
    s.ints(L08 + LCH, "((List.range 20).map (ch (fun (s : Nat) => (let r := predict_run_08_outputs (mk8 s) (an s); tR r.1 ++ tR r.2)) rj8 20000))",
           csr8, gen=True)
    fuzz[U08] = {"seeds": "20000..23999", "generated": tot_g, "kept": tot_k, "python_raises_inside_precondition": raises_in,
                 "note": "19 pool names (the 15 kept, base_rate, x, AGE, default_flag) each present with 85 %, rotated order, 0-2 rows; "
                         "age_name from age, AGE, Age, x, row_id, zz, base_rate; outside the precondition Python raises except when the frame has "
                         f"no age column and age_name is age ({len(rej_returns)} seeds of 20000..23999; those of 20000..20999, {kr8}, sent as rejected); "
                         "one case = digest of the kept seeds of a block of 50"}
    s.write()
    (suite_mod.WORK / "fz_p0708.fuzz.json").write_text(json.dumps(
        {"fuzzer": "port-translator-10", "generator": "diffeval/units/fz_t10t17_gen.py", "units": {U07: fuzz[U07], U08: fuzz[U08]}}, indent=1))
    print("08: generated", tot_g, "kept", tot_k, "raises inside", len(raises_in))

    # ------------------------------------------------------------ train 12
    suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")
    t = Suite("fz_train12")

    def d12(seed: int, integer: bool = False):
        a_, b_ = frame(seed, integer), frame(seed + 500000)
        assert (pre_pd(a_) and pre_pd(b_)) == (not integer)
        ns = S12({"logit_scored_train": a_, "logit_scored_valid": b_})
        return cmp.digest(cmp.tokens(cmp.canon_frame(ns["risk_scores_train"])) + cmp.tokens(cmp.canon_frame(ns["risk_scores_validation"])))

    T12 = "(let r := train_run_12_risk_scores ({a} s) (mk (s + 500000)); tR r.1 ++ tR r.2)"
    for a in range(1):
        cs, g, k = chunk_cases(U12, "Float64 pd,", 40000, 48, d12, "kept")
        t.ints(LE + LN + LMK + LCH, f"((List.range 48).map (ch (fun (s : Nat) => {T12.format(a='mk')}) yes 40000))", cs, gen=True)
    csr, gr, kr = chunk_cases(U12, "Int64 pd in the training frame (outside the precondition),", 49000, 6, lambda z: d12(z, True), "rejected")
    t.ints(LE + LN + LMK + LCH, f"((List.range 6).map (ch (fun (s : Nat) => {T12.format(a='mkI')}) yes 49000))", csr, gen=True)
    t.write()
    (suite_mod.WORK / "fz_train12.fuzz.json").write_text(json.dumps(
        {"fuzzer": "port-translator-10", "generator": "diffeval/units/fz_t10t17_gen.py", "units": {U12: {
            "seeds": "40000..42399 (both frames Float64 pd; validation frame from seed + 500000), 49000..49299 (Int64 pd in training, rejected)",
            "generated": 2400 + gr, "kept": 2400, "python_raises_inside_precondition": [],
            "note": "two frames of 0-24 rows each; same pd pool as step 07; one case = digest of 50 seeds"}}}, indent=1))
    for st in (s, t):
        for i, inp in enumerate(st.inputs):
            print(st.name, i, len(inp["text"]), "chars")


main()
