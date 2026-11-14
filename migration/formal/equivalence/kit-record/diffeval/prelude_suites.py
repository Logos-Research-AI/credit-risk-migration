"""Part 2: differential test of every prelude primitive (RULEBOOK 2.3, 2.4, 6) against polars / numpy.

Written for the FROZEN preludes (RULEBOOK v3): scalar-zero rule in `+`/`-`, `Col.null` / `Pl.litNull`,
`Np.rint` odd. A recorded limit of the model (RULEBOOK section 6) is a case with `expect_diff`
(`lim(...)`): its `under_diagnosis` field is the value the prelude must return if the limit is the
WHOLE difference; explain.py checks it against what Lean returned.

  uv run python migration/diffeval/prelude_suites.py [suite ...]   -> work/<suite>.json + .inputs.json
Suites: ff int boolstr horiz aggsel agggrp frames ranknp logexp
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

import numpy as np
import polars as pl

import copy
import datetime as dt

import compare as cmp
import leanterm as lt
from dsl import *  # noqa: F403
from dsl import LETS, NONE, X, Col, cat, col, elist, frame, gb, gf, gi, gs, lit, lits, pairs
from suite import WORK, Suite

INF, NAN = math.inf, math.nan
EA = [None, 0.0, -0.0, 1.0, -1.0, 2.5, -2.5, INF, -INF, NAN, 1e308, 5e-324, 0.1]
EZ = [v for v in EA if not (v == 0.0 and math.copysign(1.0, v) < 0)]
EN = [None]
EM = [None, 0.0, -0.0, 1.0, 2.5]
EK = [None, 0.0, -0.0, NAN, 1.0, 2.5, INF]
SKIPPED: list[str] = []
RB6 = "RULEBOOK §6 recorded limit: "
NEG0 = 1 << 63
LN = X(pl.lit(None), "(Pl.litNull : Pl.Expr Float)")  # pl.lit(None) as an operand


def lim(note: str, under=None) -> dict:
    """Extra fields of a case that is a recorded limit: XFAIL while it differs. `under` = the
    canonical value the prelude returns if the limit is the whole difference (checked by explain.py)."""
    d = {"expect_diff": True, "note": RB6 + note}
    if under is not None:
        d["under_diagnosis"] = under
    return d


# ---- Python mirrors of the prelude rules behind the recorded limits (used only for `under_diagnosis`)
def as_f64(c: dict, keep=()) -> dict:
    """the same values in Float64 columns (the prelude's dtype where polars keeps an integer dtype)"""
    c = copy.deepcopy(c)
    for name, col_ in c["cols"]:
        if col_["kind"] in ("int", "bool") and name not in keep:
            col_["values"] = [None if v is None else cmp.fbits(float(v)) for v in col_["values"]]
            col_["kind"] = "f64"
    return c


def set_col(c: dict, name: str, vals: list, kind: str = "f64") -> dict:
    """the frame with column `name` replaced by the floats `vals`"""
    c = copy.deepcopy(c)
    for p in c["cols"]:
        if p[0] == name:
            p[1] = {"type": "col", "kind": kind, "values": [None if v is None else (cmp.fbits(v) if kind == "f64" else v) for v in vals]}
    return c


def stable_sorted(v):
    xs = [x for x in v if x is not None]
    return sorted([x for x in xs if not math.isnan(x)]) + [x for x in xs if math.isnan(x)]  # stable, -0.0 == 0.0, NaN last


def lean_median(v):  # Pl.median
    s = stable_sorted(v)
    n = len(s)
    if n == 0:
        return None
    if n % 2 == 1:
        return s[n // 2]
    a, b = s[n // 2 - 1], s[n // 2]
    return a if (a == b or (math.isnan(a) and math.isnan(b))) else 0.5 * (b - a) + a


def _fold(v, pick):
    xs = [x for x in v if x is not None]
    if not xs:
        return None
    acc = xs[0]
    for y in xs[1:]:
        acc = y if math.isnan(acc) else (acc if math.isnan(y) else pick(acc, y))
    return acc


def lean_min(v):  # Pl.aggMin: the first of equal values
    return _fold(v, lambda x, y: y if y < x else x)


def lean_max(v):  # Pl.aggMax
    return _fold(v, lambda x, y: y if x < y else x)


def lean_kahan(xs):
    s = c = 0.0
    for x in xs:
        y = x - c
        t = s + y
        ne = (t - s) - y
        c = ne if math.isfinite(ne) else c
        s = t
    return s


def lean_group_sum(has_nulls: bool, v):  # Pl.groupSum
    if not v:
        return 0.0
    if len(v) == 1:
        return 0.0 if v[0] is None else v[0]
    return lean_kahan([x for x in v if x is not None]) if has_nulls else lean_kahan([0.0 if x is None else x for x in v])


def ieee_plus_zero(c: dict) -> dict:
    """every -0.0 becomes +0.0 (IEEE addition of +0.0), a null becomes... stays as it is"""
    c = copy.deepcopy(c)
    for _, col_ in c["cols"]:
        if col_["kind"] == "f64":
            col_["values"] = [0 if v == NEG0 else v for v in col_["values"]]
    return c


# let-bound names for the sub-terms that the small dump cases repeat (keeps the eval_decl inputs short)
ABBREV = [("(Pl.litNull : Pl.Expr Float)", "N", "let N : Pl.Expr Float := Pl.litNull; "),
          ('((c "i").gt (Pl.litI 0))', "G", 'let G : Pl.Expr Float := (c "i").gt (Pl.litI 0); '),
          ("(Pl.litF (Float.ofBits 0))", "Z0", "let Z0 : Pl.Expr Float := Pl.litF (Float.ofBits 0); "),
          (f"(Pl.litF (Float.ofBits {NEG0}))", "NZ", f"let NZ : Pl.Expr Float := Pl.litF (Float.ofBits {NEG0}); ")]
CLET = "let c := fun (n : String) => Pl.col (α := Float) n; "


def small_lets(frames: dict) -> str:
    """`c`, the frames, the abbreviations and one `S<name> e = Pl.Frame.select <name> [("q", e)]` per frame"""
    return (CLET + "".join(lt.lean_frame_let(k, v) for k, v in frames.items()) + "".join(a[2] for a in ABBREV)
            + "".join(f'let S{k} := fun (e : Pl.Expr Float) => Pl.Frame.select {k} [("q", e)]; ' for k in frames))


def dump_chunks(s: Suite, lets: str, kind: str, cases: list, chunk: int = 200):
    """dump inputs of at most `chunk` cases (one term that does not elaborate loses only its chunk)"""
    cases = [c for c in cases if c is not None]

    def short(t: str) -> str:
        for old, new, _ in ABBREV:
            t = t.replace(old, new)
        return t

    for k in range(0, len(cases), chunk):
        s.dump(lets, kind, [(c[0], c[1], short(c[2]), *c[3:]) for c in cases[k:k + chunk]])


def sel(fv: str, df: pl.DataFrame, cid: str, prim: str, e: X, extra=None):
    """a dump case: df.select(q=e) / Pl.Frame.select fv [("q", e)]"""
    try:
        exp = cmp.canon_frame(df.select(q=e.py))
    except Exception as ex:
        SKIPPED.append(f"{cid}: python raised {type(ex).__name__}: {str(ex)[:80]}")
        return None
    if callable(extra):
        extra = extra(exp)
    return (cid, prim, f"S{fv} ({e.lean})", exp, extra or {})  # S<frame> e = Pl.Frame.select <frame> [("q", e)], see SMALL_LETS


ZN = ("zeros of opposite sign: polars returns -0.0 for min and +0.0 for max; no RealLike operation can tell the zeros apart "
      "(the prelude returns the first of the equal values)")
MDN = ("median with zeros of both signs: the prelude sorts stably (-0.0 and 0.0 keep their input order), polars does not; "
       "the sign of a zero median can differ; every other value equal")
DTN = "stated for Float64 inputs only (RULEBOOK 2.3): polars keeps an integer dtype, the prelude returns Float64; same values"


SEL = ("let S := fun (e : Pl.Expr Float) => dg (tR (Pl.Frame.select fr [e.pos])); "
       'let Q := fun (e : Pl.Expr Float) => dg (tR (Pl.Frame.select fr [("q", e)])); ')


def select_suite(name: str, lets: str, df: pl.DataFrame, cases: list[tuple]) -> Suite:
    """cases: (id, primitive, X[, named(bool)[, extra]]) evaluated as df.select(e) / fr.select [e.pos]"""
    s = Suite(name, carrier="cumsum")
    body, out = [], []
    for c in cases:
        cid, prim, e = c[0], c[1], c[2]
        named = len(c) > 3 and c[3]
        try:
            got = df.select(q=e.py) if named else df.select(e.py)
        except Exception as ex:
            SKIPPED.append(f"{name}/{cid}: python raised {type(ex).__name__}: {str(ex)[:80]}")
            continue
        body.append(f"{'Q' if named else 'S'} {e.lean}")
        exp = cmp.canon_frame(got)
        extra = c[4] if len(c) > 4 else {}
        out.append((cid, prim, exp, extra(exp) if callable(extra) else extra))
    s.digest_body(LETS + lets + SEL, "[" + ", ".join(body) + "]", out)
    return s


# ---------------------------------------------------------------------------------------------- ff
def suite_ff() -> Suite:
    pa, pb = pairs("a", "b", "f64", "EA", EA)
    n = len(EA) * len(EA) + 40
    lets_fr, df = frame("fr", [cat(pa, gf("a", 1, 40, 20, 3, "EA", EA)), cat(pb, gf("b", 2, 40, 20, 3, "EA", EA)),
                               gf("az", 12, n, 30, 3, "EZ", EZ),  # no negative zero
                               Col("z0", "f64", f"List.replicate {n} (some (Float.ofBits 0))", [0.0] * n)])
    a, b, az, z0 = col("a"), col("b"), col("az"), col("z0")
    av = df.get_column("a").to_list()

    def abs_model(exp):  # RealLike.abs keeps the sign of a zero
        return set_col(exp, "a", [-0.0 if (x is not None and cmp.fbits(x) == NEG0) else cmp_from(v) for x, v in
                                  zip(av, exp["cols"][0][1]["values"], strict=True)])

    C = [
        ("add", "add", add(a, b)), ("sub", "sub", sub(a, b)), ("mul", "mul", mul(a, b)), ("div", "div", div(a, b)),
        ("neg", "neg", neg(a)),
        ("add_f", "add", add(a, 0.5)), ("mul_i", "mul", mul(a, 2)), ("rsub_i", "sub", sub(1, a)), ("rdiv_i", "div", div(2, a)),
        ("div_0i", "div", div(a, 0)), ("div_0f", "div", div(a, 0.0)), ("mul_f", "mul", mul(a, 0.1)),
        # scalar-zero rule of addCol / subCol (RULEBOOK 2.3: `e + 0.0` is an ordinary add): a column with -0.0, 209 rows
        ("add0", "add(scalar zero)", add(a, 0.0)), ("radd0", "add(scalar zero)", add(0.0, a)), ("add0i", "add(scalar zero)", add(a, 0)),
        ("add0_expr", "add(scalar zero)", add(mul(a, b), 0.0)), ("add_neg0", "add(scalar zero)", add(a, -0.0)),
        ("add_agg0", "add(scalar zero)", add(a, sum_(z0))), ("radd_agg0", "add(scalar zero)", add(sum_(z0), a)),
        ("add_col0", "add", add(a, z0)),  # a full column of zeros: IEEE on both sides
        ("sub0", "sub(scalar zero)", sub(a, 0.0)), ("rsub0", "sub(scalar zero)", sub(0.0, a)), ("sub_neg0", "sub(scalar zero)", sub(a, -0.0)),
        ("rsub0i", "sub(scalar zero)", sub(0, a)), ("sub_agg0", "sub(scalar zero)", sub(a, sum_(z0))),
        ("rsub_agg0", "sub(scalar zero)", sub(sum_(z0), a)), ("sub_col0", "sub", sub(a, z0)),
        ("mul1", "mul", mul(a, 1.0)), ("div1", "div", div(a, 1.0)),
        ("lt", "lt", lt_(a, b)), ("le", "le", le(a, b)), ("gt", "gt", gt(a, b)), ("ge", "ge", ge(a, b)),
        ("eq", "eq", eq(a, b)), ("ne", "ne", ne(a, b)),
        ("gt_0i", "gt", gt(a, 0)), ("ge_f", "ge", ge(a, 0.5)), ("eq_0i", "eq", eq(a, 0)), ("ne_1i", "ne", ne(a, 1)),
        ("lt_f", "lt", lt_(a, 2.5)), ("le_i", "le", le(a, 1)), ("eq_self", "eq", eq(a, a)),
        ("isNull", "isNull", isNull(a)), ("isNotNull", "isNotNull", isNotNull(a)),
        ("fillNull_f", "fillNull", fillNull(a, 0.5)), ("fillNull_col", "fillNull", fillNull(a, b)),
        ("abs", "abs", abs_(az)),
        ("abs_negzero", "abs(-0.0)", abs_(a), False, lambda exp: lim(
            "polars abs(-0.0) is 0.0; RealLike.abs cannot clear the sign of a zero (the prelude returns -0.0); every other value equal",
            abs_model(exp))),
        ("floor", "floor", floor(a)), ("sign", "sign", sign(a)), ("isFinite", "isFinite", isFinite(a)),
        ("castF64", "castF64", castF64(a)),
        ("wto", "wto", wto(gt(a, b), a, b)), ("wto_null_lit", "wto", wto(isNull(a), 1.5, b)),
        ("wto_no_otherwise", "wto", wto(gt(a, 0), a)), ("wto_then_none", "wto", wto(gt(a, 0), NONE, b)),
        ("wto_chain", "wto", wchain([(gt(a, b), a), (isNull(a), 1.5)], b)),
        ("wto_chain3", "wto", wchain([(gt(a, b), a), (isNull(a), 1.5), (lt_(b, 0), 0.25)], b)),
        ("wto_int_lits", "wto", wto(lt_(a, b), 1, 0)), ("wto_int_float_lits", "wto", wto(lt_(a, b), 1, 0.5)),
        ("wto_int_no_otherwise", "wto(litNull branch)", wto(lt_(a, b), 1)),
        ("sumH2_T", "sumHorizontal", sumH(True, [a, b])), ("sumH2_F", "sumHorizontal", sumH(False, [a, b])),
        ("isInF", "isInF", isInF(a, [1.0, NAN, None, 0.0])), ("isInF_1", "isInF", isInF(a, [2.5])),
        ("mapB_div", "mapBatches2", sdiv(a, b), True), ("mapB_div_i", "mapBatches2", sdiv(a, 2), True),
        ("mapB_rdiv_i", "mapBatches2", sdiv(1, a), True), ("mapB_div_0", "mapBatches2", sdiv(a, 0), True),
        ("mapB_div_f", "mapBatches2", sdiv(a, 0.1), True),
        ("filter", "filter", filter_(a, gt(b, 0))), ("filter_null_pred", "filter", filter_(a, lt_(b, a))),
    ]
    s = select_suite("ff", elist("EA", "f64", EA) + elist("EZ", "f64", EZ) + lets_fr, df, C)
    _ff_small(s)
    return s


def cmp_from(bits_: int | None):
    return None if bits_ is None else lt.from_bits(bits_)


def _ff_small(s: Suite):
    """minimal inputs in dump mode (the whole value comes back): Pl.litNull / Col.null, the scalar-zero rule on
    1-row and 0-row frames, on two length-1 operands and on Int64 operands, recorded limits of `+` and sum_horizontal"""
    d = pl.DataFrame({"a": [-0.0, 0.0, -1.5, None, NAN], "i": [-2, 0, 3, None, 1], "p": [True, False, None, True, False],
                      "s": ["A", None, "B", "A", ""], "z": [0.0] * 5},
                     schema={"a": pl.Float64, "i": pl.Int64, "p": pl.Boolean, "s": pl.String, "z": pl.Float64})
    d1 = pl.DataFrame({"a": [-0.0], "i": [0]}, schema={"a": pl.Float64, "i": pl.Int64})
    d0 = d1.head(0)
    lets = small_lets({"d": d, "d1": d1, "d0": d0})
    a, i, p, st, z = (col(k) for k in "aipsz")
    c = gt(i, 0)
    W = "wto(litNull branch)"
    both = wto(c, NONE, NONE)
    C = [
        # ---- Pl.litNull in when/then/otherwise: the Null branch takes the dtype of the other branch
        sel("d", d, "wn_int_then", W, wto(c, 1, NONE)), sel("d", d, "wn_int_else", W, wto(c, NONE, 1)),
        sel("d", d, "wn_int_missing", W, wto(c, 1)), sel("d", d, "wn_icol_else", W, wto(c, NONE, i)),
        sel("d", d, "wn_icol_then", W, wto(c, i, NONE)),
        sel("d", d, "wn_str_then", W, wto(c, "x", NONE)), sel("d", d, "wn_str_else", W, wto(c, NONE, "y")),
        sel("d", d, "wn_str_missing", W, wto(c, "x")), sel("d", d, "wn_scol_else", W, wto(c, NONE, st)),
        sel("d", d, "wn_scol_then", W, wto(c, st, NONE)),
        sel("d", d, "wn_bool_then", W, wto(c, True, NONE)), sel("d", d, "wn_bool_else", W, wto(c, NONE, False)),
        sel("d", d, "wn_pcol_else", W, wto(c, NONE, p)), sel("d", d, "wn_pcol_missing", W, wto(c, p)),
        sel("d", d, "wn_f_then", W, wto(c, 1.5, NONE)), sel("d", d, "wn_f_else", W, wto(c, NONE, 1.5)),
        sel("d", d, "wn_acol_else", W, wto(c, NONE, a)), sel("d", d, "wn_acol_then", W, wto(c, a, NONE)),
        sel("d", d, "wn_both", W, both), sel("d", d, "wn_none_missing", W, wto(c, NONE)),
        sel("d", d, "wn_litcond_both", W, wto(lit(True), NONE, NONE)),
        sel("d", d, "wn_chain_int", W, wchain([(c, 1), (lt_(i, 0), NONE)], NONE)),
        sel("d", d, "wn_chain_f", W, wchain([(c, NONE), (lt_(i, 0), NONE)], 2.5)),
        sel("d", d, "wn_chain_str", W, wchain([(c, NONE), (lt_(i, 0), "neg")], NONE)),
        sel("d1", d1, "wn_1row_int", W, wto(gt(i, 0), 1, NONE)), sel("d1", d1, "wn_1row_both", W, wto(gt(i, 0), NONE, NONE)),
        sel("d0", d0, "wn_0row_int", W, wto(gt(i, 0), 1, NONE)),
        # ---- Col.null through the other primitives
        sel("d", d, "litNull", "litNull", LN),
        sel("d", d, "null_isNull", "isNull(Col.null)", isNull(LN)), sel("d", d, "null_isNotNull", "isNotNull(Col.null)", isNotNull(LN)),
        sel("d", d, "nullcol_isNull", "isNull(Col.null)", isNull(both)), sel("d", d, "nullcol_isNotNull", "isNotNull(Col.null)", isNotNull(both)),
        sel("d", d, "null_fill_f", "fillNull(Col.null)", fillNull(LN, 0.5)), sel("d", d, "nullcol_fill_f", "fillNull(Col.null)", fillNull(both, 0.5)),
        sel("d", d, "null_fill_acol", "fillNull(Col.null)", fillNull(LN, a)), sel("d", d, "a_fill_null", "fillNull(Col.null)", fillNull(a, LN)),
        sel("d", d, "nullcol_fill_acol", "fillNull(Col.null)", fillNull(both, a)),
        sel("d", d, "null_fill_i", "fillNull(Col.null, non-Float64)", fillNull(LN, 1)),
        sel("d", d, "null_fill_s", "fillNull(Col.null, non-Float64)", fillNull(LN, "x")),
        sel("d", d, "null_fill_b", "fillNull(Col.null, non-Float64)", fillNull(LN, True)),
        sel("d", d, "nullcol_fill_icol", "fillNull(Col.null, non-Float64)", fillNull(both, i)),
        sel("d", d, "i_fill_null", "fillNull(Col.null, non-Float64)", fillNull(i, LN)),
        sel("d", d, "s_fill_null", "fillNull(Col.null, non-Float64)", fillNull(st, LN)),
        sel("d", d, "p_fill_null", "fillNull(Col.null, non-Float64)", fillNull(p, LN)),
        sel("d", d, "a_add_null", "add(Col.null operand)", add(a, LN)), sel("d", d, "null_add_a", "add(Col.null operand)", add(LN, a)),
        sel("d", d, "nullcol_add_a", "add(Col.null operand)", add(both, a)),
        sel("d", d, "a_sub_null", "sub(Col.null operand)", sub(a, LN)), sel("d", d, "null_sub_a", "sub(Col.null operand)", sub(LN, a)),
        sel("d", d, "a_mul_null", "mul(Col.null operand)", mul(a, LN)), sel("d", d, "a_div_null", "div(Col.null operand)", div(a, LN)),
        sel("d", d, "i_div_null", "div(Col.null operand)", div(i, LN)),
        sel("d", d, "i_add_null", "add(Col.null operand, Int64 / Null other operand)", add(i, LN)),
        sel("d", d, "i_mul_null", "mul(Col.null operand, Int64 / Null other operand)", mul(i, LN)),
        sel("d", d, "null_add_null", "add(Col.null operand, Int64 / Null other operand)", add(LN, LN)),
        sel("d", d, "a_gt_null", "comparison(Col.null operand)", gt(a, LN)), sel("d", d, "a_eq_null", "comparison(Col.null operand)", eq(a, LN)),
        sel("d", d, "i_eq_null", "comparison(Col.null operand)", eq(i, LN)), sel("d", d, "null_lt_i", "comparison(Col.null operand)", lt_(LN, i)),
        sel("d", d, "s_eq_null", "comparison(Col.null operand, String)", eq(st, LN)),
        sel("d", d, "p_and_null", "and/or(Col.null operand)", and_(p, LN)), sel("d", d, "p_or_null", "and/or(Col.null operand)", or_(p, LN)),
        sel("d", d, "null_castF64", "castF64(Col.null)", castF64(LN)), sel("d", d, "nullcol_castF64", "castF64(Col.null)", castF64(both)),
        sel("d", d, "null_castI64", "castI64(Col.null)", castI64(LN)),
        sel("d", d, "null_count", "count(Col.null)", count(both)), sel("d", d, "null_sum", "sum(Col.null)", sum_(both)),
        sel("d", d, "null_mean", "mean(Col.null)", mean(both)),
        # ---- scalar-zero rule: 5 rows (a has -0.0), Int64 operands
        sel("d", d, "z5_add0", "add(scalar zero)", add(a, 0.0)), sel("d", d, "z5_radd0", "add(scalar zero)", add(0.0, a)),
        sel("d", d, "z5_rsub0", "sub(scalar zero)", sub(0.0, a)), sel("d", d, "z5_sub_neg0", "sub(scalar zero)", sub(a, -0.0)),
        sel("d", d, "z5_add_agg0", "add(scalar zero)", add(a, sum_(z))), sel("d", d, "z5_rsub_agg0", "sub(scalar zero)", sub(sum_(z), a)),
        sel("d", d, "zi_add0", "add(scalar zero, Int64 operand)", add(i, 0)), sel("d", d, "zi_radd0", "add(scalar zero, Int64 operand)", add(0, i)),
        sel("d", d, "zi_add0f", "add(scalar zero, Int64 operand)", add(i, 0.0)), sel("d", d, "zi_radd0f", "add(scalar zero, Int64 operand)", add(0.0, i)),
        sel("d", d, "zi_sub0", "sub(scalar zero, Int64 operand)", sub(i, 0)), sel("d", d, "zi_rsub0", "sub(scalar zero, Int64 operand)", sub(0, i)),
        sel("d", d, "zi_sub0f", "sub(scalar zero, Int64 operand)", sub(i, 0.0)), sel("d", d, "zi_rsub0f", "sub(scalar zero, Int64 operand)", sub(0.0, i)),
        sel("d", d, "zp_add0f", "add(scalar zero, Boolean operand)", add(p, 0.0)),
        # ---- 1-row frames (polars adds: -0.0 + 0.0 = +0.0) and 0-row frames
        sel("d1", d1, "z1_add0", "add(scalar zero, 1-row frame)", add(a, 0.0)), sel("d1", d1, "z1_radd0", "add(scalar zero, 1-row frame)", add(0.0, a)),
        sel("d1", d1, "z1_add0i", "add(scalar zero, 1-row frame)", add(a, 0)), sel("d1", d1, "z1_add_neg0", "add(scalar zero, 1-row frame)", add(a, -0.0)),
        sel("d1", d1, "z1_add_agg", "add(scalar zero, 1-row frame)", add(a, sum_(a))),
        sel("d1", d1, "z1_i_add0f", "add(scalar zero, 1-row frame)", add(i, 0.0)), sel("d1", d1, "z1_i_add0", "add(scalar zero, 1-row frame)", add(i, 0)),
        sel("d1", d1, "z1_sub0", "sub(scalar zero, 1-row frame)", sub(a, 0.0)), sel("d1", d1, "z1_rsub0", "sub(scalar zero, 1-row frame)", sub(0.0, a)),
        sel("d1", d1, "z1_sub_neg0", "sub(scalar zero, 1-row frame)", sub(a, -0.0)),
        sel("d1", d1, "z1_i_rsub0f", "sub(scalar zero, 1-row frame)", sub(0.0, i)), sel("d1", d1, "z1_i_rsub0", "sub(scalar zero, 1-row frame)", sub(0, i)),
        sel("d0", d0, "z0_add0", "add(scalar zero, 0-row frame)", add(a, 0.0)), sel("d0", d0, "z0_i_add0", "add(scalar zero, 0-row frame)", add(i, 0)),
        sel("d0", d0, "z0_rsub0", "sub(scalar zero, 0-row frame)", sub(0.0, a)),
        # ---- two length-1 operands: IEEE
        sel("d", d, "zz_add", "add(two length-1 operands)", add(lit(-0.0), lit(0.0))), sel("d", d, "zz_add_nn", "add(two length-1 operands)", add(lit(-0.0), lit(-0.0))),
        sel("d", d, "zz_add_agg", "add(two length-1 operands)", add(sum_(z), lit(-0.0))), sel("d", d, "zz_add_aggs", "add(two length-1 operands)", add(sum_(z), sum_(z))),
        sel("d", d, "zz_add_bare", "add(two length-1 operands)", add(lit(-0.0), 0.0)),
        sel("d", d, "zz_sub", "sub(two length-1 operands)", sub(lit(-0.0), lit(0.0))), sel("d", d, "zz_sub_zz", "sub(two length-1 operands)", sub(lit(0.0), lit(0.0))),
        sel("d", d, "zz_sub_zn", "sub(two length-1 operands)", sub(lit(0.0), lit(-0.0))), sel("d", d, "zz_sub_agg", "sub(two length-1 operands)", sub(lit(0.0), sum_(z))),
        sel("d", d, "zz_sub_bare", "sub(two length-1 operands)", sub(0.0, lit(0.0))),
        # ---- recorded limits
        (lambda e: ("add_litcol0", "add(frame column kept as scalar)",
                    'Pl.Frame.select (Pl.Frame.withColumns d [("w", (Pl.litF (Float.ofBits 0)))]) [("q", (c "a").add (c "w"))]', e,
                    lim("a column made by with_columns(w=pl.lit(0.0)) is kept by polars as a scalar (`a + w` leaves -0.0); "
                        "in the model it is a column of zeros (IEEE: +0.0)", ieee_plus_zero(e))))(
            cmp.canon_frame(d.with_columns(w=pl.lit(0.0)).select(q=pl.col("a") + pl.col("w")))),
    ]
    SH = "sumHorizontal(literal zero / null-literal operand)"
    shn = "a literal zero or null-literal operand of sum_horizontal: polars leaves the column unchanged (-0.0 stays), the model adds 0.0 (+0.0)"
    for cid, es in (("sumh_lit0_a", [lit(0.0), a]), ("sumh_a_lit0", [a, lit(0.0)]), ("sumh_a_null", [a, LN]), ("sumh_null_a", [LN, a]),
                    ("sumh_a_a_lit0", [a, a, lit(0.0)])):
        C.append(sel("d", d, cid, SH, sumH(True, es), lambda e: lim(shn, ieee_plus_zero(e))))
    dump_chunks(s, lets, "frame", C)


# ---------------------------------------------------------------------------------------------- int
def suite_int() -> Suite:
    IE = [None, 0, 1, -1, 7, -3, 2]
    pi, pj = pairs("i", "j", "int", "IE", IE)
    lets_fr, df = frame("fr", [cat(pi, gi("i", 3, 30, 15, 9, 4)), cat(pj, gi("j", 4, 30, 15, 9, 4)), gf("x", 5, 79, 25, 3, "EA", EA)])
    i, j, x = col("i"), col("j"), col("x")
    DT = lambda exp: lim(DTN, as_f64(exp))  # noqa: E731
    C = [
        ("add", "add", add(i, j)), ("sub", "sub", sub(i, j)), ("mul", "mul", mul(i, j)), ("div", "div", div(i, j)), ("neg", "neg", neg(i)),
        ("lt", "lt", lt_(i, j)), ("le", "le", le(i, j)), ("gt", "gt", gt(i, j)), ("ge", "ge", ge(i, j)), ("eq", "eq", eq(i, j)), ("ne", "ne", ne(i, j)),
        ("add_i", "add", add(i, 1)), ("mul_i", "mul", mul(i, 2)), ("mul_f", "mul", mul(i, 0.5)), ("add_f", "add", add(i, 0.5)),
        ("div_i", "div", div(i, 2)), ("rsub_i", "sub", sub(10, i)), ("gt_i", "gt", gt(i, 0)), ("eq_i", "eq", eq(i, 1)),
        ("ge_f", "ge", ge(i, 0.5)), ("eq_f", "eq", eq(i, 1.0)), ("lt_f", "lt", lt_(i, 0.5)),
        ("add_x", "add", add(i, x)), ("rsub_x", "sub", sub(x, i)), ("mul_x", "mul", mul(i, x)), ("div_x", "div", div(i, x)),
        ("lt_x", "lt", lt_(i, x)), ("eq_x", "eq", eq(i, x)), ("ge_x", "ge", ge(x, i)), ("ne_x", "ne", ne(i, x)),
        ("castF64", "castF64", castF64(i)), ("castI64", "castI64", castI64(i)),
        ("abs", "abs(Int64 input)", abs_(i), False, DT), ("floor", "floor(Int64 input)", floor(i), False, DT),
        ("sign", "sign(Int64 input)", sign(i), False, DT),
        ("isFinite", "isFinite", isFinite(i)), ("isNull", "isNull", isNull(i)),
        ("fillNull_i", "fillNull", fillNull(i, 0)), ("fillNull_col", "fillNull", fillNull(i, j)),
        ("wto_int_lits", "wto", wto(gt(i, 0), 1, 0)), ("wto_int_float", "wto", wto(gt(i, 0), 1, 0.5)),
        ("wto_cols", "wto", wto(gt(i, 0), i, x)), ("wto_int_cols", "wto", wto(gt(i, j), i, j)),
        ("wto_int_no_otherwise", "wto(litNull branch)", wto(gt(i, 0), 1)),
        ("wto_intcol_no_otherwise", "wto(litNull branch)", wto(gt(i, 0), i)),
        ("wto_f_no_otherwise", "wto", wto(gt(i, 0), x)), ("wto_then_none", "wto", wto(gt(i, 0), NONE, x)),
        ("wto_then_none_int", "wto(litNull branch)", wto(gt(i, 0), NONE, i)),
        ("sumH_int", "sumHorizontal(Int64 input)", sumH(True, [i, j]), False, DT),
        ("mapB_div", "mapBatches2", sdiv(i, j), True), ("mapB_div_i", "mapBatches2", sdiv(i, 2), True),
        ("mapB_div_x", "mapBatches2", sdiv(x, i), True),
        ("cumSum", "cumSum", cumSum(i)), ("cumSum_x", "cumSum", cumSum(x)),
    ]
    return select_suite("int", elist("IE", "int", IE) + elist("EA", "f64", EA) + lets_fr, df, C)


# ---------------------------------------------------------------------------------------------- boolstr
def suite_boolstr() -> Suite:
    BE = [None, True, False]
    SL = ["A", "B", "", "a", "é", "AB"]
    pp, pq = pairs("p", "q", "bool", "BE", BE)
    lets_fr, df = frame("fr", [cat(pp, gb("p", 6, 30, 20)), cat(pq, gb("q", 7, 30, 20)), gb("r", 8, 39, 20),
                               gs("s", 9, 39, 15, SL), gs("t", 10, 39, 15, SL), gf("x", 11, 39, 20, 3, "EA", EA)])
    p, q, r, s, t, x = (col(n) for n in "pqrstx")
    C = [
        ("and", "and", and_(p, q)), ("or", "or", or_(p, q)), ("not", "not", not_(p)),
        ("and_lit", "and", and_(p, True)), ("or_lit", "or", or_(p, False)),
        ("fillNull_F", "fillNull", fillNull(p, False)), ("fillNull_T", "fillNull", fillNull(p, True)),
        ("castI64", "castI64", castI64(p)), ("castF64", "castF64", castF64(p)),
        ("eq_bool", "eq(Boolean operands)", eq(p, q)), ("ne_bool", "ne(Boolean operands)", ne(p, q)),
        ("allH1", "allHorizontal", allH([p])), ("allH2", "allHorizontal", allH([p, q])), ("allH3", "allHorizontal", allH([p, q, r])),
        ("allH4", "allHorizontal", allH([p, q, r, not_(p)])), ("allH_isnull", "allHorizontal", allH([isNull(x), isNull(p), isNull(s)])),
        ("wto_lits", "wto", wto(p, 1.0, 2.0)), ("wto_col_lit", "wto", wto(p, x, 0.5)),
        ("wto_chain", "wto", wchain([(p, x), (q, 1.5)], 2.5)), ("wto_bool_branches", "wto", wto(p, q, r)),
        ("wto_bool_lits", "wto", wto(p, True, False)),
        ("isNull", "isNull", isNull(p)), ("and_isnull", "and", and_(isNull(x), p)), ("not_isnull", "not", not_(isNull(x))),
        ("eq_lit", "eq", eq(s, "A")), ("ne_lit", "ne", ne(s, "A")), ("eq_col", "eq", eq(s, t)), ("ne_col", "ne", ne(s, t)),
        ("lt_col", "lt", lt_(s, t)), ("le_col", "le", le(s, t)), ("gt_lit", "gt", gt(s, "A")), ("ge_col", "ge", ge(s, t)),
        ("isInS", "isInS", isInS(s, ["A", "B"])), ("isInS_1", "isInS", isInS(s, ["é"])),
        ("fillNull_s", "fillNull", fillNull(s, "Z")), ("isNull_s", "isNull", isNull(s)),
        ("wto_str", "wto", wto(eq(s, "A"), "x", s)), ("wto_str_lits", "wto", wto(eq(s, "A"), "x", "y")),
        ("wto_str_no_otherwise", "wto(litNull branch)", wto(isNull(s), "n")),
        ("wto_str_then_none", "wto(litNull branch)", wto(isNull(s), NONE, s)), ("wto_bool_no_otherwise", "wto(litNull branch)", wto(p, q)),
        ("wto_bool_then_none", "wto(litNull branch)", wto(p, NONE, True)),
        ("count_s", "count", count(s)), ("count_p", "count", count(p)),
    ]
    lets = elist("BE", "bool", BE) + elist("EA", "f64", EA) + 'let SL := ["A", "B", "", "a", "é", "AB"]; ' + lets_fr
    return select_suite("boolstr", lets, df, C)


# ---------------------------------------------------------------------------------------------- horiz
def _horiz(full: bool):
    cols = [gf(f"h{k}", 20 + k, 150, 30, 2, "EZ", EZ) for k in range(6)] + [gf(f"g{k}", 30 + k, 150, 8, 2, "EN", EN) for k in range(6)]
    cols += [gf("za", 40, 150, 100, 2, "EZZ", [0.0, -0.0]), gf("zb", 41, 150, 100, 2, "EZZ", [0.0, -0.0]),
             gf("nz", 42, 150, 100, 2, "ENZ", [None, -0.0])]
    lets_fr, df = frame("fr", cols)
    lets = elist("EZ", "f64", EZ) + elist("EN", "f64", EN) + elist("EZZ", "f64", [0.0, -0.0]) + elist("ENZ", "f64", [None, -0.0]) + lets_fr
    tag = "T" if full else "F"
    C = []
    for nm, fn, prim in (("sum", sumH, "sumHorizontal"), ("min", minH, "minHorizontal"), ("max", maxH, "maxHorizontal")):
        for st in "hg":
            for n in range(2, 7):
                C.append((f"{nm}_{st}{n}_{tag}", f"{prim}(full={str(full).lower()})", fn(full, [col(f"{st}{k}") for k in range(n)])))
    za, zb, nz = col("za"), col("zb"), col("nz")
    C += [(f"sum_negzero_null_{tag}", f"sumHorizontal(full={str(full).lower()})", sumH(full, [za, nz])),
          (f"sum_negzero_null3_{tag}", f"sumHorizontal(full={str(full).lower()})", sumH(full, [nz, za, nz]))]
    if full:
        zav = df.get_column("za").to_list()
        # minIgnoreNan / maxIgnoreNan return the first operand when the two compare equal
        hl = lambda exp: lim(ZN, set_col(exp, "za", zav))  # noqa: E731
        C += [("min_signed_zero", "minHorizontal(zeros of opposite sign)", minH(True, [za, zb]), False, hl),
              ("max_signed_zero", "maxHorizontal(zeros of opposite sign)", maxH(True, [za, zb]), False, hl)]
    return lets, df, C


def _horiz_expected(full: bool) -> dict:
    _, df, C = _horiz(full)
    return {c[0]: cmp.canon_frame(df.select(c[2].py)) for c in C}


def suite_horiz() -> Suite:
    lets, df, CT = _horiz(True)
    _, _, CF = _horiz(False)

    def other(threads: int, full: bool) -> dict:
        env = dict(os.environ, POLARS_MAX_THREADS=str(threads))
        r = subprocess.run([sys.executable, __file__, "--hexp", "1" if full else "0"], env=env, capture_output=True, text=True, check=True)
        return json.loads(r.stdout)

    exp_f = other(1, False)  # full = false is the behaviour with POLARS_MAX_THREADS=1
    s = Suite("horiz", carrier="cumsum")
    # the 30 regular cases of each `full` are enumerated in Lean in the order of _horiz: fn, column set, N
    hh = ("let HS := fun (st : String) (n : Nat) => (List.range n).map (fun (k : Nat) => c (st ++ toString k)); "
          "let HH := fun (full : Bool) => ([Pl.sumHorizontal full, Pl.minHorizontal full, Pl.maxHorizontal full] : "
          "List (List (Pl.Expr Float) → Pl.Expr Float)).flatMap (fun (f : List (Pl.Expr Float) → Pl.Expr Float) => "
          "[\"h\", \"g\"].flatMap (fun (st : String) => [2, 3, 4, 5, 6].map (fun (n : Nat) => S (f (HS st n))))); ")
    body = ("HH true ++ [" + ", ".join(f"S {c[2].lean}" for c in CT[30:]) + "] ++ HH false ++ ["
            + ", ".join(f"S {c[2].lean}" for c in CF[30:]) + "]")
    out = []
    for c in CT:
        exp = cmp.canon_frame(df.select(c[2].py))
        extra = c[4] if len(c) > 4 else {}
        out.append((c[0], c[1], exp, extra(exp) if callable(extra) else extra))
    out += [(c[0], c[1], exp_f[c[0]], {}) for c in CF]
    s.digest_body(LETS + lets + SEL + hh, body, out)
    # python-only: thread counts 2, 3, 4 give the same results as this process (pool size below)
    mine = {c[0]: cmp.canon_frame(df.select(c[2].py)) for c in CT}
    notes = {"pool_size_here": pl.thread_pool_size()}
    for th in (2, 3, 4):
        o = other(th, True)
        notes[f"threads={th} differs from here in"] = [k for k in mine if o[k] != mine[k]]
    one = other(1, True)
    notes["threads=1 differs from here in"] = [k for k in mine if one[k] != mine[k]]
    (WORK / "horiz_threads.json").write_text(json.dumps(notes, indent=1))
    return s


# ---------------------------------------------------------------------------------------------- aggsel
AGG = [("sum", "fs", "sum"), ("mean", "fm", "mean"), ("min", "fn", "min"), ("max", "fx", "max"), ("median", "fd", "median"),
       ("count", "fc", "count")]
FLETS = "".join(f"let {v} := fun (e : Pl.Expr Float) => e.{m}; " for _, v, m in AGG) + "let fq := fun (e : Pl.Expr Float) => e.cumSum; "
K6, K4, K5 = ["x", "y", "z", "m", "i", "n"], ["x", "y", "z", "n"], ["x", "y", "z", "i", "n"]  # K5: no zeros of both signs
KLETS = 'let K6 := ["x", "y", "z", "m", "i", "n"]; let K4 := ["x", "y", "z", "n"]; let K5 := ["x", "y", "z", "i", "n"]; '


def _pyagg(name: str, k: str) -> pl.Expr:
    return getattr(pl.col(k), {"cumSum": "cum_sum"}.get(name, name))()


def suite_aggsel() -> Suite:
    L = 1300
    LENS = [0, 1, 2, 3, 7, 8, 15, 16, 17, 127, 128, 129, 130, 255, 256, 257, 300, 301, 383, 384, 385, 512, 640, 1000, 1300]
    X_, Y, Z, M = gf("x", 50, L, 12, 3, "EN", EN), gf("y", 51, L, 0, 3), gf("z", 52, L, 35, 2, "EZ", EZ), gf("m", 53, L, 50, 2, "EM", EM)
    I, B = gi("i", 54, L, 10, 50, 20), gb("b", 55, L, 10)
    df = pl.DataFrame([c.series() for c in (X_, Y, Z, M, I)] + [pl.Series("n", [None] * L, dtype=pl.Float64), B.series()])
    lets = (elist("EN", "f64", EN) + elist("EZ", "f64", EZ) + elist("EM", "f64", EM)
            + f"let X := {X_.lean}; let Y := {Y.lean}; let Z := {Z.lean}; let M := {M.lean}; let I := {I.lean}; let B := {B.lean}; "
            + 'let F := fun (n : Nat) => ([("x", .f64 (X.take n)), ("y", .f64 (Y.take n)), ("z", .f64 (Z.take n)), ("m", .f64 (M.take n)), '
              '("i", .int (I.take n)), ("n", .f64 (List.replicate n none)), ("b", .bool (B.take n))] : Pl.Frame Float); '
            + KLETS + FLETS
            + "let A := fun (n : Nat) (ks : List String) (f : Pl.Expr Float → Pl.Expr Float) (ex : List (String × Pl.Expr Float)) => "
              "dg (tR (Pl.Frame.select (F n) (ks.map (fun (k : String) => (f (c k)).pos) ++ ex))); ")
    body = ("(" + lt.lean_list([str(n) for n in LENS], "List Nat") + ".flatMap (fun (n : Nat) => [A n K6 fs [], A n K6 fm [], A n K4 fn [], "
            'A n K4 fx [], A n K5 fd [], A n ["m"] fd [], A n K6 fc [Pl.len.pos]]))')
    out = []
    mv = df.get_column("m").to_list()
    for n in LENS:
        d = df.head(n)
        for name, _, _ in AGG:
            ks = K4 if name in ("min", "max") else (K5 if name == "median" else K6)
            ex = [pl.len()] if name == "count" else []
            out.append((f"{name}_n{n}", name if name != "count" else "count,len", cmp.canon_frame(d.select([_pyagg(name, k) for k in ks] + ex))))
            if name == "median":  # the column with zeros of both signs, apart
                e = cmp.canon_frame(d.select(pl.col("m").median()))
                out.append((f"median_m_n{n}", "median(zeros of both signs)", e, lim(MDN, set_col(e, "m", [lean_median(mv[:n])]))))
    extra = []

    def add_case(cid, prim, lean, pyexprs, n=300, model=None, note=None, **kw):
        extra.append(lean)
        d = df.head(n)
        e = cmp.canon_frame(d.select(**pyexprs) if isinstance(pyexprs, dict) else d.select(pyexprs))
        out.append((cid, prim, e, lim(note, model(e)) if model else kw))

    for n in (0, 1, 5, 300):
        add_case(f"cumSum_n{n}", "cumSum", f'A {n} ["x", "z", "m", "i"] fq []', [pl.col(k).cum_sum() for k in "xzmi"], n)
    add_case("sum_bool", "sum(Boolean input)", 'A 300 ["b"] fs []', [pl.col("b").sum()], model=as_f64,
             note="Boolean input of sum: polars returns an integer dtype, the prelude Float64; same value")
    add_case("mean_bool", "mean(Boolean input)", 'A 300 ["b"] fm []', [pl.col("b").mean()])
    add_case("min_int", "min(Int64 input)", 'A 300 ["i"] fn []', [pl.col("i").min()], model=as_f64, note=DTN)
    add_case("max_int", "max(Int64 input)", 'A 300 ["i"] fx []', [pl.col("i").max()], model=as_f64, note=DTN)
    add_case("min_signed_zero", "min(zeros of opposite sign)", 'A 300 ["m"] fn []', [pl.col("m").min()],
             model=lambda e: set_col(e, "m", [lean_min(mv[:300])]), note=ZN)
    add_case("max_signed_zero", "max(zeros of opposite sign)", 'A 300 ["m"] fx []', [pl.col("m").max()],
             model=lambda e: set_col(e, "m", [lean_max(mv[:300])]), note=ZN)
    pred_l, pred_p = '((c "y").gt (Pl.litF (Float.ofBits 0)))', pl.col("y") > 0.0
    for nm in ("sum", "mean", "count", "min", "median"):
        add_case(f"filter_{nm}", "filter", f'A 300 ["x", "z"] (fun (e : Pl.Expr Float) => (e.filter {pred_l}).{nm}) []',
                 [getattr(pl.col(k).filter(pred_p), nm)() for k in "xz"])
    add_case("filter_plain", "filter", f'A 300 ["x", "z", "i"] (fun (e : Pl.Expr Float) => e.filter {pred_l}) []',
             [pl.col(k).filter(pred_p) for k in "xzi"])
    add_case("sum_expr", "sum", 'A 300 [] fs [("p", ((c "x").mul (c "y")).sum), ("d", ((c "x").sum).div Pl.len)]',
             {"p": (pl.col("x") * pl.col("y")).sum(), "d": pl.col("x").sum() / pl.len()})
    s = Suite("aggsel", carrier="cumsum")
    s.digest_body(LETS + lets, body + " ++ [" + ", ".join(extra) + "]", out)
    # minimal inputs (dump mode): min / max of zeros of opposite sign, where the first-of-equals rule shows
    dz, lz = _zeros_frame()
    C = []
    for cid, k, f, lean_f in (("min_zeros_u", "u", "min", lean_min), ("max_zeros_u", "u", "max", lean_max),
                              ("min_zeros_v", "v", "min", lean_min), ("max_zeros_v", "v", "max", lean_max)):
        e = cmp.canon_frame(dz.select(q=getattr(pl.col(k), f)()))
        C.append((cid, f"{f}(zeros of opposite sign)", f'Pl.Frame.select dz [("q", (c "{k}").{f})]', e,
                  lim(ZN, set_col(e, "q", [lean_f(dz.get_column(k).to_list())]))))
    dump_chunks(s, lz, "frame", C)
    # documented limit, python side: a column in several chunks can sum differently
    hits = []
    xs = [v for v in Y.vals]
    for cut in (100, 128, 200, 333, 517, 640):
        one = pl.Series(xs[:1000], dtype=pl.Float64).sum()
        two = pl.concat([pl.Series(xs[:cut], dtype=pl.Float64), pl.Series(xs[cut:1000], dtype=pl.Float64)], rechunk=False)
        if two.n_chunks() == 2 and cmp.fbits(two.sum()) != cmp.fbits(one):
            hits.append(cut)
    (WORK / "multichunk.json").write_text(json.dumps({"sum of y[:1000] differs when split in 2 chunks at": hits}))
    return s


def _zeros_frame():
    dz = pl.DataFrame({"g": [1, 1, 2, 2, 3, 3, 3], "u": [0.0, -0.0, -0.0, 0.0, None, 0.0, -0.0], "v": [-0.0, 0.0, 0.0, -0.0, NAN, -0.0, 0.0]},
                      schema={"g": pl.Int64, "u": pl.Float64, "v": pl.Float64})
    return dz, CLET + lt.lean_frame_let("dz", dz)


# ---------------------------------------------------------------------------------------------- agggrp
def suite_agggrp() -> Suite:
    n = 600
    SL = ["A", "B", "", "é"]
    cols = [cat(gi("k", 60, n, 4, 5, 0), lits("k", "int", [100, 200, 200, 200, 300, 300])), gs("ks", 61, n + 6, 5, SL),
            gf("kf", 62, n + 6, 100, 2, "EK", EK), gi("k3", 70, n + 6, 0, 120, 0),
            cat(gf("x", 63, n, 12, 3, "EN", EN), lits("x", "f64", [1.5, None, None, None, NAN, NAN])),
            gf("y", 64, n + 6, 0, 3), gf("z", 65, n + 6, 35, 2, "EZ", EZ), gf("m", 66, n + 6, 50, 2, "EM", EM),
            gi("i", 67, n + 6, 10, 50, 20), Col("n", "f64", f"List.replicate {n + 6} none", [None] * (n + 6))]
    lets_fr, df = frame("fr", cols)
    lets = (elist("EN", "f64", EN) + elist("EZ", "f64", EZ) + elist("EM", "f64", EM) + elist("EK", "f64", EK)
            + 'let SL := ["A", "B", "", "é"]; ' + lets_fr
            + "let fs2 : Pl.Frame Float := fr.map (fun p => (p.1, Pl.Col.take p.2 (List.range 250))); " + KLETS + FLETS
            + "let G := fun (f : Pl.Frame Float) (b : List String) (ks : List String) (g : Pl.Expr Float → Pl.Expr Float) "
              "(ex : List (String × Pl.Expr Float)) => dg (tR (Pl.Frame.groupByAgg f b (ks.map (fun (k : String) => (g (c k)).pos) ++ ex))); ")
    six = ('[G {f} b K6 fs [], G {f} b K6 fm [], G {f} b K4 fn [], G {f} b K4 fx [], G {f} b K5 fd [], G {f} b ["m"] fd [], '
           "G {f} b K6 fc [Pl.len.pos]]")
    KV = [["k"], ["ks"], ["kf"], ["k", "ks"]]
    body = ("(" + lt.lean_list([lt.lean_list([lt.lean_str(k) for k in b]) for b in KV], "List (List String)")
            + ".flatMap (fun (b : List String) => " + six.format(f="fr") + ')) ++ (fun (b : List String) => ' + six.format(f="fs2") + ') ["k3"]')
    out = []

    def py(d, b, name):
        ks = K4 if name in ("min", "max") else (K5 if name == "median" else K6)
        ex = [pl.len()] if name == "count" else []
        return cmp.canon_frame(d.group_by(b, maintain_order=True).agg([_pyagg(name, k) for k in ks] + ex))

    def rows_of(d, b):  # the row indices of each group, in group order
        return d.with_row_index("r_").group_by(b, maintain_order=True).agg(pl.col("r_"))["r_"].to_list()

    def per_group(d, b, k, f):  # f applied to column k of each group
        v = d.get_column(k).to_list()
        return [f([v[r] for r in g]) for g in rows_of(d, b)]

    def med_m(d, b, tag):
        e = cmp.canon_frame(d.group_by(b, maintain_order=True).agg(pl.col("m").median()))
        return (f"median_m_by_{tag}", "group:median(zeros of both signs)", e, lim(MDN, set_col(e, "m", per_group(d, b, "m", lean_median))))

    for b in KV:
        for name, _, _ in AGG:
            out.append((f"{name}_by_{'_'.join(b)}", f"group:{name}" if name != "count" else "group:count,len", py(df, b, name)))
            if name == "median":
                out.append(med_m(df, b, "_".join(b)))
    for name, _, _ in AGG:
        out.append((f"{name}_by_k3_small_groups", f"group:{name}" if name != "count" else "group:count,len", py(df.head(250), ["k3"], name)))
        if name == "median":
            out.append(med_m(df.head(250), ["k3"], "k3_small_groups"))
    extra = []

    def add_case(cid, prim, lean, aggs, model=None, note=None, **kw):
        try:
            e = cmp.canon_frame(df.group_by("k", maintain_order=True).agg(**aggs) if isinstance(aggs, dict)
                                else df.group_by("k", maintain_order=True).agg(aggs))
        except Exception as ex:
            SKIPPED.append(f"agggrp/{cid}: python raised {type(ex).__name__}: {str(ex)[:80]}")
            return
        extra.append(lean)
        out.append((cid, prim, e, lim(note, model(e)) if model else kw))

    keyf = lambda e: as_f64(e, keep=("k",))  # noqa: E731
    add_case("min_int", "group:min(Int64 input)", 'G fr ["k"] ["i"] fn []', [pl.col("i").min()], model=keyf, note=DTN)
    add_case("max_int", "group:max(Int64 input)", 'G fr ["k"] ["i"] fx []', [pl.col("i").max()], model=keyf, note=DTN)
    add_case("min_signed_zero", "group:min(zeros of opposite sign)", 'G fr ["k"] ["m"] fn []', [pl.col("m").min()],
             model=lambda e: set_col(e, "m", per_group(df, ["k"], "m", lean_min)), note=ZN)
    add_case("max_signed_zero", "group:max(zeros of opposite sign)", 'G fr ["k"] ["m"] fx []', [pl.col("m").max()],
             model=lambda e: set_col(e, "m", per_group(df, ["k"], "m", lean_max)), note=ZN)
    add_case("sum_expr", "group:sum", 'G fr ["k"] [] fs [("p", ((c "x").mul (c "y")).sum)]', {"p": (pl.col("x") * pl.col("y")).sum()})
    add_case("mapB_div", "group:mapBatches2", 'G fr ["k"] [] fs [("q", Pl.mapBatches2 (c "x").sum Pl.len run)]',
             {"q": sc.div(pl.col("x").sum(), pl.len())})
    add_case("mean_div", "group:sum", 'G fr ["k"] [] fs [("q", ((c "y").sum).div Pl.len)]', {"q": pl.col("y").sum() / pl.len()})
    xv, yv = df.get_column("x").to_list(), df.get_column("y").to_list()

    def filter_model(e):  # Expr.filter ignores the groups: the group's row indices are read in the filtered column
        v = [x for x, y in zip(xv, yv, strict=True) if y > 0.0]
        hn = any(x is None for x in v)
        return set_col(e, "f", [lean_group_sum(hn, [v[r] if r < len(v) else None for r in g]) for g in rows_of(df, ["k"])])

    def cumsum_model(e):  # Expr.cumSum ignores the groups: one running sum over the frame (height of the frame)
        acc, run = None, []
        for y in yv:
            acc = y if acc is None else acc + y
            run.append(acc)
        return set_col(e, "cs", run)

    add_case("filter_sum", "group:filter", 'G fr ["k"] [] fs [("f", ((c "x").filter ((c "y").gt (Pl.litF (Float.ofBits 0)))).sum)]',
             {"f": pl.col("x").filter(pl.col("y") > 0.0).sum()}, model=filter_model,
             note="`filter` is stated for select context only (RULEBOOK 2.3): inside group_by().agg Expr.filter ignores the groups (other values)")
    add_case("cumSum", "group:cumSum", 'G fr ["k"] [] fs [("cs", (c "y").cumSum)]', {"cs": pl.col("y").cum_sum()}, model=cumsum_model,
             note="`cumSum` is stated for select context only (RULEBOOK 2.3): inside group_by().agg polars returns a List column, "
                  "Expr.cumSum the running sum over the whole frame")
    s = Suite("agggrp", carrier="cumsum")
    s.digest_body(LETS + lets, body + " ++ [" + ", ".join(extra) + "]", out)
    # minimal inputs (dump mode): min / max of zeros of opposite sign per group
    dz, lz = _zeros_frame()
    C = []
    for cid, k, f, lean_f in (("min_zeros_u", "u", "min", lean_min), ("max_zeros_u", "u", "max", lean_max),
                              ("min_zeros_v", "v", "min", lean_min), ("max_zeros_v", "v", "max", lean_max)):
        e = cmp.canon_frame(dz.group_by("g", maintain_order=True).agg(q=getattr(pl.col(k), f)()))
        C.append((cid, f"group:{f}(zeros of opposite sign)", f'Pl.Frame.groupByAgg dz ["g"] [("q", (c "{k}").{f})]', e,
                  lim(ZN, set_col(e, "q", per_group(dz, ["g"], k, lean_f)))))
    dump_chunks(s, lz, "frame", C)
    return s


# ---------------------------------------------------------------------------------------------- frames
def suite_frames() -> Suite:
    n = 400
    SL = ["A", "B", "", "a", "é"]
    cols = [Col("id", "int", f"(List.range {n}).map (fun (i : Nat) => some (i : Int))", list(range(n))), gf("kf", 80, n, 70, 1, "EA", EA),
            gi("ki", 81, n, 10, 6, 2), gs("ks", 82, n, 10, SL), gb("kb", 83, n, 15), gf("v", 84, n, 10, 3, "EN", EN)]
    lets_fr, df = frame("fr", cols)
    rcols = [gi("ki", 85, 60, 15, 6, 2), gf("w", 86, 60, 10, 3, "EN", EN), gf("v", 87, 60, 0, 3), gs("ks", 88, 60, 10, SL),
             gf("kf", 89, 60, 100, 1, "EK", EK), Col("id2", "int", "(List.range 60).map (fun (i : Nat) => some (i : Int))", list(range(60)))]
    lets_rr, rr = frame("rr", rcols)
    lets = (elist("EA", "f64", EA) + elist("EN", "f64", EN) + elist("EK", "f64", EK) + 'let SL := ["A", "B", "", "a", "é"]; '
            + lets_fr + lets_rr
            + "let H := fun (f : Pl.Frame Float) (a b : Nat) => Pl.Frame.takeRows f ((List.range (b - a)).map (fun (i : Nat) => a + i)); "
            + "let fl := H fr 0 120; ")
    fl = df.head(120)
    P = "Pl.Frame."
    C: list[tuple] = []

    def add_case(cid, prim, lean, pyf, kind="frame", **kw):
        try:
            got = pyf()
        except Exception as ex:
            SKIPPED.append(f"frames/{cid}: python raised {type(ex).__name__}: {str(ex)[:80]}")
            return
        e = cmp.canon_table(got) if kind == "table" else cmp.canon_frame(got)
        C.append((cid, prim, f"{'tA' if kind == 'table' else 'tR'} ({lean})", e, kw))

    for by_ in (["kf"], ["ki"], ["ks"], ["kb"], ["ki", "kf"], ["ks", "ki", "kf"], ["kf", "ki"], ["kb", "ks"]):
        add_case("sort_" + "_".join(by_), "sort", f"{P}sort fr {lt.lean_list([lt.lean_str(k) for k in by_])}",
                 lambda by_=by_: df.sort(by_, maintain_order=True))
    for by_ in (["kf"], ["ki", "ks"], ["kb"], ["kf", "kb"], ["ks"]):
        add_case("groups_" + "_".join(by_), "groups/groupByAgg", f"{P}groupByAgg fr {lt.lean_list([lt.lean_str(k) for k in by_])} [Pl.len.pos, (c \"id\").min.castF64.pos]",
                 lambda by_=by_: df.group_by(by_, maintain_order=True).agg(pl.len(), pl.col("id").min().cast(pl.Float64)))
    v, kf, ki, ks = col("v"), col("kf"), col("ki"), col("ks")
    add_case("withColumns_replace_append", "withColumns", f'{P}withColumns fr [("v", {mul(v, 2).lean}), ("w", {add(ki, 1).lean})]',
             lambda: df.with_columns(v=pl.col("v") * 2, w=pl.col("ki") + 1))
    add_case("withColumns_swap", "withColumns", f'{P}withColumns fr [("kf", {v.lean}), ("v", {kf.lean})]',
             lambda: df.with_columns(kf=pl.col("v"), v=pl.col("kf")))
    add_case("withColumns_scalars", "withColumns", f'{P}withColumns fr [("s", {v.lean}.sum), ("l", Pl.litF (Float.ofBits {lt.bits(1.5)})), ("n", Pl.len)]',
             lambda: df.with_columns(s=pl.col("v").sum(), l=pl.lit(1.5), n=pl.len()))
    add_case("withColumns_positional", "withColumns", f"{P}withColumns fr [{mul(v, 2).lean}.pos, ({kf.lean}.alias \"z\").pos]",
             lambda: df.with_columns(pl.col("v") * 2, pl.col("kf").alias("z")))
    add_case("select_broadcast", "select", f'{P}select fr [("a", {v.lean}), ("b", {v.lean}.sum), ("c", Pl.litI 3)]',
             lambda: df.select(a=pl.col("v"), b=pl.col("v").sum(), c=pl.lit(3)))
    add_case("select_scalars", "select", f'{P}select fr [("s", {v.lean}.sum), ("c", Pl.len), ("l", Pl.litS "x")]',
             lambda: df.select(s=pl.col("v").sum(), c=pl.len(), l=pl.lit("x")))
    add_case("select_name_and_named", "select", f'{P}select fr [{ki.lean}.pos, ("B", {add(v, 1.0).lean})]',
             lambda: df.select("ki", B=pl.col("v") + 1.0))
    add_case("filter_gt", "filter(frame)", f"{P}filter fr {gt(v, 0).lean}", lambda: df.filter(pl.col("v") > 0))
    add_case("filter_isnull", "filter(frame)", f"{P}filter fr {kf.lean}.isNull", lambda: df.filter(pl.col("kf").is_null()))
    add_case("filter_and", "filter(frame)", f"{P}filter fr {and_(gt(v, 0), eq(ks, 'A')).lean}", lambda: df.filter((pl.col("v") > 0) & (pl.col("ks") == "A")))
    add_case("filter_lit_true", "filter(frame)", f"{P}filter fr (Pl.litB true)", lambda: df.filter(pl.lit(True)))
    add_case("filter_nan_eq", "filter(frame)", f"{P}filter fr {eq(kf, kf).lean}", lambda: df.filter(pl.col("kf") == pl.col("kf")))
    add_case("drop", "drop", f'{P}drop fr ["v", "kb"]', lambda: df.drop("v", "kb"))
    add_case("rename", "rename", f'{P}rename fr [("v", "w"), ("id", "ID")]', lambda: df.rename({"v": "w", "id": "ID"}))
    add_case("rename_swap", "rename", f'{P}rename fr [("v", "kf"), ("kf", "v")]', lambda: df.rename({"v": "kf", "kf": "v"}))
    add_case("cols", "cols", f'{P}cols fr ["v", "id", "ks"]', lambda: df.select("v", "id", "ks"))
    keep = ["ks", "zz", "id"]
    add_case("keep", "keep", f'{P}keep fr ["ks", "zz", "id"]', lambda: df.select([c_ for c_ in df.columns if c_ in keep]))
    for inner in (False, True):
        for ne_ in (False, True):
            add_case(f"join_ki_{'inner' if inner else 'left'}_nulls_equal_{ne_}", "join",
                     f'{P}join fl rr "ki" {lt.lean_bool(inner)} {lt.lean_bool(ne_)}',
                     lambda inner=inner, ne_=ne_: fl.join(rr, on="ki", how="inner" if inner else "left", maintain_order="left", nulls_equal=ne_))
    add_case("join_ks_left", "join", f'{P}join fl rr "ks" false false', lambda: fl.join(rr, on="ks", how="left", maintain_order="left", nulls_equal=False))
    add_case("join_ks_inner_ne", "join", f'{P}join fl rr "ks" true true', lambda: fl.join(rr, on="ks", how="inner", maintain_order="left", nulls_equal=True))
    add_case("join_kf_left", "join(Float64 key)", f'{P}join fl rr "kf" false false',
             lambda: fl.join(rr, on="kf", how="left", maintain_order="left", nulls_equal=False), note="float key with NaN and signed zeros")
    add_case("join_kf_left_ne", "join(Float64 key)", f'{P}join fl rr "kf" false true',
             lambda: fl.join(rr, on="kf", how="left", maintain_order="left", nulls_equal=True), note="float key with NaN and signed zeros")
    add_case("concat2", "concat", "Pl.concat [fl, H fr 120 200]", lambda: pl.concat([fl, df[120:200]], how="vertical"))
    add_case("concat3_empty", "concat", "Pl.concat [H fr 0 0, fl, H fr 300 400]", lambda: pl.concat([df.head(0), fl, df[300:400]], how="vertical"))
    add_case("castF64", "castF64(frame)", f'{P}castF64 ({P}cols fr ["id", "ki", "kb", "v"])', lambda: df.select("id", "ki", "kb", "v").cast(pl.Float64))
    add_case("toTable", "toTable", "Pl.toTable (H fr 0 40)", lambda: df.head(40), kind="table")
    add_case("toTable_empty", "toTable", "Pl.toTable (H fr 0 0)", lambda: df.head(0), kind="table")
    num = [k for k in df.columns if k != "ks"]
    add_case("ofTable_roundtrip", "ofTable", "Pl.ofTable (Pl.toTable (H fr 0 40))", lambda: df.head(40).with_columns(pl.col(num).cast(pl.Float64)))
    add_case("ofTable_first_row_null", "ofTable", "Pl.ofTable (Pl.toTable (H fr 2 40))",
             lambda: df[2:40].with_columns(pl.col(num).cast(pl.Float64)))
    add_case("toTable_ofTable", "toTable", "Pl.toTable (Pl.ofTable (Pl.toTable (H fr 0 40)))", lambda: df.head(40), kind="table")
    s = Suite("frames", carrier="cumsum")
    s.digest(LETS + lets, C, table=True)
    _frames_small(s)
    return s


def _cell_frame(df: pl.DataFrame) -> dict:
    """canonical frame where a Date column is the `.cell` column of its boundary cells (Cell.str of the ISO date)"""
    c = cmp.canon_frame(df.with_columns([pl.col(n).cast(pl.String) for n in df.columns if df.schema[n] == pl.Date]))
    for n, col_ in c["cols"]:
        if df.schema[n] == pl.Date:
            col_["kind"], col_["values"] = "cell", [["str", v] for v in col_["values"]]
    return c


def _frames_small(s: Suite):
    """minimal inputs in dump mode: item / get / firstName / setCol / Expr.pos, litCell and Col.null through
    with_columns, select and toTable"""
    f = pl.DataFrame({"x": [1.5, None, -0.0], "i": [3, None, -1], "s": ["a", None, "é"], "b": [True, None, False]},
                     schema={"x": pl.Float64, "i": pl.Int64, "s": pl.String, "b": pl.Boolean})
    g1 = pl.DataFrame({"v": [2.5]})
    day = dt.date(2026, 1, 15)
    LC = "LC"  # pl.lit(<date>): the cell that stands for the date
    lets = (small_lets({"f": f, "g1": g1}).replace(CLET, LETS, 1)
            + f'let LC : Pl.Expr Float := Pl.litCell (Tabular.Cell.str (some "{day.isoformat()}")); ')
    F = "Pl.Frame."

    def one(name: str, col_: dict) -> dict:
        return {"type": "frame", "cols": [[name, col_]]}

    C = [
        ("itemF", "itemF", f'[("itemF", Pl.Col.f64 [{F}itemF f 0 "x", {F}itemF f 1 "x", {F}itemF f 2 "x", {F}itemF f 0 ({F}firstName f), '
                           f'{F}itemF g1 0 ({F}firstName g1)])]',
         one("itemF", cmp.canon_floats([f.item(0, "x"), f.item(1, "x"), f.item(2, "x"), f.item(0, 0), g1.item()]))),
        ("itemI", "itemI", f'[("itemI", Pl.Col.int [{F}itemI f 0 "i", {F}itemI f 1 "i", {F}itemI f 2 "i"])]',
         one("itemI", cmp.canon_ints([f.item(r, "i") for r in range(3)]))),
        ("itemS", "itemS", f'[("itemS", Pl.Col.str [{F}itemS f 0 "s", {F}itemS f 1 "s", {F}itemS f 2 "s"])]',
         one("itemS", cmp.canon_strs([f.item(r, "s") for r in range(3)]))),
        ("firstName", "firstName", f'[("firstName", Pl.Col.str [some ({F}firstName f), some ({F}firstName g1), '
                                   f'some ({F}firstName ({F}cols f ["s", "x"]))])]',
         one("firstName", cmp.canon_strs([f.columns[0], g1.columns[0], f.select("s", "x").columns[0]]))),
        ("getF", "getF", f'[("getF", Pl.Col.f64 ({F}getF f "x"))]', one("getF", cmp.canon_floats(f.get_column("x").to_list()))),
        ("getI", "getI", f'[("getI", Pl.Col.int ({F}getI f "i"))]', one("getI", cmp.canon_ints(f.get_column("i").to_list()))),
        ("getS", "getS", f'[("getS", Pl.Col.str ({F}getS f "s"))]', one("getS", cmp.canon_strs(f.get_column("s").to_list()))),
        ("height", "height", f'[("height", Pl.Col.int [some (({F}height f : Nat) : Int), some (({F}height g1 : Nat) : Int), '
                             f'some (({F}height ({F}filter f (Pl.litB false)) : Nat) : Int)])]',
         one("height", cmp.canon_ints([f.height, g1.height, f.filter(pl.lit(False)).height]))),
    ]
    for cid, name, ser in (("setCol_replace_f64", "x", pl.Series([9.5, 8.5, None], dtype=pl.Float64)),
                           ("setCol_replace_other_dtype", "i", pl.Series(["u", None, "w"], dtype=pl.String)),
                           ("setCol_append_int", "new", pl.Series([1, 2, None], dtype=pl.Int64)),
                           ("setCol_append_bool", "nb", pl.Series([None, True, False], dtype=pl.Boolean)),
                           ("setCol_replace_last", "b", pl.Series([0.5, -0.0, NAN], dtype=pl.Float64))):
        C.append((cid, "setCol", f"{F}setCol f {lt.lean_str(name)} {lt.lean_col(ser)}", cmp.canon_frame(f.with_columns(ser.alias(name)))))
    x, i, st, b = (col(k) for k in "xisb")
    named = [x, X(pl.col("x").alias("y"), '((c "x").alias "y")'), add(x, i), add(1, x), lit(1.5), lit(3), lit("t"), lit(True), LEN, sum_(x),
             wto(b, i, x), wto(b, 1), wto(b, NONE, x), sumH(True, [i, x]), minH(True, [x, i]), maxH(True, [x, i]), allH([b, b]), isNull(x), LN,
             fillNull(st, "z"), neg(x), X((pl.col("x") > 1).alias("g"), '(((c "x").gt (Pl.litI 1)).alias "g")'), castF64(i), castI64(b),
             cumSum(i), filter_(x, b), isInF(x, [1.5]), isInS(st, ["a"]),
             # the bare pl.struct(a, b).map_batches(run) of RULEBOOK 2.3 (sas_compat.div renames its result: not the prelude's business)
             X(pl.struct(pl.col("x").cast(pl.Float64).alias("a"), pl.col("i").cast(pl.Float64).alias("b"))
               .map_batches(lambda v: v.struct.field("a"), return_dtype=pl.Float64), '(Pl.mapBatches2 (c "x") (c "i") run)'), mean(x), count(x), median(x), min_(x), max_(x),
             not_(b), and_(b, b), eq(x, i), log(x), exp(x), abs_(x), floor(x), sign(x), isFinite(x), X(pl.lit(day), LC)]
    C.append(("pos_names", "Expr.pos",
              '[("pos", Pl.Col.str [' + ", ".join(f"some (Pl.Expr.pos ({e.lean} : Pl.Expr Float)).1" for e in named) + "])]",
              one("pos", cmp.canon_strs([f.select(e.py).columns[0] for e in named]))))
    C += [
        ("pos_select", "Expr.pos", f"{F}select f [(Pl.Expr.pos {add(x, i).lean}), (Pl.Expr.pos {LN.lean}), (Pl.Expr.pos {wto(b, i, x).lean})]",
         cmp.canon_frame(f.select(pl.col("x") + pl.col("i"), pl.lit(None), wto(b, i, x).py))),
        ("litCell_withColumns", "litCell", f'{F}withColumns f [("d", {LC})]', _cell_frame(f.with_columns(d=pl.lit(day)))),
        ("litCell_withColumns_replace", "litCell", f'{F}withColumns f [("i", {LC}), ("e", {LC})]', _cell_frame(f.with_columns(i=pl.lit(day), e=pl.lit(day)))),
        ("litCell_select", "litCell", f'{F}select f [(Pl.Expr.pos (c "x")), ("d", {LC})]', _cell_frame(f.select("x", d=pl.lit(day)))),
        ("litCell_select_scalar", "litCell", f'{F}select f [("d", {LC})]', _cell_frame(f.select(d=pl.lit(day)))),
        ("litCell_pos", "litCell", f"{F}select f [(Pl.Expr.pos {LC})]", _cell_frame(f.select(pl.lit(day)))),
        ("null_withColumns", "withColumns(Col.null)", f'{F}withColumns f [("n", {LN.lean})]', cmp.canon_frame(f.with_columns(n=pl.lit(None)))),
        ("null_withColumns_replace", "withColumns(Col.null)", f'{F}withColumns f [("x", {LN.lean})]', cmp.canon_frame(f.with_columns(x=pl.lit(None)))),
        ("null_select", "select(Col.null)", f'{F}select f [(Pl.Expr.pos (c "s")), ("n", {LN.lean})]', cmp.canon_frame(f.select("s", n=pl.lit(None)))),
        ("null_select_scalar", "select(Col.null)", f'{F}select f [("n", {LN.lean})]', cmp.canon_frame(f.select(n=pl.lit(None)))),
        ("null_filter", "filter(frame, Col.null column)", f'{F}filter ({F}withColumns f [("n", {LN.lean})]) (c "b")',
         cmp.canon_frame(f.with_columns(n=pl.lit(None)).filter(pl.col("b")))),
        ("null_sort", "sort(Col.null column)", f'{F}sort ({F}withColumns f [("n", {LN.lean})]) ["i"]',
         cmp.canon_frame(f.with_columns(n=pl.lit(None)).sort("i", maintain_order=True))),
        ("null_castF64", "castF64(frame, Col.null column)", f'{F}castF64 ({F}withColumns ({F}cols f ["x", "i"]) [("n", {LN.lean})])',
         cmp.canon_frame(f.select("x", "i").with_columns(n=pl.lit(None)).cast(pl.Float64))),
    ]
    dump_chunks(s, lets, "frame", C)
    fn = f.with_columns(n=pl.lit(None))
    T = [
        ("null_toTable", "toTable(Col.null)", f'Pl.toTable ({F}withColumns f [("n", {LN.lean})])', cmp.canon_table(fn)),
        ("null_toTable_only", "toTable(Col.null)", f'Pl.toTable ({F}select f [(Pl.Expr.pos (c "i")), ("n", {LN.lean})])',
         cmp.canon_table(f.select("i", n=pl.lit(None)))),
        ("nullcol_toTable", "toTable(Col.null)", f'Pl.toTable ({F}select f [("w", (Pl.wto (c "b") {LN.lean} {LN.lean})), ("x", (c "x"))])',
         cmp.canon_table(f.select(w=pl.when(pl.col("b")).then(None).otherwise(None), x=pl.col("x")))),
        ("litCell_toTable", "litCell", f'Pl.toTable ({F}withColumns f [("d", {LC})])',
         cmp.canon_table(f.with_columns(d=pl.lit(day).cast(pl.String)))),
        ("litCell_toTable_select", "litCell", f'Pl.toTable ({F}select f [("d", {LC}), ("s", (c "s"))])',
         cmp.canon_table(f.select(d=pl.lit(day).cast(pl.String), s=pl.col("s")))),
        ("small_toTable", "toTable", "Pl.toTable f", cmp.canon_table(f)),
    ]
    dump_chunks(s, lets, "table", T)


# ---------------------------------------------------------------------------------------------- ranknp
def suite_ranknp() -> Suite:
    s = Suite("ranknp", carrier="cumsum")
    C: list[tuple] = []
    R = [gf("r1", 90, 300, 60, 1, "EA", EA), gf("r2", 91, 50, 0, 3), lits("r3", "f64", []), lits("r4", "f64", [None]),
         lits("r5", "f64", [2.5]), lits("r6", "f64", [1.0, 1.0, 1.0, None, 1.0]), lits("r7", "f64", [NAN, 0.0, -0.0, NAN, None, INF, -INF]),
         gf("r8", 92, 40, 100, 1, "EA", EA)]
    lets = elist("EA", "f64", EA) + "".join(f"let {r.name} : List (Option Float) := {r.lean}; " for r in R)
    for r in R:
        for d in (False, True):
            C.append((f"rank_{r.name}_{'desc' if d else 'asc'}", "rankAverage", f"tC (.f64 (Pl.rankAverage {r.name} {lt.lean_bool(d)}))",
                      cmp.canon_series(pl.Series(r.vals, dtype=pl.Float64).rank("average", descending=d))))
    # ---- numpy
    def plain(name, sd, n, eh, pe=0, ename="[]", E=()):
        c_ = gf(name, sd, n, pe, eh, ename, E)
        return name, f"let {name} : List Float := ({c_.lean}).filterMap id; ", np.array(c_.vals, dtype=np.float64)

    arrs = [plain("NA", 100, 5000, 3), plain("NB", 101, 5000, 30), plain("NC", 102, 300, 2, 100, "EZZ", [0.0, -0.0]),
            plain("ND", 103, 300, 2, 100, "EMZ", [-0.0])]
    lets += elist("EZZ", "f64", [0.0, -0.0]) + elist("EMZ", "f64", [-0.0]) + "".join(a[1] for a in arrs)
    lets += ("let sums := fun (xs : List Float) (a n : Nat) => tC (.f64 ((List.range n).map (fun (k : Nat) => some (Np.sum (xs.take (a + k)))))); "
             "let vars := fun (xs : List Float) (a n : Nat) => tC (.f64 ((List.range n).map (fun (k : Nat) => some (Np.var1 (xs.take (a + k)))))); "
             "let fl := fun (xs : List Float) => tC (.f64 (xs.map some)); "
             "let nl := fun (xs : List Nat) => tC (.int (xs.map (fun (n : Nat) => some (n : Int)))); ")
    for name, _, arr in arrs:
        for a, cnt in ((0, 9), (9, 120), (129, 172)):
            C.append((f"sum_{name}_len{a}..{a + cnt - 1}", "Np.sum", f"sums {name} {a} {cnt}",
                      cmp.canon_floats([float(np.sum(arr[:a + k])) for k in range(cnt)])))
    for name, _, arr in arrs[:2]:
        for ln in (1000, 2048, 3000, 5000):
            C.append((f"sum_{name}_len{ln}", "Np.sum", f"sums {name} {ln} 1", cmp.canon_floats([float(arr[:ln].sum())])))
        for a, cnt in ((2, 127), (129, 172)):
            C.append((f"var1_{name}_len{a}..{a + cnt - 1}", "Np.var1", f"vars {name} {a} {cnt}",
                      cmp.canon_floats([float(np.var(arr[:a + k], ddof=1)) for k in range(cnt)])))
        for ln in (1000, 3000):
            C.append((f"var1_{name}_len{ln}", "Np.var1", f"vars {name} {ln} 1", cmp.canon_floats([float(np.var(arr[:ln], ddof=1))])))
    EZS = [v for v in EZ if v is not None]
    s1 = gf("S1", 104, 200, 50, 2, "EZS", EZS)          # NaN, inf, ties, no negative zero
    s2 = gf("S2", 105, 120, 60, 2, "EAS", EZS + [-0.0])  # also zeros of both signs
    keys = gf("KY", 106, 60, 50, 2, "EAS", EZS + [-0.0])
    lets += (elist("EZS", "f64", EZS) + elist("EAS", "f64", EZS + [-0.0])
             + f"let S1 : List Float := ({s1.lean}).filterMap id; let S2 : List Float := ({s2.lean}).filterMap id; "
             + f"let KY : List Float := (({keys.lean}).filterMap id) ++ S1.take 25; let SA := Np.sort S1; let SB := Np.sort S2; ")
    a1, a2 = np.array(s1.vals, dtype=np.float64), np.array(s2.vals, dtype=np.float64)
    ky = np.array(keys.vals + s1.vals[:25], dtype=np.float64)
    C.append(("sort_S1", "Np.sort", "fl (Np.sort S1)", cmp.canon_floats(np.sort(a1).tolist())))
    C.append(("sort_S2_signed_zeros", "Np.sort(zeros of both signs)", "fl (Np.sort S2)", cmp.canon_floats(np.sort(a2).tolist()),
              lim("np.sort with zeros of both signs: np.sort is not stable, Np.sort keeps the input order of -0.0 and 0.0; "
                  "every other position equal", cmp.canon_floats(stable_sorted(s2.vals)))))
    C.append(("sort_empty", "Np.sort", "fl (Np.sort [])", cmp.canon_floats([])))
    C.append(("argsort_S1", "Np.argsortStable", "nl (Np.argsortStable S1)", cmp.canon_ints(np.argsort(a1, kind="stable").tolist())))
    C.append(("argsort_S2_signed_zeros", "Np.argsortStable", "nl (Np.argsortStable S2)", cmp.canon_ints(np.argsort(a2, kind="stable").tolist())))
    for side in ("left", "right"):
        f = "Np.searchsortedLeft" if side == "left" else "Np.searchsortedRight"
        C.append((f"searchsorted_{side}_S1", f, f"nl (KY.map (fun (k : Float) => {f} SA k))",
                  cmp.canon_ints(np.searchsorted(np.sort(a1), ky, side=side).tolist())))
        C.append((f"searchsorted_{side}_S2_signed_zeros", f, f"nl (KY.map (fun (k : Float) => {f} SB k))",
                  cmp.canon_ints(np.searchsorted(np.sort(a2), ky, side=side).tolist())))
        C.append((f"searchsorted_{side}_empty", f, f"nl (KY.map (fun (k : Float) => {f} [] k))",
                  cmp.canon_ints(np.searchsorted(np.array([], dtype=np.float64), ky, side=side).tolist())))
    ci = gi("CI", 107, 80, 0, 2001, 1000)
    lets += f"let CI : List Int := ({ci.lean}).filterMap id; "
    C.append(("cumsumInt", "Np.cumsumInt", "tC (.int ((Np.cumsumInt CI).map some))", cmp.canon_ints(np.cumsum(np.array(ci.vals, dtype=np.int64)).tolist())))
    C.append(("cumsumInt_empty", "Np.cumsumInt", "tC (.int ((Np.cumsumInt []).map some))", cmp.canon_ints([])))
    rv = gf("RV", 108, 200, 0, 5)
    redge = [0.0, -0.0, NAN, INF, -INF, 1e15, 1e300, 1e306, -1e-5, 5e-324, 0.0005, 0.0015, 0.0025, -0.0005, -0.0015, 2.5, 1.2345, 1.2355,
             -1.2345, 123456.7895, 0.9995, -0.9995, 4503599627370497.0, 1e-4, 4.9e-4, 5.1e-4]
    lets += (f"let RV : List Float := ({rv.lean}).filterMap id; let RG : List Float := (List.range 41).map (fun (k : Nat) => "
             f"(Float.ofNat k - {lt.lean_float(19.5)}) / {lt.lean_float(1000.0)}); let RE : List Float := {lt.lean_floats(redge)}; "
             f"let RK : List Float := (List.range 2101).map (fun (k : Nat) => (Float.ofNat k - {lt.lean_float(100.0)}) * {lt.lean_float(0.02)}); ")
    grid = [(k - 19.5) / 1000.0 for k in range(41)]
    rk = [(k - 100.0) * 0.02 for k in range(2101)]
    for nm, vals in (("RV", rv.vals), ("RG", grid), ("RE", redge), ("RK", rk)):
        C.append((f"round3_{nm}", "Np.round3", f"fl ({nm}.map Np.round3)", cmp.canon_floats(np.round(np.array(vals, dtype=np.float64), 3).tolist())))
    s.digest(lets, C, table=False)
    # negative values and exact halves, in bits mode (the whole list comes back)
    with np.errstate(all="ignore"):
        halves = [-0.5, -1.5, -2.5, -3.5, -4.5, 0.5, 1.5, 2.5, 3.5, 4.5, -0.0, 0.0, -0.4, -0.6, -1.0, -7.0, -6.5, -1e-300, -5e-324,
                  -0.49999999999999994, 0.49999999999999994, -0.5000000000000001, -2.4999999999999996, -2.5000000000000004,
                  -4503599627370495.5, 4503599627370495.5, -4503599627370496.5, -4503599627370497.0, -9007199254740993.0, -1e16, 1e16, -1e300,
                  -INF, INF, NAN, -1023.5, -1024.5, 1e15 + 0.5, -(1e15 + 0.5), -(1e15 + 1.5)]
        s.bits("rint_negative_and_halves", "Np.rint", f"{lt.lean_floats(halves)}.map Np.rint",
               cmp.canon_floats(np.rint(np.array(halves, dtype=np.float64)).tolist()))
        # x * 1000 is an exact half for x = k / 16 (k odd) and x = k + 0.5 / 1000 is not: both kinds, both signs
        r3 = [-0.0625, 0.0625, -0.1875, 0.1875, -0.3125, 0.3125, -0.4375, 0.4375, -1.0625, 1.0625, -2.5, 2.5, -0.5, 0.5, -0.0005, 0.0005,
              -0.0015, 0.0015, -0.0025, 0.0025, -1.0005, 1.0005, -0.0004, -0.0006, -0.0, 0.0, -1e-5, -5e-324, -1e-300, -123456.7895,
              -0.9995, -1.2345, -1.2355, -1e15, -1e300, -1e306, -4503599627370497.0, -8.0625, -1024.0625, -INF, NAN,
              -1.0, -7.0, -0.001, -0.002, -65536.1875]
        s.bits("round3_negative_and_halves", "Np.round3", f"{lt.lean_floats(r3)}.map Np.round3",
               cmp.canon_floats(np.round(np.array(r3, dtype=np.float64), 3).tolist()))
    return s


# ---------------------------------------------------------------------------------------------- logexp
def suite_logexp() -> Suite:
    """exp / log may differ in the last bit between Lean's runtime and polars: tokens mode, 1 ulp tolerated and reported apart"""
    s = Suite("logexp", carrier="cumsum")
    e = cat(lits("e", "f64", EA), gf("e", 97, 20, 0, 4))
    lets_fr, df = frame("fr", [e])
    s.tokens(LETS + lets_fr, "log_exp", "log,exp", f'tR (Pl.Frame.select fr [("log", {log(col("e")).lean}), ("exp", {exp(col("e")).lean})])',
             "frame", cmp.canon_frame(df.select(log=pl.col("e").log(), exp=pl.col("e").exp())), ulp_tol=1)
    return s


SUITES = {"ff": suite_ff, "int": suite_int, "boolstr": suite_boolstr, "horiz": suite_horiz, "aggsel": suite_aggsel,
          "agggrp": suite_agggrp, "frames": suite_frames, "ranknp": suite_ranknp, "logexp": suite_logexp}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--hexp":
        print(json.dumps(_horiz_expected(sys.argv[2] == "1")))
        sys.exit(0)
    for name in sys.argv[1:] or list(SUITES):
        SUITES[name]().write()
    for line in SKIPPED:
        print("SKIPPED", line)
