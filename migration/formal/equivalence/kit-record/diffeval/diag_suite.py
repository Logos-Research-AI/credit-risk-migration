"""Minimal inputs for the differences found by prelude_suites.py, in dump / bits mode (exact paths).

Against the FROZEN preludes (RULEBOOK v3): the former D2 (scalar zero in + / -), D3 (when/then with a
Null branch) and D10 (Np.round3 sign) cases are expected to PASS; the recorded limits (RULEBOOK 6)
are `lim(...)` cases (XFAIL) with the value the prelude returns under the diagnosis."""
from __future__ import annotations

import math

import numpy as np
import polars as pl

import compare as cmp
import leanterm as lt
from prelude_suites import DTN, MDN, NEG0, as_f64, ieee_plus_zero, lean_group_sum, lean_median, lim, set_col, stable_sorted
from suite import Suite

NAN = math.nan
d = pl.DataFrame({"a": [-0.0, 0.0, -1.5, None, NAN], "i": [-2, 0, 3, None, 1], "p": [True, False, None, True, False],
                  "s": ["A", None, "B", "A", ""], "g": [1, 1, 2, 2, 2], "y": [1.0, -1.0, 2.0, 3.0, -4.0],
                  "m": [0.0, -0.0, -1.0, None, None]},
                 schema={"a": pl.Float64, "i": pl.Int64, "p": pl.Boolean, "s": pl.String, "g": pl.Int64, "y": pl.Float64, "m": pl.Float64})
LETS = f"let c := fun (n : String) => Pl.col (α := Float) n; let d := {lt.lean_frame(d)}; "
Z = "(Pl.litF (Float.ofBits 0))"
a, i = pl.col("a"), pl.col("i")
DT = lambda e: lim(DTN, as_f64(e, keep=("g",)))  # noqa: E731
av = d.get_column("a").to_list()
SEL = [  # name, primitive, Lean expression, polars expression, extra (a recorded limit) or None
    ("abs_a", "abs(-0.0)", '(c "a").abs', a.abs(),
     lambda e: lim("polars abs(-0.0) is 0.0; RealLike.abs cannot clear the sign of a zero",
                   set_col(e, "abs_a", [-0.0 if (x is not None and cmp.fbits(x) == NEG0) else (None if x is None else abs(x)) for x in av]))),
    ("add0", "add(scalar zero)", f'(c "a").add {Z}', a + 0.0, None),            # former D2
    ("radd0", "add(scalar zero)", f'{Z}.add (c "a")', 0.0 + a, None),           # former D2
    ("add0i", "add(scalar zero)", '(c "a").add (Pl.litI 0)', a + 0, None),      # former D2
    ("wto_i", "wto(litNull branch)", '(Pl.wto ((c "i").gt (Pl.litI 0)) (Pl.litI 1) Pl.litNull)', pl.when(i > 0).then(1), None),  # former D3
    ("abs_i", "abs(Int64 input)", '(c "i").abs', i.abs(), DT), ("floor_i", "floor(Int64 input)", '(c "i").floor', i.floor(), DT),
    ("sign_i", "sign(Int64 input)", '(c "i").sign', i.sign(), DT),
    ("sumh_i", "sumHorizontal(Int64 input)", '(Pl.sumHorizontal true [(c "i"), (c "i")])', pl.sum_horizontal([i, i]), DT),
    ("sum_p", "sum(Boolean input)", '(c "p").sum', pl.col("p").sum(), DT), ("min_i", "min(Int64 input)", '(c "i").min', i.min(), DT),
    ("max_i", "max(Int64 input)", '(c "i").max', i.max(), DT),
    ("wto_s", "wto(litNull branch)", '(Pl.wto (c "s").isNull (Pl.litS "n") Pl.litNull)', pl.when(pl.col("s").is_null()).then(pl.lit("n")), None),  # former D3
    ("med_m", "median", '(c "m").median', pl.col("m").median(), None),
]
s = Suite("diag", carrier="cumsum")
cases = []
for n, prim, le, pe, extra in SEL:
    e = cmp.canon_frame(d.select(pe.alias(n)))
    cases.append((n, prim, f'Pl.Frame.select d [("{n}", {le})]', e, extra(e) if extra else {}))
g = d.group_by("g", maintain_order=True)
yv = d.get_column("y").to_list()
vf = [y for y in yv if y > 0.0]                       # Expr.filter ignores the groups
rows = [[0, 1], [2, 3, 4]]
e_f = cmp.canon_frame(g.agg(f=pl.col("y").filter(pl.col("y") > 0.0).sum()))
e_c = cmp.canon_frame(g.agg(cs=pl.col("y").cum_sum()))
e_m = cmp.canon_frame(g.agg(mi=i.min()))
run_, acc = [], None
for y in yv:
    acc = y if acc is None else acc + y
    run_.append(acc)
