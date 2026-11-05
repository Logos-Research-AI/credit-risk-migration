import sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge"); sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/arith")
import polars as pl, math
from compare import sas_best12
from best12b import best12_15
R = "/Users/cristophersalvi/GitHub/sas-migration"
raw = pl.read_csv(f"{R}/data/cs-training.csv", infer_schema=False).select(pl.col("").cast(pl.Int64).alias("row_id"), pl.col("RevolvingUtilizationOfUnsecuredLines").alias("r"), pl.col("DebtRatio").alias("d"))
ref = pl.concat([pl.read_csv(f"{R}/judge/reference/model_features_{p}.csv", infer_schema=False).select(pl.col("row_id").cast(pl.Int64), "utilization_debt_interaction") for p in ["train","validation"]])
j = ref.join(raw, on="row_id")
n=0; bad = {}; within1 = 0; offby=0
for row in j.iter_rows(named=True):
    r, d = float(row["r"]), float(row["d"]); v = r*100*(d*100)/100; ref_s=row["utilization_debt_interaction"]
    n+=1
    # neighbours: is ref reproduced by v or by v +- k ulp?
    if sas_best12(v)==ref_s: continue
    ok=None
    for k in range(1,5):
        for s in (1,-1):
            w=v
            for _ in range(k): w=math.nextafter(w, s*math.inf)
            if sas_best12(w)==ref_s and ok is None: ok=s*k
    bad[ok]=bad.get(ok,0)+1
print(n, bad)
