"""Bundle B2 differential checks (sas_compat: div, sas_sum, sas_min, sas_max, sas_log, sas_exp,
sql_sum, sql_mean, sql_min, sql_max): the accepted Lean against the real Python, bit for bit,
through the carrier item `def:zz_carrier`.

  uv run python migration/diffeval/units/b2_gen.py
        writes, per suite S, migration/diffeval/work/b2_S.inputs.json (the eval_decl call: item,
        decl, inputs) and work/b2_S.expected.json (labels, expected token lists, Lean terms).
        The suites `sum` and `minmax` hold every case twice: Lean `full = true` against Python with
        the default thread pool, and Lean `full = false` against a child process run with
        POLARS_MAX_THREADS=1.
        Also writes work/b2_S.json (the suite in the format of suite.py: one `ints` input, one
        digest per case, `primitive` = the unit under test), so that compare.py and
        `receipts.py units b2` apply.
  evaluate: eval_decl(item_id="def:zz_carrier", decl="zz_carrier", inputs=<inputs>) and save the
        `output` of each input, one per line, in work/b2_S.out.txt (one digest per case).
  uv run python migration/diffeval/compare.py migration/diffeval/work/b2_S.json migration/diffeval/work/b2_S.out.txt
        compares the digests. A case marked expect_diff is a recorded limit of the prelude
        (RULEBOOK §6; reason in its note): XFAIL while it differs, XPASS when it no longer does.
  uv run python migration/diffeval/receipts.py units b2
        one row per unit in receipts/units.tsv
  uv run python migration/diffeval/units/b2_gen.py full S i
        prints the eval_decl input that returns the whole token list of case i
  uv run python migration/diffeval/units/b2_gen.py tok S i '<the output>'
        decodes it and prints where it differs from the expected value.

Data are generated inside Lean by the kit's seeded generators (kit.GEN) and mirrored in Python
(kit.gF / kit.gI), which keeps the inputs short.
"""
from __future__ import annotations

import ast
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent))
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

WORK = HERE.parent / "work"
NANB = 0x7FF8000000000000
NAN, INF = math.nan, math.inf
T1 = "--t1" in sys.argv  # child process: one polars thread, Lean `full = false`
FULL = "false" if T1 else "true"

# ------------------------------------------------------------------ token kit (Lean and Python)
KIT = (
    "let tS := fun (s : String) => ((s.length : Int) :: s.toList.map (fun (ch : Char) => (ch.toNat : Int))); "
    "let tC := fun (c : Pl.Col Float) => (match c with "
    "| .f64 v => 1 :: (v.length : Int) :: v.flatMap (fun (o : Option Float) => (match o with | none => [0] | some x => [1, (x.toBits.toNat : Int)] : List Int)) "
    "| .int v => 2 :: (v.length : Int) :: v.flatMap (fun (o : Option Int) => (match o with | none => [0] | some n => [1, n] : List Int)) "
    "| .null n => [6, (n : Int)] | _ => [9] : List Int); "
    "let tR := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => tS p.1 ++ tC p.2); "
    "let dg := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1000003 + x + 7) % 2305843009213693951) 17; "
    "let c := fun (n : String) => Pl.col (α := Float) n; "
    "let X := fun (n : String) => ExprOrNum.expr (c n); "
    "let L := fun (b : UInt64) => (ExprOrNum.float (Float.ofBits b) : ExprOrNum Float); "
    "let I := fun (n : Int) => (ExprOrNum.int n : ExprOrNum Float); "
    "let li := fun (n : Int) => (Pl.litI n : Pl.Expr Float); "
    "let W := fun (e : Pl.Expr Float) => ExprOrNum.expr e; "
)


def fb(x: float) -> int:
    return NANB if x != x else struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def tS(s: str) -> list[int]:
    return [len(s)] + [ord(ch) for ch in s]


def tC(s: pl.Series) -> list[int]:
    k, v = lt.col_kind(s.dtype), s.to_list()
    if k == "f64":
        return [1, len(v)] + [t for x in v for t in ([0] if x is None else [1, fb(x)])]
    if k == "int":
        return [2, len(v)] + [t for x in v for t in ([0] if x is None else [1, x])]
    if k == "bool":
        return [3, len(v)] + [t for x in v for t in ([0] if x is None else [1, int(x)])]
    if k == "null":
        return [6, len(v)]
    raise TypeError(s.dtype)


def tR(df: pl.DataFrame) -> list[int]:
    return [df.width] + [t for n in df.columns for t in tS(n) + tC(df.get_column(n))]


def dg(t: list[int]) -> int:
    h = 17
    for x in t:
        h = (h * 1000003 + x + 7) % 2305843009213693951
    return h


