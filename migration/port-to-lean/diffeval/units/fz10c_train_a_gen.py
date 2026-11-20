"""Fidelity pass for the public claim, 2026-11-20, third attempt, label train-a.
Units: def:train_run_01_fit_frame, def:train_run_02_stepwise_summary, def:train_run_04_score_train of blueprint
5365851c-5549-44b7-9207-4bd4c422031d, evaluated through def:zz_carrier_fid_2 (decl zz_carrier_fid_2, identity on
List Int; it depends on the three units).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_a_gen.py [n01 n02 n04 chunk]

Expected values: the CURRENT port/credit_risk/train.py (HEAD 4a757fb). Each unit's source segment is cut out of the
file by its first and last line (printed with its line numbers), dedented and EXECUTED with the generated
inputs; the out-of-scope calls the Lean takes as explicit parameters are stubs:
  step 01  train.py `candidates = [` .. `ybar = float(y_train.mean())`; sas_compat.stepwise_logistic returns the
           generated StepwiseResult (the Lean's parameter `stepwise`)
  step 02  `ss_step: list[str] = []` .. the write_sas_csv of stepwise_summary.csv; sas_compat.fmt_wd and
           sas_compat.sas_pvalue are injective stand-ins (bits of the float, w, d; NaN canonical), the same on both
           sides; write_sas_csv records (file name, frame); `final` is a free local (the Lean's parameter)
  step 04  `final_names = [] if final is None else final.names` .. `fit_scored = ...filter(pl.Series(fit_mask))`;
           fit_mask a numpy bool array, as step 01 makes it
Inputs are built INSIDE Lean from the seed (kit.GEN) and mirrored here bit for bit (kit.gF / kit.gI / kit.hsh).

Step 01, seed s: frame of NR[hsh(s,1) % 12] rows (0, 1, 2, 3, 5, 8, 9, 17, 40, 130, 300), the 36 candidates and
  default_flag (Float64; a column is "nully" when hsh(s, 500+j) % 10 == 0: its edge pool holds null), plus "id"
  (Int64) and/or "seg" (String) by hsh(s,2) % 4, columns rotated by hsh(s,3). Pools: null, NaN, +-inf, +-0, 1e300,
  1e-300, subnormal, ...; default_flag 0/1 with NaN, 0.5, -0.0, inf. StepwiseResult: by hsh(s,4) % 20: 0-2 no fit,
  3 intercept_only only, 4 final only, else both fits (names Intercept + candidates, beta, 2-D cov, loglik from
  an edge pool with NaN/inf/-0, n_iter, converged, separation); no step.
  Precondition (def:train_run_01_fit_frame_precond): distinct names, one height (by construction), candidates and
  default_flag Float64 (by construction), intercept_only.isNone == final.isNone, final None -> no step, n_obs != 0.
  Compared per seed: digest of (candidates, fit_mask, fit_frame, final, intercept_only, n_obs, y_train, ybar) and,
  separately, the bits of m2ll0.
Step 02, seed s: the generator of fz3_step02_gen.py (0..6 steps; step ints in [-500, 500); entered/removed None or
  a name of 0..30 characters incl. accents and emoji; df in [-1, 5); score/wald Option floats with None, NaN, +-inf,
  +-0, 1e300, subnormal, thresholds +-1 ulp; p_value with the format thresholds +-1 ulp) and final = None when
  hsh(s, 9) % 5 == 0. No precondition item: every input is kept. Compared: digest of the Option (name, table).
Step 04, seed s: frame of NR4 rows (0..40) with f64 columns a..h (pool with null, NaN, +-0, 1e300, 1e-300,
  subnormal), "id" Int64 and "s" String, rotated; fit_mask of the frame's height (one longer when hsh(s,20) % 40 == 0);
  candidates a rotated subset of a..h, notacol, s (one duplicated when hsh(s,22) % 33 == 0); final None when
  hsh(s,7) % 7 == 0, else names [Intercept] + 0..5 names drawn mostly from a..h (also notacol, s, Intercept,
  repeats), beta from a pool with 0, -0, NaN, +-700, +-1e300, inf, cov square with a diagonal pool 0, -0, NaN, 1,
  1e-300, subnormal.
  Precondition (def:train_run_04_score_train_precond), rendered clause by clause in pre04 below; the last clause
  (exp(-eta) finite on every row whose eta is not null) is evaluated on the eta the Python code builds (polars,
  per row of the frame).
"""
from __future__ import annotations

import json
import math
import struct
import sys
import textwrap
import types
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
CARRIER = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
TRAIN = HERE.parents[3] / "port" / "credit_risk" / "train.py"
SRC = TRAIN.read_text().splitlines()


def segment(first: str, last: str) -> tuple[str, int, int]:
    i = next(k for k, ln in enumerate(SRC) if ln.startswith(first))
    j = next(k for k in range(i, len(SRC)) if SRC[k].startswith(last))
    return textwrap.dedent("\n".join(SRC[i:j + 1])), i + 1, j + 1


SEG01 = segment("    candidates = [", "    ybar = float(y_train.mean())")
SEG02 = segment("    ss_step: list[str] = []", '        sas_compat.write_sas_csv(stepwise_summary, output_dir / "stepwise_summary.csv"')
SEG04 = segment("    final_names = [] if final is None else final.names", "    fit_scored = logit_scored_train.filter(pl.Series(fit_mask))")
CODE01, CODE02, CODE04 = (compile(s[0], f"train.py:{s[1]}-{s[2]}", "exec") for s in (SEG01, SEG02, SEG04))

NAN, INF = float("nan"), float("inf")


def fb(x: float) -> int:
    return cmp.fbits(x)


def ulp(x, k):
    b = struct.unpack("<Q", struct.pack("<d", x))[0]
    return struct.unpack("<d", struct.pack("<Q", b + k))[0]


