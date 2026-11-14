"""Differential tests of the units re-translated after commit 7927af7 (sas_round, _pairs,
roc_association, association_table, merge_one_to_one), against the NEW Python code.

  uv run python migration/diffeval/units/u7927_gen.py
      -> work/u7927_round, u7927_pairs, u7927_merge (.json + .inputs.json)
  (eval_decl each work/u7927_*.inputs.json on def:zz_carrier_p / zz_carrier_p, save work/u7927_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/u7927_<suite>.json migration/diffeval/work/u7927_<suite>.out.txt

The carrier is the item def:zz_carrier_p (decl zz_carrier_p, the identity on List Int): the item
def:zz_carrier no longer exists. Most data are enumerated inside Lean and mirrored here with
integer / IEEE arithmetic only (the eval_decl inputs stay short); one digest or one integer is
returned per case.

u7927_round  sas_round (sc:182-191)
  - specials, one integer per value: null, NaN, +-inf, +-0.0, tiny, exact integers, halves
  - sweep per k (k = 0 .. 2^60, 21 values): the bases k+0.5, k+0.5-t, k+0.5+t, k+t, k+1-t for 11
    offsets t (1e-6, 5e-7, 1e-12, ...), each with -2..+2 ulps and both signs: 450 values per k
  - seeded random columns (kit.gF) with nulls / NaN / inf / zeros mixed in
  - the literal path (`sas_round(<float>)` under pl.select), 1-row frames, an Int64 column
u7927_pairs  _pairs, roc_association (without / with label), association_table (sc:856-977)
  - tie sets built around _TIE_EPS at 7 magnitudes: [t, v, w] with v = (t - eps) -2..+2 ulps and
    w = (v - eps) -2..+2 ulps (group anchored on its largest value), both class patterns
  - explicit sets: the 21 sets of b4_gen.py, ties at / inside / outside eps next to 0, chains of
    values each within eps of the next, equal scores across classes, NaN / inf scores, nulls in
    y and / or score, Null-dtype columns, single-class and empty inputs
  - seeded random sets, continuous and on a grid with offsets of the size of eps
u7927_merge  merge_one_to_one (sc:240-259)
  - the 21 lists of b3_gen.py and new ones: a later shorter frame with a same-named column (kept
    tail), every modelled pair of dtypes under vertical_relaxed, nulls, zero-row and zero-column
    frames, three and more frames, equal heights, zero frames
  - lists outside def:merge_one_to_one_precond (Float64 meeting String, Date meeting a number;
    Date meeting Boolean, where Python raises): expect_diff, with the value under the diagnosis
"""
from __future__ import annotations

import datetime as dt
import math
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))

import b3_gen as b3  # noqa: E402
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
M64 = (1 << 64) - 1
ITEM, DECL = "def:zz_carrier_p", "zz_carrier_p"


def mk(name: str) -> Suite:
    s = Suite(name)
    s.item, s.decl = ITEM, DECL
    return s