def decode(t: list[int]) -> list:
    """token list of a frame -> [(name, kind, values)]"""
    p, out = 1, []
    for _ in range(t[0]):
        n = t[p]
        name = "".join(chr(x) for x in t[p + 1:p + 1 + n])
        p += 1 + n
        kind, ln = t[p], t[p + 1]
        p += 2
        vals = []
        if kind in (1, 2, 3):
            for _ in range(ln):
                if t[p] == 0:
                    vals.append(None)
                    p += 1
                else:
                    vals.append(t[p + 1])
                    p += 2
        out.append((name, {1: "f64", 2: "int", 3: "bool", 5: "cell", 6: "null"}[kind], vals if kind in (1, 2, 3) else ln))
    return out


# ------------------------------------------------------------------ data (Lean and Python)
E = [None, NAN, -INF, -1.5, -0.0, 0.0, 1.5, INF]
EZ = [None, NAN, -INF, -1.5, 0.0, 1.5, INF]  # no -0.0: min/max of zeros of opposite sign is a recorded limit
LE, LEZ = lt.lean_list([lt.lean_opt_float(v) for v in E]), lt.lean_list([lt.lean_opt_float(v) for v in EZ])


def cross(ev):
    return [a for a in ev for _ in ev], [b for _ in ev for b in ev]


def mk(cols: dict) -> pl.DataFrame:
    return pl.DataFrame({k: pl.Series(v, dtype=pl.Float64 if t == "f" else pl.Int64) for k, (t, v) in cols.items()})


_fx, _fc = cross(E)
F = mk({"x": ("f", _fx), "c": ("f", _fc),
        **{n: ("f", kit.gF(k + 1, 64, 30, 3, E)) for k, n in enumerate("abdef")},
        **{n: ("f", kit.gF(k + 6, 64, 30, 3, EZ)) for k, n in enumerate("pqrst")},
        "i": ("i", kit.gI(11, 64, 20, 5, 2)), "j": ("i", kit.gI(12, 64, 20, 5, 2)), "g": ("i", kit.gI(13, 64, 0, 5, 0))})
_zx, _zc = cross(EZ)
Z = mk({"x": ("f", _zx), "c": ("f", _zc)})
G = mk({"a": ("f", kit.gF(21, 300, 15, 3, [None])), "h": ("f", kit.gF(22, 300, 40, 3, E)), "hz": ("f", kit.gF(23, 300, 40, 3, EZ)),
        "i": ("i", kit.gI(24, 300, 15, 7, 3)), "g": ("i", kit.gI(25, 300, 0, 9, 0)), "g2": ("i", kit.gI(26, 300, 0, 200, 0))})
H = mk({"n": ("f", [1e308, 5e-324, -1e308, 1e-200, 1.0, 4.9e-324]), "m": ("f", [1e-308, 1e308, 1e-10, 1e200, 3.0, 2.0])})
LETS_E = f"let E : List (Option Float) := {LE}; let EZ : List (Option Float) := {LEZ}; "
LETS_F = (
    LETS_E +
    'let F : Pl.Frame Float := [("x", Pl.Col.f64 (E.flatMap (fun a => E.map (fun _ => a)))), ("c", Pl.Col.f64 (E.flatMap (fun _ => E)))] ++ '
    '[("a", 1), ("b", 2), ("d", 3), ("e", 4), ("f", 5)].map (fun (p : String × Nat) => (p.1, Pl.Col.f64 (gF p.2 64 30 3 E))) ++ '
    '[("p", 6), ("q", 7), ("r", 8), ("s", 9), ("t", 10)].map (fun (p : String × Nat) => (p.1, Pl.Col.f64 (gF p.2 64 30 3 EZ))) ++ '
    '[("i", Pl.Col.int (gI 11 64 20 5 2)), ("j", Pl.Col.int (gI 12 64 20 5 2)), ("g", Pl.Col.int (gI 13 64 0 5 0))]; '
    "let F0 : Pl.Frame Float := F.map (fun (p : String × Pl.Col Float) => (p.1, p.2.take [])); "
    "let F1 : Pl.Frame Float := F.takeRows [27]; let F2 : Pl.Frame Float := F.takeRows [9]; "
)
LETS_Z = 'let Z : Pl.Frame Float := [("x", Pl.Col.f64 (EZ.flatMap (fun a => EZ.map (fun _ => a)))), ("c", Pl.Col.f64 (EZ.flatMap (fun _ => EZ)))]; '
LETS_G = (
    LETS_E +
    'let G : Pl.Frame Float := [("a", Pl.Col.f64 (gF 21 300 15 3 [none])), ("h", Pl.Col.f64 (gF 22 300 40 3 E)), ("hz", Pl.Col.f64 (gF 23 300 40 3 EZ)), '
    '("i", Pl.Col.int (gI 24 300 15 7 3)), ("g", Pl.Col.int (gI 25 300 0 9 0)), ("g2", Pl.Col.int (gI 26 300 0 200 0))]; '
    "let G0 : Pl.Frame Float := G.map (fun (p : String × Pl.Col Float) => (p.1, p.2.take [])); "
)
LETS_H = f"let H : Pl.Frame Float := {lt.lean_frame(H)}; "
FR = {"F": F, "F0": F.clear(), "F1": F[27:28], "F2": F[9:10], "Z": Z, "G": G, "G0": G.clear(), "H": H}

