"""Fidelity pass 2026-11-20, third attempt (label train-c): seeded fuzz of
  def:train_run_08_ctable            credit_risk/train.py:479-535  suite fz10c_ct
  def:train_run_11_confusion_valid   credit_risk/train.py:640-700  suite fz10c_cv
on blueprint 5365851c-5549-44b7-9207-4bd4c422031d, carrier def:zz_carrier_fid_2 / zz_carrier_fid_2 (it depends on
both units directly).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_train_gen.py
  (eval_decl every input of work/fz10c_ct.inputs.json, work/fz10c_cv.inputs.json;
   python3 diffeval/units/fz10_collect.py <session record> <suite>; compare.py; fuzz_receipt.py)

Every input is built INSIDE Lean from its seed (kit.GEN: hsh, gF, gI; R s k m = hsh s k % m) and mirrored here
bit for bit. One eval input = one block of seeds of one class (kept / rejected); it returns ONE digest: dg of the
concatenation, over the seeds of the block in order, of the token streams of the generated INPUTS and of the
unit's RESULT (so the digest also checks that both sides built the same inputs). A block that differs is split
seed by seed (`--seeds` mode).

Expected = the source lines of the step at HEAD executed as they stand (sliced from credit_risk/train.py by text
markers, dedented, exec'd with the module's globals).

Step 11 (fz10c_cv). Frame: rows n in {0,1,1,2,3,4,5,7,10,16,25,40}; default_flag Float64 from the edge pool
EF = {null, 0, 1, -0.0, NaN, 2, 0.5} (weighted to 0 and 1) [60 %], Int64 in {0,1,2} with 0/20/50 % nulls [30 %],
absent [10 %]; pred_logistic Int64 {0,1} with 0/10/30/100 % nulls, or {-1..2} with 10 % nulls; a third Float64
column `zz` (random floats and edges) in one layout; column orders [d, p], [p, d], [d, zz, p].
Precondition (def:train_run_11_confusion_valid_precond) rendered in Python: names distinct, columns of one length
(by construction), default_flag Float64 or Int64 when present (by construction), pred_logistic Int64. Rejected
class: pred_logistic Float64 (layout pk = 5, one seed in six); Python returns there (sent, counted as narrowing
where Lean equals Python).

Step 08 (fz10c_ct). As fz5_ctable_gen (fifth round), generated in Lean: n in {0,1,1,2,2,3,4,5,6,9,11,26}; 0, 1 or 2
predictors (modes: random ints -3..3, constant 1, zero, {0,-0,1}, twice x1, the name x1 repeated); an `extra`
column 30 %; 0-2 rows outside the fit mask (pd there from {null, 0.5, 2.0, NaN}); y 0/1 (intercept-only models with
event shares 0/10/50/90/100 %); pd = clamp(base + {-1,0,0,1} * spread) with base on and off the printed grid; a
null pd on the first complete case 4 %; a final fit 80 % with diagonal covariance from {1,1,1,0,-0,2.5,NaN,0}.
Explicit parameters (RULEBOOK section 3), the same function on both sides: fmt_wd = "<bits of the value or N>:w:d"
(injective, so every cell, its w and its d are compared); inv = the matrix with `a` at [0][0] and 0 elsewhere
(a in {0,0,0.25,1,4}); solve = Cramer's rule for 1x1 / 2x2 (Python: the same formulas); log1p = log(1 + x)
(Python: np.log(1.0 + x)); dot, matmul, einsum_q = sequential sums (Python: numpy's `@` and np.einsum, NOT
replaced: on these inputs every product they form is exact, or feeds only the pivot test of _kept); matvec is not
reached (pd is given).
Precondition (def:train_run_08_ctable_precond) rendered in Python per clause:
  0 <= n; predictor columns Float64 of n values, no null with a fit; pd_logistic Float64 of the mask's length
  (all by construction); ctable_made -> no null pd on a complete case; a fit -> classification_is_made_precond:
  with the stand-in matmul, x.T @ x of an x with no row is ncols empty rows, not square (_kept_precond), so n = 0
  with a fit is REJECTED; ctable_made -> classification_table_precond: (3) 0 < pd < 1 with a predictor (clamped),
  (6') n != 1 intercept only, (7) ps has no NaN and 0 <= klo <= khi <= 50 (read off the levels Python printed:
  first ProbLevel >= 0 and last <= 1), (8) n1 integral (y is 0/1).
"""
from __future__ import annotations

