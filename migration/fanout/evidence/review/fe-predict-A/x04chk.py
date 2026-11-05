import numpy as np, polars as pl
from decimal import Decimal, ROUND_HALF_UP
S="/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/fe-predict-A/"
R="/Users/cristophersalvi/GitHub/sas-migration/judge/reference/"
fe=pl.read_parquet(S+"fe.parquet")
ref=pl.concat([pl.read_csv(R+f"model_features_{s}.csv",infer_schema=False) for s in ("train","validation")]).with_columns(pl.col("row_id").cast(pl.Float64))
m=ref.select("row_id","utilization_debt_interaction").join(fe.select("row_id","credit_utilization","debt_ratio"),on="row_id")
p=m["credit_utilization"].to_numpy()*m["debt_ratio"].to_numpy()
def b12(x):
    if x==0: return "0"
    d=Decimal(f"{x:.15g}")
    ip=len(str(int(abs(d)))) if abs(d)>=1 else 1
    dec=max(0,12-ip-1-(1 if x<0 else 0))
    q=d.quantize(Decimal(1).scaleb(-dec),rounding=ROUND_HALF_UP)
    s=format(q,"f")
    if "." in s: s=s.rstrip("0").rstrip(".")
    return s
for name,v in [("ieee",np.divide(p,100.0)),("recip",p*(1/100.0))]:
    bad=sum(1 for r,x in zip(m["utilization_debt_interaction"].to_list(),v) if "E" not in r and b12(float(x))!=r)
    print(name,bad)
