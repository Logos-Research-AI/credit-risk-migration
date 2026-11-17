"""Fuzz of 2026-11-17 (prompts/fuzz-2026-11-16.md), by port-translator-3, who wrote neither unit:
def:classification_table (sas_compat.py:1236-1341, precondition as the filter) and
def:train_run_08_ctable (train.py:418-455). Blueprint 5365851c-..., carrier def:zz_carrier_c.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_ctable_gen.py
      -> diffeval/work/fz_ctable.json, fz_ctable.inputs.json, fz_ctable.fuzz.json
  eval_decl each input on def:zz_carrier_c; python3 diffeval/fuzz_collect.py 3 fz_ctable; compare.py; receipt

Inputs are built inside Lean (kit.GEN's hsh) and mirrored here. One case = one call, one digest of
the whole returned frame (step 08: of the file name and the whole table).

Blocks
  IE  intercept only, enumerated: x = n rows [1.0], every n = 2..60 with every number of events
      0..n (1888 cases); the arrangement of the events, the call shape (pd keyword / inventory order
      (X, y, pd) / fit / fit and pd) and the constant pd come from a hash of (n, events).
  IR  intercept only, seeded: n from a pool (1, 2, .., 60; n - 1 dividing 50 or 100 often, so that
      the leave-one-out means are printed levels); 60 %: one event becomes 1 + d and one non-event
      -d (d = +-2^-33, 2^-40, 2^-31, 2^-20: the sum stays an exact integer and every probability
      moves by d / (n - 1), inside or outside the 1e-9 of the range rule); 20 %: one y replaced by
      2, -1, 0.5, NaN, 1, 0.
  V   fit with a variable, seeded: x = [1, t_i], fit.beta = [0, 1] (so x @ beta = t exactly), call
      shape (y, x, fit). t_i is drawn from the 37 floats eta with _expit(eta) equal, bit for bit, to
      a printed level k * 0.02 (experiments/fz_ctable_pool.py; -800 gives 0.0 and 40 gives 1.0), or
      the float just below or above one (20 % each). np.linalg.inv is replaced, on both sides, by
      a routine that returns [[a, 0], [0, 0]], a from (0, 0, 0, 0.25, 1, -0.5, 4, 0): then
      q = einsum(x, v, x) = a exactly (asserted against numpy's einsum) and, for a = 0, the
      leave-one-out probability is _expit(t_i) itself: a probability EQUAL to a printed level, lower
      levels included. y is 0 / 1 by hash, one value in 40 is 2.
  S8  step 08, seeded: the source lines train.py:418-455 executed as they stand. fit_mask with up to
      3 rows outside the fit frame, pd_logistic null or not there; final model the intercept alone
      or one variable (then np.linalg.inv as in V, and pd from a pool of 16 probabilities with
      np.log1p as a table); 5 %: a null pd_logistic on a complete case; 10 %: a y equal to 2.
Library routines. Intercept only: the five routines of the Lean are doubles that return nothing
(the result may not depend on them); Python runs numpy as it is. With a variable: `inv` as said,
`matvec` a plain dot product (exact here), `einsum_q` returns v[0][0] for every row, `matmul`
unused by that `inv`, `log1p` a table (S8) or unused (V: no pd). So the fuzz does not test what
the unit hands to inv / matmul / einsum_q (the evaluation and the review did, with keyed doubles);
it tests everything after them. exp and log are the real ones on both sides; the generator adds
check cases (primitive "pool check") that Lean's _expit and log give numpy's bits on the pools.

Precondition (def:classification_table_precond) rendered in Python, clause by clause:
  (1), (2), (4), (5)  true by construction (shapes, a fit or a pd, beta of the right length;
                      1.0 + exp(-e) is never 0.0 on floats)
  (3)   pd has the length of y (S8 with a null pd on a complete case: false); with a variable
        0 < pd_i < 1 (S8 pool: true)
  (6)   with a variable: every 1.0 - h_i != 0.0, h = p * (1 - p) * a
  (6')  intercept only: n - 1.0 != 0.0
  (7)   ps not empty, no NaN; 0 <= klo, khi <= 50, klo <= khi with ps, klo, khi computed as the Lean
        text does (same float operations as sc:1289-1295)
  (8)   n1 = y.sum() finite and floor(n1) == n1
  (9)   true (at most 60 rows)
def:train_run_08_ctable_precond: 0 <= n_obs, the fit's columns Float64 of n_obs values without
null, pd_logistic Float64 of the length of the mask (all true by construction), every complete case
has a pd_logistic (false on the 5 % edge), and the precondition above on (y_train, x_final, pd_train).
A seed on which Python raises is not sent to Lean (the Lean body skips the listed seeds); if the
precondition admitted it, it is recorded in python_raises_inside_precondition.
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
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "experiments"))

import fz_ctable_pool as pool  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

WORK = HERE.parent / "work"
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
ITEM, DECL = "def:zz_carrier_c", "zz_carrier_c"
U_CT, U_S8, U_CHK = "classification_table", "train_run_08_ctable", "pool check"
nan = float("nan")
SENT = struct.unpack("<Q", struct.pack("<d", -7.25))[0]

IR0, IRN = 20000, 500
V0, VN = 30000, 1800
S0, SN = 40000, 2400
PER = 600  # seeds per eval input


def raw(x) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def unraw(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def lf(x) -> str:
    return f"(Float.ofBits {raw(x)})"


def h(s: int, k: int) -> int:
    return kit.hsh(s, k)


def w(t) -> int:
    hh = 14695981039346656037
    for x in t:
        hh = (hh * 1099511628211 + x + 7) % 18446744073709551616
    return hh


def ts(s: str):
    return [len(s)] + [ord(c) for c in s]


def o(v):
    if v is None:
        return [0]
    b = raw(v)
    return [1, kit.NAN_BITS if v != v else b]


def frame_tok(df: pl.DataFrame):
    out = [df.width]
    for name in df.columns:
        c = df.get_column(name)
        out += ts(name)
        if c.dtype == pl.Float64:
            out += [1, len(c)] + [t for v in c.to_list() for t in o(v)]
        elif c.dtype == pl.Int64:
            out += [2, len(c)] + [t for v in c.to_list() for t in ([0] if v is None else [1, v])]
        else:
            out += [99]
    return out


# ------------------------------------------------------------------ pools
PD4 = [0.3, 0.999, 1e-300, 0.5]
NP = [1, 2, 3, 5, 6, 11, 21, 26, 41, 51, 60, 4]
DP = [2.0 ** -33, 2.0 ** -40, 2.0 ** -31, 2.0 ** -20]
EY = [2.0, -1.0, 0.5, nan, 1.0, 0.0]
HITS = {k: (1e-300 if v == 0.0 else v) for k, v in pool.hits().items()}  # 0.5: _expit(1e-300) = 0.5 too, and its neighbours are floats
assert all(v is None or float(sc._expit(np.array([v]))[0]) == float(np.round(k * 0.02, 3)) for k, v in HITS.items())
EP = [raw(v) for k, v in sorted(HITS.items()) if v is not None]
EPK = [k for k, v in sorted(HITS.items()) if v is not None]
AP = [0.0, 0.0, 0.0, 0.25, 1.0, -0.5, 4.0, 0.0]
NV2 = [2, 3, 4, 5, 8, 13, 24, 40, 60, 7]
N8 = [2, 3, 4, 5, 6, 9, 11, 17, 26, 33, 51, 40]
PP = [0.5, 0.25, 0.75, 0.02, 0.98, 0.3, 0.7, 0.1, 0.9, 0.04, 0.4, 0.6, 0.999, 0.001, 0.5000000001, 0.62]
LEVELS = [float(z) for z in np.round(np.arange(0, 51) * 0.02, 3)]

# ------------------------------------------------------------------ Lean text
BASE = (
    "let W := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
    "let o := fun (v : Option Float) => (match v with | none => [0] | some x => [1, (x.toBits.toNat : Int)] : List Int); "
    "let ts := fun (s : String) => (s.length : Int) :: s.toList.map (fun (c : Char) => (c.toNat : Int)); "
    "let h := fun (s k : Nat) => (hsh s k).toNat; "
    "let NM := fun (_ _ : List (List Float)) => ([] : List (List Float)); "
    f"let NL := fun (_ : Float) => Float.ofBits {SENT}; "
    "let YB := fun (n k v : Nat) => (List.range n).map (fun (i : Nat) => if v % 2 == 0 then (if (i + v / 2) % n < k then (1.0 : Float) else 0.0) "
    "else Float.ofNat (((i + 1) * k) / n - (i * k) / n)); "
)
FT = (
    "let tc := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: (v.length : Int) :: v.flatMap o "
    "| .int v => 2 :: (v.length : Int) :: v.flatMap (fun (x : Option Int) => (match x with | none => [0] | some n => [1, n] : List Int)) | _ => [99] : List Int); "
    "let ft := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
)
ICPT = (
    "let NI := fun (_ : List (List Float)) => ([] : List (List Float)); "
    "let NV := fun (_ : List (List Float)) (_ : List Float) => ([] : List Float); "
    "let NE := fun (_ _ : List (List Float)) => ([] : List Float); "
    f"let PD : List Float := [{', '.join(lf(v) for v in PD4)}]; "
    "let CI := fun (y : List Float) (v : Nat) => let n := y.length; let ya : FloatArray_ Float := Np.NDArray.d1 y; "
    "let x : FloatArray_ Float := Np.NDArray.d2 (List.replicate n [1.0]); "
    "let p : FloatArray_ Float := Np.NDArray.d1 (List.replicate n (PD.getD (v / 4 % 4) 0.5)); "
    'let f : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 [0.25], cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true }; '
    "W (ft (match v % 4 with | 0 => classification_table (α := Float) NI NM NV NE NL ya x none (some p) "
    "| 1 => classification_table (α := Float) NI NM NV NE NL x ya (some (Sum.inr p)) none "
    "| 2 => classification_table (α := Float) NI NM NV NE NL ya x (some (Sum.inl f)) none "
    "| _ => classification_table (α := Float) NI NM NV NE NL ya x (some (Sum.inl f)) (some p))); "
)
IRL = (
    f"let NP : List Nat := {NP}; let DP : List Float := [{', '.join(lf(v) for v in DP)}]; "
    "let EY : List Float := [2.0, (-1.0), 0.5, (0.0 / 0.0), 1.0, 0.0]; "
    "let RI := fun (s : Nat) => let n := NP.getD (h s 1 % 12) 2; let k := h s 2 % (n + 1); let y0 := YB n k (h s 3); let m := h s 4 % 10; "
    "let y := if m < 6 then (let d := DP.getD (h s 5 % 4) 0.0; let dd := if h s 7 % 2 == 0 then d else (0.0 - d); "
    "(match (List.range n).find? (fun (i : Nat) => y0.getD i 0.0 == 1.0), (List.range n).find? (fun (i : Nat) => y0.getD i 1.0 == 0.0) with "
    "| some i1, some i0 => (List.range n).map (fun (i : Nat) => if i == i1 then 1.0 + dd else if i == i0 then 0.0 - dd else y0.getD i 0.0) "
    "| _, _ => y0)) "
    "else if m < 8 then (let j := h s 5 % n; let e := EY.getD (h s 6 % 6) 0.0; (List.range n).map (fun (i : Nat) => if i == j then e else y0.getD i 0.0)) "
    "else y0; CI y (h s 8); "
)
VARL = (
    "let dotf := fun (u v : List Float) => (List.zip u v).foldl (fun (s : Float) (p : Float × Float) => s + p.1 * p.2) 0.0; "
    "let MV := fun (m : List (List Float)) (v : List Float) => m.map (fun (r : List Float) => dotf r v); "
    "let EQ := fun (x v : List (List Float)) => x.map (fun (_ : List Float) => (v.headD []).headD 0.0); "
    f"let AP : List Float := [{', '.join(lf(v) for v in AP)}]; "
)
VL = (
    f"let EP : List UInt64 := {EP}; let NV2 : List Nat := {NV2}; "
    "let RV := fun (s : Nat) => let n := NV2.getD (h s 1 % 10) 2; let a := AP.getD (h s 2 % 8) 0.0; "
    "let t := (List.range n).map (fun (i : Nat) => let u := h s (10 + i); let b := EP.getD (u % EP.length) 0; "
    "Float.ofBits (match (u / 1000) % 10 with | 0 | 1 => b + 1 | 2 | 3 => b - 1 | _ => b)); "
    "let y := (List.range n).map (fun (i : Nat) => let u := h s (200 + i); if u % 40 == 0 then (2.0 : Float) else Float.ofNat (u % 2)); "
    'let f : LogisticFit Float := { names := ["Intercept", "v"], beta := Np.NDArray.d1 [0.0, 1.0], cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true }; '
    "W (ft (classification_table (α := Float) (fun (_ : List (List Float)) => [[a, 0.0], [0.0, 0.0]]) NM MV EQ NL (Np.NDArray.d1 y) "
    "(Np.NDArray.d2 (t.map (fun (e : Float) => [1.0, e]))) (some (Sum.inl f)) none)); "
)
S8L = (
    f"let N8 : List Nat := {N8}; let PP : List UInt64 := {[raw(p) for p in PP]}; "
    f"let L1T : List (UInt64 × UInt64) := [{', '.join(f'({raw(-p)}, {raw(float(np.log1p(-p)))})' for p in PP)}]; "
    f"let L1 := fun (x : Float) => (match L1T.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with | some t => Float.ofBits t.2 | none => Float.ofBits {SENT} : Float); "
    'let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
    'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
    "let tt := fun (t : Tabular.Table Float) => (t.length : Int) :: t.flatMap (fun (r : Tabular.Row Float) => r.flatMap (fun (p : String × Tabular.Cell Float) => "
    "ts p.1 ++ (match p.2 with | .str (some s) => ts s | _ => [-1] : List Int))); "
    "let R8 := fun (s : Nat) => let n := N8.getD (h s 1 % 12) 2; let k := h s 2 % (n + 1); let y0 := YB n k (h s 3); "
    "let y := if h s 9 % 10 == 0 then (let j := h s 10 % n; (List.range n).map (fun (i : Nat) => if i == j then (2.0 : Float) else y0.getD i 0.0)) else y0; "
    "let var := h s 4 % 2 == 1; let ex := h s 5 % 4; let m := n + ex; let rot := h s 6; let a := AP.getD (h s 7 % 8) 0.0; "
    "let mask := (List.range m).map (fun (i : Nat) => !(decide ((i + rot) % m < ex))); "
    "let ft1 := if h s 8 % 20 == 0 then (List.range m).find? (fun (i : Nat) => mask.getD i false) else none; "
    "let pda : List (Option Float) := (List.range m).map (fun (i : Nat) => let u := h s (300 + i); "
    "if mask.getD i false then (if ft1 == some i then none else some (Float.ofBits (PP.getD (u % 16) 0))) "
    "else (if u % 2 == 0 then none else some (Float.ofBits (PP.getD (u / 2 % 16) 0)))); "
    "let vc : List (Option Float) := (List.range n).map (fun (i : Nat) => some (Float.ofNat (h s (500 + i) % 7) - 3.0)); "
    'let ff : Pl.Frame Float := [("v", Pl.Col.f64 vc), ("default_flag", Pl.Col.f64 (y.map some))]; '
    'let fin : LogisticFit Float := { names := if var then ["Intercept", "v"] else ["Intercept"], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true }; '
    "let r := train_run_08_ctable (α := Float) fw (fun (_ : List (List Float)) => [[a, 0.0], [0.0, 0.0]]) NM MV EQ L1 mask ff fin (n : Int) y "
    '[("pd_logistic", Pl.Col.f64 pda)]; W (ts r.1 ++ tt r.2); '
)


# ------------------------------------------------------------------ Python mirrors
def yb(n: int, k: int, v: int) -> list[float]:
    if v % 2 == 0:
        return [1.0 if (i + v // 2) % n < k else 0.0 for i in range(n)]
    return [float(((i + 1) * k) // n - (i * k) // n) for i in range(n)]


class _NP:
    """numpy with np.linalg.inv replaced (the Lean's explicit parameter `inv`)."""

    def __init__(self, a: float):
        self.linalg = types.SimpleNamespace(inv=lambda m: np.array([[a, 0.0], [0.0, 0.0]]))

    def __getattr__(self, k):
        return getattr(np, k)


def with_inv(a: float | None, fn):
    """Run fn with sas_compat's numpy replaced when a is given; (result, None) or (None, exception)."""
    old = sc.np
    try:
        if a is not None:
            sc.np = _NP(a)
        with np.errstate(all="ignore"):
            return fn(), None
    except Exception as ex:  # noqa: BLE001  any exception of the port is "Python raises"
        return None, ex
    finally:
        sc.np = old


def core_precond(y: np.ndarray, ps: np.ndarray, icpt: bool) -> bool:
    """Clauses (6'), (7), (8) with the Lean's own operations."""
    n = len(y)
    if icpt and n - 1.0 == 0.0:
        return False
    if len(ps) == 0 or any(t != t for t in ps):
        return False
    tol = 1e-9 if icpt else 0.0
    psmin = psmax = float(ps[0])
    for t in ps:
        t = float(t)
        if t < psmin:
            psmin = t
        if psmax < t:
            psmax = t
    a, b = psmin / 0.02 + tol, -(psmax / 0.02 - tol)
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    klo, khi = float(math.floor(a)), -float(math.floor(b))
    if not (0.0 <= klo and khi <= 50.0 and klo <= khi):
        return False
    n1 = float(np.sum(y))
    return math.isfinite(n1) and float(math.floor(n1)) == n1


COV = {"I": {}, "V": {}, "S8": {}}


def cover(tag: str, ps, icpt: bool, kept: bool):
    """Which edges a kept case reaches (for the report; not used for expected values)."""
    if not kept:
        return
    c = COV[tag]

    def add(k):
        c[k] = c.get(k, 0) + 1

    tol = 1e-9 if icpt else 0.0
    klo = math.floor(float(min(ps)) / 0.02 + tol)
    khi = math.ceil(float(max(ps)) / 0.02 - tol)
    grid = LEVELS[klo:khi + 1]
    add("cases")
    if khi == 50:
        add("khi = 50")
    if any(float(t) == 1.0 for t in ps):
        add("a probability equal to 1.0")
    low = [float(t) for t in ps if float(t) in grid and float(t) < 1.0]
    if low:
        add("a probability equal to a printed level below 1.000")
    if any(0.0 < float(t) for t in low):
        add("a probability equal to a printed level strictly between 0 and 1")
    if any(float(t) not in LEVELS and min(abs(float(t) - g) for g in LEVELS) < 1e-9 for t in ps):
        add("a probability within 1e-9 of a printed level, not equal")
    for t in ps:
        if float(t) in LEVELS:
            c.setdefault("levels hit", set()).add(LEVELS.index(float(t)))


def ci_py(y: list[float], v: int):
    """Intercept-only call, real numpy. Returns (digest or None, exception, precondition, ps)."""
    n = len(y)
    ya = np.array(y, dtype=np.float64)
    x = np.ones((n, 1))
    pd = np.full(n, PD4[(v // 4) % 4])
    fit = sc.LogisticFit(["Intercept"], np.array([0.25]), np.eye(1), -1.0, 1, True)
    sh = v % 4
    call = [lambda: sc.classification_table(ya, x, pd=pd), lambda: sc.classification_table(x, ya, pd),
            lambda: sc.classification_table(ya, x, fit), lambda: sc.classification_table(ya, x, fit, pd=pd)][sh]
    res, ex = with_inv(None, call)
    with np.errstate(all="ignore"):
        ps = (float(ya.sum()) - ya) / (n - 1.0) if n else ya
    pre = core_precond(ya, ps, True)
    return res, ex, pre, ps


def digest_frame(res: pl.DataFrame) -> int:
    res = res.with_columns(pl.col("CorrectNonevents").cast(pl.Float64), pl.col("IncorrectNonevents").cast(pl.Float64))  # R-F2I
    return w(frame_tok(res))


def ri_y(s: int) -> list[float]:
    n = NP[h(s, 1) % 12]
    k = h(s, 2) % (n + 1)
    y = yb(n, k, h(s, 3))
    m = h(s, 4) % 10
    if m < 6:
        d = DP[h(s, 5) % 4]
        dd = d if h(s, 7) % 2 == 0 else 0.0 - d
        i1 = next((i for i in range(n) if y[i] == 1.0), None)
        i0 = next((i for i in range(n) if y[i] == 0.0), None)
        if i1 is not None and i0 is not None:
            y = [1.0 + dd if i == i1 else 0.0 - dd if i == i0 else y[i] for i in range(n)]
    elif m < 8:
        j = h(s, 5) % n
        e = EY[h(s, 6) % 6]
        y = [e if i == j else y[i] for i in range(n)]
    return y


def rv_py(s: int):
    n = NV2[h(s, 1) % 10]
    a = AP[h(s, 2) % 8]
    t = []
    for i in range(n):
        u = h(s, 10 + i)
        b = EP[u % len(EP)]
        sel = (u // 1000) % 10
        t.append(unraw(b + 1 if sel in (0, 1) else b - 1 if sel in (2, 3) else b))
    y = []
    for i in range(n):
        u = h(s, 200 + i)
        y.append(2.0 if u % 40 == 0 else float(u % 2))
    ya, ta = np.array(y), np.array(t)
    x = np.column_stack([np.ones(n), ta])
    beta = np.array([0.0, 1.0])
    fit = sc.LogisticFit(["Intercept", "v"], beta, np.eye(2), -1.0, 1, True)
    assert [raw(v) for v in x @ beta] == [raw(v) for v in t], "x @ beta is not t"
    q = np.einsum("ij,jk,ik->i", x, np.array([[a, 0.0], [0.0, 0.0]]), x)
    assert all(raw(v) == raw(a) for v in q), "einsum is not a"
    res, ex = with_inv(a, lambda: sc.classification_table(ya, x, fit))
    with np.errstate(all="ignore"):
        p = sc._expit(ta)
        hh = p * (1.0 - p) * a
        ps = sc._expit(ta - (ya - p) * q / (1.0 - hh))
    pre = bool(np.all((1.0 - hh) != 0.0)) and core_precond(ya, ps, False)
    return res, ex, pre, ps


def step08_slice() -> str:
    src = Path(train.__file__).read_text().splitlines()
    first = next(i for i, ln in enumerate(src) if ln.strip() == "x_final = np.column_stack(")
    last = next(i for i, ln in enumerate(src) if 'output_dir / "printed_classification.csv"' in ln)
    assert (first + 1, last + 1) == (418, 455), (first + 1, last + 1)
    return textwrap.dedent("\n".join(src[first:last + 1]))


SLICE = step08_slice()


def enc(v, wd, d) -> str:
    if v is None:
        return f"wN/{wd}/{d}"
    v = float(v)
    return f"w{kit.NAN_BITS if v != v else raw(v)}/{wd}/{d}"


def r8_py(s: int):
    n = N8[h(s, 1) % 12]
    k = h(s, 2) % (n + 1)
    y = yb(n, k, h(s, 3))
    if h(s, 9) % 10 == 0:
        j = h(s, 10) % n
        y = [2.0 if i == j else y[i] for i in range(n)]
    var = h(s, 4) % 2 == 1
    ex_ = h(s, 5) % 4
    m = n + ex_
    rot = h(s, 6)
    a = AP[h(s, 7) % 8]
    mask = [not ((i + rot) % m < ex_) for i in range(m)]
    ft1 = next((i for i in range(m) if mask[i]), None) if h(s, 8) % 20 == 0 else None
    pda: list[float | None] = []
    for i in range(m):
        u = h(s, 300 + i)
        if mask[i]:
            pda.append(None if ft1 == i else PP[u % 16])
        else:
            pda.append(None if u % 2 == 0 else PP[(u // 2) % 16])
    vc = [float(h(s, 500 + i) % 7) - 3.0 for i in range(n)]
    ya = np.array(y, dtype=np.float64)
    fit_frame = pl.DataFrame({"v": pl.Series(vc, dtype=pl.Float64), "default_flag": pl.Series(y, dtype=pl.Float64)})
    scored = pl.DataFrame({"pd_logistic": pl.Series(pda, dtype=pl.Float64)})
    writes: list[tuple[str, pl.DataFrame]] = []
    proxy = types.SimpleNamespace(classification_table=sc.classification_table, fmt_wd=enc,
                                  write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ns = {"np": np, "pl": pl, "sas_compat": proxy, "fit_frame": fit_frame, "n_obs": n, "y_train": ya,
          "final": types.SimpleNamespace(names=["Intercept", "v"] if var else ["Intercept"]),
          "logit_scored_train": scored, "fit_mask": np.array(mask, dtype=bool), "output_dir": Path("out")}
    _, ex = with_inv(a if var else None, lambda: exec(compile(SLICE, "train.py:418-455", "exec"), ns))  # noqa: S102
    # precondition
    pdt = [pda[i] for i in range(m) if mask[i]]
    ok = all(v is not None for v in pdt)
    ps = None
    if ok:
        pt = np.array(pdt, dtype=np.float64)
        with np.errstate(all="ignore"):
            if var:
                eta = np.log(pt) - np.log1p(-pt)
                hh = pt * (1.0 - pt) * a
                ps = sc._expit(eta - (ya - pt) * a / (1.0 - hh))
                ok = bool(np.all((pt > 0.0) & (pt < 1.0))) and bool(np.all((1.0 - hh) != 0.0)) and core_precond(ya, ps, False)
            else:
                ps = (float(ya.sum()) - ya) / (n - 1.0)
                ok = core_precond(ya, ps, True)
    dg = None
    if ex is None:
        (name, df), = writes
        toks = ts(name) + [df.height]
        for r in df.rows():
            for c, v in zip(df.columns, r, strict=True):
                toks += ts(c) + ts(v)
        dg = w(toks)
    return dg, ex, ok, ps, var


# ------------------------------------------------------------------ the suite
def main() -> None:
    su = Suite("fz_ctable")
    su.item, su.decl = ITEM, DECL
    stats = {U_CT: {"generated": 0, "kept": 0, "raises_in": [], "dropped": 0, "rejected_returns": 0},
             U_S8: {"generated": 0, "kept": 0, "raises_in": [], "dropped": 0, "rejected_returns": 0}}

    def account(unit, tag, cid, dg, ex, pre, ps, icpt, cases, skip, seed):
        st = stats[unit]
        st["generated"] += 1
        if ex is not None:
            skip.append(seed)
            if pre:
                st["raises_in"].append(seed)
            else:
                st["dropped"] += 1
            return
        if pre:
            st["kept"] += 1
            cover(tag, ps, icpt, True)
        else:
            st["rejected_returns"] += 1
        cases.append((cid, unit, dg, {"fz": "kept" if pre else "rejected"}))

    # ---- IE: enumerated intercept-only
    for n0, n1 in ((2, 35), (36, 49), (50, 60)):
        cases: list = []
        for n in range(n0, n1 + 1):
            for k in range(n + 1):
                key = n * 100 + k
                res, ex, pre, ps = ci_py(yb(n, k, h(key, 7)), h(key, 8))
                assert ex is None and pre, (n, k, ex)
                stats[U_CT]["generated"] += 1
                stats[U_CT]["kept"] += 1
                cover("I", ps, True, True)
                cases.append((f"IE n={n} events={k}", U_CT, digest_frame(res), {"fz": "kept"}))
        body = (f"((List.range' {n0} {n1 - n0 + 1}).flatMap (fun (n : Nat) => (List.range (n + 1)).map "
                "(fun (k : Nat) => CI (YB n k (h (n * 100 + k) 7)) (h (n * 100 + k) 8))))")
        su.ints(BASE + FT + ICPT, body, cases, gen=True, use_kit=False)

    # ---- IR: seeded intercept-only
    cases, skip = [], []
    for s in range(IR0, IR0 + IRN):
        y = ri_y(s)
        res, ex, pre, ps = ci_py(y, h(s, 8))
        account(U_CT, "I", f"IR seed {s}", None if ex else digest_frame(res), ex, pre, ps, True, cases, skip, s)
    body = f"(((List.range' {IR0} {IRN}).filter (fun (s : Nat) => !({skip}.contains s))).map RI)"
    su.ints(BASE + FT + ICPT + IRL, body, cases, gen=True, use_kit=False)

    # ---- pool checks: Lean's exp (through _expit) and log on the pools give numpy's bits
    ep3 = [b + d for b in EP for d in (-1, 0, 1)]
    exp_bits = [raw(v) for v in sc._expit(np.array([unraw(b) for b in ep3]))]
    log_bits = [raw(v) for v in np.log(np.array(PP))]
    cases = [(f"_expit on pool eta {i}", U_CHK, b, {"fz": "kept"}) for i, b in enumerate(exp_bits)]
    cases += [(f"log on pool pd {PP[i]!r}", U_CHK, b, {"fz": "kept"}) for i, b in enumerate(log_bits)]
    body = (f"((match _expit (α := Float) (Np.NDArray.d1 (({EP} : List UInt64).flatMap (fun (b : UInt64) => [Float.ofBits (b - 1), Float.ofBits b, Float.ofBits (b + 1)]))) with "
            "| .d1 v => v.map (fun (x : Float) => (x.toBits.toNat : Int)) | .d2 _ => []) ++ "
            f"({[raw(p) for p in PP]} : List UInt64).map (fun (b : UInt64) => ((Tabular.RealLike.log (Float.ofBits b)).toBits.toNat : Int)))")
    su.ints("", body, cases, gen=False, use_kit=False)

    # ---- V: seeded, fit with a variable
    for a0 in range(V0, V0 + VN, PER):
        cases, skip = [], []
        for s in range(a0, a0 + PER):
            res, ex, pre, ps = rv_py(s)
            account(U_CT, "V", f"V seed {s}", None if ex else digest_frame(res), ex, pre, ps, False, cases, skip, s)
        body = f"(((List.range' {a0} {PER}).filter (fun (s : Nat) => !({skip}.contains s))).map RV)"
        su.ints(BASE + FT + VARL + VL, body, cases, gen=True, use_kit=False)

    # ---- S8: seeded, step 08
    for a0 in range(S0, S0 + SN, PER):
        cases, skip = [], []
        for s in range(a0, a0 + PER):
            dg, ex, pre, ps, var = r8_py(s)
            account(U_S8, "S8", f"S8 seed {s}", dg, ex, pre, ps, not var, cases, skip, s)
            if pre and ex is None:
                COV["S8"]["with a variable" if var else "intercept only"] = COV["S8"].get("with a variable" if var else "intercept only", 0) + 1
        body = f"(((List.range' {a0} {PER}).filter (fun (s : Nat) => !({skip}.contains s))).map R8)"
        su.ints(BASE + VARL + S8L, body, cases, gen=True, use_kit=False)

    su.write()
    for tag in COV:
        if "levels hit" in COV[tag]:
            COV[tag]["levels hit"] = sorted(COV[tag]["levels hit"])
    note_ct = (f"IE: n = 2..60 x events 0..n enumerated (1888); IR seeds {IR0}..{IR0 + IRN - 1}; V seeds {V0}..{V0 + VN - 1}; "
               f"rejected inputs on which Python returns: {stats[U_CT]['rejected_returns']}; rejected and Python raises (dropped): {stats[U_CT]['dropped']}; "
               f"reached by kept cases: intercept only {COV['I']}; with a variable {COV['V']}; "
               f"levels with an eta whose _expit is the level exactly: {EPK}; "
               "library routines: see the generator's docstring (inv replaced on both sides with a variable)")
    note_s8 = (f"seeds {S0}..{S0 + SN - 1}; rejected inputs on which Python returns: {stats[U_S8]['rejected_returns']}; "
               f"rejected and Python raises (dropped): {stats[U_S8]['dropped']}; reached by kept cases: {COV['S8']}; "
               "expected = train.py:418-455 executed as it stands; with a variable np.linalg.inv is replaced on both sides, log1p is a table")
    fz = {"fuzzer": "port-translator-3", "generator": "port-to-lean/diffeval/units/fz_ctable_gen.py", "blueprint": BLUEPRINT,
          "units": {
              U_CT: {"seeds": f"enumerated n=2..60; {IR0}..{IR0 + IRN - 1}; {V0}..{V0 + VN - 1}", "generated": stats[U_CT]["generated"],
                     "kept": stats[U_CT]["kept"], "python_raises_inside_precondition": stats[U_CT]["raises_in"], "note": note_ct},
              U_S8: {"seeds": f"{S0}..{S0 + SN - 1}", "generated": stats[U_S8]["generated"], "kept": stats[U_S8]["kept"],
                     "python_raises_inside_precondition": stats[U_S8]["raises_in"], "note": note_s8}}}
    (WORK / "fz_ctable.fuzz.json").write_text(json.dumps(fz, indent=1))
    for u, st in stats.items():
        print(u, {k: (v if not isinstance(v, list) else v[:10]) for k, v in st.items()})
    for tag, c in COV.items():
        print(tag, c)
    print("input sizes:", [len(i["text"]) for i in su.inputs])


if __name__ == "__main__":
    main()
