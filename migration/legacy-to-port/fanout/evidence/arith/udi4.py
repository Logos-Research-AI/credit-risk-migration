import sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
import polars as pl
from compare import sas_best12
R = "/Users/cristophersalvi/GitHub/sas-migration"
raw = pl.read_csv(f"{R}/data/cs-training.csv", infer_schema=False).select(pl.col("").cast(pl.Int64).alias("row_id"), pl.col("RevolvingUtilizationOfUnsecuredLines").alias("r"), pl.col("DebtRatio").alias("d"))
ref = pl.concat([pl.read_csv(f"{R}/judge/reference/model_features_{p}.csv", infer_schema=False).select(pl.col("row_id").cast(pl.Int64), "utilization_debt_interaction") for p in ["train","validation"]])
j = ref.join(raw, on="row_id")
diffval=0; diffprint=0; ieee_wins=0; recip_wins=0; neither=0
for row in j.iter_rows(named=True):
    cu, dr = float(row["r"])*100, float(row["d"])*100
    a = cu*dr/100; b = cu*dr*(1/100)
    if a != b: diffval += 1
    sa, sb = sas_best12(a), sas_best12(b)
    if sa != sb:
        diffprint += 1
        if sa == row["utilization_debt_interaction"]: ieee_wins += 1
        elif sb == row["utilization_debt_interaction"]: recip_wins += 1
        else: neither += 1
print(f"rows {j.height}; ieee!=recip bitwise {diffval}; printed differently {diffprint}: ieee matches SAS {ieee_wins}, recip matches SAS {recip_wins}, neither {neither}")
