import sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge"); sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/arith")
import polars as pl, numpy as np
from fractions import Fraction
from compare import sas_best12 as _b
from best12b import best12_15 as sas_best12
R = "/Users/cristophersalvi/GitHub/sas-migration"
raw = pl.read_csv(f"{R}/data/cs-training.csv", infer_schema=False).select(pl.col("").cast(pl.Int64).alias("row_id"), pl.col("RevolvingUtilizationOfUnsecuredLines").alias("r"), pl.col("DebtRatio").alias("d"))
ref = pl.concat([pl.read_csv(f"{R}/judge/reference/model_features_{p}.csv", infer_schema=False).select(pl.col("row_id").cast(pl.Int64), "credit_utilization","debt_ratio","utilization_debt_interaction") for p in ["train","validation"]])
j = ref.join(raw, on="row_id")
variants = {k:0 for k in ["v1 cu*dr/100","v2 cu*(dr/100)","v3 exact","v5 longdouble","v6 cu/100*dr", "v7 r*d*100", "v8 (r*100)*(d*100)/100 fma-ish"]}
ex = []
for row in j.iter_rows(named=True):
    r, d = float(row["r"]), float(row["d"])
    cu, dr = r*100, d*100
    ref_s = row["utilization_debt_interaction"]
    vals = {
        "v1 cu*dr/100": cu*dr/100,
        "v2 cu*(dr/100)": cu*(dr/100),
        "v3 exact": float(Fraction(row["r"])*Fraction(row["d"])*100),
        "v5 longdouble": float(np.longdouble(cu)*np.longdouble(dr)/np.longdouble(100)),
        "v6 cu/100*dr": cu/100*dr,
        "v7 r*d*100": r*d*100,
        "v8 (r*100)*(d*100)/100 fma-ish": float(Fraction(cu)*Fraction(dr)/100),
    }
    for k,v in vals.items():
        if sas_best12(v) != ref_s: variants[k]+=1
    if sas_best12(cu*dr/100) != ref_s and len(ex)<5: ex.append((row["row_id"], row["r"], row["d"], repr(cu*dr/100), ref_s, repr(float(Fraction(cu)*Fraction(dr)/100))))
print(variants); print(*ex, sep="\n")
print("longdouble info", np.finfo(np.longdouble))
