import polars as pl, math
from credit_risk import sas_compat as sc
nan, inf = float("nan"), float("inf")
for x in (inf, -inf, nan, -0.0, 0.0, 1e308, 5e-324, 1234567890123.0, -1e-300, 2.0**53, None):
    try:
        print(repr(x), "->", repr(sc.sas_best12(x)))
    except Exception as ex:
        print(repr(x), "raises", type(ex).__name__, ex)
vals = [inf, -inf, nan, -0.0, None, 1234567890123.0, 5e-324, 1e308]
df = pl.DataFrame({"MonthlyIncome": pl.Series(vals, dtype=pl.Float64), "NumberOfDependents": ["2", "NA", None, " 3 ", "", "1e2", "١", "0x10"],
                   "MonthlyIncome_num": list(range(8))})
credit_raw = df
def input_best32(v):
    if credit_raw.schema[v] != pl.String:
        return sc.input_best32(pl.col(v).map_elements(sc.sas_best12, return_dtype=pl.String))
    return sc.input_best32(pl.col(v))
try:
    m = df.select(pl.col("MonthlyIncome").map_elements(sc.sas_best12, return_dtype=pl.String))
    print(m.rows())
    out = (credit_raw.with_columns(MonthlyIncome_num=input_best32("MonthlyIncome"), NumberOfDependents_num=input_best32("NumberOfDependents"))
       .drop("MonthlyIncome", "NumberOfDependents").rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"}))
    print(out.schema, out.rows())
except Exception as ex:
    print("raises", type(ex).__name__, str(ex)[:300])
# all-null Float64, Int64, Boolean, Null columns
for s in (pl.Series([None, None], dtype=pl.Float64), pl.Series([1, None], dtype=pl.Int64), pl.Series([True, None]), pl.Series([None, None])):
    try:
        r = pl.DataFrame({"x": s}).select(pl.col("x").map_elements(sc.sas_best12, return_dtype=pl.String))
        print(s.dtype, "->", r.schema, r.rows())
    except Exception as ex:
        print(s.dtype, "raises", type(ex).__name__, str(ex)[:200])
# a frame that already has NumberOfDependents_num, and column order
d2 = pl.DataFrame({"a": [1.0], "NumberOfDependents_num": ["z"], "MonthlyIncome": ["5"], "b": [2.0], "NumberOfDependents": [3.0]})
credit_raw = d2
print((credit_raw.with_columns(MonthlyIncome_num=input_best32("MonthlyIncome"), NumberOfDependents_num=input_best32("NumberOfDependents"))
       .drop("MonthlyIncome", "NumberOfDependents").rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"})))