def lf(x) -> str:
    """Exact Lean Float term."""
    if x != x:
        return "(0.0/0.0 : Float)"
    if x == INF:
        return "(1.0/0.0 : Float)"
    if x == -INF:
        return "(-1.0/0.0 : Float)"
    if x == 0.0:
        return "(-0.0 : Float)" if math.copysign(1, x) < 0 else "(0.0 : Float)"
    d = lean_float_decimal(x)
    if d is not None:
        return f"({d if '.' in d else d + '.0'} : Float)"
    return f"(Float.ofBits {fb(x)})"


def lean_float_decimal(x: float):
    """copy of t18_gen.lean_float_decimal: a decimal token Lean reads back as exactly x, or None."""
    s = repr(x)
    if "e" in s or "E" in s:
        return None
    if s.endswith(".0"):
        s = s[:-2]
    neg = s.startswith("-")
    u = s[1:] if neg else s
    ip, _, fp = u.partition(".")
    m, e = int(ip + fp), len(fp)
    if m == 0:
        v = 0.0
    else:
        sh = max(64 - (m.bit_length() - 1), 0)
        mm = (m << (3 * e + sh)) // 5**e
        ex = -4 * e - sh
        s2 = max((mm.bit_length() - 1) - 63, 0)
        v = math.ldexp(float(mm >> s2), ex + s2)
    if neg:
        v = -v
    return s if fb(v) == fb(x) else None


def lol(E) -> str:
    return "[" + ", ".join("none" if x is None else f"some {lf(x)}" for x in E) + "]"


CANDS = [
    "credit_utilization_capped", "debt_ratio_capped", "num_late_30_59", "num_late_60_89", "num_late_90_plus",
    "total_late_payments", "has_delinquency", "has_serious_delinquency", "age", "monthly_income",
    "log_monthly_income", "num_credit_lines", "num_real_estate_loans", "log_num_credit_lines", "num_dependents",
    "income_per_dependent", "credit_lines_per_person", "flag_high_utilization", "flag_very_high_utilization",
    "flag_high_debt_ratio", "flag_very_high_debt_ratio", "flag_recent_late_payments", "flag_serious_delinquency",
    "flag_multiple_delinquencies", "flag_low_income", "flag_many_dependents", "flag_few_credit_lines",
    "total_risk_flags", "credit_util_category", "debt_category", "age_category", "financial_health",
    "age_income_interaction", "utilization_debt_interaction", "MonthlyIncome_missing", "Dependents_missing"]
SP = ["", "x", "NA", " 1", "-2.5", "é"]
NR = [0, 1, 2, 3, 5, 8, 9, 17, 40, 130, 300, 1]
EF = [None] * 6 + [NAN, INF, -INF, 0.0, -0.0, 1.0, 1e300, -1e300, 5e-324, 1e-300, 2.5, -7.0]
E0 = [NAN, INF, -INF, 0.0, -0.0, 1.0, -1.0, 1e300, 5e-324, 0.5, 3.0]
EY = [0.0, 1.0] * 6 + [NAN, 0.5, -0.0, INF]
EYN = EY + [None] * 4
EL = [NAN, INF, -INF, 0.0, -0.0, -1e300, -5e-324, -0.6931471805599453, -12345.678, 1e-300]

PN = ["a", "b", "c", "d", "e", "f", "g", "h", "notacol", "s", "Intercept"]
QN = [0, 1, 2, 3, 4, 5, 6, 7] * 2 + [8, 9, 10]
NR4 = [0, 1, 1, 2, 3, 4, 5, 8, 13, 40]
EV = [None, None, None, NAN, 0.0, -0.0, 1.0, -1.0, 2.0, 0.5, 1e-300, 5e-324, 1e300]
EB = [0.0, -0.0, NAN, 1.0, -1.0, 700.0, -700.0, 1e300, -1e300, INF, 1e-300, 0.5]
EC = [0.0, -0.0, NAN, 1.0, 1e-300, 5e-324, 2.5, -1.0]

# fz3_step02_gen pools
POOL = ["", "x", " ", "a" * 20, "b" * 21, "c" * 30, "café_" + "d" * 19, "\U0001F600" * 22]
E1 = [None, None, NAN, NAN, INF, -INF, 0.0, -0.0, 1e300, -1e300, 1e-300, 5e-324, 1.5e-16, ulp(1.5e-16, 1),
      ulp(1.5e-16, -1), 1.0, ulp(1.0, 1), ulp(1.0, -1), 3.84, 123456789.0, -0.00001, 0.99999999, 1e15, 1e16, 99999.99995]
E2 = [NAN, INF, -INF, 0.0, -0.0, 1e-4, ulp(1e-4, 1), ulp(1e-4, -1), 0.05, ulp(0.05, 1), 1.0, ulp(1.0, 1), ulp(1.0, -1),
      0.99995, 1e-300, 5e-324, 1e300, 0.5, 0.00005, 2.0]


def ls(xs) -> str:
    return "[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in xs) + "]"


def ln(xs) -> str:
    return "[" + ", ".join(str(x) for x in xs) + "]"


H = "(fun (a b : Nat) => (hsh a b).toNat)"  # not used in Lean text; hsh is UInt64 there

# ------------------------------------------------------------------ Lean token helpers (beyond the kit)
TOK = (
    "let tArr := fun (a : Np.NDArray Float) => (match a with | .d1 v => 1 :: tF (v.map some) "
    "| .d2 rows => 2 :: rows.length.toUInt64 :: rows.flatMap (fun (r : List Float) => tF (r.map some)) : List UInt64); "
    "let tFit := fun (o : Option (LogisticFit Float)) => (match o with | none => [0] | some f => "
    "1 :: tT (f.names.map some) ++ tArr f.beta ++ tArr f.cov ++ [f.loglik.toBits] ++ tI [some f.n_iter] "
    "++ [if f.converged then 1 else 0] ++ tT [f.separation] : List UInt64); "
)


