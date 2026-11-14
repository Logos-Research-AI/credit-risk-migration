"""Bundle B1 differential tests (sas_compat helpers, comparisons, sas_round, confusion_metrics).

  uv run python migration/diffeval/units/b1_gen.py
      -> work/b1_isscalar, b1_cmp, b1_round, b1_confusion, b1_direct (.json + .inputs.json)
  (eval_decl each work/b1_*.inputs.json on def:zz_carrier / zz_carrier, save work/b1_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b1_<suite>.json migration/diffeval/work/b1_<suite>.out.txt
  uv run python migration/diffeval/receipts.py units b1

Units: _e, _named, _has_bare_column, _is_scalar, lt, le, gt, ge, eq, flag, sas_round,
confusion_metrics, _TWO52, _ROUND_FUZZ.  The cases of b1_isscalar / b1_cmp / b1_round /
b1_confusion are the implementers' cases (ported from their scratch generator); b1_direct adds
direct cases for the units that were only exercised through the others.
"""
from __future__ import annotations

import datetime as dt
import math
import random
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # the harness
sys.path.insert(0, str(HERE.parents[2]))      # the workspace root (credit_risk)

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

C = "let c := fun (n : String) => Pl.col (α := Float) n; "
F = lt.lean_float


def EF(x):
    return f"(.float {F(x)})"


def EI(n):
    return f"(.int {lt.lean_int(n)})"


def EX(s):
    return f"(.expr ({s}))"


def LI(n):
    return f"(Pl.litI {lt.lean_int(n)} : Pl.Expr Float)"


def LF(v):
    return f"(Pl.litF {F(v)})"


def fdig(*frames) -> int:
    """digest of the token streams of several frames, concatenated (mirrors `dg (tR a ++ tR b)`)"""
    return cmp.digest([t for f in frames for t in cmp.tokens(cmp.canon_frame(f))])


