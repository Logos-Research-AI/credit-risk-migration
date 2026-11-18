import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_t14_gen as g
import polars as pl
rp, td = g.rp, g.td
base = g.env14(300002)
for k in ("training_metrics","validation_metrics","roc_train","roc_valid","risk_scores_train"):
    print(k, base[k].shape)
def tryit(name, **ch):
    e = dict(base); e.update(ch)
    try:
        td.run_slice("s14", e); r = "returns"
    except Exception as ex: r = f"RAISES {type(ex).__name__}: {str(ex)[:60]}"
    print(f"{name:55s} pre={rp.pre(e)!s:5s} {r}")
tm, vm = base["training_metrics"], base["validation_metrics"]
rs = base["risk_scores_train"]
n = tm.height
tryit("as generated")
for big in (9.999999999999994e75, 9.999999999999996e75, 1e76, -1e76, 1e300):
    tryit(f"train_precision = {big}", training_metrics=tm.with_columns(train_precision=pl.Series([big]*n, dtype=pl.Float64)) if n else tm)
    tryit(f"interest_rate = {big} (train set)", risk_scores_train=rs.with_columns(interest_rate=pl.Series([big]*rs.height, dtype=pl.Float64)) if rs.height else rs)
    tryit(f"Area (roc_train) = {big}", roc_train=base["roc_train"].with_columns(Area=pl.Series([big]*base["roc_train"].height, dtype=pl.Float64)))
# Int64 vs text in the merge with different heights
a = pl.DataFrame({"zz": pl.Series([1,2,3], dtype=pl.Int64), "train_precision":[0.5]*3,"train_recall":[0.5]*3,"train_f1_score":[0.5]*3,"train_accuracy":[0.5]*3})
b = pl.DataFrame({"zz": pl.Series(["a"], dtype=pl.String), "valid_precision":[0.5],"valid_recall":[0.5],"valid_f1_score":[0.5],"valid_accuracy":[0.5]})
tryit("zz Int64 (3 rows) then text (1 row)", training_metrics=a, validation_metrics=b)
tryit("zz text (1 row) then Int64 (3 rows) in valid", training_metrics=b.rename({c:c.replace("valid","train") for c in b.columns if c!="zz"}), validation_metrics=a.rename({c:c.replace("train","valid") for c in a.columns if c!="zz"}))
a2 = a.with_columns(zz=pl.Series([True,False,True]))
tryit("zz Boolean (3 rows) then text (1 row)", training_metrics=a2, validation_metrics=b)
print("--- interest_rate with a row")
r1 = pl.DataFrame({"interest_rate": pl.Series([1e76], dtype=pl.Float64)})
tryit("risk_scores_train = [interest_rate 1e76]", risk_scores_train=r1)
tryit("risk_scores_validation = [interest_rate 1e76]", risk_scores_validation=r1)
tryit("risk_scores_train = [interest_rate 9.999999999999994e75]", risk_scores_train=r1.with_columns(interest_rate=pl.lit(9.999999999999994e75)))
tryit("risk_scores_train = [interest_rate 1e76, other col 1e300]", risk_scores_train=r1.with_columns(age=pl.lit(1e300)))