import json
import math
import struct
import sys
import textwrap
import types
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")

import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

nan = float("nan")
BP = "5365851c-5549-44b7-9207-4bd4c422031d"
GENERATOR = "migration/port-to-lean/diffeval/units/fz10c_train_gen.py"
U08, U11 = "train_run_08_ctable", "train_run_11_confusion_valid"
SRC = Path(train.__file__).read_text().splitlines()


def R(s: int, k: int, m: int) -> int:
    return kit.hsh(s, k) % m


def fb(x: float) -> int:
    return cmp.fbits(x)


def slice_src(first, last_pred, extra: int):
    a = next(i for i, l in enumerate(SRC) if first(l))
    b = next(i for i in range(a, len(SRC)) if last_pred(SRC[i])) + extra
    return compile(textwrap.dedent("\n".join(SRC[a:b + 1])), f"train.py:{a + 1}-{b + 1}", "exec"), a + 1, b + 1


S11, A11, B11 = slice_src(lambda l: l.strip() == "confusion_matrix = (",
                          lambda l: ".head(min(confusion_matrix.height, 1))" in l, 1)
S08, A08, B08 = slice_src(lambda l: l.strip() == "x_final = np.column_stack(",
                          lambda l: 'output_dir / "printed_classification.csv"' in l, 1)

RLET = "let R := fun (s k m : Nat) => ((hsh s k) % m.toUInt64).toNat; "

# ================================================================ step 11
EF = [None, 0.0, 1.0, -0.0, nan, 2.0, 0.5, 1.0, 0.0, 1.0, 0.0]
NS11 = [0, 1, 1, 2, 3, 4, 5, 7, 10, 16, 25, 40]
PN = [0, 10, 30, 10, 100]
L11 = (
    "let EF : List (Option Float) := [none, some 0.0, some 1.0, some (-0.0), some (0.0/0.0), some 2.0, some 0.5, "
    "some 1.0, some 0.0, some 1.0, some 0.0]; "
    "let NS : List Nat := [0, 1, 1, 2, 3, 4, 5, 7, 10, 16, 25, 40]; "
    "let PN : List UInt64 := [0, 10, 30, 10, 100]; "
    "let mk := fun (s : Nat) => "
    "let n := NS.getD (R s 0 12) 0; let dk := R s 1 10; let pk := R s 2 6; let ok := R s 3 4; "
    "let dfc : Pl.Col Float := if dk < 6 then Pl.Col.f64 (gF (4*s+1) n 100 0 EF) "
    "else Pl.Col.int (gI (4*s+1) n (([0, 20, 50] : List UInt64).getD (R s 4 3) 0) 3 0); "
    "let plc : Pl.Col Float := if pk == 5 then Pl.Col.f64 (gF (4*s+2) n 100 0 EF) "
    "else if pk == 3 then Pl.Col.int (gI (4*s+2) n 10 4 1) else Pl.Col.int (gI (4*s+2) n (PN.getD pk 0) 2 0); "
    "let D : Pl.Frame Float := if dk == 9 then [] else [(\"default_flag\", dfc)]; "
    "let P : Pl.Frame Float := [(\"pred_logistic\", plc)]; "
    "let Z : Pl.Frame Float := [(\"zz\", Pl.Col.f64 (gF (4*s+3) n 30 3 EF))]; "
    "(if ok == 2 then P ++ D else if ok == 3 then D ++ Z ++ P else D ++ P : Pl.Frame Float); "
    "let tok := fun (s : Nat) => let fr := mk s; let r := train_run_11_confusion_valid fr; "
    "tR fr ++ tR r.1 ++ tR r.2; "
)