# ---------------------------------------------------------------- suite 1: _is_scalar
def suite_isscalar() -> Suite:
    x, y = pl.col("x"), pl.col("y")
    S = [
        ("fe207/predict210 a", pl.col("credit_utilization") * pl.col("debt_ratio"), '(c "credit_utilization").mul (c "debt_ratio")'),
        ("fe207 b = _e(100)", sc._e(100), "_e (.int 100 : ExprOrNum Float)"),
        ("train436 a", 100 * pl.col("COUNT"), f'{LI(100)}.mul (c "COUNT")'),
        ("train436 b", pl.col("COUNT").sum(), '(c "COUNT").sum'),
        ("mc126 a", pl.col("cum_good"), 'c "cum_good"'),
        ("mc126 b lit(v,F64)", pl.lit(12.0, pl.Float64), f"Pl.litOptF (some {F(12.0)})"),
        ("lit(None,F64)", pl.lit(None, pl.Float64), "Pl.litOptF (none : Option Float)"),
        ("mc185 a", pl.col("defaults"), 'c "defaults"'),
        ("mc236 a", pl.col("cum_defaults") / pl.col("cum_count"), '(c "cum_defaults").div (c "cum_count")'),
        ("mc264 a", pl.col("cnt"), 'c "cnt"'),
        ("mc264 b = _e(height)", sc._e(7), "_e (.int 7 : ExprOrNum Float)"),
        ("_e(float)", sc._e(2.5), f"_e (.float {F(2.5)})"),
        ("sum/sum", x.sum() / y.sum(), '(c "x").sum.div (c "y").sum'),
        ("mean*100", x.mean() * 100, f'(c "x").mean.mul {LI(100)}'),
        ("len", pl.len(), "(Pl.len : Pl.Expr Float)"),
        ("len.cast", pl.len().cast(pl.Int64), "(Pl.len : Pl.Expr Float).castI64"),
        ("count", x.count(), '(c "x").count'), ("min", x.min(), '(c "x").min'), ("max", x.max(), '(c "x").max'),
        ("median", x.median(), '(c "x").median'),
        ("filter.sum", x.filter(y > 0).sum(), f'((c "x").filter ((c "y").gt {LI(0)})).sum'),
        ("filter bare", x.filter(y > 0), f'(c "x").filter ((c "y").gt {LI(0)})'),
        ("sum + col", x.sum() + y, '(c "x").sum.add (c "y")'),
        ("col / sum", x / x.sum(), '(c "x").div (c "x").sum'),
        ("litF", pl.lit(1.5), LF(1.5)), ("litI", pl.lit(3), LI(3)), ("litS", pl.lit("A"), '(Pl.litS "A" : Pl.Expr Float)'),
        ("litS Column", pl.lit("Column"), '(Pl.litS "Column" : Pl.Expr Float)'),
        ("col named Agg", pl.col("Agg"), 'c "Agg"'),
        ("litB", pl.lit(False), "(Pl.litB false : Pl.Expr Float)"), ("litNull", pl.lit(None), "(Pl.litNull : Pl.Expr Float)"),
        ("lit+lit", pl.lit(1.0) + pl.lit(2), f"{LF(1.0)}.add {LI(2)}"),
        ("when lit", pl.when(pl.lit(True)).then(1).otherwise(0), f"Pl.wto (Pl.litB true) {LI(1)} {LI(0)}"),
        ("when col", pl.when(x > 0).then(1).otherwise(0), f'Pl.wto ((c "x").gt {LI(0)}) {LI(1)} {LI(0)}'),
        ("when agg none", pl.when(x.sum() > 0).then(pl.lit(1)).otherwise(None), f'Pl.wto ((c "x").sum.gt {LI(0)}) {LI(1)} Pl.litNull'),
        ("when agg no otherwise", pl.when(x.sum() > 0).then(pl.lit(1)), f'Pl.wto ((c "x").sum.gt {LI(0)}) {LI(1)} Pl.litNull'),
        ("cum_sum", x.cum_sum(), '(c "x").cumSum'), ("alias", x.alias("z"), '(c "x").alias "z"'),
        ("agg alias", x.sum().alias("Column"), '(c "x").sum.alias "Column"'),
        ("castF", x.cast(pl.Float64), '(c "x").castF64'), ("agg castF", x.sum().cast(pl.Float64), '(c "x").sum.castF64'),
        ("is_null", x.is_null(), '(c "x").isNull'), ("is_not_null agg", x.max().is_not_null(), '(c "x").max.isNotNull'),
        ("fill_null", x.fill_null(0.0), f'(c "x").fillNull {LF(0.0)}'), ("fill_null agg", x.mean().fill_null(0.0), f'(c "x").mean.fillNull {LF(0.0)}'),
        ("neg", -x, '(c "x").neg'), ("neg agg", -x.sum(), '(c "x").sum.neg'), ("not", ~(x > 0), f'((c "x").gt {LI(0)}).not'),
        ("log", x.log(), '(c "x").log'), ("exp agg", x.sum().exp(), '(c "x").sum.exp'), ("abs", x.abs(), '(c "x").abs'),
        ("floor lit", pl.lit(1.5).floor(), f"{LF(1.5)}.floor"), ("sign", x.sign(), '(c "x").sign'), ("is_finite agg", x.sum().is_finite(), '(c "x").sum.isFinite'),
        ("is_in F", x.is_in(pl.Series([1.0, 2.0]).implode()), f'(c "x").isInF [some {F(1.0)}, some {F(2.0)}]'),
        ("is_in F agg", x.max().is_in(pl.Series([1.0, 2.0]).implode()), f'(c "x").max.isInF [some {F(1.0)}, some {F(2.0)}]'),
        ("is_in S", x.is_in(["A", "B"]), '(c "x").isInS ["A", "B"]'),
        ("is_in S lit", pl.lit("A").is_in(["A", "B"]), '(Pl.litS "A" : Pl.Expr Float).isInS ["A", "B"]'),
        ("allH cols", pl.all_horizontal([x.is_null(), y.is_null()]), 'Pl.allHorizontal [(c "x").isNull, (c "y").isNull]'),
        ("allH names", pl.all_horizontal(pl.col("x", "y").is_not_null()), 'Pl.allHorizontal (["x", "y"].map fun n => (c n).isNotNull)'),
        ("allH aggs", pl.all_horizontal([x.sum() > 0, pl.lit(True)]), f'Pl.allHorizontal [(c "x").sum.gt {LI(0)}, Pl.litB true]'),
        ("sumH cols", pl.sum_horizontal([x, y]), 'Pl.sumHorizontal true [c "x", c "y"]'),
        ("sumH aggs", pl.sum_horizontal([x.sum(), pl.lit(1.0)]), f'Pl.sumHorizontal true [(c "x").sum, {LF(1.0)}]'),
        ("minH lit col", pl.min_horizontal([x, pl.lit(200.0)]), f'Pl.minHorizontal true [c "x", {LF(200.0)}]'),
        ("maxH lits", pl.max_horizontal(pl.lit(1.0), pl.lit(2.0)), f'Pl.maxHorizontal true [{LF(1.0)}, {LF(2.0)}]'),
        ("maxH aggs", pl.max_horizontal(x.min(), y.max()), 'Pl.maxHorizontal true [(c "x").min, (c "y").max]'),
        ("lit date", pl.lit(dt.date(2026, 1, 1)), "Pl.litCell (Tabular.Cell.num (none : Option Float))"),
        ("lt col", sc.lt(x, 0.5), f'lt {EX("c \"x\"")} {EF(0.5)}'), ("lt lits", sc.lt(1, 2), "lt (.int 1 : ExprOrNum Float) (.int 2)"),
        ("gt agg", sc.gt(x.sum(), 0), f'gt {EX("(c \"x\").sum")} (.int 0)'),
        ("le", sc.le(x, y), f'le {EX("c \"x\"")} {EX("c \"y\"")}'), ("ge agg lit", sc.ge(x.mean(), 0.5), f'ge {EX("(c \"x\").mean")} {EF(0.5)}'),
        ("eq", sc.eq(x, 1), f'eq {EX("c \"x\"")} (.int 1)'), ("eq lits", sc.eq(1.0, 1), f"eq {EF(1.0)} (.int 1)"),
        ("flag", sc.flag(x > 0), f'flag ((c "x").gt {LI(0)})'), ("flag agg", sc.flag(x.sum() > 0), f'flag ((c "x").sum.gt {LI(0)})'),
        ("sas_round col", sc.sas_round(x), f'sas_round {EX("c \"x\"")}'), ("sas_round lit", sc.sas_round(1.5), f"sas_round {EF(1.5)}"),
        ("sas_round agg", sc.sas_round(x.mean()), f'sas_round {EX("(c \"x\").mean")}'),
        ("div out cols (mapBatches2)", sc.div(x, y), 'Pl.mapBatches2 (c "x").castF64 (c "y").castF64 (fun a _ => a)'),
        ("div out agg/lit", sc.div(x.sum(), 100), f'Pl.mapBatches2 (c "x").sum.castF64 {LI(100)}.castF64 (fun a _ => a)'),
        ("rank-free: sum of filter of when", pl.when(x > 0).then(x).otherwise(None).sum(), f'(Pl.wto ((c "x").gt {LI(0)}) (c "x") Pl.litNull).sum'),
    ]
    # known and expected differences (reported by the implementers)
    KNOWN = {"allH names": "pl.col('x','y') serializes as a Selector (no \"Column\" key): Python True, Lean false",
             "div out cols (mapBatches2)": "map_batches cannot be serialized: Python raises (expected -1), Lean returns a Bool",
             "div out agg/lit": "map_batches cannot be serialized: Python raises (expected -1), Lean returns a Bool"}
    cases = []
    for k, (lab, p, _) in enumerate(S):
        try:
            e = int(sc._is_scalar(p))
        except Exception as ex:
            print("PY RAISES", lab, type(ex).__name__, str(ex)[:80])
            e = -1
        cases.append((f"{k:02d} {lab}", "_is_scalar", e, {"expect_diff": True, "note": KNOWN[lab]} if lab in KNOWN else {}))
    s = Suite("b1_isscalar")
    s.ints(C, "[" + ", ".join(f"(if _is_scalar ({l}) then 1 else 0)" for _, _, l in S) + "]", cases, use_kit=False)
    return s