# ------------------------------------------------------------------ dual terms: (python, lean)
# An operand is a pair (Python ExprOrNum, Lean term of type ExprOrNum Float); an expression is a
# pair (pl.Expr, Lean term of type Pl.Expr Float).


def X(n):
    return pl.col(n), f'(X "{n}")'


def Lf(v: float):
    return v, f"(L {fb(v) if v == v else NANB})"


def Li(n: int):
    return n, f"(I {lt.lean_int(n)})"


def W(e):  # an expression pair used as an operand
    return e[0], f"(W {e[1]})"


def ex(py, lean):  # an expression pair given by hand
    return py, f"({lean})"


def u(name, *ops):  # a one- or two-operand unit
    return getattr(sc, name)(*[o[0] for o in ops]), f"({name} {' '.join(o[1] for o in ops)})"


def v(name, *ops):  # a list unit (sas_sum, sas_min, sas_max) with the `full` of this process
    return getattr(sc, name)(*[o[0] for o in ops]), f"({name} {FULL} [{', '.join(o[1] for o in ops)}])"


def col(n):
    return pl.col(n), f'(c "{n}")'


NULLF = ex(pl.lit(None, pl.Float64), "Pl.litOptF none")
NULL = ex(pl.lit(None), "Pl.litNull")
SUITES: dict[str, dict] = {}
UNIT = ""  # the unit under test of the cases that follow (the `primitive` of the receipt)


def case(suite, label, frame, how, exprs, xfail=""):
    """how: sel (named select), selp (positional select), wc (named with_columns), wcp (positional),
    agg:<key> (group_by(key, maintain_order=True).agg, named). exprs: dict name -> pair, or a pair."""
    df = FR[frame]
    try:
        if how == "selp":
            py, lean = df.select(exprs[0]), f"{frame}.select [{exprs[1]}.pos]"
        elif how == "wcp":
            py, lean = df.with_columns(exprs[0]), f"{frame}.withColumns [{exprs[1]}.pos]"
        else:
            named = {k: e[0] for k, e in exprs.items()}
            ll = "[" + ", ".join(f'("{k}", {e[1]})' for k, e in exprs.items()) + "]"
            if how == "sel":
                py, lean = df.select(**named), f"{frame}.select {ll}"
            elif how == "wc":
                py, lean = df.with_columns(**named), f"{frame}.withColumns {ll}"
            else:
                key = how.split(":")[1]
                py, lean = df.group_by(key, maintain_order=True).agg(**named), f'{frame}.groupByAgg ["{key}"] {ll}'
    except Exception as exn:  # Python raises: a case is never dropped silently (README)
        raise RuntimeError(f"PYTHON RAISES {suite}/{label}: {type(exn).__name__}: {str(exn)[:120]}") from exn
    s = SUITES.setdefault(suite, {"labels": [], "units": [], "expected": [], "terms": [], "xfail": []})
    s["units"].append(UNIT)
    s["labels"].append(label)
    s["expected"].append(tR(py))
    s["terms"].append(f"tR ({lean})")
    s["xfail"].append(xfail)


x, c, a, b, d, e, f, i, j = (X(n) for n in "xcabdefij")
p, q, r, s_, t = (X(n) for n in "pqrst")