def p_tT(xs):
    out = [len(xs)]
    for x in xs:
        out += [0] if x is None else [1] + cmp.tok_str(x)
    return out


def p_tF(xs):
    out = [len(xs)]
    for x in xs:
        out += [0] if x is None else [1, fb(float(x))]
    return out


def p_tI(xs):
    out = [len(xs)]
    for x in xs:
        out += [0] if x is None else [2 if x < 0 else 1, abs(int(x))]
    return out


def p_tB(xs):
    out = [len(xs)]
    for x in xs:
        out += [0] if x is None else [1, 1 if x else 0]
    return out


def p_arr(a):
    a = np.asarray(a)
    if a.ndim == 1:
        return [1] + p_tF(a.tolist())
    assert a.ndim == 2
    out = [2, a.shape[0]]
    for r in a.tolist():
        out += p_tF(r)
    return out


def p_fit(f):
    if f is None:
        return [0]
    return ([1] + p_tT(list(f.names)) + p_arr(f.beta) + p_arr(f.cov) + [fb(f.loglik)] + p_tI([f.n_iter])
            + [1 if f.converged else 0] + p_tT([f.separation]))


def p_frame(df):
    return cmp.tokens(cmp.canon_frame(df))


def hs(s, i):
    return kit.hsh(s, i)


# ================================================================== step 01
LETS01 = (
    TOK
    + f"let EF : List (Option Float) := {lol(EF)}; let E0 : List (Option Float) := {lol(E0)}; "
    + f"let EY : List (Option Float) := {lol(EY)}; let EYN : List (Option Float) := {lol(EYN)}; "
    + f"let EL : List (Option Float) := {lol(EL)}; "
    + f"let CANDS : List String := {ls(CANDS)}; let SP : List String := {ls(SP)}; let NR : List Nat := {ln(NR)}; "
    "let mkF := fun (s : Nat) => let n := NR.getD (hsh s 1 % NR.length.toUInt64).toNat 0; "
    'let base := CANDS ++ ["default_flag"]; '
    "let fc : List (String × Pl.Col Float) := (List.range base.length).map (fun (j : Nat) => "
    "let nully := hsh s (500 + j) % 10 == 0; "
    '(base.getD j "", Pl.Col.f64 (if j == 36 then gF (s*64+j) n 90 2 (if nully then EYN else EY) '
    "else gF (s*64+j) n 30 4 (if nully then EF else E0)))); "
    "let e := hsh s 2 % 4; "
    'let ex : List (String × Pl.Col Float) := (if e % 2 == 1 then [("id", Pl.Col.int (gI (s*64+40) n 10 1000 500))] else []) '
    '++ (if e >= 2 then [("seg", Pl.Col.str ((gI (s*64+41) n 20 SP.length.toUInt64 0).map (fun (o : Option Int) => '
    'o.map (fun (k : Int) => SP.getD k.toNat ""))))] else []); '
    "let cols := fc ++ ex; let r := (hsh s 3 % cols.length.toUInt64).toNat; "
    "((cols.drop r ++ cols.take r) : Pl.Frame Float); "
    "let mkFit := fun (s : Nat) => let m := (hsh s 1 % 5).toNat; "
    'let nm := "Intercept" :: (List.range m).map (fun (i : Nat) => CANDS.getD (hsh s (10+i) % 36).toNat ""); '
    "let bv := (gF (s+1) (m+1) 30 6 EL).map (fun (o : Option Float) => o.getD 0.0); "
    "let cv := (List.range (m+1)).map (fun (i : Nat) => (gF (s*7+i+3) (m+1) 30 6 EL).map (fun (o : Option Float) => o.getD 0.0)); "
    "let ll := ((gF (s+2) 1 60 8 EL).getD 0 none).getD 0.0; "
    "({ names := nm, beta := Np.NDArray.d1 bv, cov := Np.NDArray.d2 cv, loglik := ll, n_iter := ((hsh s 4 % 30).toNat : Int), "
    'converged := hsh s 5 % 3 != 0, separation := (if hsh s 6 % 4 == 0 then some "quasi" else none) } : LogisticFit Float); '
    "let mkSW := fun (s : Nat) => let k := hsh s 4 % 20; "
    "({ steps := [], final := (if k <= 3 then none else some (mkFit (s*16+1))), "
    "intercept_only := (if k <= 2 || k == 4 then none else some (mkFit (s*16+2))) } : StepwiseResult Float); "
)


def py_frame01(s):
    n = NR[hs(s, 1) % len(NR)]
    base = CANDS + ["default_flag"]
    cols = []
    for j, name in enumerate(base):
        nully = hs(s, 500 + j) % 10 == 0
        if j == 36:
            v = kit.gF(s * 64 + j, n, 90, 2, EYN if nully else EY)
        else:
            v = kit.gF(s * 64 + j, n, 30, 4, EF if nully else E0)
        cols.append(pl.Series(name, v, dtype=pl.Float64))
    e = hs(s, 2) % 4
    if e % 2 == 1:
        cols.append(pl.Series("id", kit.gI(s * 64 + 40, n, 10, 1000, 500), dtype=pl.Int64))
    if e >= 2:
        cols.append(pl.Series("seg", [None if k is None else SP[k] for k in kit.gI(s * 64 + 41, n, 20, len(SP), 0)],
                              dtype=pl.String))
    r = hs(s, 3) % len(cols)
    cols = cols[r:] + cols[:r]
    return pl.DataFrame(cols)


def py_fit01(s):
    m = hs(s, 1) % 5
    nm = ["Intercept"] + [CANDS[hs(s, 10 + i) % 36] for i in range(m)]
    bv = [0.0 if x is None else x for x in kit.gF(s + 1, m + 1, 30, 6, EL)]
    cv = [[0.0 if x is None else x for x in kit.gF(s * 7 + i + 3, m + 1, 30, 6, EL)] for i in range(m + 1)]
    g = kit.gF(s + 2, 1, 60, 8, EL)[0]
    ll = 0.0 if g is None else g
    return sc.LogisticFit(nm, np.array(bv, dtype=np.float64), np.array(cv, dtype=np.float64).reshape(m + 1, m + 1),
                          ll, hs(s, 4) % 30, hs(s, 5) % 3 != 0, "quasi" if hs(s, 6) % 4 == 0 else None)