cases += [
    ("group_filter_sum", "group:filter", f'Pl.Frame.groupByAgg d ["g"] [("f", ((c "y").filter ((c "y").gt {Z})).sum)]', e_f,
     lim("`filter` is stated for select context only (RULEBOOK 2.3): inside group_by().agg Expr.filter ignores the groups",
         set_col(e_f, "f", [lean_group_sum(False, [vf[r] if r < len(vf) else None for r in gr]) for gr in rows]))),
    ("group_min_i", "group:min(Int64 input)", 'Pl.Frame.groupByAgg d ["g"] [("mi", (c "i").min)]', e_m, DT(e_m)),
    ("group_cumSum", "group:cumSum", 'Pl.Frame.groupByAgg d ["g"] [("cs", (c "y").cumSum)]', e_c,
     lim("`cumSum` is stated for select context only (RULEBOOK 2.3): polars returns a List column per group, Expr.cumSum the running "
         "sum over the whole frame", set_col(e_c, "cs", run_))),
    ("group_median_m", "group:median", 'Pl.Frame.groupByAgg d ["g"] [("md", (c "m").median)]', cmp.canon_frame(g.agg(md=pl.col("m").median()))),
]
s.dump(LETS, "frame", cases)
r3 = [-1e-5, -0.0005, -0.0004, -0.0, 0.0004, 0.0005]   # former D10
s.bits("round3", "Np.round3", f"{lt.lean_floats(r3)}.map Np.round3", cmp.canon_floats(np.round(np.array(r3), 3).tolist()))
z = [0.0, -0.0, 1.0, -0.0, 0.0]
s.bits("sort_signed_zeros", "Np.sort(zeros of both signs)", f"Np.sort {lt.lean_floats(z)}", cmp.canon_floats(np.sort(np.array(z)).tolist()),
       **lim("np.sort is not stable: the order of -0.0 and 0.0; Np.sort keeps the input order", cmp.canon_floats(stable_sorted(z))))
s.write()

# median with zeros of both signs: the smallest case found by search (17 values); select and group context agree in polars
mv = [-1.0, -0.0, 1.0, 0.0, 1.0, -0.0, 0.0, -1.0, 1.0, 1.0, 1.0, -0.0, 1.0, -0.0, -0.0, -0.0, -0.0]
s2 = Suite("diag2", carrier="cumsum")
s2.bits("median_signed_zero", "median(zeros of both signs)", f"(Pl.median {lt.lean_opt_floats(mv)}).toList",
        cmp.canon_floats([pl.Series(mv, dtype=pl.Float64).median()]), **lim(MDN, cmp.canon_floats([lean_median(mv)])))
s2.write()

# scalar kernels of polars: a scalar zero operand (literal, aggregate, or a literal column kept by with_columns)
d3 = pl.DataFrame({"a": [0.0, -0.0, 1.5], "z": [0.0, 0.0, 0.0]})
L3 = f"let c := fun (n : String) => Pl.col (α := Float) n; let d := {lt.lean_frame(d3)}; "
NZ = f"(Pl.litF {lt.lean_float(-0.0)})"
a3 = pl.col("a")
s3 = Suite("diag3", carrier="cumsum")
e_l = cmp.canon_frame(d3.with_columns(w=pl.lit(0.0)).select(r=a3 + pl.col("w")))
s3.dump(L3, "frame", [
    ("rsub0", "sub(scalar zero)", f'Pl.Frame.select d [("r", {Z}.sub (c "a"))]', cmp.canon_frame(d3.select(r=0.0 - a3))),
    ("sub_neg0", "sub(scalar zero)", f'Pl.Frame.select d [("r", (c "a").sub {NZ})]', cmp.canon_frame(d3.select(r=a3 - (-0.0)))),
    ("add_agg0", "add(scalar zero)", 'Pl.Frame.select d [("r", (c "a").add (c "z").sum)]', cmp.canon_frame(d3.select(r=a3 + pl.col("z").sum()))),
    ("add_litcol0", "add(frame column kept as scalar)", f'Pl.Frame.select (Pl.Frame.withColumns d [("w", {Z})]) [("r", (c "a").add (c "w"))]', e_l,
     lim("a column made by with_columns(w=pl.lit(0.0)) is kept by polars as a scalar; in the model it is a column of zeros", ieee_plus_zero(e_l))),
    ("add_col0", "add", 'Pl.Frame.select d [("r", (c "a").add (c "z"))]', cmp.canon_frame(d3.select(r=a3 + pl.col("z")))),
])
s3.write()