# ---------------------------------------------------------------- suite 2: comparisons + flag
def suite_cmp() -> Suite:
    E = [None, float("nan"), -math.inf, -1.5, -0.0, 0.0, 1.5, math.inf]
    fr = pl.DataFrame({"x": pl.Series([a for a in E for _ in E], dtype=pl.Float64), "c": pl.Series([b for _ in E for b in E], dtype=pl.Float64)})
    EI_ = [None, -1, 0, 2]
    fi = pl.DataFrame({"i": pl.Series([a for a in EI_ for _ in EI_], dtype=pl.Int64), "j": pl.Series([b for _ in EI_ for b in EI_], dtype=pl.Int64),
                       "y": pl.Series([None, -1.0, 0.5, float("nan")] * 4, dtype=pl.Float64),
                       "b": pl.Series([True, None, False, True] * 4, dtype=pl.Boolean)})
    LETS2 = ("let E : List (Option Float) := [" + ", ".join(lt.lean_opt_float(v) for v in E) + "]; "
             "let fr : Pl.Frame Float := [(\"x\", .f64 (E.flatMap (fun a => E.map (fun _ => a)))), (\"c\", .f64 (E.flatMap (fun _ => E)))]; "
             + lt.lean_frame_let("fi", fi))
    terms, cases = [], []

    def case2(unit, label, pyres, lean):
        terms.append(f"dg (tR ({lean}))")
        cases.append((f"{len(cases):03d} {label}", unit, cmp.canon_frame(pyres)))

    cx, cc = EX('c "x"'), EX('c "c"')
    for nm in ["lt", "le", "gt", "ge", "eq"]:
        f = getattr(sc, nm)
        A = [("col,col", fr, "fr", (pl.col("x"), pl.col("c")), (cx, cc)),
             ("col,0.0", fr, "fr", (pl.col("x"), 0.0), (cx, EF(0.0))),
             ("col,1.5", fr, "fr", (pl.col("x"), 1.5), (cx, EF(1.5))),
             ("1.5,col", fr, "fr", (1.5, pl.col("c")), (EF(1.5), cc)),
             ("col,0", fr, "fr", (pl.col("x"), 0), (cx, EI(0))),
             ("0,col", fr, "fr", (0, pl.col("x")), (EI(0), cx)),
             ("col,nullF", fr, "fr", (pl.col("x"), pl.lit(None, pl.Float64)), (cx, EX("Pl.litOptF none"))),
             ("nullF,col", fr, "fr", (pl.lit(None, pl.Float64), pl.col("x")), (EX("Pl.litOptF none"), cx)),
             ("1.5,2.5", fr, "fr", (1.5, 2.5), (EF(1.5), EF(2.5))),
             ("2,2", fr, "fr", (2, 2), (EI(2), EI(2))),
             ("1,2.0", fr, "fr", (1, 2.0), (EI(1), EF(2.0))),
             ("i,j", fi, "fi", (pl.col("i"), pl.col("j")), (EX('c "i"'), EX('c "j"'))),
             ("i,0", fi, "fi", (pl.col("i"), 0), (EX('c "i"'), EI(0))),
             ("i,0.5", fi, "fi", (pl.col("i"), 0.5), (EX('c "i"'), EF(0.5))),
             ("i,y", fi, "fi", (pl.col("i"), pl.col("y")), (EX('c "i"'), EX('c "y"'))),
             ("y,sum(i)", fi, "fi", (pl.col("y"), pl.col("i").sum()), (EX('c "y"'), EX('(c "i").sum')))]
        for lab, df, dfl, pa, la in A:
            case2(nm, f"{nm} select {lab}", df.select(f(*pa)), f"{dfl}.select [({nm} {la[0]} {la[1]}).pos]")
        case2(nm, f"{nm} with_columns col,col", fr.with_columns(f(pl.col("x"), pl.col("c"))), f"fr.withColumns [({nm} {cx} {cc}).pos]")
        case2(nm, f"{nm} with_columns 1.5,col", fr.with_columns(f(1.5, pl.col("c"))), f"fr.withColumns [({nm} {EF(1.5)} {cc}).pos]")
        case2(nm, f"{nm} named Z", fi.with_columns(Z=f(pl.col("y"), 0.5)), f'fi.withColumns [("Z", {nm} {EX("c \"y\"")} {EF(0.5)})]')
    FL = [("flag x>c", fr, "fr", sc.flag(pl.col("x") > pl.col("c")), 'flag ((c "x").gt (c "c"))'),
          ("flag x>=0.5", fr, "fr", sc.flag(pl.col("x") >= 0.5), f'flag ((c "x").ge {LF(0.5)})'),
          ("flag bool col", fi, "fi", sc.flag(pl.col("b")), 'flag (c "b")'),
          ("flag lit True", fi, "fi", sc.flag(pl.lit(True)), "flag (Pl.litB true)"),
          ("flag ge()", fr, "fr", sc.flag(sc.ge(pl.col("x"), 0.5)), f"flag (ge {cx} {EF(0.5)})"),
          ("flag i==j", fi, "fi", sc.flag(pl.col("i") == pl.col("j")), 'flag ((c "i").eq (c "j"))')]
    for lab, df, dfl, pe, le_ in FL:
        case2("flag", lab + " select", df.select(pe), f"{dfl}.select [({le_}).pos]")
        case2("flag", lab + " with_columns", df.with_columns(pe), f"{dfl}.withColumns [({le_}).pos]")
    # the 5 comparison units share their 19 terms: one Lean lambda P over the unit (short input)
    per = 19
    gen = lambda t: t.replace("(lt ", "(f ").replace(", lt ", ", f ")  # noqa: E731
    tmpl = [gen(t) for t in terms[:per]]
    for k, nm in enumerate(["lt", "le", "gt", "ge", "eq"]):
        assert [t.replace(f"({nm} ", "(f ").replace(f", {nm} ", ", f ") for t in terms[k * per:(k + 1) * per]] == tmpl
    lets = (C + LETS2 + "let P := fun (f : ExprOrNum Float → ExprOrNum Float → Pl.Expr Float) => [" + ", ".join(tmpl) + "]; ")
    body = ("(([lt, le, gt, ge, eq] : List (ExprOrNum Float → ExprOrNum Float → Pl.Expr Float)).flatMap P ++ [" + ", ".join(terms[5 * per:]) + "])")
    short = [("(Float.ofBits 4609434218613702656)", "v15"), ("(Float.ofBits 4602678819172646912)", "v05"),
             ("(Float.ofBits 9221120237041090560)", "vn"), ("(Float.ofBits 13830554455654793216)", "vm1")]
    for a, b in short:
        lets, body = lets.replace(a, b), body.replace(a, b)
    lets = "".join(f"let {b} := {a[1:-1]}; " for a, b in short) + lets
    s = Suite("b1_cmp")
    s.digest_body(lets, body, cases, gen=False, table=False)
    return s