def mk11(s: int) -> tuple[pl.DataFrame, int]:
    n, dk, pk, ok = NS11[R(s, 0, 12)], R(s, 1, 10), R(s, 2, 6), R(s, 3, 4)
    if dk < 6:
        dfc = pl.Series("default_flag", kit.gF(4 * s + 1, n, 100, 0, EF), dtype=pl.Float64)
    else:
        dfc = pl.Series("default_flag", kit.gI(4 * s + 1, n, [0, 20, 50][R(s, 4, 3)], 3, 0), dtype=pl.Int64)
    if pk == 5:
        plc = pl.Series("pred_logistic", kit.gF(4 * s + 2, n, 100, 0, EF), dtype=pl.Float64)
    elif pk == 3:
        plc = pl.Series("pred_logistic", kit.gI(4 * s + 2, n, 10, 4, 1), dtype=pl.Int64)
    else:
        plc = pl.Series("pred_logistic", kit.gI(4 * s + 2, n, PN[pk], 2, 0), dtype=pl.Int64)
    zz = pl.Series("zz", kit.gF(4 * s + 3, n, 30, 3, EF), dtype=pl.Float64)
    D = [] if dk == 9 else [dfc]
    cols = [plc] + D if ok == 2 else D + [zz, plc] if ok == 3 else D + [plc]
    return pl.DataFrame(cols), pk


def run11(fr: pl.DataFrame):
    ns = dict(vars(train))
    ns["logit_scored_valid"] = fr
    exec(S11, ns)  # noqa: S102
    return ns["confusion_matrix"], ns["validation_metrics"]


def tok11(s: int):
    fr, pk = mk11(s)
    try:
        cm, vm = run11(fr)
    except Exception as ex:  # noqa: BLE001
        return None, pk != 5, ex, fr
    t = cmp.tokens(cmp.canon_frame(fr)) + cmp.tokens(cmp.canon_frame(cm)) + cmp.tokens(cmp.canon_frame(vm))
    return t, pk != 5, None, fr


# ================================================================ step 08
NS08 = [0, 1, 1, 2, 2, 3, 4, 5, 6, 9, 11, 26]
PB = [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875]
SP = [0.0, 0.0, 0.005, 0.01]
CV = [1.0, 1.0, 1.0, 0.0, -0.0, 2.5, nan, 0.0]
AA = [0.0, 0.0, 0.25, 1.0, 4.0]
PX = [None, 0.5, 2.0, nan]
DD = [-1.0, 0.0, 0.0, 1.0]

FMT = ('(fun (v : Option Float) (w d : Int) => (match v with | none => "N" | some x => toString x.toBits.toNat : String)'
       ' ++ ":" ++ toString w ++ ":" ++ toString d)')
INV = ("(fun (a : Float) (m : List (List Float)) => m.mapIdx (fun (i : Nat) (r : List Float) => "
       "r.mapIdx (fun (j : Nat) (_ : Float) => if i + j == 0 then a else 0.0)))")
SOLVE = ("(fun (m : List (List Float)) (b : List Float) => (match m, b with | [[a]], [x] => [x / a] "
         "| [[a, p], [c, d]], [x, y] => [(x * d - p * y) / (a * d - p * c), (a * y - c * x) / (a * d - p * c)] "
         "| _, _ => b : List Float))")
DOT = "(fun (u v : List Float) => (u.zip v).foldl (fun (s : Float) (p : Float × Float) => s + p.1 * p.2) 0.0)"
MATMUL = ("(fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range (b.headD []).length).map "
          "(fun (j : Nat) => (r.zip (b.map (fun (q : List Float) => q.getD j 0.0))).foldl "
          "(fun (s : Float) (p : Float × Float) => s + p.1 * p.2) 0.0)))")
