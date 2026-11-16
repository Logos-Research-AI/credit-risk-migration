"""Review of T1 (port-translator-2) by port-translator-3: edge inputs for def:_groups, def:_pairs,
def:roc_association, run on the port and typed as Lean terms (carrier def:zz_carrier_s).
fsum in Lean is a left fold; a case is kept only when Python gives the same result with math.fsum
replaced by a left fold (so the comparison does not depend on the fsum parameter)."""
import sys, math, json
from pathlib import Path
import numpy as np
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "diffeval"))
import leanterm as lt, compare as cmp
from credit_risk import sas_compat as sc

nan, inf = float("nan"), float("inf")
T = sc._TIE_EPS
CASES = [
    ("tie_area_not_se", [1.0, 0.0], [0.5, 0.5 + 5e-9]),
    ("three", [1.0, 0.0, 0.0], [0.9, 0.1, 0.2]),
    ("nan_score", [1.0, 0.0, 1.0, 0.0], [nan, 0.2, 0.7, 0.4]),
    ("nan_score_last", [1.0, 0.0, 1.0, 0.0], [0.3, 0.2, 0.7, nan]),
    ("odd_y", [1.0, 0.0, 2.0, nan, None, 1.0, 0.0], [0.3, 0.6, 0.1, 0.2, 0.5, None, 0.25]),
    ("single_class", [1.0, 1.0], [0.1, 0.2]),
    ("single_class0", [0.0, 0.0, 0.0], [0.1, 0.2, 0.2]),
    ("empty", [], []),
    ("one_row", [1.0], [0.5]),
    ("inf_scores", [1.0, 0.0, 1.0, 0.0], [inf, inf, 1.0, -inf]),
    ("chain", [1.0, 0.0, 1.0, 0.0], [0.5, 0.5 + 0.9e-8, 0.5 + 1.8e-8, 0.5 + 2.7e-8]),
    ("exact_eps", [1.0, 0.0, 0.0], [0.5, 0.5 + T, math.nextafter(0.5 + T, 1.0)]),
    ("se_eps_edge", [1.0, 0.0, 0.0, 1.0], [0.5, 0.5 + 1000 * 2.0**-53, 0.5 + 1001 * 2.0**-53, 0.25]),
    ("neg_zero", [1.0, 0.0, -0.0, 1.0], [0.0, -0.0, 0.5, 0.5]),
    ("all_tied", [1.0, 0.0, 1.0, 0.0], [0.3, 0.3, 0.3, 0.3]),
    ("reverse", [0.0, 0.0, 1.0, 1.0], [0.9, 0.8, 0.2, 0.1]),
    ("above_one", [1.0, 0.0, 1.0, 0.0, 1.0], [1.5, -2.0, 0.75, 0.75, 0.125]),
]
DT = [("bool_int", pl.Series([True, False, True, None]), pl.Series([3, 1, 2, 5])),
      ("null_dtype", pl.Series([None, None], dtype=pl.Null), pl.Series([0.1, 0.2]))]

def ob(v): return -1 if v is None else cmp.fbits(v)

def py(y, s):
    q = sc._pairs(y, s)
    r = sc.roc_association(y, s)
    real = [r.area, r.std_err, r.lower, r.upper, r.somers_d, r.gamma, r.tau_a]
    o = math.fsum
    try:
        math.fsum = lambda xs: sum(xs, 0.0)
        r2 = sc.roc_association(y, s)
    finally:
        math.fsum = o
    fold = [r2.area, r2.std_err, r2.lower, r2.upper, r2.somers_d, r2.gamma, r2.tau_a]
    fr = sc.roc_association(y, s, "L")
    assert fr.row(0)[0] == "L" and [ob(v) for v in fr.row(0)[1:]] == [ob(v) for v in real] and fr.columns[0] == "ROCModel"
    exp = [q.conc, q.disc, q.tied, q.n1, q.n0, len(q.v10)] + [ob(float(v)) for v in q.v10] + [len(q.v01)] + [ob(float(v)) for v in q.v01] + [ob(v) for v in real]
    return exp, [ob(v) for v in real] == [ob(v) for v in fold], real

terms, expected, names = [], [], []
for name, y, s in [(n, pl.Series(y, dtype=pl.Float64), pl.Series(s, dtype=pl.Float64)) for n, y, s in CASES] + DT:
    exp, same, real = py(y, s)
    print(f"{name:18s} fsum==fold:{same}  real={real}")
    if not same:
        continue
    names.append((name, len(exp))); expected.append(exp)
    terms.append(f"one {lt.lean_col(y)} {lt.lean_col(s)}")
# _groups alone, with NaN
G = [("g_nan", [0.5, nan, 0.7, nan, 0.5], 0.1), ("g_inf", [inf, 1.0, inf, -inf, -inf], 0.5), ("g_empty", [], 0.5),
     ("g_eps_nan", [0.5, 0.6, 0.7], nan), ("g_neg_eps", [0.5, 0.5, 0.4], -1.0)]
gterms = []
for name, ss, eps in G:
    g = sc._groups(np.asarray(ss, dtype=np.float64), eps).tolist()
    print(name, g)
    names.append((name, len(g))); expected.append(g)
    gterms.append(f"_groups (α := Float) (Np.NDArray.d1 {lt.lean_floats(ss)}) {lt.lean_float(eps)}")
body = ("(let ob := fun (o : Option Float) => (match o with | none => (-1 : Int) | some x => (x.toBits.toNat : Int)); "
        "let fb := fun (a : FloatArray_ Float) => (match a with | .d1 v => (v.length : Int) :: v.map (fun (x : Float) => (x.toBits.toNat : Int)) | .d2 _ => [-7] : List Int); "
        "let fs := fun (l : List Float) => l.foldl (fun (a x : Float) => a + x) 0.0; "
        "let one := fun (y s : Pl.Col Float) => let q := _pairs y s; [q.conc, q.disc, q.tied, q.n1, q.n0] ++ fb q.v10 ++ fb q.v01 ++ "
        "(match roc_association fs y s none with | .inl r => [ob r.area, ob r.std_err, ob r.lower, ob r.upper, ob r.somers_d, ob r.gamma, ob r.tau_a] | .inr _ => [-9]); "
        + " ++ ".join(terms + gterms) + ")")
json.dump({"names": names, "expected": expected, "input": body}, open(HERE / "rev_t1.json", "w"))
print(len(body)); print(body)
try:
    pl.DataFrame({"y": pl.Series([1.0]), "s": pl.Series([0.1, 0.2])}); print("length-1 with length-2: NO raise")
except Exception as e: print("length-1 with length-2 raises", type(e).__name__)