# ---------------------------------------------------------------- suite 3: sas_round
def suite_round() -> Suite:
    V = [-0.3, 0.3, 0.5, -0.5, 1.5, -1.5, 2.5, -2.5, 0.5 - 1e-14, 0.5 - 1e-10, 0.49999999999999994, 1.5 - 1e-13, 1000000.5 - 1e-7,
         1000000.4999999999, 2.0**52, 2.0**52 - 0.5, 2.0**52 - 1.5, 2.0**52 + 1, -2.0**53, None, float("nan"), math.inf, -math.inf, -0.0, 0.0,
         123456.5, 5e-324, 4503599627370495.5, 0.7, -2.4999999999999996, 1e300, -0.49, 7.0, -7.0, 3.4999999999995, 3.49999999999]
    fv = pl.DataFrame({"x": pl.Series(V, dtype=pl.Float64), "g": pl.Series([i % 3 for i in range(len(V))], dtype=pl.Int64)})
    fint = pl.DataFrame({"i": pl.Series([None, -3, 0, 5], dtype=pl.Int64)})
    fm = pl.DataFrame({"x": pl.Series([-0.25, -0.35, -0.2, -0.4, -0.3, -0.3], dtype=pl.Float64), "g": pl.Series([0, 0, 1, 1, 2, 2], dtype=pl.Int64)})
    lets = C + lt.lean_frame_let("fv", fv) + lt.lean_frame_let("fint", fint) + lt.lean_frame_let("fm", fm) + "let f0 : Pl.Frame Float := []; "
    cases = []

    def case3(label, pyres, lean):
        cases.append((f"{len(cases):02d} {label}", "sas_round", f"tR ({lean})", cmp.canon_frame(pyres)))

    sx = f'sas_round {EX("c \"x\"")}'
    case3("col multi-row select", fv.select(sc.sas_round(pl.col("x"))), f"fv.select [({sx}).pos]")
    case3("col multi-row with_columns", fv.with_columns(sc.sas_round(pl.col("x"))), f"fv.withColumns [({sx}).pos]")
    case3("int col", fint.select(sc.sas_round(pl.col("i"))), f'fint.select [(sas_round {EX("c \"i\"")}).pos]')
    for v in [-0.3, -0.0, 0.3, 2.5, None, -0.5, float("nan")]:
        f1 = pl.DataFrame({"x": pl.Series([v], dtype=pl.Float64)})
        case3(f"1-row frame {v} select", f1.select(sc.sas_round(pl.col("x"))), f"{lt.lean_frame(f1)}.select [({sx}).pos]")
        case3(f"1-row frame {v} with_columns", f1.with_columns(sc.sas_round(pl.col("x"))), f"{lt.lean_frame(f1)}.withColumns [({sx}).pos]")
    for v in [-0.3, -0.0, 0.0, 0.3, 2.5, -2.5, 1e300, -0.5, 0.5 - 1e-14]:
        case3(f"literal {v} pl.select", pl.select(sc.sas_round(v)), f"f0.select [(sas_round {EF(v)}).pos]")
        case3(f"literal {v} fv.select", fv.select(sc.sas_round(v)), f"fv.select [(sas_round {EF(v)}).pos]")
        case3(f"literal {v} fv.with_columns", fint.with_columns(sc.sas_round(v)), f"fint.withColumns [(sas_round {EF(v)}).pos]")
    for n in [3, 0, -4]:
        case3(f"int literal {n}", fint.select(sc.sas_round(n)), f"fint.select [(sas_round {EI(n)}).pos]")
    case3("agg mean (-0.3) select", fm.select(sc.sas_round(pl.col("x").mean())), f'fm.select [(sas_round {EX("(c \"x\").mean")}).pos]')
    case3("agg mean with_columns", fm.with_columns(sc.sas_round(pl.col("x").mean())), f'fm.withColumns [(sas_round {EX("(c \"x\").mean")}).pos]')
    case3("group_by 3 groups mean", fm.group_by("g", maintain_order=True).agg(r=sc.sas_round(pl.col("x").mean())),
          f'fm.groupByAgg ["g"] [("r", sas_round {EX("(c \"x\").mean")})]')
    fm1 = fm.with_columns(g=pl.lit(0, pl.Int64))
    case3("group_by 1 group mean", fm1.group_by("g", maintain_order=True).agg(r=sc.sas_round(pl.col("x").mean())),
          f'{lt.lean_frame(fm1)}.groupByAgg ["g"] [("r", sas_round {EX("(c \"x\").mean")})]')
    s = Suite("b1_round")
    s.digest(lets, cases, gen=False, table=False)
    return s