MATVEC = "(fun (_ : List (List Float)) (_ : List Float) => ([] : List Float))"
EINSUM = ("(fun (x v : List (List Float)) => x.map (fun (r : List Float) => (List.range r.length).foldl "
          "(fun (s : Float) (j : Nat) => (List.range r.length).foldl (fun (t : Float) (k : Nat) => "
          "t + r.getD j 0.0 * (v.getD j []).getD k 0.0 * r.getD k 0.0) s) 0.0))")
LOG1P = "(fun (x : Float) => Float.log (1.0 + x))"

L08 = (
    f"let FMT := {FMT}; let INV := {INV}; let SOLVE := {SOLVE}; let DOT := {DOT}; let MATMUL := {MATMUL}; "
    f"let MATVEC := {MATVEC}; let EINSUM := {EINSUM}; let LOG1P := {LOG1P}; "
    "let NS : List Nat := [0, 1, 1, 2, 2, 3, 4, 5, 6, 9, 11, 26]; "
    "let PB : List Float := [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875]; "
    "let SP : List Float := [0.0, 0.0, 0.005, 0.01]; "
    "let CV : List Float := [1.0, 1.0, 1.0, 0.0, -0.0, 2.5, 0.0/0.0, 0.0]; "
    "let AA : List Float := [0.0, 0.0, 0.25, 1.0, 4.0]; "
    "let PX : List (Option Float) := [none, some 0.5, some 2.0, some (0.0/0.0)]; "
    "let DD : List Float := [-1.0, 0.0, 0.0, 1.0]; "
    "let col := fun (s k n md : Nat) (x1 : List Float) => (List.range n).map (fun (i : Nat) => "
    "(if md == 0 then Float.ofInt (Int.ofNat (R s (1000*k+i) 7) - 3) else if md == 1 then 1.0 else if md == 2 then 0.0 "
    "else if md == 3 then ([0.0, -0.0, 1.0] : List Float).getD (R s (1000*k+i) 3) 0.0 else 2.0 * x1.getD i 0.0 : Float)); "
    "let tok := fun (s : Nat) => "
    "let n := NS.getD (R s 0 12) 0; "
    "let nv := ([0, 0, 1, 1, 2] : List Nat).getD (R s 1 5) 0; "
    "let m1 := ([0, 0, 0, 1, 2, 3] : List Nat).getD (R s 3 6) 0; "
    "let m2 := ([0, 0, 5, 1, 2, 4, 3] : List Nat).getD (R s 4 7) 0; "
    "let x1 := col s 1 n m1 []; let x2 := col s 2 n m2 x1; "
    "let names : List String := if nv == 0 then [\"Intercept\"] else if nv == 1 then [\"Intercept\", \"x1\"] "
    "else if m2 == 5 then [\"Intercept\", \"x1\", \"x1\"] else [\"Intercept\", \"x1\", \"x2\"]; "
    "let ff : Pl.Frame Float := (if nv ≥ 1 then [(\"x1\", Pl.Col.f64 (x1.map some))] else []) ++ "
    "(if nv == 2 && m2 != 5 then [(\"x2\", Pl.Col.f64 (x2.map some))] else []) ++ "
    "(if R s 5 10 < 3 then [(\"extra\", Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofNat (R s (3000+i) 5)))))] else []); "
    "let NN := n + ([0, 0, 1, 2] : List Nat).getD (R s 6 4) 0; "
    "let off := R s 7 (max NN 1); "
    "let mask : List Bool := (List.range NN).map (fun (i : Nat) => decide ((i + off) % NN < n)); "
    "let pr := ([0, 10, 50, 90, 100] : List Nat).getD (R s 8 5) 0; "
    "let y : List Float := (List.range n).map (fun (i : Nat) => if nv == 0 && n ≥ 2 then "
    "(if R s (4000+i) 100 < pr then 1.0 else 0.0) else Float.ofNat (R s (4000+i) 2)); "
    "let pb := PB.getD (R s 9 9) 0.0; let sp := SP.getD (R s 10 4) 0.0; "
    "let nullAt : Nat := if R s 11 100 < 4 then mask.findIdx (fun (b : Bool) => b) else NN + 1; "
    "let pd : List (Option Float) := (List.range NN).map (fun (i : Nat) => if mask.getD i false then "
    "(if i == nullAt then none else (let v := pb + DD.getD (R s (5000+i) 4) 0.0 * sp; "
    "let v := (if v > 0.001 then v else 0.001); some (if v < 0.999 then v else 0.999))) "
    "else PX.getD (R s (5000+i) 4) none); "
    "let diag : List Float := (List.range names.length).map (fun (i : Nat) => CV.getD (R s (6000+i) 8) 0.0); "
    "let cov : List (List Float) := (List.range names.length).map (fun (i : Nat) => (List.range names.length).map "
    "(fun (j : Nat) => if i == j then diag.getD i 0.0 else 0.0)); "
    "let fin : Option (LogisticFit Float) := if R s 2 10 < 8 then some { names := names, beta := Np.NDArray.d1 [], "
    "cov := Np.NDArray.d2 cov, loglik := 0.0, n_iter := 0, converged := true } else none; "
    "let a := AA.getD (R s 12 5) 0.0; "
    "let sd : Pl.Frame Float := [(\"pd_logistic\", Pl.Col.f64 pd)]; "
    "let r := train_run_08_ctable (α := Float) FMT (INV a) SOLVE DOT MATMUL MATVEC EINSUM LOG1P mask ff fin names "
    "(n : Int) y sd; "
    "tR ff ++ tR sd ++ tC (Pl.Col.bool (mask.map some)) ++ tC (Pl.Col.f64 (y.map some)) ++ "
    "tC (Pl.Col.str (names.map some)) ++ tC (Pl.Col.f64 (diag.map some)) ++ [a.toBits] ++ "
    "(r.length.toUInt64 :: r.flatMap (fun (p : String × Tabular.Table Float) => tS p.1 ++ tA p.2)); "
)


