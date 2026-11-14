"""Dual expressions: one object carries the polars expression and the Lean term of the prelude
that the RULEBOOK (section 2.3) maps it to. Used to write a test case once for both sides.

The Lean terms assume these lets (see LETS):  c "x" = Pl.col "x";  run = the function the real
sas_compat.div passes to map_batches.
"""
from __future__ import annotations

import operator
import sys
from pathlib import Path

import polars as pl

import kit
import leanterm as lt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from credit_risk import sas_compat as sc  # noqa: E402

LETS = (
    "let c := fun (n : String) => Pl.col (α := Float) n; "
    "let run := fun (x y : List (Option Float)) => List.zipWith (fun (p q : Option Float) => "
    "(match p, q with | some a, some b => (if (a / b).isFinite then some (a / b) else none) | _, _ => none : Option Float)) x y; "
)


class X:
    def __init__(self, py, lean: str):
        self.py, self.lean = py, lean


def _p(v):
    return v.py if isinstance(v, X) else v


def _l(v) -> str:
    if isinstance(v, X):
        return v.lean
    if isinstance(v, bool):
        return f"(Pl.litB {lt.lean_bool(v)})"
    if isinstance(v, int):
        return f"(Pl.litI {lt.lean_int(v)})"
    if isinstance(v, float):
        return f"(Pl.litF {lt.lean_float(v)})"
    if isinstance(v, str):
        return f"(Pl.litS {lt.lean_str(v)})"
    raise TypeError(v)


# then(None) / otherwise(None) / pl.lit(None): the Null-dtype literal of the prelude (`Pl.Col.null`).
# (`pl.lit(None, pl.Float64)` is `Pl.litOptF none`.)
NONE = X(None, "(Pl.litNull : Pl.Expr Float)")
MISSING = object()
LEN = X(pl.len(), "Pl.len")


def col(n: str) -> X:
    return X(pl.col(n), f'(c "{n}")')


def lit(v) -> X:  # an explicit pl.lit(v)
    return X(pl.lit(v), _l(v))


def _bin(name, op):
    def f(a, b) -> X:
        return X(op(_p(a), _p(b)), f"({_l(a)}.{name} {_l(b)})")
    return f


add, sub, mul, div = _bin("add", operator.add), _bin("sub", operator.sub), _bin("mul", operator.mul), _bin("div", operator.truediv)
lt_, le, gt, ge = _bin("lt", operator.lt), _bin("le", operator.le), _bin("gt", operator.gt), _bin("ge", operator.ge)
eq, ne = _bin("eq", operator.eq), _bin("ne", operator.ne)
and_, or_ = _bin("and", operator.and_), _bin("or", operator.or_)


def _un(name, f):
    def g(e: X) -> X:
        return X(f(e.py), f"{e.lean}.{name}")
    return g


neg = lambda e: X(-e.py, f"{e.lean}.neg")  # noqa: E731
not_ = lambda e: X(~e.py, f"{e.lean}.not")  # noqa: E731
isNull, isNotNull = _un("isNull", lambda e: e.is_null()), _un("isNotNull", lambda e: e.is_not_null())
castF64, castI64 = _un("castF64", lambda e: e.cast(pl.Float64)), _un("castI64", lambda e: e.cast(pl.Int64))
log, exp, abs_, floor = _un("log", lambda e: e.log()), _un("exp", lambda e: e.exp()), _un("abs", lambda e: e.abs()), _un("floor", lambda e: e.floor())
sign, isFinite = _un("sign", lambda e: e.sign()), _un("isFinite", lambda e: e.is_finite())
count, sum_, mean, min_, max_ = (_un("count", lambda e: e.count()), _un("sum", lambda e: e.sum()), _un("mean", lambda e: e.mean()),
                                 _un("min", lambda e: e.min()), _un("max", lambda e: e.max()))
median, cumSum = _un("median", lambda e: e.median()), _un("cumSum", lambda e: e.cum_sum())


def fillNull(e: X, v) -> X:
    return X(e.py.fill_null(_p(v)), f"({e.lean}.fillNull {_l(v)})")


def filter_(e: X, p: X) -> X:
    return X(e.py.filter(p.py), f"({e.lean}.filter {p.lean})")


def isInF(e: X, vals: list) -> X:
    return X(e.py.is_in(pl.Series(vals, dtype=pl.Float64).implode()),
             f"({e.lean}.isInF [{', '.join(lt.lean_opt_float(v) for v in vals)}])")


def isInS(e: X, vals: list[str]) -> X:
    return X(e.py.is_in(vals), f"({e.lean}.isInS ([{', '.join(lt.lean_str(v) for v in vals)}] : List String))")


def _pb(v):
    """a then/otherwise branch: polars reads a bare str there as a column name, so a string literal is pl.lit"""
    return pl.lit(v) if isinstance(v, str) else _p(v)


def wto(cnd: X, a, b=MISSING) -> X:
    w = pl.when(cnd.py).then(_pb(a))
    if b is MISSING:
        return X(w, f"(Pl.wto {cnd.lean} {_l(a)} Pl.litNull)")  # a missing otherwise is the Null-dtype literal
    return X(w.otherwise(_pb(b)), f"(Pl.wto {cnd.lean} {_l(a)} {_l(b)})")