def py_sw01(s):
    k = hs(s, 4) % 20
    return sc.StepwiseResult([], None if k <= 3 else py_fit01(s * 16 + 1),
                             None if (k <= 2 or k == 4) else py_fit01(s * 16 + 2))


def run01(sw, df):
    ns = {"pl": pl, "np": np, "math": math, "model_features_train": df,
          "sas_compat": types.SimpleNamespace(stepwise_logistic=lambda *a, **k: sw)}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with np.errstate(all="ignore"):
            exec(CODE01, ns)
    return ns


def pre01(sw, df, ns):
    names_ok = len(set(df.columns)) == len(df.columns)
    f64 = all(c in df.columns and df.schema[c] == pl.Float64 for c in CANDS + ["default_flag"])
    fits = (sw.intercept_only is None) == (sw.final is None)
    steps = sw.final is not None or sw.steps == []
    return names_ok and f64 and fits and steps and ns["n_obs"] != 0


VAL01 = ("(match train_run_01_fit_frame (α := Float) (mkSW s) (mkF s) with | (c, mk, ff, fin, io, nobs, ytr, m0, yb) => "
         "dg (tT (c.map some) ++ tB (mk.map some) ++ tR ff ++ tFit fin ++ tFit io ++ tI [some nobs] ++ tF (ytr.map some) "
         "++ [yb.toBits] ++ (if io.isSome then [m0.toBits] else [])) : Int)")
# the m2ll0 of the kept seeds without an intercept-only fit, distinct values (Python: NaN)
M001 = ("(match train_run_01_fit_frame (α := Float) (mkSW s) (mkF s) with | (_, _, _, _, io, _, _, m0, _) => "
        "(if io.isNone then [(m0.toBits.toNat : Int)] else []) : List Int)")


def seed01(sd):
    sw, df = py_sw01(sd), py_frame01(sd)
    ns = run01(sw, df)  # a raise propagates: no seed of this generator raises (the run would stop)
    kept = pre01(sw, df, ns)
    toks = (p_tT(ns["candidates"]) + p_tB([bool(b) for b in ns["fit_mask"].tolist()]) + p_frame(ns["fit_frame"])
            + p_fit(ns["final"]) + p_fit(ns["intercept_only"]) + p_tI([ns["n_obs"]])
            + p_tF(ns["y_train"].tolist()) + [fb(ns["ybar"])] + ([fb(ns["m2ll0"])] if sw.intercept_only is not None else []))
    return cmp.digest(toks), ("kept" if kept else "rejected"), (fb(ns["m2ll0"]) if sw.intercept_only is None else None), ns


# ================================================================== step 02
LETS02 = (
    'let fw := fun (x : Option Float) (w d : Int) => (match x with | none => "N" | some v => '
    '"w" ++ toString v.toBits.toNat ++ "/" ++ toString w ++ "/" ++ toString d : String); '
    'let pv := fun (x : Option Float) => (match x with | none => "N" | some v => "p" ++ toString v.toBits.toNat : String); '
    f"let E1 : List (Option Float) := {lol(E1)}; let E2 : List (Option Float) := {lol(E2)}; let POOL : List String := {ls(POOL)}; "
    'let dum : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := 0.0, n_iter := 0, converged := true }; '
    "let mk := fun (s : Nat) => let k := (hsh s 0 % 7).toNat; "
    "let sc := gF (8*s+1) k 60 30 E1; let wd := gF (8*s+2) k 60 30 E1; let pv_ := gF (8*s+3) k 60 30 E2; "
    f"let en_ := gI (8*s+4) k 30 {len(POOL)} 0; let rm := gI (8*s+6) k 30 {len(POOL)} 0; "
    "let sp := gI (8*s+5) k 0 1000 500; let dfv := gI (8*s+7) k 0 6 1; let nim := gI (8*s+8) k 0 9 0; "
    "({ steps := (List.range k).map (fun (i : Nat) => ({ step := (sp.getD i none).getD 0, "
    "entered := (en_.getD i none).map (fun (j : Int) => POOL.getD j.toNat \"\"), "
    "removed := (rm.getD i none).map (fun (j : Int) => POOL.getD j.toNat \"\"), "
    "df := (dfv.getD i none).getD 0, number_in_model := (nim.getD i none).getD 0, "
    "score_chisq := (sc.getD i none), wald_chisq := (wd.getD i none), "
    "p_value := ((pv_.getD i none).getD 0.0), fit := dum } : StepwiseStep Float)), "
    "final := none, intercept_only := none } : StepwiseResult Float); "
    "let fin := fun (s : Nat) => (if hsh s 9 % 5 == 0 then none else some dum : Option (LogisticFit Float)); "
)
VAL02 = "dg (match train_run_02_stepwise_summary fw pv (mk s) (fin s) with | none => [0] | some p => 1 :: tS p.1 ++ tA p.2 : List UInt64)"


def p_fmt_wd(x, w, d):
    return f"w{fb(float(x))}/{w}/{d}"


def p_pvalue(x):
    return f"p{fb(float(x))}"