def fmt_py(v, w, d):
    return ("N" if v is None else str(fb(float(v)))) + f":{w}:{d}"


def solve_py(m, b):
    m = np.asarray(m, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    with np.errstate(all="ignore"):
        if m.shape == (1, 1):
            return np.array([b[0] / m[0, 0]])
        if m.shape == (2, 2):
            a, p, c, d = m[0, 0], m[0, 1], m[1, 0], m[1, 1]
            x, y = b[0], b[1]
            return np.array([(x * d - p * y) / (a * d - p * c), (a * y - c * x) / (a * d - p * c)])
        return b


class NPX:
    """sas_compat.np with the explicit parameters (RULEBOOK section 3) replaced: linalg.inv, linalg.solve, log1p."""

    def __init__(self, a):
        def inv(m):
            k = m.shape[0]
            o = np.zeros((k, k))
            if k:
                o[0, 0] = a
            return o

        self.linalg = types.SimpleNamespace(solve=solve_py, inv=inv)

    def log1p(self, x):
        with np.errstate(all="ignore"):
            return np.log(1.0 + x)

    def __getattr__(self, k):
        return getattr(np, k)


def col08(s, k, n, md, x1):
    out = []
    for i in range(n):
        if md == 0:
            out.append(float(R(s, 1000 * k + i, 7) - 3))
        elif md == 1:
            out.append(1.0)
        elif md == 2:
            out.append(0.0)
        elif md == 3:
            out.append([0.0, -0.0, 1.0][R(s, 1000 * k + i, 3)])
        else:
            out.append(2.0 * x1[i])
    return out


def mk08(s):
    n = NS08[R(s, 0, 12)]
    nv = [0, 0, 1, 1, 2][R(s, 1, 5)]
    m1 = [0, 0, 0, 1, 2, 3][R(s, 3, 6)]
    m2 = [0, 0, 5, 1, 2, 4, 3][R(s, 4, 7)]
    x1 = col08(s, 1, n, m1, [])
    x2 = col08(s, 2, n, m2, x1)
    names = (["Intercept"] if nv == 0 else ["Intercept", "x1"] if nv == 1
             else ["Intercept", "x1", "x1"] if m2 == 5 else ["Intercept", "x1", "x2"])
    cols = {}
    if nv >= 1:
        cols["x1"] = x1
    if nv == 2 and m2 != 5:
        cols["x2"] = x2
    if R(s, 5, 10) < 3:
        cols["extra"] = [float(R(s, 3000 + i, 5)) for i in range(n)]
    NN = n + [0, 0, 1, 2][R(s, 6, 4)]
    off = R(s, 7, max(NN, 1))
    mask = [((i + off) % NN) < n for i in range(NN)]
    pr = [0, 10, 50, 90, 100][R(s, 8, 5)]
    y = [(1.0 if R(s, 4000 + i, 100) < pr else 0.0) if (nv == 0 and n >= 2) else float(R(s, 4000 + i, 2))
         for i in range(n)]
    pb, sp = PB[R(s, 9, 9)], SP[R(s, 10, 4)]
    null_at = (mask.index(True) if True in mask else NN) if R(s, 11, 100) < 4 else NN + 1
    pd = []
    for i in range(NN):
        if mask[i]:
            if i == null_at:
                pd.append(None)
            else:
                v = pb + DD[R(s, 5000 + i, 4)] * sp
                v = v if v > 0.001 else 0.001
                pd.append(v if v < 0.999 else 0.999)
        else:
            pd.append(PX[R(s, 5000 + i, 4)])
    diag = [CV[R(s, 6000 + i, 8)] for i in range(len(names))]
    fin = diag if R(s, 2, 10) < 8 else None
    a = AA[R(s, 12, 5)]
    return dict(n=n, names=names, cols=cols, mask=mask, y=y, pd=pd, diag=diag, final=fin, a=a)


def run08(c):
    writes = []
    proxy = types.SimpleNamespace(classification_table=sc.classification_table,
                                  classification_is_made=sc.classification_is_made, fmt_wd=fmt_py,
                                  write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ff = pl.DataFrame([pl.Series(k, v, dtype=pl.Float64) for k, v in c["cols"].items()])
    sd = pl.DataFrame({"pd_logistic": pl.Series(c["pd"], dtype=pl.Float64)})
    fin = None
    if c["final"] is not None:
        k = len(c["names"])
        cov = np.zeros((k, k))
        for i, v in enumerate(c["final"]):
            cov[i, i] = v
        fin = sc.LogisticFit(list(c["names"]), np.zeros(k), cov, 0.0, 0, True)
    ns = {"np": np, "pl": pl, "sas_compat": proxy, "fit_frame": ff, "n_obs": c["n"],
          "y_train": np.array(c["y"], dtype=np.float64), "final": fin, "final_names": list(c["names"]),
          "logit_scored_train": sd, "fit_mask": np.array(c["mask"], dtype=bool), "output_dir": Path("out")}
    old = sc.np
    sc.np = NPX(c["a"])
    try:
        with np.errstate(all="ignore"):
            exec(S08, ns)  # noqa: S102
        return ns, writes, None, ff, sd
    except Exception as ex:  # noqa: BLE001
        return ns, writes, ex, ff, sd
    finally:
        sc.np = old


def pre08(c, ns, ex) -> bool:
    """def:train_run_08_ctable_precond on the generated input (clauses held by construction are not re-tested)."""
    made = ns.get("ctable_made")
    if made is None:  # Python raised before :490
        made = False
    null_complete = any(m and p is None for m, p in zip(c["mask"], c["pd"]))
    if made and null_complete:
        return False
    if c["final"] is not None and c["n"] == 0:  # _kept_precond of matmul(xT, []) (ncols empty rows)
        return False
    if made:
        icpt = len(c["names"]) == 1
        if icpt and c["n"] == 1:
            return False
        if ex is not None:
            return True  # a raise inside: a defect (counted by the caller)
        lv = ns["ctable"].get_column("ProbLevel").to_list()
        if not lv or not (lv[0] >= 0.0 and lv[-1] <= 1.0):
            return False
    return True


def tok08(s):
    c = mk08(s)
    ns, writes, ex, ff, sd = run08(c)
    pre = pre08(c, ns, ex)
    if ex is not None:
        return None, pre, ex, c, ns
    t = cmp.tokens(cmp.canon_frame(ff)) + cmp.tokens(cmp.canon_frame(sd))
    t += cmp.tok_col(cmp.canon_bools(c["mask"])) + cmp.tok_col(cmp.canon_floats(c["y"]))
    t += cmp.tok_col(cmp.canon_strs(c["names"])) + cmp.tok_col(cmp.canon_floats(c["diag"])) + [fb(c["a"])]
    t += [len(writes)]
    for name, df in writes:
        t += cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df))
    return t, pre, None, c, ns