# ---------------------------------------------------------------- suite 4: confusion_metrics
def suite_confusion() -> Suite:
    nan = float("nan")
    pd_ = [0.1, 0.5, 0.9, 0.5, None, nan, 0.3, 0.7, 0.2, 0.8, 0.5000000000000001, 0.49999999999999994]
    dfl = [0, 1, 1, 0, 1, 0, None, 1, 0, 1, 1, 1]
    F1 = pl.DataFrame({"id": [f"r{i}" for i in range(12)], "pd_logistic": pl.Series(pd_, dtype=pl.Float64), "default_flag": pl.Series(dfl, dtype=pl.Float64)})
    F2 = F1.with_columns(default_flag=pl.Series(dfl, dtype=pl.Int64))
    F4 = F1.with_columns(default_flag=pl.lit(0.0))
    F5 = F1.head(0)
    F6 = F1.slice(2, 1)
    F7 = pl.DataFrame({"predicted": pl.Series([9.5, 9.5, 9.5, 9.5, 9.5, 9.5]), "pd_logistic": pl.Series([0.9, 0.1, 0.6, 0.4, 0.7, 0.2]),
                       "default_flag": pl.Series([2.0, nan, 1.0, 0.0, nan, 2.0]), "z": pl.Series([1, 2, 3, 4, 5, 6])})
    F8 = pl.DataFrame({"pd_logistic": pl.Series([0, 1, 1, 0, None, 1], dtype=pl.Int64), "default_flag": pl.Series([1, 1, 0, 0, 1, None], dtype=pl.Int64)})
    F9 = pl.DataFrame({"pd_logistic": pl.Series([0.9, 0.8, 0.1, 0.2]), "default_flag": pl.Series([0.0, 0.0, 1.0, 1.0])})
    rnd = random.Random(7)
    F10 = pl.DataFrame({"default_flag": pl.Series([rnd.choice([0, 1, 1, 0, None]) for _ in range(60)], dtype=pl.Int64),
                        "pd_logistic": pl.Series([rnd.choice([None, nan, round(rnd.random(), 2), 0.5, rnd.random()]) for _ in range(60)], dtype=pl.Float64)})
    CM = [("F1 0.5", F1, 0.5), ("F1 0.3", F1, 0.3), ("F1 0.7", F1, 0.7), ("F1 2.0 (no positives)", F1, 2.0), ("F1 -1 (all positive)", F1, -1.0),
          ("F1 nan", F1, nan), ("F2 int flag 0.5", F2, 0.5), ("F4 one class", F4, 0.5), ("F5 empty", F5, 0.5), ("F6 one row", F6, 0.5),
          ("F7 odd flags, predicted exists", F7, 0.5), ("F8 int pd", F8, 0.5), ("F9 p=r=0", F9, 0.5), ("F10 random 0.5", F10, 0.5), ("F10 random 0.37", F10, 0.37)]
    FR = {"F1": F1, "F2": F2, "F4": F4, "F5": F5, "F6": F6, "F7": F7, "F8": F8, "F9": F9, "F10": F10}
    lets = "".join(lt.lean_frame_let(k, v) for k, v in FR.items()) + \
        'let cm := fun (t : Float) (fr : Pl.Frame Float) => let r := confusion_metrics t "sfx" fr; dg (tR r.1 ++ tR r.2.1 ++ tR r.2.2); '
    terms, cases = [], []
    for k, (lab, df, thr) in enumerate(CM):
        a, b, m = mc.confusion_metrics(thr, "sfx", df)
        terms.append(f"cm {F(thr)} {lab.split()[0]}")
        cases.append((f"{k:02d} {lab}", "confusion_metrics", fdig(a, b, m)))
    s = Suite("b1_confusion")
    s.ints(lets, "[" + ", ".join(terms) + "]", cases)
    return s