# ================================================================== suite div
if not T1:
    S = UNIT = "div"
    num100 = W(ex(100 * pl.col("i"), '(li 100).mul (c "i")'))  # tr:436  div(100 * COUNT, COUNT.sum())
    isum = W(ex(pl.col("i").sum(), '(c "i").sum'))
    asum = W(ex(pl.col("a").sum(), '(c "a").sum'))
    icnt = W(ex(pl.col("i").count(), '(c "i").count'))
    case(S, "select columns/literals/ints/aggregates", "F", "sel", {
        "o0": u("div", x, c), "o1": u("div", x, Lf(2.0)), "o2": u("div", Lf(2.0), c), "o3": u("div", x, Li(0)),
        "o4": u("div", x, Lf(0.0)), "o5": u("div", x, Lf(-0.0)), "o6": u("div", i, j), "o7": u("div", i, Li(100)),
        "o8": u("div", num100, isum), "o9": u("div", x, W(ex(pl.lit(1.5, pl.Float64), f"Pl.litOptF (some {lt.lean_float(1.5)})"))),
        "o10": u("div", x, W(NULLF)), "o11": u("div", isum, i), "o12": u("div", a, b), "o13": u("div", a, x),
        "o14": u("div", Lf(-0.0), c), "o15": u("div", Li(-3), x), "o16": u("div", W(ex(pl.col("a") / pl.col("b"), '(c "a").div (c "b")')), Lf(0.5))})
    case(S, "with_columns positional col/col (replaces x)", "F", "wcp", u("div", x, c))
    case(S, "with_columns positional lit/col (appends literal)", "F", "wcp", u("div", Lf(2.0), c))
    case(S, "select positional col/col (name x)", "F", "selp", u("div", x, c))
    case(S, "select positional lit/col (name literal)", "F", "selp", u("div", Lf(2.0), x))
    case(S, "select positional alias q", "F", "selp", u("div", W(ex(pl.col("x").alias("q"), '(c "x").alias "q"')), c))
    case(S, "select scalars (1 row)", "F", "sel", {
        "o0": u("div", Lf(3.0), Li(2)), "o1": u("div", Li(3), Li(0)), "o2": u("div", Lf(0.0), Lf(0.0)), "o3": u("div", asum, isum),
        "o4": u("div", isum, icnt), "o5": u("div", W(ex(pl.len(), "Pl.len")), Li(7)), "o6": u("div", Lf(1.0), Lf(-0.0)),
        "o7": u("div", Lf(NAN), Lf(1.0)), "o8": u("div", Lf(INF), Lf(INF)), "o9": u("div", Lf(1.0), Lf(INF)), "o10": u("div", W(NULLF), Lf(1.0))})
    case(S, "with_columns positional lit/lit (broadcast)", "F", "wcp", u("div", Lf(3.0), Li(2)))
    case(S, "with_columns named agg/agg (broadcast)", "F", "wc", {"q": u("div", isum, icnt), "x": u("div", x, isum)})
    case(S, "overflow / underflow", "H", "sel", {"o0": u("div", X("n"), X("m")), "o1": u("div", X("m"), X("n")), "o2": u("div", X("n"), Lf(1e-300))})
    case(S, "empty frame select", "F0", "sel", {"o0": u("div", x, c), "o1": u("div", x, Lf(2.0)), "o2": u("div", Lf(1.0), Lf(2.0)), "o3": u("div", asum, x)})
    case(S, "empty frame select lit/lit alone", "F0", "selp", u("div", Lf(1.0), Lf(2.0)))
    case(S, "empty frame with_columns lit/lit", "F0", "wcp", u("div", Lf(1.0), Lf(2.0)))
    case(S, "empty frame agg/agg", "F0", "sel", {"o": u("div", asum, icnt)})
    case(S, "1-row frame", "F1", "sel", {"o0": u("div", x, c), "o1": u("div", Lf(2.0), c), "o2": u("div", a, isum)})
    case(S, "1-row frame with_columns", "F2", "wcp", u("div", Lf(1.0), c))
    case(S, "group_by agg (aggregates and literals)", "F", "agg:g", {
        "o0": u("div", asum, isum), "o1": u("div", isum, Li(2)), "o2": u("div", Lf(1.0), Li(2)),
        "o3": u("div", asum, W(ex(pl.len(), "Pl.len"))), "o4": u("div", W(ex(pl.col("a").mean(), '(c "a").mean')), icnt)})

# ================================================================== suite sum (sas_sum)
S = "sum_t1" if T1 else "sum"
UNIT = "sas_sum"
fl = lambda n: W(ex(sc.flag(pl.col(n) > 0), f'flag ((c "{n}").gt (li 0))'))  # noqa: E731  Int64 flags, fe:185
ops7 = [a, b, d, e, f, i, x]
case(S, "select 1..7 operands", "F", "sel", {f"o{n}": v("sas_sum", *ops7[:n]) for n in range(1, 8)})
case(S, "select literal operands, Int64 flags, int columns", "F", "sel", {
    "o0": v("sas_sum", Lf(1.5), a, b), "o1": v("sas_sum", a, Li(2), b), "o2": v("sas_sum", a, b, Lf(0.1)),
    "o3": v("sas_sum", a, Lf(0.0), b, Lf(-0.0), d), "o4": v("sas_sum", fl("a"), fl("b"), fl("d"), fl("e"), fl("f")),
    "o5": v("sas_sum", i, j, i), "o7": v("sas_sum", x, c),
    "o8": v("sas_sum", x, c, a), "o9": v("sas_sum", Lf(0.1), a, b, d, e), "o10": v("sas_sum", a, b, d, e, Lf(0.3))})