# ================================================================ suites
def build(name, unit, lets, tokf, seeds, block, notes_fn):
    s = Suite(name, generator=GENERATOR)
    kept, rej, raises_in, dropped, info = [], [], [], 0, []
    toks = {}
    for sd in seeds:
        t, pre, ex, *rest = tokf(sd)
        if ex is not None:
            if pre:
                raises_in.append(sd)
            else:
                dropped += 1
            continue
        toks[sd] = t
        (kept if pre else rej).append(sd)
        info.append((sd, pre, rest))
    # one input per (range of `block` consecutive seeds, class): the seeds of the class are the set bits of M
    for b0 in range(0, len(seeds), block):
        rng = seeds[b0:b0 + block]
        for cls, lst in (("kept", set(kept)), ("rejected", set(rej))):
            part = [x for x in rng if x in lst]
            if not part:
                continue
            m = sum(1 << (x - rng[0]) for x in part)
            body = (f"[dg (((List.range {len(rng)}).filter (fun (i : Nat) => Nat.testBit {m} i)).flatMap "
                    f"(fun (i : Nat) => tok ({rng[0]} + i)))]")
            exp = cmp.digest([x for sd in part for x in toks[sd]])
            s.ints(lets, body, [(f"{cls} {rng[0]}..{rng[-1]} ({len(part)})", unit, exp,
                                 {"fz": cls, "covers": len(part), "seeds": part})], gen=True, table=True)
    s.write()
    stats = notes_fn(info)
    fz = {"fuzzer": "port-translator (fidelity pass 2026-11-20 third attempt, train-c)", "generator": GENERATOR,
          "blueprint": BP,
          "units": {unit: {"seeds": f"{seeds[0]}..{seeds[-1]}", "generated": len(seeds), "kept": len(kept),
                           "python_raises_inside_precondition": raises_in,
                           "note": f"rejected and Python returns: {len(rej)}; rejected and Python raises (dropped): "
                                   f"{dropped}; {stats}"}}}
    (s.name and (HERE.parent / "work" / f"{name}.fuzz.json").write_text(json.dumps(fz, indent=1)))
    print(name, "kept", len(kept), "rejected", len(rej), "raises inside", raises_in[:10], "dropped", dropped)
    print("  ", stats)
    return toks