# ---------------------------------------------------------------- suite 5: direct cases (added when porting)
def lean_json(o) -> str:
    """A parsed JSON value as a `Pl.Json` term (dict / list / anything else is an atom)."""
    if isinstance(o, dict):
        return "(Pl.Json.dict [" + ", ".join(f"({lt.lean_str(k)}, {lean_json(v)})" for k, v in o.items()) + "])"
    if isinstance(o, list):
        return "(Pl.Json.list [" + ", ".join(lean_json(v) for v in o) + "])"
    return "Pl.Json.atom"


def suite_direct() -> Suite:
    terms, cases = [], []

    def add(unit, label, term, expected):
        terms.append(term)
        cases.append((f"{len(cases):02d} {label}", unit, expected))

    add("_TWO52", "_TWO52 bits", "((_TWO52 (α := Float)).toBits.toNat : Int)", cmp.fbits(sc._TWO52))
    add("_ROUND_FUZZ", "_ROUND_FUZZ bits", "((_ROUND_FUZZ (α := Float)).toBits.toNat : Int)", cmp.fbits(sc._ROUND_FUZZ))
    J = [{}, [], "x", None, 3, {"Column": "x"}, {"Agg": {"Column": "x"}}, {"Agg": 1, "Column": 2}, {"Column": 2, "Agg": 1},
         {"a": {"Column": 1}}, {"a": {"Agg": {"Column": 1}}}, [{"Agg": {"Column": 1}}, {"Column": 1}], [[], [[{"b": [{"Column": 0}]}]]],
         {"a": [1, {"b": {"Column": 0}}]}, {"Column": {"Agg": 1}}, {"x": {"Agg": 1}, "y": {"Column": 1}}, {"x": {"y": {"z": []}}, "w": "Column"},
         {"BinaryExpr": {"left": {"Agg": {"Sum": {"Column": "x"}}}, "op": "Plus", "right": {"Column": "y"}}}, ["Column", "Agg"]]
    for k, o in enumerate(J):
        add("_has_bare_column", f"json {k}: {o!r}", f"(if _has_bare_column {lean_json(o)} then 1 else 0)", int(sc._has_bare_column(o)))
    fz = pl.DataFrame({"x": pl.Series([1.5, None], dtype=pl.Float64), "y": pl.Series([2, 3], dtype=pl.Int64)})
    x, y = pl.col("x"), pl.col("y")
    for lab, py, le_ in [("_e(2.5)", sc._e(2.5), f"_e {EF(2.5)}"), ("_e(-0.0)", sc._e(-0.0), f"_e {EF(-0.0)}"),
                         ("_e(nan)", sc._e(float("nan")), f"_e {EF(float('nan'))}"), ("_e(7)", sc._e(7), f"_e {EI(7)}"),
                         ("_e(-3)", sc._e(-3), f"_e {EI(-3)}"), ("_e(col x)", sc._e(x), f'_e {EX("c \"x\"")}')]:
        add("_e", lab + " select", f"dg (tR (fz.select [({le_}).pos]))", fdig(fz.select(py)))
    for lab, py, le_ in [("first=col x", sc._named(x, y + 1), f'_named {EX("c \"x\"")} ((c "y").add {LI(1)})'),
                         ("first=2.5 (literal)", sc._named(2.5, y), f'_named {EF(2.5)} (c "y")'),
                         ("first=x.alias(z)", sc._named(x.alias("z"), y), f'_named {EX("(c \"x\").alias \"z\"")} (c "y")'),
                         ("first=col '' (empty name)", sc._named(pl.col(""), y), f'_named {EX("c \"\"")} (c "y")'),
                         ("first=x+y", sc._named(x + y, y), f'_named {EX("(c \"x\").add (c \"y\")")} (c "y")')]:
        add("_named", lab + " select", f"dg (tR (fz.select [({le_}).pos]))", fdig(fz.select(py)))
    s = Suite("b1_direct")
    s.ints(C + lt.lean_frame_let("fz", fz), "[" + ", ".join(terms) + "]", cases)
    added = "direct cases added when porting the generator (the implementers exercised this unit only through the others)"
    s.notes = {"_TWO52": added + ": sas_round", "_ROUND_FUZZ": added + ": sas_round", "_has_bare_column": added + ": _is_scalar",
               "_e": added + ": lt..eq, sas_round, _is_scalar", "_named": added + ": lt..eq, flag, sas_round"}
    return s


if __name__ == "__main__":
    for mk in (suite_isscalar, suite_cmp, suite_round, suite_confusion, suite_direct):
        mk().write()