def py_sw02(s):
    k = hs(s, 0) % 7
    scs = kit.gF(8 * s + 1, k, 60, 30, E1)
    wds = kit.gF(8 * s + 2, k, 60, 30, E1)
    pvs = kit.gF(8 * s + 3, k, 60, 30, E2)
    en = kit.gI(8 * s + 4, k, 30, len(POOL), 0)
    rm = kit.gI(8 * s + 6, k, 30, len(POOL), 0)
    sp = kit.gI(8 * s + 5, k, 0, 1000, 500)
    dfv = kit.gI(8 * s + 7, k, 0, 6, 1)
    nim = kit.gI(8 * s + 8, k, 0, 9, 0)
    dummy = sc.LogisticFit(["Intercept"], np.zeros(0), np.zeros((0, 0)), 0.0, 0, True)
    steps = [sc.StepwiseStep(sp[i], None if en[i] is None else POOL[en[i]], None if rm[i] is None else POOL[rm[i]],
                             dfv[i], nim[i], scs[i], wds[i], 0.0 if pvs[i] is None else pvs[i], dummy) for i in range(k)]
    return sc.StepwiseResult(steps, None, None), (None if hs(s, 9) % 5 == 0 else dummy)


def run02(sw, final):
    got = []
    shim = types.SimpleNamespace(fmt_wd=p_fmt_wd, sas_pvalue=p_pvalue,
                                 write_sas_csv=lambda df, path, formats=None: got.append((Path(path).name, df)))
    ns = {"pl": pl, "np": np, "math": math, "sas_compat": shim, "stepwise": sw, "final": final,
          "output_dir": Path("/nonexistent")}
    exec(CODE02, ns)
    assert len(got) <= 1
    return got[0] if got else None


def seed02(sd):
    sw, final = py_sw02(sd)
    r = run02(sw, final)
    toks = [0] if r is None else [1] + cmp.tok_str(r[0]) + cmp.tokens(cmp.canon_table(r[1]))
    return cmp.digest(toks), "kept", r, sw


# ================================================================== step 04
LETS04 = (
    f"let PN : List String := {ls(PN)}; let QN : List Nat := {ln(QN)}; let NR4 : List Nat := {ln(NR4)}; "
    f"let SP : List String := {ls(SP)}; "
    f"let EV : List (Option Float) := {lol(EV)}; let EB : List (Option Float) := {lol(EB)}; let EC : List (Option Float) := {lol(EC)}; "
    "let nOf := fun (s : Nat) => NR4.getD (hsh s 1 % NR4.length.toUInt64).toNat 0; "
    "let mkF := fun (s : Nat) => let n := nOf s; "
    'let fc : List (String × Pl.Col Float) := (List.range 8).map (fun (j : Nat) => (PN.getD j "", Pl.Col.f64 (gF (s*64+j) n 40 3 EV))); '
    'let cols := fc ++ [("id", Pl.Col.int (gI (s*64+40) n 10 1000 500)), ("s", Pl.Col.str ((gI (s*64+41) n 20 SP.length.toUInt64 0).map '
    '(fun (o : Option Int) => o.map (fun (k : Int) => SP.getD k.toNat ""))))]; '
    "let r := (hsh s 3 % cols.length.toUInt64).toNat; ((cols.drop r ++ cols.take r) : Pl.Frame Float); "
    "let mkM := fun (s : Nat) => (List.range (nOf s + (if hsh s 20 % 40 == 0 then 1 else 0))).map (fun (i : Nat) => hsh (s+77) i % 4 != 0); "
    "let mkC := fun (s : Nat) => let l := (List.range 10).filter (fun (j : Nat) => hsh s (600+j) % 3 != 0); "
    "let r := (hsh s 21 % (l.length.toUInt64 + 1)).toNat; "
    'let l2 := (l.drop r ++ l.take r).map (fun (j : Nat) => PN.getD j ""); if hsh s 22 % 33 == 0 then l2 ++ l2.take 1 else l2; '
    "let mkFit := fun (s : Nat) => let m := (hsh s 6 % 6).toNat; "
    'let nm := (if hsh s 5 % 5 != 0 then ["Intercept"] else []) ++ (List.range m).map (fun (i : Nat) => '
    'PN.getD (QN.getD (hsh s (700+i) % QN.length.toUInt64).toNat 0) ""); '
    "let L := nm.length; "
    "let bv := (gF (s*64+50) L 30 3 EB).map (fun (o : Option Float) => o.getD 0.0); "
    "let dv := (gF (s*64+51) L 40 2 EC).map (fun (o : Option Float) => o.getD 0.0); "
    "let cv := (List.range L).map (fun (i : Nat) => (List.range L).map (fun (j : Nat) => if i == j then dv.getD i 0.0 else 0.125)); "
    "({ names := nm, beta := Np.NDArray.d1 bv, cov := Np.NDArray.d2 cv, loglik := -1.0, n_iter := 3, converged := true } : LogisticFit Float); "
    "let mkFin := fun (s : Nat) => (if hsh s 7 % 7 == 0 then none else some (mkFit s) : Option (LogisticFit Float)); "
)
VAL04 = ("(match train_run_04_score_train (α := Float) (mkC s) (mkM s) (mkFin s) (mkF s) with "
         "| (nm, ef, ix, lo, ic, co, lst, fsc) => dg (tT (nm.map some) ++ tT (ef.map some) ++ tI (ix.map some) ++ tI (lo.map some) "
         "++ tF [ic] ++ (co.length.toUInt64 :: co.flatMap (fun (p : String × Float) => tS p.1 ++ [p.2.toBits])) ++ tR lst ++ tR fsc) : Int)")


def py_frame04(s):
    n = NR4[hs(s, 1) % len(NR4)]
    cols = [pl.Series(PN[j], kit.gF(s * 64 + j, n, 40, 3, EV), dtype=pl.Float64) for j in range(8)]
    cols.append(pl.Series("id", kit.gI(s * 64 + 40, n, 10, 1000, 500), dtype=pl.Int64))
    cols.append(pl.Series("s", [None if k is None else SP[k] for k in kit.gI(s * 64 + 41, n, 20, len(SP), 0)], dtype=pl.String))
    r = hs(s, 3) % len(cols)
    return pl.DataFrame(cols[r:] + cols[:r])


