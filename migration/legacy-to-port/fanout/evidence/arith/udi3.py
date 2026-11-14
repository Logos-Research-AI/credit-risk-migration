import sys, math
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
import polars as pl
from compare import sas_best12
R = "/Users/cristophersalvi/GitHub/sas-migration"
raw = pl.read_csv(f"{R}/data/cs-training.csv", infer_schema=False).select(pl.col("").cast(pl.Int64).alias("row_id"), pl.col("RevolvingUtilizationOfUnsecuredLines").alias("r"), pl.col("DebtRatio").alias("d"))
ref = pl.concat([pl.read_csv(f"{R}/judge/reference/model_features_{p}.csv", infer_schema=False).select(pl.col("row_id").cast(pl.Int64), "utilization_debt_interaction") for p in ["train","validation"]])
j = ref.join(raw, on="row_id")
inv = 1/100
V = {"ieee (cu*dr)/100": lambda cu,dr: cu*dr/100, "recip (cu*dr)*0.01": lambda cu,dr: cu*dr*inv, "cu*dr*0.01 lit": lambda cu,dr: cu*dr*0.01}
cnt = {k:0 for k in V}; ulp = {}
for row in j.iter_rows(named=True):
    r, d = float(row["r"]), float(row["d"]); cu, dr = r*100, d*100; ref_s = row["utilization_debt_interaction"]
    for k,f in V.items():
        v = f(cu,dr)
        if sas_best12(v) != ref_s:
            cnt[k]+=1
            if k.startswith("recip"):
                ok=None
                for kk in range(1,4):
                    for s in (1,-1):
                        w=v
                        for _ in range(kk): w=math.nextafter(w, s*math.inf)
                        if sas_best12(w)==ref_s and ok is None: ok=s*kk
                ulp[ok]=ulp.get(ok,0)+1
print(cnt, "recip mismatch ulp distances:", ulp)