def wchain(branches: list[tuple], b) -> X:
    """pl.when(c1).then(a1).when(c2).then(a2)...otherwise(b) -> nested Pl.wto"""
    w = pl.when(branches[0][0].py).then(_pb(branches[0][1]))
    for cnd, a in branches[1:]:
        w = w.when(cnd.py).then(_pb(a))
    lean = _l(b)
    for cnd, a in reversed(branches):
        lean = f"(Pl.wto {cnd.lean} {_l(a)} {lean})"
    return X(w.otherwise(_pb(b)), lean)


def _lst(es) -> str:
    return "[" + ", ".join(e.lean for e in es) + "]"


def allH(es) -> X:
    return X(pl.all_horizontal([e.py for e in es]), f"(Pl.allHorizontal {_lst(es)})")


def sumH(full: bool, es) -> X:
    return X(pl.sum_horizontal([e.py for e in es]), f"(Pl.sumHorizontal {lt.lean_bool(full)} {_lst(es)})")


def minH(full: bool, es) -> X:
    return X(pl.min_horizontal([e.py for e in es]), f"(Pl.minHorizontal {lt.lean_bool(full)} {_lst(es)})")


def maxH(full: bool, es) -> X:
    return X(pl.max_horizontal([e.py for e in es]), f"(Pl.maxHorizontal {lt.lean_bool(full)} {_lst(es)})")


def sdiv(a, b) -> X:
    """the real sas_compat.div -> Pl.mapBatches2 a b run"""
    return X(sc.div(_p(a), _p(b)), f"(Pl.mapBatches2 {_l(a)} {_l(b)} run)")


# ------------------------------------------------------------------ data columns (Lean text + values)
class Col:
    def __init__(self, name: str, kind: str, lean: str, vals: list):
        self.name, self.kind, self.lean, self.vals = name, kind, lean, vals

    def series(self) -> pl.Series:
        dt = {"f64": pl.Float64, "int": pl.Int64, "bool": pl.Boolean, "str": pl.String}[self.kind]
        return pl.Series(self.name, self.vals, dtype=dt)


def gf(name, s, n, pe, eh, ename="[]", E=()) -> Col:
    return Col(name, "f64", f"gF {s} {n} {pe} {eh} {ename}", kit.gF(s, n, pe, eh, list(E)))


def gi(name, s, n, pn, m, off) -> Col:
    return Col(name, "int", f"gI {s} {n} {pn} {m} {lt.lean_int(off)}", kit.gI(s, n, pn, m, off))


def gb(name, s, n, pn) -> Col:
    return Col(name, "bool", f"(gI {s} {n} {pn} 2 0).map (fun o => o.map (fun k => k == 1))",
               [None if v is None else v == 1 for v in kit.gI(s, n, pn, 2, 0)])


def gs(name, s, n, pn, words: list[str], wname="SL") -> Col:
    return Col(name, "str", f'(gI {s} {n} {pn} {len(words)} 0).map (fun o => o.map (fun k => {wname}.getD k.toNat ""))',
               [None if v is None else words[v] for v in kit.gI(s, n, pn, len(words), 0)])


def pairs(n1, n2, kind, ename, E) -> tuple[Col, Col]:
    """all ordered pairs of the edge list E (Lean name `ename`)"""
    E = list(E)
    return (Col(n1, kind, f"{ename}.flatMap (fun x => {ename}.map (fun _ => x))", [x for x in E for _ in E]),
            Col(n2, kind, f"{ename}.flatMap (fun _ => {ename})", [y for _ in E for y in E]))


def cat(a: Col, b: Col) -> Col:
    return Col(a.name, a.kind, f"({a.lean}) ++ ({b.lean})", a.vals + b.vals)


def lits(name, kind, vals) -> Col:
    f = {"f64": lt.lean_opt_float, "int": lambda v: lt.lean_opt(v, lt.lean_int), "bool": lambda v: lt.lean_opt(v, lt.lean_bool),
         "str": lambda v: lt.lean_opt(v, lt.lean_str)}[kind]
    return Col(name, kind, "[" + ", ".join(f(v) for v in vals) + "]", list(vals))


def elist(name: str, kind: str, vals) -> str:
    """`let NAME : List (Option T) := [...]; ` for an edge list"""
    c = lits(name, kind, vals)
    t = {"f64": "Float", "int": "Int", "bool": "Bool", "str": "String"}[kind]
    return f"let {name} : List (Option {t}) := {c.lean}; "


def frame(var: str, cols: list[Col]) -> tuple[str, pl.DataFrame]:
    """`let VAR : Pl.Frame Float := [...]; ` and the same polars frame"""
    items = ", ".join(f'("{c.name}", .{c.kind} ({c.lean}))' for c in cols)
    return f"let {var} : Pl.Frame Float := [{items}]; ", pl.DataFrame([c.series() for c in cols])