def py_inputs04(s):
    n = NR4[hs(s, 1) % len(NR4)]
    mask = [hs(s + 77, i) % 4 != 0 for i in range(n + (1 if hs(s, 20) % 40 == 0 else 0))]
    lst = [j for j in range(10) if hs(s, 600 + j) % 3 != 0]
    r = hs(s, 21) % (len(lst) + 1)
    cands = [PN[j] for j in lst[r:] + lst[:r]]
    if hs(s, 22) % 33 == 0:
        cands = cands + cands[:1]
    fit = None
    if hs(s, 7) % 7 != 0:
        m = hs(s, 6) % 6
        nm = (["Intercept"] if hs(s, 5) % 5 != 0 else []) + [PN[QN[hs(s, 700 + i) % len(QN)]] for i in range(m)]
        L = len(nm)
        bv = [0.0 if x is None else x for x in kit.gF(s * 64 + 50, L, 30, 3, EB)]
        dv = [0.0 if x is None else x for x in kit.gF(s * 64 + 51, L, 40, 2, EC)]
        cv = [[dv[i] if i == j else 0.125 for j in range(L)] for i in range(L)]
        fit = sc.LogisticFit(nm, np.array(bv, dtype=np.float64), np.array(cv, dtype=np.float64).reshape(L, L), -1.0, 3, True)
    return cands, mask, fit, py_frame04(s)


def run04(cands, mask, fit, df):
    ns = {"pl": pl, "np": np, "math": math, "final": fit, "candidates": cands,
          "fit_mask": np.array(mask, dtype=bool), "model_features_train": df}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with np.errstate(all="ignore"):
            exec(CODE04, ns)
    return ns


def pre04_static(cands, mask, fit, df):
    if len(set(df.columns)) != len(df.columns):
        return False
    if len(mask) != df.height or len(set(cands)) != len(cands):
        return False
    if fit is not None:
        L = len(fit.names)
        cov = np.asarray(fit.cov)
        if cov.ndim != 2 or any(not (i < cov.shape[0] and i < cov.shape[1]) for i in range(L)):
            return False
        b = np.asarray(fit.beta)
        if b.ndim != 1 or len(b) != L or len(b) < 1:
            return False
        for c in cands:
            if c in fit.names and not (c in df.columns and df.schema[c] == pl.Float64):
                return False
    return True


def pre04_exp(ns, df):
    """last clause: for every row whose -eta is not null, exp(-eta) is finite (eta as the Python code builds it)."""
    e = df.with_columns((-ns["eta_train"]).alias("__e")).get_column("__e").to_list()
    with np.errstate(all="ignore"):
        return all(v is None or math.isfinite(float(np.exp(np.float64(v)))) for v in e)


def seed04(sd):
    cands, mask, fit, df = py_inputs04(sd)
    st = pre04_static(cands, mask, fit, df)
    try:
        ns = run04(cands, mask, fit, df)
    except Exception as ex:  # noqa: BLE001
        # inside the static clauses a raise is a defect of the precondition (the exp clause cannot make polars raise)
        return None, ("defect" if st else "dropped"), type(ex).__name__, fit
    kept = st and pre04_exp(ns, df)
    toks = (p_tT(ns["final_names"]) + p_tT(ns["final_effects"]) + p_tI(ns["final_index"]) + p_tI(ns["left_out"])
            + p_tF([ns["intercept"]]) + [len(ns["coefficients"])]
            + [t for k, v in ns["coefficients"].items() for t in cmp.tok_str(k) + [fb(v)]]
            + p_frame(ns["logit_scored_train"]) + p_frame(ns["fit_scored"]))
    return cmp.digest(toks), ("kept" if kept else "rejected"), ns, fit


KB, RB = 50, 25  # seeds per verdict block: kept, rejected


def emit(unit, lets, val, c0, n, vals, cls, table=False, extra_lean="", extra_exp=()):
    """One eval input over seeds c0 .. c0+n-1. The Lean computes V s for every kept / rejected seed (bit masks KM,
    RM), digests them in blocks of KB / RB seeds, compares each block with the Python digest given in the input and
    returns [#kept, #rejected, -1, <kept blocks that differ>, -2, <rejected blocks that differ>, -3, <extra>].
    Expected: [#kept, #rejected, -1, -2, -3, <extra>]. The verdict is computed in Lean; the output is short."""
    K = [i for i in range(n) if cls[i] == "kept"]
    R = [i for i in range(n) if cls[i] == "rejected"]
    km, rm = sum(1 << i for i in K), sum(1 << i for i in R)
    EK = [cmp.digest([vals[i] for i in K[j:j + KB]]) for j in range(0, len(K), KB)]
    ER = [cmp.digest([vals[i] for i in R[j:j + RB]]) for j in range(0, len(R), RB)]
    body = (
        f"let V := fun (s : Nat) => ({val} : Int); let KM : Nat := {hex(km)}; let RM : Nat := {hex(rm)}; "
        f"let ks := (List.range {n}).filter (fun (i : Nat) => KM.testBit i); "
        f"let rs := (List.range {n}).filter (fun (i : Nat) => RM.testBit i); "
        f"let D := fun (l : List Nat) => dg (l.map (fun (i : Nat) => (V (i + {c0})).toNat.toUInt64)); "
        "let bad := fun (l : List Nat) (b : Nat) (E : List Int) => ((List.range E.length).filter (fun (j : Nat) => "
        "D ((l.drop (j*b)).take b) != E.getD j 0)).map (fun (j : Nat) => (j : Int)); "
        f"let EK : List Int := {ln(EK)}; let ER : List Int := {ln(ER)}; "
        f"([(ks.length : Int), (rs.length : Int), -1] ++ bad ks {KB} EK ++ [-2] ++ bad rs {RB} ER ++ [-3]{extra_lean}))"
    )
    text = "(" + (kit.KIT if table else kit.KIT_NOTABLE) + kit.GEN + lets + body
    exp = [len(K), len(R), -1, -2, -3] + list(extra_exp)
    return {"unit": unit, "c0": c0, "n": n, "kept": [c0 + i for i in K], "rejected": [c0 + i for i in R],
            "other": {c0 + i: cls[i] for i in range(n) if cls[i] not in ("kept", "rejected")},
            "kb": KB, "rb": RB, "expected": exp, "text": text}