def stats11(info):
    st = {"n=0": 0, "no default_flag": 0, "Int64 default_flag": 0, "NaN key": 0, "-0.0 key": 0, "null default_flag": 0,
          "null pred": 0, "pred -1 or 2": 0, "every key row has a null (sum 0)": 0, "40 rows": 0, "levels>=5": 0}
    for sd, pre, rest in info:
        fr = rest[0]
        n = fr.height
        st["n=0"] += n == 0
        st["40 rows"] += n == 40
        if "default_flag" not in fr.columns:
            st["no default_flag"] += 1
            continue
        d = fr.get_column("default_flag")
        p = fr.get_column("pred_logistic")
        st["Int64 default_flag"] += d.dtype == pl.Int64
        st["NaN key"] += d.dtype == pl.Float64 and bool(d.is_nan().any())
        st["-0.0 key"] += d.dtype == pl.Float64 and any(v is not None and v == 0 and math.copysign(1, v) < 0 for v in d.to_list())
        st["null default_flag"] += bool(d.is_null().any())
        st["null pred"] += bool(p.is_null().any())
        st["pred -1 or 2"] += any(v in (-1, 2) for v in p.to_list() if v is not None)
        st["every key row has a null (sum 0)"] += n > 0 and bool((d.is_null() | p.is_null()).all())
        st["levels>=5"] += fr.select(["default_flag", "pred_logistic"]).unique().height >= 5
    return "reached: " + json.dumps(st)