case(S, "select scalars (1 row)", "F", "sel", {
    "o0": v("sas_sum", Lf(1.0), Li(2), Lf(3.5)), "o1": v("sas_sum", W(NULL), W(NULLF)),
    "o2": v("sas_sum", Lf(0.1), Lf(0.2), Lf(0.3), Lf(0.4), Lf(0.5)), "o3": v("sas_sum", Lf(0.1), Lf(0.7), Lf(0.3)),
    "o4": v("sas_sum", W(ex(pl.col("a").sum(), '(c "a").sum')), W(ex(pl.col("b").sum(), '(c "b").sum')), Lf(1.0)),
    "o5": v("sas_sum", Lf(-0.0)), "o6": v("sas_sum", Lf(-0.0), Lf(-0.0)), "o7": v("sas_sum", Lf(-0.0), Lf(-0.0), W(NULLF))})
case(S, "select positional 3 operands (name a)", "F", "selp", v("sas_sum", a, b, d))
case(S, "select positional literal first (name literal)", "F", "selp", v("sas_sum", Lf(1.0), a))
case(S, "with_columns positional 5 operands (replaces a)", "F", "wcp", v("sas_sum", a, b, d, e, f))
case(S, "with_columns positional literals (broadcast)", "F", "wcp", v("sas_sum", Lf(1.0), Li(2), Lf(3.5)))
case(S, "empty frame", "F0", "sel", {"o0": v("sas_sum", a, b, d), "o1": v("sas_sum", Lf(1.0), Li(2)), "o2": v("sas_sum", a, b, d, e, f)})
case(S, "empty frame literals alone", "F0", "sel", {"o": v("sas_sum", Lf(1.0), Li(2), Lf(0.5))})
case(S, "1-row frames", "F1", "sel", {"o0": v("sas_sum", a, b, d, e, f), "o1": v("sas_sum", a, b, d)})
case(S, "1-row frame (2)", "F2", "wcp", v("sas_sum", a, b, d, e, f))
case(S, "PRELUDE null / zero literal operand with a column holding -0.0", "F", "sel",
     {"o0": v("sas_sum", W(NULLF), a, W(NULL)), "o1": v("sas_sum", Lf(0.0), a), "o2": v("sas_sum", a, W(NULLF))},
     xfail="recorded limit (RULEBOOK §6): a literal zero or null-literal operand of sum_horizontal: polars leaves the column "
           "unchanged (-0.0 stays -0.0), the model adds 0.0 (+0.0)")

# ================================================================== suite minmax (sas_min, sas_max)
S = "minmax_t1" if T1 else "minmax"
for nm in ("sas_min", "sas_max"):
    UNIT = nm
    case(S, f"{nm} cross product of edges, literals on either side", "Z", "sel", {
        "o0": v(nm, x, c), "o1": v(nm, x, Lf(200.0)), "o2": v(nm, Lf(0.0), x), "o3": v(nm, Lf(1.5), c), "o4": v(nm, x, Li(1)),
        "o5": v(nm, Li(2), x), "o6": v(nm, x, Lf(NAN)), "o7": v(nm, W(NULLF), x), "o8": v(nm, x, W(NULL))})
    case(S, f"{nm} 1, 3, 4, 5 operands, literals, int column with floats", "F", "sel", {
        "o1": v(nm, p), "o3": v(nm, p, q, r), "o4": v(nm, p, q, r, s_), "o5": v(nm, p, q, r, s_, t),
        "o6": v(nm, p, q, Lf(200.0)), "o7": v(nm, Lf(0.0), p, q, r, s_), "o8": v(nm, i, Lf(2.5)), "o9": v(nm, i, p),
        "o10": v(nm, p, i, q, Li(1), r), "o11": v(nm, W(NULL), p, W(NULLF))})
    case(S, f"{nm} select positional (name p)", "F", "selp", v(nm, p, Lf(200.0)))
    case(S, f"{nm} select positional literal first (name literal)", "F", "selp", v(nm, Lf(0.0), p))
    case(S, f"{nm} with_columns positional 3 operands", "F", "wcp", v(nm, p, q, r))
    case(S, f"{nm} scalars", "F", "sel", {"o0": v(nm, Lf(1.0), Lf(2.0)), "o1": v(nm, Lf(1.0), Lf(3.0), Lf(2.0)), "o2": v(nm, Lf(NAN), Lf(1.0)),
                                           "o3": v(nm, W(NULLF), W(NULLF)), "o4": v(nm, Lf(1.0), Li(2), Lf(0.5), Lf(4.0), Li(-1))})
    case(S, f"{nm} empty frame", "F0", "sel", {"o0": v(nm, p, Lf(1.0)), "o1": v(nm, Lf(1.0), p, q)})
    case(S, f"{nm} 1-row frame", "F1", "sel", {"o0": v(nm, p, q, r, s_, t), "o1": v(nm, p, Lf(200.0))})
    case(S, f"{nm} LIMIT zeros of opposite sign", "F", "sel", {"o": v(nm, x, c)},
         xfail="recorded limit (RULEBOOK §6): min/max of zeros of opposite sign")
    case(S, f"{nm} LIMIT integer operands only", "F", "sel", {"o": v(nm, i, Li(2))},
         xfail="recorded limit (RULEBOOK §6; §2.3: the prelude states min/max for Float64 inputs): integer operands only -> polars Int64, prelude Float64 (same values)")
    case(S, f"{nm} LIMIT Null-dtype operands only", "F", "sel", {"o": v(nm, W(NULL), W(NULL))},
         xfail="recorded limit (RULEBOOK §6, `litNull`: a Null-dtype column takes the dtype of the other operand; there is none): Null-dtype operands only -> polars Null dtype, prelude Float64 nulls")

