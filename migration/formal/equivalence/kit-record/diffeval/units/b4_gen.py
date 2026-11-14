"""Bundle B4 differential tests (_TIE_EPS, Z975, _pairs, roc_association, association_table and the
records RocAssociation, AssociationTable, _Pairs).

  uv run python migration/diffeval/units/b4_gen.py
      -> work/b4_all (.json + .inputs.json)
  (eval_decl each work/b4_*.inputs.json on def:zz_carrier / zz_carrier, save work/b4_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b4_<suite>.json migration/diffeval/work/b4_<suite>.out.txt
  uv run python migration/diffeval/receipts.py units b4

The cases are the implementers' 29 (y, score) data sets (21 explicit, 8 seeded and generated on
both sides with kit.gF / kit.gI), ported from their scratch generator: _pairs on each;
roc_association without and with a label, and association_table, on each. The results are
records, so each is tokenised by hand into a List Int (below) and one digest (their fold W) is
returned per case. One direct case is added for the constant _TIE_EPS.

Suite b4_types: the bits of the constant Z975, and the three record types. Each record is built
as a literal (every field given, with None / NaN / -0.0 / empty-array values) and every field is
read back, one compared integer per field; then every field of the record that the unit returns
(roc_association without label -> RocAssociation, association_table -> AssociationTable,
_pairs -> _Pairs) is read on four data sets, again one integer per field (an absent float is -1,
a float its bits, an array the digest W of its length and bits).
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

nan, inf = float("nan"), float("inf")


def raw(x) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def lf(x) -> str:
    return f"(Float.ofBits {raw(x)})"


def col(vals, kind="f64") -> str:
    if kind == "f64":
        return "(F [" + ", ".join("none" if v is None else f"some {raw(v)}" for v in vals) + "])"
    if kind == "int":
        return "(Pl.Col.int [" + ", ".join("none" if v is None else f"some ({v})" for v in vals) + "] : Pl.Col Float)"
    return "(Pl.Col.bool [" + ", ".join("none" if v is None else f"some {'true' if v else 'false'}" for v in vals) + "] : Pl.Col Float)"


def ser(vals, kind) -> pl.Series:
    return pl.Series(vals, dtype={"f64": pl.Float64, "int": pl.Int64, "bool": pl.Boolean}[kind])


C = {}  # name -> (y values, y kind, score values, score kind)
C["simple"] = ([1., 0., 1., 0., 1.], "f64", [.9, .1, .4, .35, .8], "f64")
C["ties_eps"] = ([1., 0., 1., 0., 1., 0., 1., 0.], "f64",
                 [.5, .5 + 5e-9, .5 + 1e-8, .5 - 1e-8, .5 + 2e-8, .5 - 2e-8, 0.5000000100000001, 0.49999999], "f64")
C["ties_eps2"] = ([1., 0., 0., 0., 1., 1., 0.], "f64", [1.0, 1.0 + 1e-8, 1.0 - 1e-8, 1.00000001, 0.99999999, 3e-9, -3e-9], "f64")
C["nulls"] = ([1., None, 0., 1., 0., None, 1., 0.], "f64", [.9, .5, None, .3, .2, None, None, .7], "f64")
C["other_y"] = ([1., 2., 0., nan, -0.0, 0.5, 1., -1., 1.0000000001], "f64", [.9, .5, .1, .3, .2, .6, .15, .7, .8], "f64")
C["all_ones"] = ([1., 1., 1.], "f64", [.9, .5, .1], "f64")
C["all_zeros"] = ([0., 0., 0.], "f64", [.9, .5, .1], "f64")
C["empty"] = ([], "f64", [], "f64")
C["all_null"] = ([None, 1.], "f64", [.3, None], "f64")
C["n1_1"] = ([1., 0., 0., 0.], "f64", [.5, .1, .5, .9], "f64")
C["n0_1"] = ([1., 1., 0., 1.], "f64", [.5, .1, .5, .9], "f64")
C["n1n0_1"] = ([1., 0.], "f64", [.7, .2], "f64")
C["single"] = ([1.], "f64", [.7], "f64")
C["all_tied"] = ([1., 0., 1., 0., 0., 1.], "f64", [.25] * 6, "f64")
C["nan_scores"] = ([1., 0., 1., 0., 1., 0.], "f64", [.1, .2, nan, .3, .5, nan], "f64")
C["nan_ev_only"] = ([1., 0., 1., 0., 1., 0.], "f64", [.1, .2, nan, .3, nan, .05], "f64")
C["inf_scores"] = ([1., 0., 1., 0., 1., 0.], "f64", [inf, -inf, .5, inf, -inf, .5], "f64")
C["neg_zero"] = ([1., 0., 1., 0.], "f64", [0.0, -0.0, -0.0, 0.0], "f64")
C["int_y"] = ([1, 0, None, 1, 0, 2, 0], "int", [.9, .1, .4, .35, .8, .2, .35], "f64")
C["bool_y_int_s"] = ([True, False, None, True, False, True], "bool", [3, 1, 2, None, 3, -4], "int")
C["huge"] = ([1., 0., 1., 0.], "f64", [1e300, 1e300, -1e300, 1e-300], "f64")
J = [0.0, 0.0, 3e-9, -4e-9, 1e-8, -1e-8, 1.2e-8]
JL = "[" + ", ".join(lf(j) for j in J) + "]"
EDGE = [None, nan, inf, -inf, 0.0, -0.0, 0.5]
EL = "[" + ", ".join("none" if e is None else f"some {lf(e)}" for e in EDGE) + "]"
G = {}  # name -> (Lean y, Lean score, Python y Series, Python score Series)


def gen(name, seed, n, mode):
    yi = kit.gI(seed, n, 5, 3, 0)                     # ints 0, 1, 2 with 5% nulls
    Y = f"(RI {seed} {n})"
    if mode == "grid":
        k = kit.gI(seed + 1, n, 4, 50, 0)
        j = kit.gI(seed + 2, n, 0, 7, 0)
        sv = [None if a is None else float(a) / 100.0 + J[b] for a, b in zip(k, j)]
        S = f"(RG {seed + 1} {n})"
    else:
        pe, eh = (0, 3) if mode == "cont" else (8, 40)
        sv = kit.gF(seed + 1, n, pe, eh, EDGE)
        S = f"(RC {seed + 1} {n} {pe} {eh})"
    G[name] = (Y, S, pl.Series(yi, dtype=pl.Int64), pl.Series(sv, dtype=pl.Float64, nan_to_null=False))


gen("rand_cont_300", 11, 300, "cont")
gen("rand_grid_400", 21, 400, "grid")
gen("rand_mix_250", 31, 250, "mix")
gen("rand_grid_130", 41, 130, "grid")
gen("rand_cont_9", 51, 9, "cont")
gen("rand_grid_17", 61, 17, "grid")
gen("rand_mix_40", 71, 40, "mix")
gen("rand_grid_64", 81, 64, "grid")
for name, (yv, yk, sv, sk) in C.items():
    G[name] = (col(yv, yk), col(sv, sk), ser(yv, yk), ser(sv, sk))


# ---- the record tokens, Python side (floats by their bits, every NaN the canonical one)
def w(t) -> int:
    h = 14695981039346656037
    for x in t:
        h = (h * 1099511628211 + x + 7) % 18446744073709551616
    return h


def o(v):
    return [0] if v is None else [1, cmp.fbits(v)]


def ts(s):
    return [len(s)] + [ord(c) for c in s]


def fa(a):
    return [len(a)] + [cmp.fbits(x) for x in a]


def roc_tok(r):
    return [t for f in (r.area, r.std_err, r.lower, r.upper, r.somers_d, r.gamma, r.tau_a) for t in o(f)]


def frame_tok(df):
    out = [df.width]
    for name in df.columns:
        c = df.get_column(name)
        out += ts(name)
        if c.dtype == pl.Float64:
            out += [1, len(c)] + [t for v in c.to_list() for t in o(v)]
        elif c.dtype == pl.String:
            out += [4, len(c)] + [t for v in c.to_list() for t in ([0] if v is None else [1] + ts(v))]
        else:
            out += [99]
    return out


# ---- the same, Lean side
W = "let W := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
FA = "let fa := fun (a : FloatArray_ Float) => (match a with | .d1 v => (v.length : Int) :: v.map (fun (x : Float) => (x.toBits.toNat : Int)) | .d2 _ => [-1] : List Int); "
OF = "let o := fun (v : Option Float) => (match v with | none => [0] | some x => [1, (x.toBits.toNat : Int)] : List Int); "
TS = "let ts := fun (s : String) => (s.length : Int) :: s.toList.map (fun (c : Char) => (c.toNat : Int)); "
TCOL = ("let tc := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: (v.length : Int) :: v.flatMap o "
        "| .str v => 4 :: (v.length : Int) :: v.flatMap (fun (x : Option String) => (match x with | none => [0] | some s => 1 :: ts s : List Int)) | _ => [99] : List Int); ")
FCOL = "let F := fun (v : List (Option UInt64)) => (Pl.Col.f64 (v.map (fun (o : Option UInt64) => o.map Float.ofBits)) : Pl.Col Float); "
RGEN = ("let RI := fun (s n : Nat) => (Pl.Col.int (gI s n 5 3 0) : Pl.Col Float); "
        f"let RC := fun (s n : Nat) (pe eh : UInt64) => (Pl.Col.f64 (gF s n pe eh {EL}) : Pl.Col Float); "
        f"let RG := fun (s n : Nat) => (Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => some (Float.ofInt a / 100.0 + ({JL} : List Float).getD b.toNat 0.0) | _, _ => none : Option Float)) "
        "(gI s n 4 50 0) (gI (s + 1) n 0 7 0)) : Pl.Col Float); ")
DATA = "let D : List (Pl.Col Float × Pl.Col Float) := [" + ", ".join(f"({Y}, {S})" for Y, S, _, _ in G.values()) + "]; "


def suite_all() -> Suite:
    """One input (the data sets are shared): 29 _pairs digests, the bits of _TIE_EPS, then for each
    data set roc_association without label, with label, association_table."""
    cases = []
    for name, (_, _, y, s) in G.items():
        q = sc._pairs(y, s)
        cases.append((name, "_pairs", w([q.conc, q.disc, q.tied, q.n1, q.n0] + fa(q.v10) + fa(q.v01))))
    cases.append(("_TIE_EPS bits", "_TIE_EPS", cmp.fbits(sc._TIE_EPS)))
    for name, (_, _, y, s) in G.items():
        r0 = sc.roc_association(y, s)
        r1 = sc.roc_association(y, s, "Logistic Model")
        r = sc.association_table(y, s)
        cases += [(name + " (no label -> record)", "roc_association", w([0] + roc_tok(r0))),
                  (name + " (label -> frame)", "roc_association", w([1] + frame_tok(r1))),
                  (name, "association_table", w(o(r.concordant_pct) + o(r.discordant_pct) + o(r.tied_pct) + [r.pairs] + o(r.somers_d)
                                                + o(r.gamma) + o(r.tau_a) + o(r.c)))]
    P = "let P := fun (y s : Pl.Col Float) => let q := _pairs (α := Float) y s; W ([q.conc, q.disc, q.tied, q.n1, q.n0] ++ fa q.v10 ++ fa q.v01); "
    R = ("let R := fun (y s : Pl.Col Float) (l : Option String) => W (match roc_association (α := Float) y s l with "
         "| .inl r => 0 :: (o r.area ++ o r.std_err ++ o r.lower ++ o r.upper ++ o r.somers_d ++ o r.gamma ++ o r.tau_a) "
         "| .inr fr => 1 :: (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2) : List Int); ")
    A = ("let A := fun (y s : Pl.Col Float) => let r := association_table (α := Float) y s; W (o r.concordant_pct ++ o r.discordant_pct ++ o r.tied_pct ++ [r.pairs] ++ "
         "o r.somers_d ++ o r.gamma ++ o r.tau_a ++ o r.c); ")
    st = Suite("b4_all")
    st.ints(RGEN + FCOL + W + FA + P + OF + TS + TCOL + R + A + DATA,
            "(D.map (fun (d : Pl.Col Float × Pl.Col Float) => P d.1 d.2) ++ [((_TIE_EPS (α := Float)).toBits.toNat : Int)] ++ "
            'D.flatMap (fun (d : Pl.Col Float × Pl.Col Float) => [R d.1 d.2 none, R d.1 d.2 (some "Logistic Model"), A d.1 d.2]))',
            cases, gen=True, use_kit=False)
    st.notes = {"_TIE_EPS": "direct case added when porting the generator (the implementers exercised the constant only through _pairs)"}
    return st


ROC_F = ["area", "std_err", "lower", "upper", "somers_d", "gamma", "tau_a"]
ASSOC_F = ["concordant_pct", "discordant_pct", "tied_pct", "pairs", "somers_d", "gamma", "tau_a", "c"]
PAIRS_F = ["conc", "disc", "tied", "n1", "n0", "v10", "v01"]


def ob(v) -> int:
    return -1 if v is None else cmp.fbits(v)


def lo(v) -> str:
    return "none" if v is None else f"(some {lf(v)})"


def lfa(a) -> str:
    return "(Np.NDArray.d1 [" + ", ".join(lf(x) for x in a) + "])"


def suite_types() -> Suite:
    """Z975, RocAssociation, AssociationTable, _Pairs: one integer per field."""
    OB = "let ob := fun (v : Option Float) => (match v with | none => (-1 : Int) | some x => (x.toBits.toNat : Int) : Int); "
    RR = "let rr := fun (r : RocAssociation Float) => [" + ", ".join(f"ob r.{f}" for f in ROC_F) + "]; "
    AR = "let ar := fun (r : AssociationTable Float) => [" + ", ".join("r.pairs" if f == "pairs" else f"ob r.{f}" for f in ASSOC_F) + "]; "
    PR = "let pr := fun (q : _Pairs Float) => [q.conc, q.disc, q.tied, q.n1, q.n0, W (fa q.v10), W (fa q.v01)]; "
    cases = [("Z975 bits", "Z975", cmp.fbits(sc.Z975))]
    parts = ["[((Z975 (α := Float)).toBits.toNat : Int)]"]
    # ---- literals: build the record, read every field back
    for tag, vals in (("literal all present", (0.75, 0.125, 0.5, 1.0, -0.0, 1e-300, 0.1)), ("literal None / NaN / inf", (None, nan, None, inf, -inf, None, 5e-324))):
        r = sc.RocAssociation(*vals)
        parts.append("rr { " + ", ".join(f"{f} := {lo(x)}" for f, x in zip(ROC_F, vals)) + " }")
        cases += [(f"{tag}: {f}", "RocAssociation", ob(getattr(r, f))) for f in ROC_F]
    for tag, vals in (("literal all present", (85.92, 13.5, 0.58, 123456789012, 0.7242, -0.0, 0.25, 0.8621)), ("literal None / NaN / negative pairs", (None, nan, None, -3, None, inf, None, None))):
        r = sc.AssociationTable(*vals)
        parts.append("ar { " + ", ".join(f"{f} := ({x})" if f == "pairs" else f"{f} := {lo(x)}" for f, x in zip(ASSOC_F, vals)) + " }")
        cases += [(f"{tag}: {f}", "AssociationTable", getattr(r, f) if f == "pairs" else ob(getattr(r, f))) for f in ASSOC_F]
    for tag, vals in (("literal", (3, -2, 0, 2, 5, [0.5, -0.0, nan, 1e300], [])), ("literal empty arrays", (0, 0, 0, 0, 0, [], [inf]))):
        q = sc._Pairs(*vals[:5], np.array(vals[5], dtype=np.float64), np.array(vals[6], dtype=np.float64))
        parts.append("pr { " + ", ".join(f"{f} := {lfa(x) if f in ('v10', 'v01') else f'({x})'}" for f, x in zip(PAIRS_F, vals)) + " }")
        cases += [(f"{tag}: {f}", "_Pairs", w(fa(getattr(q, f))) if f in ("v10", "v01") else getattr(q, f)) for f in PAIRS_F]
    # ---- the records the units return: every field
    for name in ("simple", "nulls", "all_ones", "empty"):
        Y, S, y, s = G[name]
        r = sc.roc_association(y, s)
        assert isinstance(r, sc.RocAssociation)
        parts.append(f"(match roc_association (α := Float) {Y} {S} none with | .inl r => rr r | .inr _ => ([] : List Int))")
        cases += [(f"roc_association({name}).{f}", "RocAssociation", ob(getattr(r, f))) for f in ROC_F]
        a = sc.association_table(y, s)
        assert isinstance(a, sc.AssociationTable)
        parts.append(f"ar (association_table (α := Float) {Y} {S})")
        cases += [(f"association_table({name}).{f}", "AssociationTable", getattr(a, f) if f == "pairs" else ob(getattr(a, f))) for f in ASSOC_F]
        q = sc._pairs(y, s)
        assert isinstance(q, sc._Pairs)
        parts.append(f"pr (_pairs (α := Float) {Y} {S})")
        cases += [(f"_pairs({name}).{f}", "_Pairs", w(fa(getattr(q, f))) if f in ("v10", "v01") else getattr(q, f)) for f in PAIRS_F]
    st = Suite("b4_types")
    st.ints(FCOL + W + FA + OB + RR + AR + PR, "(" + " ++ ".join(parts) + ")", cases, use_kit=False)
    note = "the record built as a literal and every field read back; every field of the record returned by {} on 4 data sets (one compared value per field)"
    st.notes = {"Z975": "bits of the constant", "RocAssociation": note.format("roc_association (no label)"),
                "AssociationTable": note.format("association_table"), "_Pairs": note.format("_pairs")}
    return st


if __name__ == "__main__":
    assert not math.isnan(sc._TIE_EPS)
    suite_all().write()
    suite_types().write()