def stats08(info):
    st = {"no fit": 0, "fit, table made": 0, "fit, no table": 0, "intercept only, made": 0, "with a variable, made": 0,
          "dupname": 0, "khi=50 (last level 1.000)": 0, "a level 0.000": 0, "null pd on a complete case": 0,
          "rows outside the mask": 0, "table rows max": 0}
    for sd, pre, rest in info:
        c, ns = rest
        made = bool(ns.get("ctable_made"))
        if c["final"] is None:
            st["no fit"] += 1
        elif made:
            st["fit, table made"] += 1
            st["intercept only, made" if len(c["names"]) == 1 else "with a variable, made"] += 1
            lv = ns["ctable"].get_column("ProbLevel").to_list()
            st["khi=50 (last level 1.000)"] += bool(lv) and lv[-1] == 1.0
            st["a level 0.000"] += bool(lv) and lv[0] == 0.0
            st["table rows max"] = max(st["table rows max"], len(lv))
        else:
            st["fit, no table"] += 1
        st["dupname"] += len(c["names"]) == 3 and c["names"][2] == "x1"
        st["null pd on a complete case"] += any(m and p is None for m, p in zip(c["mask"], c["pd"]))
        st["rows outside the mask"] += len(c["mask"]) > c["n"]
    return "reached: " + json.dumps(st)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--seeds":  # one input per seed (localising a differing block)
        unit, seeds = args[1], [int(x) for x in args[2].split(",")]
        lets, tokf, nm = (L11, tok11, "fz10c_cv_seeds") if unit == "cv" else (L08, tok08, "fz10c_ct_seeds")
        s = Suite(nm, generator=GENERATOR)
        for sd in seeds:
            t = tokf(sd)[0]
            s.ints(RLET + lets, f"[dg (tok {sd})]", [(f"seed {sd}", U11 if unit == "cv" else U08, cmp.digest(t))],
                   gen=True, table=True)
        s.write()
        sys.exit(0)
    n11 = int(args[0]) if args else 2400
    n08 = int(args[1]) if len(args) > 1 else 2600
    b11 = int(args[2]) if len(args) > 2 else 100
    b08 = int(args[3]) if len(args) > 3 else 100
    print("slices: step 11 train.py", A11, B11, "; step 08 train.py", A08, B08)
    build("fz10c_cv", U11, RLET + L11, tok11, list(range(7_100_000, 7_100_000 + n11)), b11, stats11)
    build("fz10c_ct", U08, RLET + L08, tok08, list(range(7_200_000, 7_200_000 + n08)), b08, stats08)