# ================================================================== suite logexp (sas_log, sas_exp)
if not T1:
    S = "logexp"
    xp1 = W(ex(pl.col("x") + 1, '(c "x").add (li 1)'))  # fe:195  sas_log(col + 1)
    ab = W(ex(pl.col("a") / pl.col("b"), '(c "a").div (c "b")'))  # mc:288  sas_log(col / col)
    negx = W(ex(-pl.col("x"), '(c "x").neg'))  # pr:234  sas_exp(-col)
    a200 = W(ex(pl.col("a") * 200, '(c "a").mul (li 200)'))
    isum = W(ex(pl.col("i").sum(), '(c "i").sum'))
    amean = W(ex(pl.col("a").mean(), '(c "a").mean'))
    UNIT = "sas_log"
    case(S, "sas_log select columns", "F", "sel", {
        "o0": u("sas_log", x), "o1": u("sas_log", a), "o2": u("sas_log", i), "o3": u("sas_log", xp1), "o4": u("sas_log", ab)})
    case(S, "sas_log select scalars (1 row)", "F", "sel", {
        "o0": u("sas_log", Lf(2.0)), "o1": u("sas_log", Lf(-1.0)), "o2": u("sas_log", Li(3)), "o3": u("sas_log", Li(0)),
        "o4": u("sas_log", Lf(0.0)), "o5": u("sas_log", Lf(NAN)), "o11": u("sas_log", isum), "o13": u("sas_log", Lf(INF)),
        "o14": u("sas_log", Lf(-0.0)), "o16": u("sas_log", W(NULLF)), "o18": u("sas_log", Lf(5e-324))})
    case(S, "select positional sas_log (name x)", "F", "selp", u("sas_log", x))
    case(S, "select positional sas_log literal (name literal)", "F", "selp", u("sas_log", Lf(2.0)))
    case(S, "with_columns positional sas_log literal (broadcast)", "F", "wcp", u("sas_log", Lf(2.0)))
    case(S, "with_columns positional sas_log of a negative literal (null broadcast)", "F", "wcp", u("sas_log", Li(-1)))
    case(S, "sas_log with_columns named", "F", "wc", {"a": u("sas_log", a), "x": u("sas_log", xp1)})
    case(S, "sas_log empty frame", "F0", "sel", {"o0": u("sas_log", x), "o1": u("sas_log", i), "o2": u("sas_log", Lf(-1.0))})
    case(S, "sas_log empty frame literal alone", "F0", "sel", {"o0": u("sas_log", Lf(2.0))})
    case(S, "sas_log 1-row frame", "F1", "sel", {"o0": u("sas_log", x), "o2": u("sas_log", i)})
    UNIT = "sas_exp"
    case(S, "sas_exp select columns", "F", "sel", {
        "o5": u("sas_exp", x), "o6": u("sas_exp", a), "o7": u("sas_exp", i), "o8": u("sas_exp", negx), "o9": u("sas_exp", a200)})
    case(S, "sas_exp select scalars (1 row)", "F", "sel", {
        "o6": u("sas_exp", Lf(1000.0)), "o7": u("sas_exp", Li(1)), "o8": u("sas_exp", Lf(-1000.0)), "o9": u("sas_exp", Lf(709.0)),
        "o10": u("sas_exp", Lf(710.0)), "o12": u("sas_exp", amean), "o15": u("sas_exp", Lf(NAN)), "o17": u("sas_exp", W(NULLF)),
        "o19": u("sas_exp", Lf(-INF))})
    case(S, "with_columns positional sas_exp (replaces x)", "F", "wcp", u("sas_exp", x))
    case(S, "sas_exp with_columns named", "F", "wc", {"z": u("sas_exp", a)})
    case(S, "sas_exp empty frame", "F0", "sel", {"o3": u("sas_exp", x), "o4": u("sas_exp", Lf(1000.0))})
    case(S, "sas_exp empty frame literal alone", "F0", "sel", {"o1": u("sas_exp", Lf(1000.0))})
    case(S, "sas_exp 1-row frame", "F1", "sel", {"o1": u("sas_exp", a)})
    case(S, "sas_exp 1-row frame (2)", "F2", "wcp", u("sas_exp", x))

