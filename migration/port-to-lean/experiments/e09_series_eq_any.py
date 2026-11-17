"""E09 (T-D, 2026-11-17): the lines train.py:715-718 and :792-797.
`Series == 1`, `Series != 1`, `.any()` on a Boolean Series, against the expression `pl.col == 1` /
`!= 1` in select context (prelude Expr.eq / Expr.ne with Pl.litI 1); `df.clear().select(names)`.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e09_series_eq_any.py
"""
import random

import polars as pl

nan, inf = float("nan"), float("inf")
random.seed(9)
POOL = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 1.0, 1.0000000000000002, 0.9999999999999999, 2.0, -1.0, 0.5]
n = d_eq = d_ne = d_any = 0
for case in range(3000):
    k = random.choice([0, 1, 2, 3, 5, 12])
    vals = [random.choice(POOL) for _ in range(k)]
    for dtype in (pl.Float64, pl.Int64):
        if dtype == pl.Float64:
            s = pl.Series("default_flag", vals, dtype=pl.Float64, nan_to_null=False)
        elif dtype == pl.Int64:
            s = pl.Series("default_flag", [None if v is None or v != v or abs(v) == inf else int(v) for v in vals], dtype=pl.Int64)
        else:
            s = pl.Series("default_flag", [None if v is None or v != v else v == 1.0 for v in vals], dtype=pl.Boolean)
        f = pl.DataFrame({"default_flag": s})
        e_eq = f.select(x=pl.col("default_flag") == 1).to_series().to_list()
        e_ne = f.select(x=pl.col("default_flag") != 1).to_series().to_list()
        s_eq, s_ne = (s == 1), (s != 1)
        n += 1
        d_eq += s_eq.to_list() != e_eq
        d_ne += s_ne.to_list() != e_ne
        for b in (s_eq, s_ne):
            a = b.any()
            d_any += (type(a) is not bool) or a != any(x is True for x in b.to_list())
print("cases", n, "| Series == 1 differs from the expression:", d_eq, "| != 1:", d_ne,
      "| .any() is not `some element is True` (a Python bool):", d_any)
for vals in ([], [None], [nan], [1.0], [None, 1.0], [nan, 1.0], [0.0], [1.0, 1.0], [1.0, 0.0], [1.0000000000000002]):
    s = pl.Series("x", vals, dtype=pl.Float64, nan_to_null=False)
    print(vals, "== 1:", (s == 1).to_list(), "any", (s == 1).any(), "| != 1:", (s != 1).to_list(), "any", (s != 1).any())
for name, ser in (("String", pl.Series(["1", "a"])), ("Boolean", pl.Series([True, None])), ("Null", pl.Series([None, None]))):
    for op in ("==", "!="):
        try:
            r = (ser == 1) if op == "==" else (ser != 1)
            print(name, op, "1:", r.to_list(), r.dtype)
        except Exception as ex:  # noqa: BLE001
            print(name, op, "1 raises", type(ex).__name__, str(ex)[:90])
# the filter of :715-717 and the Series it leaves
f = pl.DataFrame({"default_flag": [1.0, None, 0.0, nan, 1.0], "pd_logistic": [0.5, 0.5, None, 0.1, nan]})
u = f.filter(pl.col("default_flag").is_not_null() & pl.col("pd_logistic").is_not_null()).get_column("default_flag")
print("used:", u.to_list(), "created:", bool((u == 1).any()) and bool((u != 1).any()))
# :794-796 df.clear().select([... if c != "Valid_AUC"] + ["Valid_AUC"])
m = pl.DataFrame({"Train_AUC": [0.9], "Valid_AUC": [None], "train_precision": [0.5], "model_name": ["L"]}, schema_overrides={"Valid_AUC": pl.Float64})
c = m.clear().select([x for x in m.columns if x != "Valid_AUC"] + ["Valid_AUC"])
print("clear().select:", c.schema, "height", c.height)
try:
    m.drop("Valid_AUC").clear().select(["Train_AUC", "Valid_AUC"])
except Exception as ex:  # noqa: BLE001
    print("select of an absent Valid_AUC raises", type(ex).__name__)
import io, tempfile, pathlib
from credit_risk import sas_compat as sc
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d) / "model_summary.csv"
    sc.write_sas_csv(c, p, formats={})
    print("written file:", repr(p.read_text()))