def main():
    a = [int(x) for x in sys.argv[1:]]
    n01, n02, n04, ch01, ch02, ch04 = (a + [3200, 2400, 4000, 1600, 2400, 2000][len(a):])[:6]
    first = 100000
    print("segments:", [(s[1], s[2]) for s in (SEG01, SEG02, SEG04)])
    suites = {}
    # ---- 01
    ins, st = [], {"kept": 0, "rejected": 0, "nofit_kept": 0, "fit_kept": 0, "n_obs_ge_128_kept": 0, "nan_in_y_kept": 0,
                   "nully_default_flag_kept": 0}
    for c0 in range(first, first + n01, ch01):
        n = min(ch01, first + n01 - c0)
        vals, cls, m0 = [], [], set()
        for sd in range(c0, c0 + n):
            v, c, m, ns = seed01(sd)
            vals.append(v)
            cls.append(c)
            st[c] += 1
            if c == "kept":
                if m is not None:
                    m0.add(m)
                    st["nofit_kept"] += 1
                else:
                    st["fit_kept"] += 1
                st["n_obs_ge_128_kept"] += ns["n_obs"] >= 128
                st["nan_in_y_kept"] += bool(np.isnan(ns["y_train"]).any())
                st["nully_default_flag_kept"] += ns["fit_mask"].sum() < len(ns["fit_mask"])
        extra = (f" ++ (((List.range {n}).filter (fun (i : Nat) => KM.testBit i)).flatMap (fun (i : Nat) => let s := i + {c0}; "
                 + M001 + ")).eraseDups")
        ins.append(emit("train_run_01_fit_frame", LETS01, VAL01, c0, n, vals, cls, extra_lean=extra, extra_exp=sorted(m0)))
        ins[-1]["note_extra"] = "after -3: distinct m2ll0 bits of the kept seeds with intercept_only None (Python: NaN)"
    suites["fz10c_ta01"] = (ins, st)
    # ---- 02
    ins, st = [], {"kept": 0, "rejected": 0, "none": 0, "empty_table": 0}
    for c0 in range(first, first + n02, ch02):
        n = min(ch02, first + n02 - c0)
        vals, cls = [], []
        for sd in range(c0, c0 + n):
            v, c, r, _ = seed02(sd)
            vals.append(v)
            cls.append(c)
            st[c] += 1
            st["none"] += r is None
            st["empty_table"] += r is not None and r[1].height == 0
        ins.append(emit("train_run_02_stepwise_summary", LETS02, VAL02, c0, n, vals, cls, table=True))
    suites["fz10c_ta02"] = (ins, st)
    # ---- 04
    ins, st = [], {"kept": 0, "rejected": 0, "dropped": 0, "defect": 0, "nofit_kept": 0, "leftout_kept": 0,
                   "intercept_leftout_kept": 0, "null_pd_kept": 0, "empty_frame_kept": 0}
    defects = []
    for c0 in range(first, first + n04, ch04):
        n = min(ch04, first + n04 - c0)
        vals, cls = [], []
        for sd in range(c0, c0 + n):
            v, c, ns, fit = seed04(sd)
            vals.append(v)
            cls.append(c)
            st[c] += 1
            if c == "defect":
                defects.append((sd, ns))
            if c == "kept":
                st["nofit_kept"] += fit is None
                st["leftout_kept"] += bool(ns["left_out"])
                st["intercept_leftout_kept"] += 0 in ns["left_out"]
                st["null_pd_kept"] += ns["logit_scored_train"].get_column("pd_logistic").null_count() > 0
                st["empty_frame_kept"] += ns["logit_scored_train"].height == 0
        ins.append(emit("train_run_04_score_train", LETS04, VAL04, c0, n, vals, cls))
    st["defects"] = defects[:10]
    suites["fz10c_ta04"] = (ins, st)
    W = HERE.parent / "work"
    for name, (ins, st) in suites.items():
        calls = [{"item": CARRIER[0], "decl": CARRIER[1], "inputs": [i["text"] for i in ins]}]
        (W / f"{name}.inputs.json").write_text(json.dumps(calls, indent=1, ensure_ascii=False))
        (W / f"{name}.json").write_text(json.dumps({
            "suite": name, "generator": "diffeval/units/fz10c_train_a_gen.py", "blueprint": BLUEPRINT,
            "carrier": CARRIER, "stats": {k: v for k, v in st.items()},
            "segments": {"01": SEG01[1:], "02": SEG02[1:], "04": SEG04[1:]},
            "inputs": [{k: v for k, v in i.items() if k != "text"} for i in ins]}, default=str))
        print(name, len(ins), "inputs", [len(i["text"]) for i in ins], st)


def compare(name):
    d = json.loads((HERE.parent / "work" / f"{name}.json").read_text())
    outs = (HERE.parent / "work" / f"{name}.out.txt").read_text().splitlines()
    for inp, o in zip(d["inputs"], outs, strict=True):
        got = json.loads(o)
        print(name, inp["c0"], "PASS" if got == inp["expected"] else "DIFF", "expected", inp["expected"], "got", got)