# ================================================================== suite sql (sql_sum, sql_mean, sql_min, sql_max)
if not T1:
    S = "sql"
    ga = col("a")
    g_ne2 = W(ex(pl.when(pl.col("g") != 2).then(pl.col("a")), 'Pl.wto ((c "g").ne (li 2)) (c "a") Pl.litNull'))  # group g = 2 all null
    allnull = W(ex(pl.when(pl.col("a") > 1e9).then(pl.col("a")), f'Pl.wto ((c "a").gt (Pl.litF {lt.lean_float(1e9)})) (c "a") Pl.litNull'))
    inull = W(ex(pl.when(pl.col("i") > 99).then(pl.col("i")), 'Pl.wto ((c "i").gt (li 99)) (c "i") Pl.litNull'))
    i_ne2 = W(ex(pl.when(pl.col("g") != 2).then(pl.col("i")), 'Pl.wto ((c "g").ne (li 2)) (c "i") Pl.litNull'))
    flg = W(ex(sc.flag(pl.col("a") > 0), 'flag ((c "a").gt (li 0))'))  # mc:112  sql_sum(flag(...)) inside agg
    A, Hh, Hz, Ii = X("a"), X("h"), X("hz"), X("i")
    for nm in ("sql_sum", "sql_mean", "sql_min", "sql_max"):
        UNIT = nm
        mm = nm in ("sql_min", "sql_max")
        lim = ("recorded limit (RULEBOOK §6; §2.3: the prelude states min/max for Float64 inputs): min/max of an Int64 input -> "
               "polars Int64, prelude Float64 (same values)") if mm else ""
        f64 = {"o0": u(nm, A), "o1": u(nm, Hz), "o2": u(nm, g_ne2), "o3": u(nm, allnull)}
        ints = {"o0": u(nm, Ii), "o1": u(nm, flg), "o2": u(nm, inull), "o3": u(nm, i_ne2)}
        case(S, f"{nm} select Float64", "G", "sel", f64)
        case(S, f"{nm} select Int64", "G", "sel", ints, xfail=lim)
        case(S, f"{nm} agg Float64 by g (group 2 all null)", "G", "agg:g", f64)
        case(S, f"{nm} agg Int64 by g", "G", "agg:g", ints, xfail=lim)
        case(S, f"{nm} agg Float64 by g2 (1- and 2-row groups)", "G", "agg:g2", f64)
        case(S, f"{nm} agg Int64 by g2", "G", "agg:g2", {"o0": u(nm, Ii), "o1": u(nm, flg)}, xfail=lim)
        case(S, f"{nm} select positional (name a)", "G", "selp", u(nm, A))
        case(S, f"{nm} with_columns positional (broadcast, replaces a)", "G", "wcp", u(nm, A))
        case(S, f"{nm} select literals", "G", "sel", {"o0": u(nm, Lf(1.5)), "o1": u(nm, Lf(-0.0)), "o2": u(nm, W(NULLF))})
        case(S, f"{nm} empty frame select Float64", "G0", "sel", {"o0": u(nm, A), "o1": u(nm, Hz)})
        case(S, f"{nm} empty frame select Int64", "G0", "sel", {"o0": u(nm, Ii), "o1": u(nm, flg)}, xfail=lim)
        case(S, f"{nm} empty frame agg", "G0", "agg:g", {"o0": u(nm, A), "o1": u(nm, Hz)})
        # h holds zeros of both signs, but every group also holds -inf and inf: min/max are not zeros
        case(S, f"{nm} select edges incl. -0.0", "G", "sel", {"o": u(nm, Hh)})
        case(S, f"{nm} agg edges incl. -0.0", "G", "agg:g", {"o": u(nm, Hh)})
        case(S, f"{nm} LIMIT literal operand inside agg", "G", "agg:g", {"o": u(nm, Lf(2.5))},
             xfail="recorded limit (RULEBOOK §6): a literal passed to sql_* inside group_by().agg: polars gives the literal per group, the prelude's count reads row indices of a length-1 column")
        case(S, f"{nm} LIMIT Null-dtype input", "G", "sel", {"o": u(nm, W(NULL))},
             xfail="recorded limit (RULEBOOK §6, `litNull`: a Null-dtype column takes the dtype of the other operand; there is none): Null-dtype input -> polars keeps dtype Null, the prelude gives a Float64 null")

LETS = {"div": LETS_F + LETS_H, "sum": LETS_F, "minmax": LETS_F + LETS_Z, "logexp": LETS_F, "sql": LETS_G}
TLIST = "Bool → List (ExprOrNum Float) → Pl.Expr Float"


def same(xs, ys):
    assert xs == ys, "cases of a factored suite do not share one template"
    return xs


