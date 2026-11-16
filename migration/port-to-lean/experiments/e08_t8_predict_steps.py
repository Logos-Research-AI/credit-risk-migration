"""E08 (T8, 2026-11-16): library behaviour behind predict steps 01, 02, 04 that E07 does not show.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/e08_t8_predict_steps.py
"""
import polars as pl

from credit_risk import sas_compat as sc

nan = float("nan")


def show(label, f):
    try:
        print(f"{label}: {f()}")
    except Exception as e:  # noqa: BLE001
        print(f"{label}: RAISES {type(e).__name__}: {str(e)[:150]}")


def join(l, r):
    return l.join(r, left_on=pl.col("age_group").cast(pl.Float64), right_on="age_group", how="left", maintain_order="left")


print("== join with left_on expression: position of the right key, clashes, keys")
l = pl.DataFrame({"VAR1": [1.0, 2.0, 3.0, 4.0], "age_group": pl.Series([1, 2, 5, 3], dtype=pl.Int32), "x": ["a", "b", "c", "d"]})
r = pl.DataFrame({"median_income": [10.0, None, 30.0], "age_group": [1.0, 2.0, 3.0], "overall_median_income": [33.0] * 3, "x": [7.0, 8.0, 9.0]})
show("right key not first: schema", lambda: join(l, r).schema)
show("right key not first: rows", lambda: join(l, r).rows())
r_b = r.with_columns(age_group_right=pl.lit(1.0))
show("right already has age_group_right", lambda: join(l, r_b).schema)
r_c = r.with_columns(x_right=pl.lit(1.0))
show("right has x and x_right", lambda: join(l, r_c).schema)
l_b = l.with_columns(age_group_right=pl.lit(5.0))
show("left already has age_group_right", lambda: join(l_b, r).schema)
l_c = l.with_columns(x_right=pl.lit(5.0))
show("left has x and x_right", lambda: join(l_c, r).schema)
show("right key NaN / -0.0 / null / inf vs left ints", lambda: join(
    pl.DataFrame({"age_group": pl.Series([0, 1, None], dtype=pl.Int32)}),
    pl.DataFrame({"age_group": [nan, -0.0, None, float("inf"), 1.0], "m": [1.0, 2.0, 3.0, 4.0, 5.0]})).rows())
show("left Int64 key", lambda: join(l.with_columns(pl.col("age_group").cast(pl.Int64)), r).rows())
show("empty left", lambda: (join(l.clear(), r).schema, join(l.clear(), r).shape))
show("right key Int64 column", lambda: join(l, r.with_columns(pl.col("age_group").cast(pl.Int64))).schema)
show("right key absent", lambda: join(l, r.drop("age_group")).schema)
show("right with no row", lambda: join(l, r.clear()).rows())

print("== coalesce / when on the joined columns")
j = pl.DataFrame({"miss": pl.Series([1, 1, 0, 1, 0], dtype=pl.Int32), "median_income": [10.0, None, None, None, nan],
                  "overall_median_income": [5.0, 6.0, 7.0, None, 8.0], "MonthlyIncome": [None, None, 3.0, None, 4.0]})
sel = lambda d: d.select(pl.when(pl.col("miss") == 1).then(pl.coalesce(pl.col("median_income"), pl.col("overall_median_income"))).otherwise(pl.col("MonthlyIncome")).alias("monthly_income"))  # noqa: E731
show("f64/f64", lambda: (sel(j).schema, sel(j).to_series().to_list()))
js = j.with_columns(median_income=pl.Series(["1", None, None, None, "x"]))
show("String median_income", lambda: (sel(js).schema, sel(js).to_series().to_list()))
jo = j.with_columns(overall_median_income=pl.Series(["1", None, None, None, "x"]))
show("String overall_median_income", lambda: (sel(jo).schema, sel(jo).to_series().to_list()))
jm = j.with_columns(MonthlyIncome=pl.Series(["1", None, None, None, "x"]))
show("String MonthlyIncome", lambda: (sel(jm).schema, sel(jm).to_series().to_list()))
show("miss Float64 == 1", lambda: sel(j.with_columns(pl.col("miss").cast(pl.Float64))).to_series().to_list())
show("coalesce name", lambda: j.select(pl.coalesce(pl.col("median_income"), pl.col("overall_median_income"))).columns)

print("== step 01: map_elements(sas_best12) then input_best32, kinds and empty frames")
m = pl.DataFrame({"v": [1234567890123.0, None, 5.0, nan, float("inf"), -0.0, 1e20]})
e = sc.input_best32(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String))
show("map_elements dtype", lambda: m.select(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String)).schema)
show("round trip values", lambda: m.select(e).to_series().to_list())
show("round trip name / dtype", lambda: m.select(e).schema)
show("empty frame map_elements dtype", lambda: m.clear().select(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String)).schema)
show("empty frame round trip", lambda: (m.clear().select(e).schema, m.clear().select(e).shape))
show("all-null f64", lambda: (pl.DataFrame({"v": pl.Series([None, None], dtype=pl.Float64)}).select(pl.col("v").map_elements(sc.sas_best12, return_dtype=pl.String)).schema,
                               pl.DataFrame({"v": pl.Series([None, None], dtype=pl.Float64)}).select(e).to_series().to_list()))
show("empty String column input_best32", lambda: pl.DataFrame({"v": pl.Series([], dtype=pl.String)}).select(sc.input_best32(pl.col("v"))).schema)
t = pl.DataFrame({"VAR1": [1.0, 2.0], "MonthlyIncome": [1.0, 2.0], "NumberOfDependents": ["NA", "1"], "z": [1, 2]})
show("with_columns/drop/rename order", lambda: t.with_columns(MonthlyIncome_num=pl.col("MonthlyIncome"), NumberOfDependents_num=pl.col("NumberOfDependents")).drop("MonthlyIncome", "NumberOfDependents").rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"}).columns)
show("schema[absent]", lambda: t.schema["nope"])
show("frame already has MonthlyIncome_num", lambda: t.with_columns(MonthlyIncome_num=pl.lit(0.0)).with_columns(MonthlyIncome_num=pl.col("MonthlyIncome"), NumberOfDependents_num=pl.col("NumberOfDependents")).drop("MonthlyIncome", "NumberOfDependents").rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"}).columns)

print("== step 02: the case-blind rename")


def ren(cols):
    df = pl.DataFrame({c: [float(i)] for i, c in enumerate(cols)})
    up = [n.upper() for n in df.columns]
    mapping = {
        name: name.lower()
        for i, name in enumerate(df.columns)
        if name.upper() in ("AGE_GROUP", "MEDIAN_INCOME", "OVERALL_MEDIAN_INCOME")
        and name.upper() not in up[:i]
        and (name.lower() == name or name.lower() not in df.columns)
    }
    return mapping, df.rename(mapping).columns


for cols in (["age_group", "median_income", "overall_median_income"], ["AGE_GROUP", "Median_Income", "x"],
             ["Age_Group", "age_group", "m"], ["age_group", "AGE_GROUP"], ["AGE_GROUP", "Age_Group", "median_income"],
             ["AGE_GROUP", "aGE_GROUP", "age_group"], ["median_ıncome", "age_group"], ["VAR1", "Overall_Median_Income"]):
    show(f"rename {cols}", lambda cols=cols: ren(cols))
show("upper/lower non-ASCII", lambda: ("median_ıncome".upper(), "ß".upper(), "İ".lower().encode("unicode_escape")))