def localise(name, which):
    """--loc <suite> <input index>:<k|r>:<block>,...: one eval input that returns the seeds of those blocks whose
    value differs from Python's (seed list and per-seed expected values given in the input). Writes
    work/<suite>.loc.inputs.json and prints the seeds and expected list."""
    d = json.loads((HERE.parent / "work" / f"{name}.json").read_text())
    unit = {"fz10c_ta01": (LETS01, VAL01, False, seed01), "fz10c_ta02": (LETS02, VAL02, True, seed02),
            "fz10c_ta04": (LETS04, VAL04, False, seed04)}[name]
    seeds = []
    for w in which.split(","):
        ii, kr, b = w.split(":")
        inp = d["inputs"][int(ii)]
        lst, size = (inp["kept"], inp["kb"]) if kr == "k" else (inp["rejected"], inp["rb"])
        seeds += lst[int(b) * size:(int(b) + 1) * size]
    exp = [unit[3](sd)[0] for sd in seeds]
    body = (f"let V := fun (s : Nat) => ({unit[1]} : Int); let S : List Nat := {ln(seeds)}; let E : List Int := {ln(exp)}; "
            "((List.range S.length).filter (fun (j : Nat) => V (S.getD j 0) != E.getD j 0)).map (fun (j : Nat) => ((S.getD j 0 : Nat) : Int)))")
    text = "(" + (kit.KIT if unit[2] else kit.KIT_NOTABLE) + kit.GEN + unit[0] + body
    (HERE.parent / "work" / f"{name}.loc.inputs.json").write_text(json.dumps(
        [{"item": CARRIER[0], "decl": CARRIER[1], "which": which, "seeds": seeds, "inputs": [text]}], ensure_ascii=False))
    print(len(seeds), "seeds; body:", body[body.index("let S"):][:300])


def exp_args04(sd):
    """(-eta) of every row with a non-null eta, and polars' exp of it (bits), as train.py computes pd_logistic."""
    cands, mask, fit, df = py_inputs04(sd)
    ns = run04(cands, mask, fit, df)
    e = df.select((-ns["eta_train"]).alias("e")).to_series()
    if len(e) != df.height:  # a literal-only eta: broadcast like with_columns
        e = pl.Series("e", [e[0]] * df.height, dtype=pl.Float64) if df.height else e.head(0)
    ex = e.exp().to_list()
    return [(fb(a), fb(x)) for a, x in zip(e.to_list(), ex) if a is not None], ns


def explain04(seeds_s, table_s=""):
    """--exp04 <seeds> : eval input returning [seed, bits of -eta, bits of Lean's Float.exp] wherever Lean's exp
    differs from polars' exp on the arguments of those seeds.
    --exp04 <seeds> <seed:argbits:leanbits,...> : eval input checking that V s equals the Python digest recomputed
    with Lean's exp value on those arguments (RULEBOOK section 6, last bit of exp); returns the seeds where not."""
    seeds = [int(x) for x in seeds_s.split(",")]
    if not table_s:
        rows = [(sd, a, b) for sd in seeds for a, b in exp_args04(sd)[0]]
        body = (f"let A : List (Nat × UInt64 × UInt64) := [{', '.join(f'({s}, {a}, {b})' for s, a, b in rows)}]; "
                "(A.filter (fun (p : Nat × UInt64 × UInt64) => (Float.exp (Float.ofBits p.2.1)).toBits != p.2.2)).flatMap "
                "(fun (p : Nat × UInt64 × UInt64) => [(p.1 : Int), (p.2.1.toNat : Int), ((Float.exp (Float.ofBits p.2.1)).toBits.toNat : Int)]))")
        text = "(" + body
        print(len(rows), "arguments")
    else:
        sub = {}
        for w in table_s.split(","):
            s, a, b = (int(x) for x in w.split(":"))
            sub[(s, a)] = b
        exp = []
        import polars as _pl
        for sd in seeds:
            cands, mask, fit, df = py_inputs04(sd)
            ns = run04(cands, mask, fit, df)
            e = df.with_columns((-ns["eta_train"]).alias("__e")).get_column("__e").to_list()
            pd_ = []
            for a in e:
                if a is None:
                    pd_.append(None)
                    continue
                ab = fb(a)
                xv = float(_pl.Series([a]).exp()[0])
                if (sd, ab) in sub:
                    xv = struct.unpack("<d", struct.pack("<Q", sub[(sd, ab)]))[0]
                pd_.append(float(_pl.Series([1.0]) [0] / (1.0 + xv)))
            lst = ns["logit_scored_train"].with_columns(_pl.Series("pd_logistic", pd_, dtype=_pl.Float64))
            fsc = lst.filter(_pl.Series(np.array(mask, dtype=bool)))
            toks = (p_tT(ns["final_names"]) + p_tT(ns["final_effects"]) + p_tI(ns["final_index"]) + p_tI(ns["left_out"])
                    + p_tF([ns["intercept"]]) + [len(ns["coefficients"])]
                    + [t for k, v in ns["coefficients"].items() for t in cmp.tok_str(k) + [fb(v)]]
                    + p_frame(lst) + p_frame(fsc))
            exp.append(cmp.digest(toks))
            # check the recomputation itself: without substitution it must give the port's own digest
            assert any(k[0] == sd for k in sub) or exp[-1] == seed04(sd)[0]
            if any(k[0] == sd for k in sub):
                print(sd, "recomputed with Lean's exp", exp[-1], "port", seed04(sd)[0])
        body = (f"let V := fun (s : Nat) => ({VAL04} : Int); let S : List Nat := {ln(seeds)}; let E : List Int := {ln(exp)}; "
                "((List.range S.length).filter (fun (j : Nat) => V (S.getD j 0) != E.getD j 0)).map (fun (j : Nat) => ((S.getD j 0 : Nat) : Int)))")
        text = "(" + kit.KIT_NOTABLE + kit.GEN + LETS04 + body
    (HERE.parent / "work" / "fz10c_ta04.exp.inputs.json").write_text(json.dumps(
        [{"item": CARRIER[0], "decl": CARRIER[1], "seeds": seeds, "table": table_s, "inputs": [text]}], ensure_ascii=False))
    print(text if not table_s else text[text.index("let V :="):])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--exp04":
        explain04(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    elif len(sys.argv) > 1 and sys.argv[1] == "--loc":
        localise(sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 1 and sys.argv[1] == "--cmp":
        for nm in sys.argv[2:]:
            compare(nm)
    else:
        main()