def raw(x) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def fb(b: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


def lf(x) -> str:
    return f"(Float.ofBits {raw(x)})"


def ob(v) -> int:
    return -1 if v is None else cmp.fbits(v)


def fdig(vals) -> int:
    return cmp.digest(cmp.tok_col(cmp.canon_floats(vals)))


# ================================================================ sas_round
KS = [0, 1, 2, 3, 4, 7, 10, 99, 1000, 10**6, 10**6 + 1, 10**9, 123456789, 2**31, 2**40, 2**50, 2**51, 2**52 - 1, 2**52, 2**53, 2**60]
TS_ = [1e-6, 5e-7, 2e-6, 1e-7, 1e-9, 1e-12, 5e-13, 1e-13, 1e-3, 0.25, 0.4999999]
up, dn = (lambda x: math.nextafter(x, inf)), (lambda x: math.nextafter(x, -inf))
SP = [None, nan, inf, -inf, 0.0, -0.0, 5e-324, -5e-324, 1e-300, 1e-20, 1e-13, 1e-12, 1e-7, 1e-6, 0.3, -0.3,
      0.49999999999999994, 0.5, up(0.5), -0.5, dn(-0.5), up(-0.5), 1.5, -1.5, 2.5, -2.5, 0.5 - 5e-13, dn(0.5 - 5e-13), 0.5 - 1e-12,
      0.4999995, 0.499999, 0.4999989, 1e6 + 0.5, dn(1e6 + 0.5), up(1e6 + 0.5), 1e6 + 0.5 - 1e-6, 1e6 + 0.5 - 1.1e-6, 1e9 + 0.5,
      dn(1e9 + 0.5), 1e9 + 0.5 - 1e-6, 1e9 + 0.499998, 2.0**52 - 0.5, 2.0**52 - 1.0, 2.0**52 - 1.5, 2.0**52, 2.0**52 + 1, dn(2.0**52),
      2.0**53, 2.0**53 + 2, dn(2.0**53), -(2.0**53), -(2.0**52) + 0.5, 1e300, -1e300, 1.7976931348623157e308, 123456.5, 7.0, -7.0,
      1e15 + 0.5, 1e15 + 0.25, -1e15 - 0.5, 1.0, -1.0, 1e6, 1e9, -1e9, 3.4999999999995, 3.49999999999, 0.7, -0.49]
EDGE = [None, nan, inf, -inf, 0.0, -0.0, 0.5, -0.5, 1.5, 2.5, 1e6 + 0.5, 4503599627370495.5]
RND = [(101, 400, 10, 60), (102, 400, 10, 3), (103, 300, 30, 20), (104, 300, 0, 52), (105, 257, 5, 1), (106, 2, 50, 3)]


def sweep_vals(k: int) -> list:
    kf = float(k)
    bases = [kf + 0.5] + [b for t in TS_ for b in ((kf + 0.5) - t, (kf + 0.5) + t, kf + t, (kf + 1.0) - t)]
    out = []
    for b in bases:
        for d in range(5):
            x = fb(raw(b) + d - 2)
            out += [x, -x]
    return out


def py_round(vals) -> list:
    r = pl.DataFrame({"x": pl.Series(vals, dtype=pl.Float64)}).select(sc.sas_round(pl.col("x")))
    assert r.columns == ["x"] and r.schema["x"] == pl.Float64, r.schema
    return r.get_column("x").to_list()


def suite_round() -> Suite:
    s = mk("u7927_round")
    C = "let c := fun (n : String) => Pl.col (α := Float) n; "
    RS = ('let RS := fun (v : List (Option Float)) => (let f : Pl.Frame Float := [("x", Pl.Col.f64 v)]; '
          'Pl.Frame.getF (f.select [(sas_round (.expr (c "x"))).pos]) "x"); ')
    OB = "let ob := fun (o : Option Float) => (match o with | none => (-1 : Int) | some x => (x.toBits.toNat : Int)); "
    # ---- specials: one integer per value
    s.ints(C + RS + OB + f"let SP : List (Option Float) := {lt.lean_opt_floats(SP)}; ", "((RS SP).map ob)",
           [(f"special {i:02d} {v!r}", "sas_round", ob(r)) for i, (v, r) in enumerate(zip(SP, py_round(SP), strict=True))], use_kit=False)
    # ---- sweep per k, random columns
    SV = (f"let T : List Float := [{', '.join(lf(t) for t in TS_)}]; "
          "let SV := fun (k : Nat) => let kf := k.toFloat; let B := (kf + 0.5) :: T.flatMap (fun (t : Float) => [(kf + 0.5) - t, (kf + 0.5) + t, kf + t, (kf + 1.0) - t]); "
          "B.flatMap (fun (b : Float) => (List.range 5).flatMap (fun (d : Nat) => let x := Float.ofBits (b.toBits + d.toUInt64 - 2); [some x, some (-x)])); ")
    cases = []
    for k in KS:
        v = sweep_vals(k)
        cases.append((f"sweep k={k} ({len(v)} values around k+0.5, k, k+1)", "sas_round", fdig(py_round(v)), {"covers": len(v)}))
    for sd, n, pe, eh in RND:
        v = kit.gF(sd, n, pe, eh, EDGE)
        cases.append((f"random seed={sd} n={n} edges={pe}% exp=+-{eh}", "sas_round", fdig(py_round(v)), {"covers": n}))
    s.ints(C + RS + SV + f"let E := {lt.lean_opt_floats(EDGE)}; ",
           f"((({KS} : List Nat).map (fun (k : Nat) => dg (tC (Pl.Col.f64 (RS (SV k)))))) ++ "
           f"([{', '.join(f'({a}, {b}, {c}, {d})' for a, b, c, d in RND)}] : List (Nat × Nat × UInt64 × UInt64)).map "
           "(fun (q : Nat × Nat × UInt64 × UInt64) => dg (tC (Pl.Col.f64 (RS (gF q.1 q.2.1 q.2.2.1 q.2.2.2 E))))))", cases, gen=True)
    # ---- other contexts: literal under pl.select, 1-row frames, Int64 column, with_columns
    LV = [-0.3, -0.0, 0.0, 0.3, 0.5, -0.5, 2.5, -2.5, 0.49999999999999994, 0.5 - 5e-13, dn(0.5 - 5e-13), 1e6 + 0.5 - 1e-6, 1e6 + 0.5 - 1.1e-6,
          2.0**52 - 0.5, 2.0**53, 1e300, 5e-324, nan, inf, -inf, 7.0]
    cases = []
    for v in LV:
        cases.append((f"literal {v!r} pl.select", "sas_round", cmp.digest(cmp.tokens(cmp.canon_frame(pl.select(sc.sas_round(v)))))))
    for v in LV + [None]:
        f1 = pl.DataFrame({"x": pl.Series([v], dtype=pl.Float64)})
        cases.append((f"1-row frame {v!r} select", "sas_round", cmp.digest(cmp.tokens(cmp.canon_frame(f1.select(sc.sas_round(pl.col("x"))))))))
    fint = pl.DataFrame({"i": pl.Series([None, -3, 0, 5, 2**40], dtype=pl.Int64), "x": pl.Series([0.5, None, -1.5, nan, 2.4999999], dtype=pl.Float64)})
    cases.append(("Int64 column select", "sas_round", cmp.digest(cmp.tokens(cmp.canon_frame(fint.select(sc.sas_round(pl.col("i"))))))))
    cases.append(("with_columns", "sas_round", cmp.digest(cmp.tokens(cmp.canon_frame(fint.with_columns(sc.sas_round(pl.col("x"))))))))
    for n in (3, 0, -4):
        cases.append((f"int literal {n}", "sas_round", cmp.digest(cmp.tokens(cmp.canon_frame(fint.select(sc.sas_round(n)))))))
    LVL = "[" + ", ".join(lf(v) for v in LV) + "]"
    s.ints(C + f"let LV : List Float := {LVL}; let OV : List (Option Float) := LV.map (fun (x : Float) => some x) ++ [none]; let f0 : Pl.Frame Float := []; " + lt.lean_frame_let("fi", fint),
           "(LV.map (fun (x : Float) => dg (tR (f0.select [(sas_round (.float x)).pos]))) ++ "
           'OV.map (fun (o : Option Float) => let f : Pl.Frame Float := [("x", Pl.Col.f64 [o])]; dg (tR (f.select [(sas_round (.expr (c "x"))).pos]))) ++ '
           '[dg (tR (fi.select [(sas_round (.expr (c "i"))).pos])), dg (tR (fi.withColumns [(sas_round (.expr (c "x"))).pos]))] ++ '
           "([3, 0, -4] : List Int).map (fun (n : Int) => dg (tR (fi.select [(sas_round (.int n)).pos]))))", cases)
    return s


# ================================================================ _pairs, roc_association, association_table
EPS = sc._TIE_EPS
TOPS = [2 * EPS, 0.5, 0.75, 1.0, 1e-3, 1e6, 3.0]
J2 = [0.0, EPS, -EPS, EPS / 2, up(EPS), dn(EPS), 2 * EPS, 0.75 * EPS]
LABEL = "Logistic Model"
PRE = (b4.FCOL + b4.W + b4.FA
       + "let P := fun (y s : Pl.Col Float) => let q := _pairs (α := Float) y s; W ([q.conc, q.disc, q.tied, q.n1, q.n0] ++ fa q.v10 ++ fa q.v01); "
       + b4.OF + b4.TS + b4.TCOL
       + "let R := fun (y s : Pl.Col Float) (l : Option String) => W (match roc_association (α := Float) y s l with "
         "| .inl r => 0 :: (o r.area ++ o r.std_err ++ o r.lower ++ o r.upper ++ o r.somers_d ++ o r.gamma ++ o r.tau_a) "
         "| .inr fr => 1 :: (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2) : List Int); "
       + "let A := fun (y s : Pl.Col Float) => let r := association_table (α := Float) y s; W (o r.concordant_pct ++ o r.discordant_pct ++ o r.tied_pct ++ [r.pairs] ++ "
         "o r.somers_d ++ o r.gamma ++ o r.tau_a ++ o r.c); ")
BODY = ("(DG.flatMap (fun (g : List (Pl.Col Float × Pl.Col Float)) => [W (g.map (fun (d : Pl.Col Float × Pl.Col Float) => P d.1 d.2)), "
        f'W (g.flatMap (fun (d : Pl.Col Float × Pl.Col Float) => [R d.1 d.2 none, R d.1 d.2 (some "{LABEL}")])), '
        "W (g.map (fun (d : Pl.Col Float × Pl.Col Float) => A d.1 d.2))]))")


def four(y: pl.Series, s: pl.Series) -> list:
    """the digests of _pairs, roc_association without label, with label, association_table"""
    q = sc._pairs(y, s)
    r0 = sc.roc_association(y, s)
    r1 = sc.roc_association(y, s, LABEL)
    a = sc.association_table(y, s)
    return [b4.w([q.conc, q.disc, q.tied, q.n1, q.n0] + b4.fa(q.v10) + b4.fa(q.v01)),
            b4.w([0] + b4.roc_tok(r0)), b4.w([1] + b4.roc_tok(r1) if False else [1] + b4.frame_tok(r1)),
            b4.w(b4.o(a.concordant_pct) + b4.o(a.discordant_pct) + b4.o(a.tied_pct) + [a.pairs] + b4.o(a.somers_d)
                 + b4.o(a.gamma) + b4.o(a.tau_a) + b4.o(a.c))]


def group(name: str, sets: list) -> list:
    """sets: (y, s) Series pairs of one group -> three cases (one digest over the group per unit)"""
    f = [four(y, s) for y, s in sets]
    k = len(sets)
    return [(f"{name}: {k} data sets", "_pairs", b4.w([x[0] for x in f]), {"covers": k}),
            (f"{name}: {k} data sets, without and with label", "roc_association", b4.w([v for x in f for v in (x[1], x[2])]), {"covers": 2 * k}),
            (f"{name}: {k} data sets", "association_table", b4.w([x[3] for x in f]), {"covers": k})]


def fs(vals) -> pl.Series:
    return pl.Series(vals, dtype=pl.Float64, nan_to_null=False)


def suite_pairs() -> Suite:
    st = mk("u7927_pairs")
    # ---- tie sets around eps, enumerated in Lean
    cases, ntied = [], [0, 0]
    for t in TOPS:
        sets = []
        for d in range(5):
            v = fb(raw(t - EPS) + d - 2)
            for e in range(5):
                w = fb(raw(v - EPS) + e - 2)
                ntied[0 if t - v > EPS else 1] += 1
                sets += [(fs(yv), fs([t, v, w])) for yv in ([1.0, 0.0, 1.0], [0.0, 1.0, 0.0])]
        cases += group(f"tie sets [t, v, w], t={t!r}, v = (t-eps) -2..+2 ulp, w = (v-eps) -2..+2 ulp, y = 1,0,1 / 0,1,0", sets)
    print(f"pairs tie sets: t-v > eps on {ntied[0]}, <= eps on {ntied[1]} of the (t, v, w) triples")
    st.ints(PRE + f"let E : Float := {lf(EPS)}; let TOPS : List Float := [{', '.join(lf(t) for t in TOPS)}]; "
            "let Y := fun (a b : Float) => (Pl.Col.f64 [some a, some b, some a] : Pl.Col Float); "
            "let DG : List (List (Pl.Col Float × Pl.Col Float)) := TOPS.map (fun (t : Float) => (List.range 5).flatMap (fun (d : Nat) => "
            "let v := Float.ofBits ((t - E).toBits + d.toUInt64 - 2); (List.range 5).flatMap (fun (e : Nat) => "
            "let w := Float.ofBits ((v - E).toBits + e.toUInt64 - 2); let s : Pl.Col Float := Pl.Col.f64 [some t, some v, some w]; [(Y 1.0 0.0, s), (Y 0.0 1.0, s)]))); ",
            BODY, cases, use_kit=False)
    # ---- explicit sets
    X = dict(b4.C)
    e = EPS
    X["eps_exact"] = ([1., 0.], "f64", [2 * e, e], "f64")
    X["eps_inside"] = ([1., 0.], "f64", [2 * e, up(e)], "f64")
    X["eps_outside"] = ([1., 0.], "f64", [2 * e, dn(e)], "f64")
    X["eps_exact_rev"] = ([0., 1.], "f64", [e, 2 * e], "f64")
    X["eps_outside_rev"] = ([0., 1.], "f64", [dn(e), 2 * e], "f64")
    X["chain_06"] = ([1., 0.] * 6, "f64", [1.0 - 0.6 * e * i for i in range(12)], "f64")
    X["chain_06_perm"] = ([1., 1., 0., 0., 1., 0., 0., 1., 1., 0., 1., 0., 0.], "f64",
                          [1.0 - 0.6 * e * i for i in (7, 2, 11, 0, 5, 5, 9, 1, 10, 3, 0, 8, 4)], "f64")
    X["chain_half"] = ([0., 1.] * 5 + [0.], "f64", [k * (e / 2) for k in range(11)], "f64")
    X["chain_099"] = ([1., 0., 0., 1., 0., 1., 1., 0.], "f64", [0.25 - 0.99 * e * i for i in range(8)], "f64")
    X["equal_cross"] = ([1., 0., 1., 0., 1., 0., 0.], "f64", [.3, .3, .3, .2, .2, .3, .2], "f64")
    X["equal_blocks"] = ([1., 1., 0., 0., 1., 0., 1., 0., 0., 1.], "f64", [.5, .1, .5, .1, .9, .9, .1, .5, .9, .5], "f64")
    X["nan_first"] = ([0., 1., 0., 1.], "f64", [nan, .9, .1, .5], "f64")
    X["nan_ties"] = ([1., 0., 1., 0., 1.], "f64", [.5, .5 + e / 2, nan, 1.0, nan], "f64")
    X["nan_last_only"] = ([1., 0., 1., 0.], "f64", [.2, .4, .6, nan], "f64")
    X["inf_mix"] = ([1., 0., 1., 0., 1., 0.], "f64", [inf, inf, 1.7e308, -inf, -inf, 0.0], "f64")
    X["nulls_y_only"] = ([None, 1., 0., None, 1., 0., None], "f64", [.5, .5, .5 - e, .1, .5 - 2 * e, .9, .3], "f64")
    X["nulls_s_only"] = ([1., 0., 1., 0., 1., 0.], "f64", [None, .5, None, .5 + e / 3, .7, None], "f64")
    X["nulls_both"] = ([None, 0., 1., None, 1., 0., 1., None], "f64", [.1, None, .3, None, .3 + e, .3 - e, None, .2], "f64")
    X["null_y_dtype"] = ([None, None, None], "null", [.1, .2, .3], "f64")
    X["null_s_dtype"] = ([1., 0., 1.], "f64", [None, None, None], "null")
    X["null_both_dtype"] = ([None, None], "null", [None, None], "null")
    X["int_s_nulls"] = ([1, 0, 1, 0, None, 1, 0], "int", [5, 5, None, 4, 4, 6, 5], "int")
    X["bool_y"] = ([True, False, True, False, None, True], "bool", [.5, .5 - e, .5 - e / 2, .5 + e, .9, None], "f64")
    X["one_class_ties"] = ([1., 1., 1., 1.], "f64", [.5, .5, .5 - e, .5 - 3 * e], "f64")
    X["one_row_other"] = ([2.], "f64", [.5], "f64")
    X["y_none_usable"] = ([2., 3., nan], "f64", [.5, .6, .7], "f64")
    X["eps_at_0"] = ([1., 0., 1., 0., 1., 0.], "f64", [e, 0.0, -0.0, -5e-324, -dn(e) + e, up(e)], "f64")

    def lcol(vals, kind):
        return f"(Pl.Col.null {len(vals)} : Pl.Col Float)" if kind == "null" else b4.col(vals, kind)

    def pser(vals, kind):
        return pl.Series(vals, dtype=pl.Null) if kind == "null" else (fs(vals) if kind == "f64" else b4.ser(vals, kind))

    cases, terms, names = [], [], list(X)
    for g in range(0, len(names), 6):
        part = names[g:g + 6]
        cases += group("explicit sets " + ", ".join(part), [(pser(X[n][0], X[n][1]), pser(X[n][2], X[n][3])) for n in part])
        terms.append("[" + ", ".join(f"({lcol(X[n][0], X[n][1])}, {lcol(X[n][2], X[n][3])})" for n in part) + "]")
    st.ints(PRE + "let DG : List (List (Pl.Col Float × Pl.Col Float)) := [" + ", ".join(terms) + "]; ", BODY, cases, use_kit=False)
    # ---- seeded random sets
    EL = "[" + ", ".join("none" if x is None else f"some {lf(x)}" for x in b4.EDGE) + "]"
    RG = ("let RI := fun (s n : Nat) => (Pl.Col.int (gI s n 5 3 0) : Pl.Col Float); "
          f"let RC := fun (s n : Nat) (pe eh : UInt64) => (Pl.Col.f64 (gF s n pe eh {EL}) : Pl.Col Float); "
          f"let J : List Float := [{', '.join(lf(j) for j in J2)}]; "
          "let RG := fun (s n : Nat) (m : UInt64) => (Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => some (Float.ofInt a / 100.0 + J.getD b.toNat 0.0) | _, _ => none : Option Float)) "
          "(gI s n 4 m 0) (gI (s + 1) n 0 8 0)) : Pl.Col Float); ")
    cases, terms = [], []
    for seed, n, mode in [(211, 300, "cont"), (221, 400, 50), (231, 250, "mix"), (241, 130, 6), (251, 9, "cont"), (261, 17, 3), (271, 40, "mix"),
                          (281, 64, 12), (291, 200, 2), (301, 150, 1)]:
        y = pl.Series(kit.gI(seed, n, 5, 3, 0), dtype=pl.Int64)
        if isinstance(mode, int):
            k, j = kit.gI(seed + 1, n, 4, mode, 0), kit.gI(seed + 2, n, 0, 8, 0)
            sv = [None if a is None else float(a) / 100.0 + J2[b] for a, b in zip(k, j, strict=True)]
            terms.append(f"(RI {seed} {n}, RG {seed + 1} {n} {mode})")
        else:
            pe, eh = (0, 3) if mode == "cont" else (8, 40)
            sv = kit.gF(seed + 1, n, pe, eh, b4.EDGE)
            terms.append(f"(RI {seed} {n}, RC {seed + 1} {n} {pe} {eh})")
        cases += group(f"random seed={seed} n={n} {mode if isinstance(mode, str) else f'grid of {mode} levels + eps offsets'}", [(y, fs(sv))])
    st.ints(PRE + RG + "let DG : List (List (Pl.Col Float × Pl.Col Float)) := [" + ", ".join(f"[{x}]" for x in terms) + "]; ", BODY, cases, gen=True, use_kit=False)
    return st


# ================================================================ merge_one_to_one
def kind(s: pl.Series) -> str:
    return "cell" if s.dtype == pl.Date else lt.col_kind(s.dtype)


def unmodelled(a: str, b: str) -> bool:
    """the pairs of kinds excluded by def:merge_one_to_one_precond (symmetric)"""
    if "cell" in (a, b):
        return not (a == b or "null" in (a, b))
    return {a, b} == {"f64", "str"}


def sup(a: str, b: str) -> str:
    if a == "null":
        return b
    if b == "null":
        return a
    for k in ("str", "cell", "f64", "int"):
        if k in (a, b):
            return k
    return "bool"


def meets(frames) -> str | None:
    """the first unmodelled pair of dtypes that actually meets in a concat (sc:254-258), or None.
    Follows the code with the real Series. A Float64 part without any non-null value meeting
    String is exact (nothing is rendered) and is not reported."""
    n = max((f.height for f in frames), default=0)
    cols: dict[str, pl.Series] = {}
    for f in frames:
        for s in f.iter_columns():
            pad, prev = n - s.len(), cols.get(s.name)
            if pad == 0:
                cols[s.name] = s
            elif prev is None:
                cols[s.name] = pl.concat([s, pl.Series(s.name, [None] * pad, dtype=s.dtype)])
            else:
                rest = prev.slice(s.len())
                k, kp = kind(s), kind(rest)
                if unmodelled(k, kp):
                    fpart = s if k == "f64" else rest
                    if not ({k, kp} == {"f64", "str"} and fpart.null_count() == fpart.len()):
                        return f"{k} meets {kp} in column {s.name!r}"
                cols[s.name] = pl.concat([s.to_frame(), rest.to_frame()], how="vertical_relaxed").to_series()
    return None


def precond(frames) -> bool:
    """def:merge_one_to_one_precond on DataFrames (which are well-formed): the pairwise dtype clause"""
    cs = [(s.name, kind(s)) for f in frames for s in f.iter_columns()]
    return not any(a[0] == b[0] and unmodelled(a[1], b[1]) for a in cs for b in cs)


def suite_merge() -> Suite:
    s = mk("u7927_merge")
    D = dt.date
    N = {}
    # the frames of b3_gen.py
    N["a"] = pl.DataFrame({"d": [D(2024, 1, 2)], "x": [1.5], "s": ["p"]})
    N["b"] = pl.DataFrame({"y": [1, 2, 3], "x": ["a", "b", None]})
    N["c"] = pl.DataFrame({"x": [True, None], "z": [nan, -0.0], "y": [None, 2.5], "d": [None, D(1960, 1, 1)]})
    N["z"] = pl.DataFrame({"q": pl.Series([], dtype=pl.Float64), "y": pl.Series([], dtype=pl.String), "d": pl.Series([], dtype=pl.Date)})
    N["nl"] = pl.DataFrame({"n": pl.Series([None, None, None], dtype=pl.Null), "x": [7, 8, 9]})
    N["e"] = pl.DataFrame()
    N["one"] = pl.DataFrame({"AUC": [0.7], "Gini": [0.4]})
    N["ks"] = pl.DataFrame({"KS": [0.5, 0.3], "cut": [0.1, 0.2]})
    N["psi"] = pl.DataFrame({"PSI": [0.01], "PSI_interpretation": ["Stable"]})
    # new frames: one column "x" of each dtype, long (4 rows, with nulls) and short
    N["F4"] = pl.DataFrame({"x": [1.5, None, nan, -0.0], "k": [1, 2, 3, 4]})
    N["I4"] = pl.DataFrame({"x": [1, None, -3, 0], "t": ["p", None, "r", ""]})
    N["B4"] = pl.DataFrame({"x": [True, None, False, True]})
    N["S4"] = pl.DataFrame({"x": ["a", None, "1.5", ""]})
    N["D4"] = pl.DataFrame({"x": [D(2024, 1, 2), None, D(1960, 1, 1), D(1970, 1, 1)]})
    N["N4"] = pl.DataFrame({"x": pl.Series([None] * 4, dtype=pl.Null)})
    N["F1"] = pl.DataFrame({"x": [9.25]})
    N["F2"] = pl.DataFrame({"x": [None, inf]})
    N["I1"] = pl.DataFrame({"x": [7]})
    N["I2"] = pl.DataFrame({"x": [None, -12]})
    N["B2"] = pl.DataFrame({"x": [False, None]})
    N["S1"] = pl.DataFrame({"x": ["u"]})
    N["S2"] = pl.DataFrame({"x": [None, "true"]})
    N["D1"] = pl.DataFrame({"x": [D(2000, 2, 29)]})
    N["N1"] = pl.DataFrame({"x": pl.Series([None], dtype=pl.Null)})
    N["F0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Float64)})
    N["I0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Int64)})
    N["B0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Boolean)})
    N["S0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.String)})
    N["D0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Date)})
    N["N0"] = pl.DataFrame({"x": pl.Series([], dtype=pl.Null)})
    N["W3"] = pl.DataFrame({"k": [10, 20, 30], "x": [0.5, 0.25, None], "u": [None, "m", "n"]})
    lets = "".join(f"let f{n} : Pl.Frame Float := {b3.lframe_items(f)}; " for n, f in N.items())
    L = [[], ["a"], ["a", "b"], ["b", "a"], ["a", "b", "c"], ["c", "b", "a"], ["z"], ["z", "b"], ["b", "z"], ["z", "z"], ["e"], ["e", "b"],
         ["e", "e"], ["nl", "b"], ["b", "nl"], ["nl", "a"], ["a", "a"], ["one", "ks", "psi"], ["c", "c", "a", "z", "b"], ["ks", "one", "c"], ["c", "ks"]]
    long_, short = ["F4", "I4", "B4", "S4", "D4", "N4"], ["F1", "F2", "I1", "I2", "B2", "S1", "S2", "D1", "N1", "F0", "I0", "B0", "S0", "D0", "N0"]
    L += [[a, b] for a in long_ for b in short]                                   # a later shorter frame: kept tail, every dtype pair
    L += [[b, a] for a in ("F4", "I4", "S4", "N4") for b in ("F1", "I2", "S1", "N1", "B0")]   # the longest frame last: it replaces the column
    L += [["F4", "I4"], ["I4", "F4"], ["S4", "B4"], ["N4", "D4"], ["F4", "F4"]]                # equal heights
    L += [["F4", "I1", "B2"], ["I4", "B2", "F1"], ["I4", "F2", "I1", "N1"], ["S4", "B2", "I1"], ["B4", "I1", "B2"], ["B4", "N1", "B2", "I0"],
          ["N4", "N1", "I2", "F1"], ["N4", "B2", "S1"], ["D4", "N1", "D1", "D0"], ["F4", "W3", "I1"], ["W3", "F4", "W3", "F2"],
          ["I4", "W3", "S1", "ks"], ["F1", "I2", "W3", "I4", "B2", "N1"], ["I4", "F4", "S1"], ["F4", "I4", "S1"], ["F4", "S4", "B2", "I1"],
          ["e", "F4", "e", "I1"], ["F0", "I0"], ["S0", "I0", "F0"], ["N0", "N0"], ["F1", "I1"], ["I1", "S1"], ["a", "F4", "c"], ["D4", "F4", "D1"]]
    terms, cases, raises, nx = [], [], [], 0
    for fsn in L:
        fr = [N[n] for n in fsn]
        why, label = meets(fr), f"merge({', '.join(fsn)})"
        if why is not None:
            assert not precond(fr), fsn
        try:
            r = sc.merge_one_to_one(*fr)
        except pl.exceptions.SchemaError as ex:
            assert why is not None and {"cell", "bool"} <= set(why.split()), (fsn, why)
            raises.append((fsn, f"{label}: Python raises SchemaError ({str(ex)[:60]}); {why}"))
            continue
        extra = {}
        if fsn == ["c", "c", "a", "z", "b"]:
            # z.y (String, 0 rows) meets c.y (Float64) and the floats become text, but b.y (Int64, the
            # greatest height) then replaces the whole column: the final frame does not hold the text
            assert why is not None and r.schema["y"] == pl.Int64
            extra = {"note": f"outside def:merge_one_to_one_precond ({why}), but the column is replaced whole by a later frame: the result is exact"}
        elif why is not None:
            nx += 1
            extra = {"expect_diff": True, "note": f"outside def:merge_one_to_one_precond: {why} (Float64 -> String text / Date as a number or "
                                                  "text is not expressible in the model; TODO(port) of the unit)"}
        elif not precond(fr):
            extra = {"note": "outside the (pairwise) precondition, but no Float64 value is rendered as text and no Date meets another dtype in a concat: exact"}
        terms.append("[" + ", ".join("f" + n for n in fsn) + "]")
        cases.append((f"{len(cases):03d} {label} -> {dict(r.schema)} h={r.height}", "merge_one_to_one", b3.cframe(r), extra))
    print(f"merge: {len(cases)} lists, {nx} with an unmodelled dtype pair (expect_diff), {len(raises)} where Python raises")
    s.digest_body(lets, "(([" + ", ".join(terms) + "] : List (List (Pl.Frame Float))).map (fun (fs : List (Pl.Frame Float)) => "
                  "dg (tR (merge_one_to_one (α := Float) fs))))", cases, gen=False, table=True)
    # Python raises (Date meets Boolean): the Lean returns a frame, the expected value is -1
    rl = "".join(f"let f{n} : Pl.Frame Float := {b3.lframe_items(N[n])}; " for n in sorted({n for fsn, _ in raises for n in fsn}))
    s.ints(rl, "([" + ", ".join("[" + ", ".join("f" + n for n in fsn) + "]" for fsn, _ in raises) + "] : List (List (Pl.Frame Float))).map "
           "(fun (fs : List (Pl.Frame Float)) => dg (tR (merge_one_to_one (α := Float) fs)))",
           [(lab, "merge_one_to_one", -1, {"expect_diff": True, "note": "Python raises SchemaError (no supertype of Date and Boolean); excluded by def:merge_one_to_one_precond"})
            for _, lab in raises], table=True)
    # whole values: the kept tail with three frames; the diagnosis of the unmodelled casts (the
    # Lean value = the Python value with the text of the Float64 values / the Date part replaced by null)
    def lets_of(names):
        return "".join(f"let f{n} : Pl.Frame Float := {b3.lframe_items(N[n])}; " for n in names)

    s.tokens(lets_of(["I4", "F2", "I1", "N1"]), "tok: merge(I4, F2, I1, N1)", "merge_one_to_one", "tR (merge_one_to_one (α := Float) [fI4, fF2, fI1, fN1])", "frame",
             b3.cframe(sc.merge_one_to_one(N["I4"], N["F2"], N["I1"], N["N1"])), gen=False, cells=True)
    s.tokens(lets_of(["N1", "W3"]), "tok: merge(N1, W3): a Null-dtype column padded from 1 to 3 rows", "merge_one_to_one", "tR (merge_one_to_one (α := Float) [fN1, fW3])", "frame",
             b3.cframe(sc.merge_one_to_one(N["N1"], N["W3"])), gen=False, cells=True)
    r = sc.merge_one_to_one(N["S4"], N["F2"])
    assert r.get_column("x").to_list() == [None, "inf", "1.5", ""]
    diag = {"type": "frame", "cols": [["x", cmp.canon_strs([None, None, "1.5", ""])]]}
    s.tokens(lets_of(["S4", "F2"]), "diagnosis: merge(S4, F2) = Python with the text of the Float64 values replaced by null", "merge_one_to_one",
             "tR (merge_one_to_one (α := Float) [fS4, fF2])", "frame", diag, gen=False, cells=True,
             note="not a case of the unit's domain: checks that the recorded TODO(port) (Float64 -> String) accounts for the whole difference of merge(S4, F2)")
    r = sc.merge_one_to_one(N["D4"], N["I1"])
    assert r.get_column("x").to_list() == [7, None, -3653, 0]
    diag = {"type": "frame", "cols": [["x", {"type": "col", "kind": "cell", "values": [["num", None], ["num", None], ["str", "1960-01-01"], ["str", "1970-01-01"]]}]]}
    s.tokens(lets_of(["D4", "I1"]), "diagnosis: merge(D4, I1) = a Date column whose Int64 part is null (Python: Int64 day numbers)", "merge_one_to_one",
             "tR (merge_one_to_one (α := Float) [fD4, fI1])", "frame", diag, gen=False, cells=True,
             note="not a case of the unit's domain: checks that the recorded TODO(port) (Date meeting a non-Date dtype) accounts for the whole difference of merge(D4, I1)")
    return s


if __name__ == "__main__":
    for mk_ in (suite_round, suite_pairs, suite_merge):
        mk_().write()