def pack(name, s):
    """The eval_decl input of a suite (one digest per case). Suites whose cases repeat one template
    are factored in Lean: `sum` over full, `minmax` over (function, full), `sql` over the function."""
    T = s["terms"]
    if name == "sum":
        h = len(T) // 2
        tm = same([z.replace("(sas_sum true ", "(sas_sum full ") for z in T[:h]], [z.replace("(sas_sum false ", "(sas_sum full ") for z in T[h:]])
        return f"let P := fun (full : Bool) => [{', '.join(tm)}]; (P true ++ P false).map dg"
    if name == "minmax":
        h = len(T) // 2
        k = h // 2

        def gen(part, fv):
            return same([z.replace(f"(sas_min {fv} ", "(f full ") for z in part[:k]], [z.replace(f"(sas_max {fv} ", "(f full ") for z in part[k:]])
        tm = same(gen(T[:h], "true"), gen(T[h:], "false"))
        return (f"let P := fun (f : {TLIST}) (full : Bool) => [{', '.join(tm)}]; "
                "([true, false].flatMap (fun (full : Bool) => P sas_min full ++ P sas_max full)).map dg")
    if name == "sql":
        k = len(T) // 4
        names = ["sql_sum", "sql_mean", "sql_min", "sql_max"]
        tms = [[z.replace(f"({nm} ", "(f ") for z in T[n * k:(n + 1) * k]] for n, nm in enumerate(names)]
        for other in tms[1:]:
            same(tms[0], other)
        return (f"let P := fun (f : ExprOrNum Float → Pl.Expr Float) => [{', '.join(tms[0])}]; "
                f"(([{', '.join(names)}] : List (ExprOrNum Float → Pl.Expr Float)).flatMap P).map dg")
    return "[" + ", ".join(T) + "].map dg"


def write_all():
    WORK.mkdir(exist_ok=True)
    env = dict(os.environ, POLARS_MAX_THREADS="1")
    r = subprocess.run([sys.executable, __file__, "--t1"], env=env, capture_output=True, text=True, check=True)
    child = json.loads(r.stdout.splitlines()[-1])
    for name in ("sum", "minmax"):  # the cases with `full = false`: expected values from one polars thread
        s, o = SUITES[name], child[name + "_t1"]
        s["labels"] = [z + " [full=true, default threads]" for z in s["labels"]] + [z + " [full=false, POLARS_MAX_THREADS=1]" for z in o["labels"]]
        for key in ("units", "expected", "terms", "xfail"):
            s[key] = s[key] + o[key]
    for name, s in SUITES.items():
        lets = KIT + kit.GEN + LETS[name]
        st = Suite(f"b2_{name}")  # carrier: def:zz_carrier; one input, one digest per case
        st.ints(lets, pack(name, s),
                [(lab, un, dg(exp), ({"expect_diff": True, "note": xf} if xf else {}))
                 for lab, un, exp, xf in zip(s["labels"], s["units"], s["expected"], s["xfail"], strict=True)], use_kit=False)
        st.write()
        (WORK / f"b2_{name}.expected.json").write_text(json.dumps({**s, "pre": "(" + lets}, ensure_ascii=False))


def load(name):
    return json.loads((WORK / f"b2_{name}.expected.json").read_text())


def tok_diff(name, k, text):
    s = load(name)
    got, exp = decode(ast.literal_eval(text)), decode(s["expected"][k])
    print(f"b2_{name}[{k}] {s['labels'][k]}")
    if len(got) != len(exp):
        print("  column count: expected", len(exp), "got", len(got))
    nd = 0
    for (en, ek, ev), (gn, gk, gv) in zip(exp, got):
        if (en, ek) != (gn, gk):
            print(f"  column {en}:{ek} got {gn}:{gk}")
            nd += 1
        if isinstance(ev, list) and isinstance(gv, list):
            if len(ev) != len(gv):
                print(f"  column {en}: length expected {len(ev)} got {len(gv)}")
                nd += 1
            for r_, (p_, q_) in enumerate(zip(ev, gv)):
                if p_ != q_:
                    nd += 1
                    sh = (lambda z: "null" if z is None else repr(lt.from_bits(z))) if ek == "f64" and gk == "f64" else repr
                    print(f"  {en}[{r_}]: expected {sh(p_)} got {sh(q_)}")
        elif ev != gv:
            print(f"  column {en}: expected {ev} got {gv}")
            nd += 1
    print("  differences:", nd)


if __name__ == "__main__":
    args = [z for z in sys.argv[1:] if z != "--t1"]
    if T1:
        assert pl.thread_pool_size() == 1
        print(json.dumps(SUITES))
    elif not args:
        write_all()
    elif args[0] == "full":
        s = load(args[1])
        print(json.dumps(s["pre"] + s["terms"][int(args[2])] + ")", ensure_ascii=False))
    elif args[0] == "tok":
        tok_diff(args[1], int(args[2]), args[3])
