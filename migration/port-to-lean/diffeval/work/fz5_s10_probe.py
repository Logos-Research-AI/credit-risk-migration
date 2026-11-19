import sys
sys.path.insert(0, "diffeval/units")
import polars as pl
from fz5_s10_py import step10
nan=float("nan")
def t(name, *a):
    try:
        r = step10(*a); print(name, r.schema, r.to_dicts())
    except Exception as e:
        print(name, "RAISES", type(e).__name__, str(e)[:100])
F = object()
t("zero-col frame, final, no coefs", 0.5, {}, F, pl.DataFrame())
t("zero-row 1 col", 0.5, {}, F, pl.DataFrame({"x": pl.Series([], dtype=pl.Float64)}))
t("zero-row coef", 0.5, {"x":1.0}, F, pl.DataFrame({"x": pl.Series([], dtype=pl.Float64)}))
t("none icpt final some no coefs", None, {}, F, pl.DataFrame({"x":[1.0,2.0]}))
t("none icpt final some coefs", None, {"x":1.0}, F, pl.DataFrame({"x":[1.0,2.0]}))
t("none icpt final some 0row", None, {}, F, pl.DataFrame({"x":pl.Series([],dtype=pl.Float64)}))
t("final none", 0.5, {"x":1.0}, None, pl.DataFrame({"x":[1.0,2.0]}))
t("final none icpt none", None, {}, None, pl.DataFrame())
t("1 row -0", 0.0, {"x":1.0}, F, pl.DataFrame({"x":[-0.0]}))
t("nulls", 0.0, {"x":1.0}, F, pl.DataFrame({"x":[None, nan, 1.0, -800.0, 800.0]}))
t("existing cols", 0.0, {"x":1.0}, F, pl.DataFrame({"x":[1.0], "pd_logistic":["a"], "predicted_logit":[1], "pred_logistic":[True]}))
t("all-null f64 col", 1.0, {"x":1.0}, F, pl.DataFrame({"x":pl.Series([None,None],dtype=pl.Float64)}))
t("null-dtype col (as lean f64?)", 1.0, {"x":1.0}, F, pl.DataFrame({"x":pl.Series([None,None])}))
