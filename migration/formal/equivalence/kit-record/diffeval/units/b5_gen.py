"""Bundle B5 differential tests (chi2_sf, LogisticFit, _expit, _hl_groups, hosmer_lemeshow,
classification_table).

  uv run python migration/diffeval/units/b5_gen.py
      -> work/b5_small, b5_expit, b5_hl, b5_ct (.json + .inputs.json)
  (eval_decl each work/b5_*.inputs.json on def:zz_carrier / zz_carrier, save work/b5_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b5_<suite>.json migration/diffeval/work/b5_<suite>.out.txt
  uv run python migration/diffeval/units/b5_gen.py --tokens b5_hl "<case id>"
      -> prints the eval_decl input that returns the raw token list of one case, and the expected
         token list (to locate a difference)

Every result is tokenised by hand into a List Int and folded into one digest (W) per case, as in
b4_gen.py. Floats travel by their bits. R-F2I: the Python Int64 columns that hold α values in Lean
(EventsObserved, NoneventsObserved; CorrectNonevents, IncorrectNonevents) are cast to Float64 on
the Python side before tokenising (same values, the kind the Lean has); the empty hosmer_lemeshow
table keeps its Python dtypes.

Library routines are passed as lambdas that return what the real routine returned in Python and
check what they are given:
  chi2    table (bits of x, df) -> bits of scipy's value; any other argument gives a sentinel
  pow2    table bits of x -> bits of Python's x ** 2
  log1p   table bits of x -> bits of np.log1p(x)
  matmul, inv, einsum_q, matvec   return numpy's result if the digest of their arguments' bits is
          the digest of the arguments numpy received, else an empty array
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

ROOT = HERE.parents[2]
nan, inf = float("nan"), float("inf")
SENT = struct.unpack("<Q", struct.pack("<d", -7.25))[0]


def fb(x) -> int:
    return cmp.fbits(float(x))


def lf(x) -> str:
    return f"(Float.ofBits {fb(x)})"


def w(t) -> int:
    h = 14695981039346656037
    for x in t:
        h = (h * 1099511628211 + x + 7) % 18446744073709551616
    return h


def o(v):
    return [0] if v is None else [1, fb(v)]


def ts(s):
    return [len(s)] + [ord(c) for c in s]


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


# ---- Lean side
W = "let W := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
BI = "let bi := fun (x : Float) => (x.toBits.toNat : Int); "
OF = "let o := fun (v : Option Float) => (match v with | none => [0] | some x => [1, (x.toBits.toNat : Int)] : List Int); "
TS = "let ts := fun (s : String) => (s.length : Int) :: s.toList.map (fun (c : Char) => (c.toNat : Int)); "
TCOL = ("let tc := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: (v.length : Int) :: v.flatMap o "
        "| .int v => 2 :: (v.length : Int) :: v.flatMap (fun (x : Option Int) => (match x with | none => [0] | some n => [1, n] : List Int)) | _ => [99] : List Int); ")
FT = "let ft := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
FL = "let FL := fun (v : List UInt64) => v.map Float.ofBits; "
FCOL = "let F := fun (v : List (Option UInt64)) => (Pl.Col.f64 (v.map (fun (o : Option UInt64) => o.map Float.ofBits)) : Pl.Col Float); "
TAB1 = (f"let T1 := fun (T : List (UInt64 × UInt64)) (x : Float) => (match T.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with "
        f"| some t => Float.ofBits t.2 | none => Float.ofBits {SENT} : Float); ")
TAB2 = (f"let T2 := fun (T : List (UInt64 × Int × UInt64)) (x : Float) (d : Int) => (match T.find? (fun (t : UInt64 × Int × UInt64) => t.1 == x.toBits && t.2.1 == d) with "
        f"| some t => Float.ofBits t.2.2 | none => Float.ofBits {SENT} : Float); ")


def fl(xs) -> str:
    return "(FL [" + ", ".join(str(fb(x)) for x in xs) + "])"


def fcol(vals) -> str:
    return "(F [" + ", ".join("none" if v is None else f"some {fb(v)}" for v in vals) + "])"


def icol(vals) -> str:
    return "(Pl.Col.int [" + ", ".join("none" if v is None else f"some ({v})" for v in vals) + "] : Pl.Col Float)"


def bcol(vals) -> str:
    return "(Pl.Col.bool [" + ", ".join("none" if v is None else f"some {'true' if v else 'false'}" for v in vals) + "] : Pl.Col Float)"


def ints(xs) -> str:
    return "([" + ", ".join(f"({int(v)})" for v in xs) + "] : List Int)"


class Cases:
    """Cases of one suite. A group is one eval_decl input: (lets, cases, gen) with cases =
    (id, primitive, Lean term : List Int (the tokens), expected tokens); one digest W per case.
    A raw group returns a List Int directly, one integer per case."""

    def __init__(self, name: str):
        self.name, self.groups, self.notes = name, [], {}

    def group(self, lets: str, cases: list, gen: bool = False):
        self.groups.append(("W", lets, cases, gen))

    def raw(self, lets: str, body: str, cases: list, gen: bool = False):
        """cases = (id, primitive, expected int), in the order of the list `body`."""
        self.groups.append(("raw", lets, (body, cases), gen))

    def suite(self) -> Suite:
        st = Suite(self.name)
        for kind, lets, cases, gen in self.groups:
            if kind == "raw":
                st.ints(lets, cases[0], cases[1], gen=gen, use_kit=False)
            else:
                st.ints(W + lets, "[" + ", ".join(f"W ({c[2]})" for c in cases) + "]",
                        [(c[0], c[1], w(c[3])) for c in cases], gen=gen, use_kit=False)
        st.notes = self.notes
        return st

    def tokens(self, cid: str):
        for kind, lets, cases, gen in self.groups:
            if kind == "raw":
                continue
            for c in cases:
                if c[0] == cid:
                    return f"({kit.GEN if gen else ''}{lets}{c[2]})", c[3]
        raise KeyError(cid)


# =============================================================== small units
def suite_small() -> Cases:
    cs = Cases("b5_small")
    # ---- chi2_sf: the parameter is the table of scipy's values
    args = [(3.841458820694124, 1), (0.0, 5), (nan, 2), (1000.0, 8), (12.5, 8), (-1.0, 3), (inf, 4), (7.0, 0), (7.0, -1)]
    tab = "[" + ", ".join(f"({fb(x)}, ({d}), {fb(sc.chi2_sf(x, d))})" for x, d in args) + "]"
    cs.group(BI + TAB2 + f"let CT : List (UInt64 × Int × UInt64) := {tab}; ",
             [(f"chi2_sf({x!r}, {d})", "chi2_sf", f"[bi (chi2_sf (α := Float) (T2 CT) {lf(x)} ({d}))]", [fb(sc.chi2_sf(x, d))])
              for x, d in args])
    # ---- LogisticFit: build the record, read every field back
    f = sc.LogisticFit(["Intercept", "a"], np.array([0.5, -1.25]), np.array([[1.0, 0.25], [0.25, 2.0]]), -12.75, 4, True)
    term = ('(let f : LogisticFit Float := { names := ["Intercept", "a"], beta := Np.NDArray.d1 ' + fl(f.beta)
            + ", cov := Np.NDArray.d2 [" + ", ".join(fl(r) for r in f.cov) + "], loglik := " + lf(f.loglik)
            + ", n_iter := 4, converged := true }; "
            "(f.names.flatMap ts) ++ (match f.beta with | .d1 v => 1 :: v.map bi | .d2 _ => [2]) ++ "
            "(match f.cov with | .d1 _ => [1] | .d2 r => 2 :: r.flatMap (fun (q : List Float) => q.map bi)) ++ "
            "[bi f.loglik, f.n_iter, if f.converged then 1 else 0])")
    exp = [t for n in f.names for t in ts(n)] + [1] + [fb(v) for v in f.beta] + [2] + [fb(v) for r in f.cov for v in r] + [fb(f.loglik), f.n_iter, 1]
    cs.group(BI + TS + FL, [("fields", "LogisticFit", term, exp)])
    # ---- _hl_groups
    hc = []
    explicit = [([], 0, 10), ([5], 5, 10), ([1] * 30, 30, 10), ([1] * 31, 31, 10), ([1] * 7, 7, 10), ([100, 1, 1, 1], 103, 10),
                ([1, 100, 1, 1], 103, 10), ([3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1], 31, 10), ([10] * 10 + [5], 105, 10),
                ([10] * 10 + [6], 106, 10), ([2, 2], 4, 1), ([2, 2], 4, 3), ([4, 9, 2, 7, 7, 1], 30, 4), ([1, 2, 3], 6, -2),
                ([0, 0, 3], 3, 10), ([3, 0, 0], 3, 10), ([50, 50, 1], 101, 2), ([50, 50, 6], 106, 2), ([7, 7, 7], 100, 10),
                ([15, 15, 15, 15, 1], 61, 10), ([15, 15, 15, 15, 3], 63, 10), ([15, 15, 15, 15, 4], 64, 10), ([1, 1, 1], 3, 2),
                ([25] * 4, 100, 10), ([9, 3, 9, 3, 9, 3, 9, 3], 48, 5), ([-2, 5, -1, 4], 6, 3), ([2, 3], 5, 2), ([1], 1, 2), ([1, 1], 2, 4),
                ([20, 20, 19, 1], 60, 3), ([6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5], 56, 10)]
    for bl, n, g in explicit:
        hc.append((f"{bl} n={n} g={g}", "_hl_groups", f"_hl_groups (α := Float) {ints(bl)} ({n}) ({g})", sc._hl_groups(list(bl), n, g)))
    for k in range(60):  # seeded: block sizes 1..mx, n = their sum (as hosmer_lemeshow calls it), g in a few values
        ln = 1 + kit.hsh(900 + k, 0) % 40
        mx = [2, 5, 12, 60][k % 4]
        g = [10, 10, 10, 4, 7, 1][k % 6]
        bl = [1 + v for v in kit.gI(1000 + k, ln, 0, mx, 0)]
        hc.append((f"seeded k={k} len={ln} max={mx} g={g}", "_hl_groups", f"GH {1000 + k} {ln} {mx} ({g})", sc._hl_groups(list(bl), sum(bl), g)))
    cs.group("let GH := fun (s n : Nat) (mx : UInt64) (g : Int) => let b := (gI s n 0 mx 0).map (fun (o : Option Int) => o.getD 0 + 1); "
             "_hl_groups (α := Float) b (b.foldl (fun (a c : Int) => a + c) 0) g; ", hc, gen=True)
    return cs


# =============================================================== _expit
EXPIT_D1 = [0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 2.0, -2.0, 30.0, -30.0, 36.7, -36.7, 37.0, -37.5, 100.0, -100.0, 709.0, -709.0,
            709.78, -709.78, 709.79, -709.79, 710.0, -710.0, 745.0, -745.0, 745.2, -746.0, 1000.0, -1000.0, 1e308, -1e308,
            inf, -inf, nan, 5e-324, -5e-324, 1e-20, -1e-20, 0.1, -0.1, 0.3, 2.5, -3.75, 12.125, -17.3, 1e-8, 3.141592653589793]
EXPIT_RAND = [v for v in kit.gF(77, 40, 0, 6, []) if v is not None]
EXPIT_D2 = [[0.0, 1.5, -2.25], [800.0, -800.0, nan], [0.75, -0.75, 4.0]]


def suite_expit() -> Cases:
    cs = Cases("b5_expit")
    cs.notes = {"_expit": "88 of the cases (ids exp(-x)[i]) compare the Lean Float.exp(-x) with np.exp(-x), the routine _expit calls, on the same inputs"}
    xs = EXPIT_D1 + EXPIT_RAND
    with np.errstate(all="ignore"):
        ex = sc._expit(np.array(xs, dtype=np.float64))
        npexp = np.exp(-np.array(xs, dtype=np.float64))
        ex2 = sc._expit(np.array(EXPIT_D2, dtype=np.float64))
        ex0 = sc._expit(np.array([], dtype=np.float64))
    # one integer per element: the bits of _expit, then the bits of the Lean exp(-x) against np.exp
    # (to explain a last-bit difference of _expit)
    cs.raw(BI + FL + f"let X : List Float := {fl(xs)}; ",
           "((match _expit (α := Float) (Np.NDArray.d1 X) with | .d1 v => v | .d2 _ => [] : List Float).map bi ++ X.map (fun (x : Float) => bi (Float.exp (-x))))",
           [(f"d1[{i}] {x!r}", "_expit", fb(ex[i])) for i, x in enumerate(xs)]
           + [(f"exp(-x)[{i}] {x!r}", "_expit", fb(npexp[i])) for i, x in enumerate(xs)])
    term = ("(match _expit (α := Float) (Np.NDArray.d2 [" + ", ".join(fl(r) for r in EXPIT_D2)
            + "]) with | .d1 _ => [1] | .d2 r => 2 :: r.flatMap (fun (q : List Float) => (q.length : Int) :: q.map bi))")
    cs.group(BI + FL, [("d2 3x3", "_expit", term, [2] + [t for r in ex2 for t in [len(r)] + [fb(v) for v in r]]),
                       ("d1 empty", "_expit", "(match _expit (α := Float) (Np.NDArray.d1 []) with | .d1 v => 1 :: v.map bi | .d2 _ => [2])", [1] + [fb(v) for v in ex0]),
                       ("d2 empty", "_expit", "(match _expit (α := Float) (Np.NDArray.d2 []) with | .d1 _ => [1] | .d2 r => [2, (r.length : Int)])", [2, 0])])
    return cs


# =============================================================== hosmer_lemeshow
HBASE = (OF + TS + TCOL + FT + TAB1 + TAB2
         + "let H := fun (PT : List (UInt64 × UInt64)) (CT : List (UInt64 × Int × UInt64)) (y pd : Pl.Col Float) => "
         "let r := hosmer_lemeshow (α := Float) (T2 CT) (T1 PT) y pd; ft r.1 ++ o r.2.1 ++ [r.2.2.1] ++ o r.2.2.2; ")
# real data: pd = k / 100 written as two digits per row, y as one digit per row
HREAL = ("let DP := fun (s : String) => let cs := s.toList.map (fun (c : Char) => c.toNat - 48); "
         "(Pl.Col.f64 ((List.range (cs.length / 2)).map (fun (i : Nat) => some (Float.ofNat (cs.getD (2 * i) 0 * 10 + cs.getD (2 * i + 1) 0) / 100.0))) : Pl.Col Float); "
         "let DY := fun (s : String) => (Pl.Col.int (s.toList.map (fun (c : Char) => some ((c.toNat : Int) - 48))) : Pl.Col Float); ")
# seeded data: y in {0, 1}; pd = a / 100 + jitter (ties within 1e-6 of each other)
HSEED = ("let JJ : List Float := [0.0, 0.0, 3e-7, -4e-7, 1e-6, -1e-6, 1.2e-6, 5e-7]; "
         "let GY := fun (s n : Nat) => (Pl.Col.int (gI s n 0 2 0) : Pl.Col Float); "
         "let GP := fun (s n : Nat) (m : UInt64) (off : Int) => (Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => "
         "(match a, b with | some a, some b => some (Float.ofInt a / 100.0 + JJ.getD b.toNat 0.0) | _, _ => none : Option Float)) "
         "(gI s n 0 m off) (gI (s + 1) n 0 8 0)) : Pl.Col Float); ")
JJ = [0.0, 0.0, 3e-7, -4e-7, 1e-6, -1e-6, 1.2e-6, 5e-7]


def hl_expected(y: pl.Series, pd: pl.Series):
    """Run the Python; return (expected tokens, pow table, chi2 table)."""
    table, chisq, dof, pv = sc.hosmer_lemeshow(y, pd)
    pt = {}
    for _, size, o1, e1, o0, e0 in table.iter_rows():
        for x in (float(o1) - e1, float(o0) - e0):  # the arguments of the two `** 2` (sc:1022)
            try:
                pt[fb(x)] = fb(x**2)
            except OverflowError:
                pass
    ct = [] if pv is None else [(fb(chisq), dof, fb(pv))]
    if table.height > 0:  # R-F2I: the two observed-count columns hold α values in the Lean
        table = table.with_columns(pl.col("EventsObserved").cast(pl.Float64), pl.col("NoneventsObserved").cast(pl.Float64))
    return frame_tok(table) + o(chisq) + [dof] + o(pv), pt, ct


def hl_case(cid: str, ly: str, lp: str, y: pl.Series, pd: pl.Series):
    exp, pt, ct = hl_expected(y, pd)
    PT = "[" + ", ".join(f"({a}, {b})" for a, b in pt.items()) + "]"
    CT = "[" + ", ".join(f"({a}, ({d}), {b})" for a, d, b in ct) + "]"
    return (cid, "hosmer_lemeshow", f"H {PT} {CT} {ly} {lp}", exp)


def suite_hl() -> Cases:
    cs = Cases("b5_hl")
    F64, I64 = pl.Float64, pl.Int64
    # ---- real data: 500-row slices of the edge_metrics_a training scores
    d = pl.read_csv(ROOT / "inputs/scenarios/edge_metrics_a/risk_scores_train.csv")
    for a, n in [(0, 500), (500, 500), (1000, 500), (3000, 500), (6500, 500), (2000, 60), (4000, 1500)]:
        s = d.slice(a, n)
        ks = [round(v * 100) for v in s["pd_logistic"].to_list()]
        assert all(0 <= k < 100 and float(k) / 100.0 == v for k, v in zip(ks, s["pd_logistic"].to_list()))
        yv = s["default_flag"].to_list()
        assert all(v in (0, 1) for v in yv)
        py = pl.Series([float(k) / 100.0 for k in ks], dtype=F64)
        cs.group(HBASE + HREAL, [hl_case(f"real rows {a}..{a + n}", '(DY "' + "".join(str(v) for v in yv) + '")',
                              '(DP "' + "".join(f"{k:02d}" for k in ks) + '")', pl.Series(yv, dtype=I64), py)])
    # ---- seeded data with jittered ties
    seeded = []
    for sd, n, m, off in [(11, 300, 60, -20), (21, 400, 8, -40), (31, 120, 3, -50), (41, 37, 90, -5), (51, 9, 4, -30),
                          (61, 250, 25, -1), (71, 64, 2, -49), (81, 200, 101, 0), (91, 150, 12, 3)]:
        ya = kit.gI(sd, n, 0, 2, 0)
        a, b = kit.gI(sd + 5, n, 0, m, off), kit.gI(sd + 6, n, 0, 8, 0)
        pv = [float(x) / 100.0 + JJ[j] for x, j in zip(a, b)]
        seeded.append(hl_case(f"seeded s={sd} n={n} m={m} off={off}", f"(GY {sd} {n})", f"(GP {sd + 5} {n} {m} ({off}))",
                              pl.Series(ya, dtype=I64), pl.Series(pv, dtype=F64)))
    cs.group(HBASE + HSEED, seeded, gen=True)
    # ---- edge cases
    E = {}
    E["empty"] = ([], "f64", [], "f64")
    E["all null"] = ([None, 1.0, None], "f64", [0.3, None, None], "f64")
    E["one row"] = ([1.0], "f64", [0.3], "f64")
    E["two rows, one block"] = ([1.0, 0.0], "f64", [0.3, 0.3], "f64")
    E["two rows, two blocks"] = ([1.0, 0.0], "f64", [0.3, 0.4], "f64")
    E["three rows"] = ([1.0, 0.0, 1.0], "f64", [0.3, 0.4, 0.5], "f64")
    E["five rows, same pd (1 group)"] = ([1.0, 0.0, 1.0, 0.0, 0.0], "f64", [0.25] * 5, "f64")
    E["two big blocks (2 groups)"] = ([1.0, 0.0] * 20, "f64", [0.2] * 20 + [0.6] * 20, "f64")
    E["three big blocks (3 groups, dof 1)"] = ([1.0, 0.0, 0.0] * 20, "f64", [0.2] * 20 + [0.6] * 20 + [0.7] * 20, "f64")
    E["ties within 1e-6 chain"] = ([1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], "f64",
                                   [0.5, 0.5 + 5e-7, 0.5 + 1e-6, 0.5 + 1.0000001e-6, 0.5 + 1.5e-6, 0.5 + 2e-6, 0.5 + 2.1e-6, 0.5 - 1e-6,
                                    0.5 - 9.99999e-7, 0.5000010000000001, 0.50000099999999, 0.4999990000000001], "f64")
    E["nulls dropped"] = ([1.0, None, 0.0, 1.0, 0.0, None, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0], "f64",
                          [0.9, 0.5, None, 0.3, 0.2, None, None, 0.7, 0.1, 0.4, 0.6, 0.8], "f64")
    E["int y, int pd"] = ([1, 0, None, 1, 0, 1, 0], "int", [0, 0, 1, 0, 0, 0, None], "int")
    E["bool y"] = ([True, False, None, True, False, True, False, False], "bool", [0.9, 0.1, 0.4, 0.35, 0.8, 0.2, 0.35, 0.5], "f64")
    E["y not 0/1 (integral: 2, 3, -1)"] = ([2.0, 0.0, 3.0, 1.0, -1.0, 2.0, 0.0, 1.0, 1.0, 5.0, 0.0, 1.0], "f64",
                                           [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.15, 0.25, 0.35], "f64")
    E["y halves summing to integers per group"] = ([0.5, 0.5, 1.5, 0.5, 0.25, 0.75], "f64", [0.2, 0.2, 0.5, 0.5, 0.8, 0.8], "f64")
    E["expected events 0 (pd = 0 group)"] = ([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0], "f64",
                                             [0.0, 0.0, 0.3, 0.3, 0.5, 0.5, 0.7, 0.7, 0.9, 0.9], "f64")
    E["expected nonevents 0 (pd = 1 group)"] = ([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0], "f64",
                                                [0.1, 0.1, 0.3, 0.3, 0.5, 0.5, 0.7, 0.7, 1.0, 1.0], "f64")
    E["pd outside [0, 1]"] = ([0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0], "f64",
                              [-0.5, -0.5, 0.3, 0.3, 0.5, 0.5, 0.7, 0.7, 1.5, 1.5], "f64")
    E["NaN pd (last group)"] = ([0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0], "f64",
                                [0.1, nan, 0.3, 0.3, 0.5, 0.5, 0.7, 0.7, 0.2, 0.2, 0.9, 0.9], "f64")
    E["inf pd"] = ([0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0], "f64", [0.1, inf, 0.3, 0.3, 0.5, 0.5, 0.7, 0.7, -inf, 0.2], "f64")
    E["signed zeros pd"] = ([0.0, 1.0, 1.0, 0.0, 1.0, 0.0], "f64", [0.0, -0.0, 0.0, -0.0, 0.5, 0.5], "f64")
    dt = {"f64": pl.Float64, "int": pl.Int64, "bool": pl.Boolean}
    lc = {"f64": fcol, "int": icol, "bool": bcol}
    cs.group(HBASE + FCOL, [hl_case(name, lc[yk](yv), lc[pk](pv), pl.Series(yv, dtype=dt[yk]), pl.Series(pv, dtype=dt[pk]))
                  for name, (yv, yk, pv, pk) in E.items()])
    return cs


# =============================================================== classification_table
CLET = (
    "let MW := fun (m : List (List Float)) => W ((m.length : Int) :: m.flatMap (fun (r : List Float) => (r.length : Int) :: r.map bi)); "
    "let VW := fun (v : List Float) => W ((v.length : Int) :: v.map bi); "
    # keyed routines: numpy's result when the arguments are the ones numpy received
    "let KMM := fun (ka kb : Int) (out : List (List Float)) (a b : List (List Float)) => if MW a == ka && MW b == kb then out else ([] : List (List Float)); "
    "let KINV := fun (ka : Int) (out : List (List Float)) (a : List (List Float)) => if MW a == ka then out else ([] : List (List Float)); "
    "let KEQ := fun (ka kb : Int) (out : List Float) (a b : List (List Float)) => if MW a == ka && MW b == kb then out else ([] : List Float); "
    "let KMV := fun (ka kb : Int) (out : List Float) (a : List (List Float)) (b : List Float) => if MW a == ka && VW b == kb then out else ([] : List Float); "
    "let GV := fun (s n : Nat) (m : UInt64) (off : Int) (d : Float) => (gI s n 0 m off).map (fun (o : Option Int) => Float.ofInt (o.getD 0) / d); "
    "let GX := fun (cols : List (List Float)) => (List.range (cols.headD []).length).map (fun (i : Nat) => cols.map (fun (c : List Float) => c.getD i 0.0)); "
)


def mw(m) -> int:
    return w([len(m)] + [t for r in m for t in [len(r)] + [fb(v) for v in r]])


def vw(v) -> int:
    return w([len(v)] + [fb(x) for x in v])


def gv(s, n, m, off, d):
    return [float(v) / d for v in kit.gI(s, n, 0, m, off)]


def ct_case(cid, ly, lx, lpd, y, x, pd, shape, fit=None, lfit=None):
    """shape: 'kw' classification_table(y, x, pd=pd) | 'inv' classification_table(X, y, pd) |
    'fit' classification_table(y, x, fit) | 'fit+kw' (y, x, fit, pd=pd) | 'arr+kw' (y, x, pd, pd=other)."""
    y, x = np.asarray(y, dtype=np.float64), np.asarray(x, dtype=np.float64)
    with np.errstate(all="ignore"):
        if shape == "kw":
            res = sc.classification_table(y, x, pd=pd)
            largs = f"(Np.NDArray.d1 {ly}) (Np.NDArray.d2 {lx}) none (some (Np.NDArray.d1 {lpd}))"
        elif shape == "inv":
            res = sc.classification_table(x, y, pd)
            largs = f"(Np.NDArray.d2 {lx}) (Np.NDArray.d1 {ly}) (some (Sum.inr (Np.NDArray.d1 {lpd}))) none"
        elif shape == "fit":
            res = sc.classification_table(y, x, fit)
            largs = f"(Np.NDArray.d1 {ly}) (Np.NDArray.d2 {lx}) (some (Sum.inl {lfit})) none"
        elif shape == "fit+kw":
            res = sc.classification_table(y, x, fit, pd=pd)
            largs = f"(Np.NDArray.d1 {ly}) (Np.NDArray.d2 {lx}) (some (Sum.inl {lfit})) (some (Np.NDArray.d1 {lpd}))"
        else:  # the positional array wins over the keyword
            res = sc.classification_table(y, x, pd, pd=np.full(len(y), 0.5))
            largs = (f"(Np.NDArray.d1 {ly}) (Np.NDArray.d2 {lx}) (some (Sum.inr (Np.NDArray.d1 {lpd}))) "
                     f"(some (Np.NDArray.d1 (List.replicate {len(y)} 0.5)))")
        # the same lines as sc:1071-1081, to get what numpy passed to and returned from the routines
        if shape == "fit":
            eta = x @ fit.beta
            p = sc._expit(eta)
            mv = f"(KMV {mw(x)} {vw(fit.beta)} {fl(eta)})"
            l1 = "(T1 [])"
        else:
            p = np.asarray(pd, dtype=np.float64)
            l1v = {fb(-v): fb(np.log1p(-v)) for v in p}
            mv = "(fun (_ : List (List Float)) (_ : List Float) => ([] : List Float))"
            l1 = "(T1 [" + ", ".join(f"({a}, {b})" for a, b in l1v.items()) + "])"
        wv = p * (1.0 - p)
        xw = x * wv[:, None]
        mm = x.T @ xw
        v = np.linalg.inv(mm)
        q = np.einsum("ij,jk,ik->i", x, v, x)
    m2 = lambda m: "[" + ", ".join(fl(r) for r in m) + "]"  # noqa: E731
    term = (f"ft (classification_table (α := Float) (KINV {mw(mm)} {m2(v)}) (KMM {mw(x.T)} {mw(xw)} {m2(mm)}) {mv} "
            f"(KEQ {mw(x)} {mw(v)} {fl(q)}) {l1} {largs})")
    res = res.with_columns(pl.col("CorrectNonevents").cast(pl.Float64), pl.col("IncorrectNonevents").cast(pl.Float64))  # R-F2I
    return (cid, "classification_table", term, frame_tok(res))


def suite_ct() -> Cases:
    cs = Cases("b5_ct")
    CB = BI + OF + TS + TCOL + FT + FL + TAB1 + CLET

    def data(sd, n, k, pm, poff, ym=2):
        cols = [[1.0] * n] + [gv(sd + 10 * j, n, 33, 16, 8.0) for j in range(1, k)]
        lx = "(GX [List.replicate " + str(n) + " 1.0" + "".join(f", GV {sd + 10 * j} {n} 33 16 8.0" for j in range(1, k)) + "])"
        x = np.array(cols).T
        y = gv(sd + 1, n, ym, 0, 1.0)
        pd = np.array(gv(sd + 2, n, pm, poff, 100.0))
        return f"(GV {sd + 1} {n} {ym} 0 1.0)", lx, f"(GV {sd + 2} {n} {pm} ({poff}) 100.0)", y, x, pd

    def fitrec(beta, k):
        f = sc.LogisticFit(["Intercept"] + [f"x{j}" for j in range(1, k)], np.array(beta, dtype=np.float64), np.eye(k), -1.0, 1, True)
        lfit = ('({ names := ["Intercept"' + "".join(f', "x{j}"' for j in range(1, k)) + "], beta := Np.NDArray.d1 " + fl(beta)
                + ", cov := Np.NDArray.d2 [], loglik := -1.0, n_iter := 1, converged := true } : LogisticFit Float)")
        return f, lfit

    D1 = data(100, 24, 2, 90, -5)          # pd in 0.05 .. 0.94
    D2 = data(200, 40, 3, 60, -20)         # pd in 0.20 .. 0.79
    D3 = data(300, 30, 2, 9, -1)           # pd in 0.01 .. 0.09: short grid from 0.000
    D4 = data(400, 30, 2, 9, -91)          # pd in 0.91 .. 0.99: grid ends at 1.000
    D5 = data(500, 16, 2, 98, -1, ym=1)    # y all 0
    D6 = data(600, 28, 3, 50, -25, ym=3)   # y in {0, 1, 2}
    D7 = data(700, 20, 2, 1, -50)          # pd = 0.5 everywhere
    cs.group(CB, [ct_case("kw pd, n=24 k=2", *D1, "kw")], gen=True)
    cs.group(CB, [ct_case("inventory order (X, y, pd), n=24 k=2", *D1, "inv")], gen=True)
    cs.group(CB, [ct_case("kw pd, n=40 k=3", *D2, "kw")], gen=True)
    cs.group(CB, [ct_case("kw pd low, n=30", *D3, "kw"), ct_case("kw pd high, n=30", *D4, "inv")], gen=True)
    cs.group(CB, [ct_case("y all 0", *D5, "kw"), ct_case("y in {0,1,2}", *D6, "kw")], gen=True)
    f0, l0 = fitrec([0.0, 0.0], 2)
    f1, l1 = fitrec([-0.75, 0.5], 2)
    cs.group(CB, [ct_case("fit beta = 0 (eta = 0, p = 0.5)", *D7, "fit", fit=f0, lfit=l0),
                  ct_case("fit and pd keyword: pd is used", *D1, "fit+kw", fit=f1, lfit=l1),
                  ct_case("positional array and pd keyword: the positional array is used", *D3, "arr+kw")], gen=True)
    cs.group(CB, [ct_case("fit beta = (-0.75, 0.5): p through exp", *D1, "fit", fit=f1, lfit=l1)], gen=True)
    return cs


SUITES = {"b5_small": suite_small, "b5_expit": suite_expit, "b5_hl": suite_hl, "b5_ct": suite_ct}

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--tokens":
        term, exp = SUITES[sys.argv[2]]().tokens(sys.argv[3])
        out = HERE.parent / "work" / "b5_tokens.txt"
        out.write_text(term + "\n" + repr(exp) + "\n")
        print(f"input and expected tokens -> {out} ({len(term)} chars)")
    else:
        for mk in SUITES.values():
            mk().suite().write()
