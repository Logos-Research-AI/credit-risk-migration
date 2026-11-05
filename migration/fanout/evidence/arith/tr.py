import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/arith")
from met import metrics
import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration/judge/reference"
ms = pl.read_csv(f"{R}/model_summary.csv", infer_schema=False)
for part, pre in [("train","train"),("validation","valid")]:
    d = pl.read_csv(f"{R}/risk_scores_{part}.csv", infer_schema=False).select(y=pl.col("default_flag").cast(pl.Int64), p=pl.col("pred_logistic").cast(pl.Int64), pd=pl.col("pd_logistic").cast(pl.Float64), g=pl.col("risk_grade"), br=pl.col("base_rate"), ir=pl.col("interest_rate"))
    y, p = d["y"], d["p"]
    tp=int(((y==1)&(p==1)).sum()); tn=int(((y==0)&(p==0)).sum()); fp=int(((y==0)&(p==1)).sum()); fn=int(((y==1)&(p==0)).sum())
    acc, pr, rc, f1, sp = metrics(tp,tn,fp,fn)
    mine = [f"{x:.4f}" for x in (pr, rc, f1, acc)]
    refs = [ms[f"{pre}_{c}"][0] for c in ["precision","recall","f1_score","accuracy"]]
    print(part, tp, tn, fp, fn, mine, refs, mine == refs, "pred==(pd>=0.5) agrees:", bool(((d["pd"]>=0.5).cast(pl.Int64)==p).all()))
    rate = {"A":0.05,"B":0.05+0.02,"C":0.05+0.04,"D":0.05+0.07,"E":0.05+0.10}
    print("  grades", d.group_by("g").agg(pl.len(), pl.col("ir").unique(), pl.col("br").unique()).sort("g").rows())
    print("  computed", {g: (repr(v), f"{v*100:.2f}%") for g, v in rate.items()}, "F", repr(0.05+0.15))
