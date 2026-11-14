"""Diff-inspector probes, part 2."""
import io

import polars as pl

from credit_risk import sas_compat as sc
from credit_risk.metrics_calculation import confusion_metrics


def show(title, f):
    try:
        r = f()
    except BaseException as e:  # noqa: BLE001
        r = f"RAISES {type(e).__name__}: {str(e).splitlines()[0][:160]}"
    print(f"{title}: {r}")


print("== Q1 constants ==")
print("2.0**52 ==", repr(2.0**52), "| == 4503599627370496.0:", 2.0**52 == 4503599627370496.0,
      "| == float(2**52):", 2.0**52 == float(2**52), "| sc._TWO52:", repr(sc._TWO52), "| sc._ROUND_FUZZ:", repr(sc._ROUND_FUZZ))
print("== Q2 duplicate column names ==")
show("pl.DataFrame with duplicate names", lambda: pl.DataFrame([pl.Series("a", [1]), pl.Series("a", [2])]))
print("== Q3 dtype is visible in the written text ==")
c, m, k = confusion_metrics(0.5, "s", pl.DataFrame({"pd_logistic": [0.9, 0.1], "default_flag": [1.0, 0.0]}))
print("confusion csv:", repr(c.write_csv()))
print("conf_matrix csv:", repr(m.write_csv()))
print("== Q4 zero-row table at a stage boundary ==")
show("pl.read_csv of a header-only file: schema", lambda: pl.read_csv(io.StringIO("pd_logistic,default_flag\n")).schema)
show("confusion_metrics on it", lambda: [f.rows() for f in confusion_metrics(0.5, "s", pl.read_csv(io.StringIO("pd_logistic,default_flag\n")))])
show("confusion_metrics on zero rows, Float64 schema", lambda: [f.rows() for f in confusion_metrics(
    0.5, "s", pl.DataFrame(schema={"pd_logistic": pl.Float64, "default_flag": pl.Float64}))])
print("== Q5 Int64 literal vs Float64 literal as max_horizontal operand, and (1 : α) vs 1.0 ==")
d = pl.DataFrame({"a": [0.25, 3.0]})
print(d.select(f=pl.max_horizontal(pl.lit(1.0), pl.col("a")), i=pl.max_horizontal(pl.lit(1), pl.col("a"))).to_dict(as_series=False))
print("== Q6 sas_round on a 1-row frame column vs the same value in a 2-row frame ==")
for n in (1, 2, 3):
    print(n, "rows:", [str(v) for v in pl.DataFrame({"x": [-0.3] * n}).select(sc.sas_round(pl.col("x"))).to_series().to_list()])
print("group context (agg over groups of size 1 and 2):",
      pl.DataFrame({"g": [1, 2, 2], "x": [-0.3, -0.3, -0.2]}).group_by("g", maintain_order=True).agg(sc.sas_round(pl.col("x"))).to_dict(as_series=False))
print("filter to one row then select:", [str(v) for v in pl.DataFrame({"x": [-0.3, 5.0]}).filter(pl.col("x") < 0).select(sc.sas_round(pl.col("x"))).to_series().to_list()])
print("with_columns on a 1-row frame:", [str(v) for v in pl.DataFrame({"x": [-0.3]}).with_columns(sc.sas_round(pl.col("x"))).to_series().to_list()])
print("plain col + 0.0, 1 row:", [str(v) for v in pl.DataFrame({"x": [-0.0]}).select(pl.col("x") + 0.0).to_series().to_list()],
      "| 2 rows:", [str(v) for v in pl.DataFrame({"x": [-0.0, -0.0]}).select(pl.col("x") + 0.0).to_series().to_list()])
