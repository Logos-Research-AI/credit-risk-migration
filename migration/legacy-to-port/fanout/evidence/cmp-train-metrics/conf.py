import polars as pl, sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
from compare import sas_best12
R="/Users/cristophersalvi/GitHub/sas-migration/judge"
def metrics(df, pred):
    conf = (df.with_columns(pred.alias("predicted"))
              .group_by(["default_flag","predicted"], maintain_order=True).len("COUNT"))
    def cell(d,p):
        return conf.filter((pl.col("default_flag")==d)&(pl.col("predicted")==p))["COUNT"].sum()
    TP,TN,FP,FN = cell(1,True),cell(0,False),cell(0,True),cell(1,False)
    g = lambda c, v: v if c else None
    acc = g(TP+TN+FP+FN>0, (TP+TN)/(TP+TN+FP+FN) if TP+TN+FP+FN else 0)
    prec = g(TP+FP>0, TP/(TP+FP) if TP+FP else 0)
    rec = g(TP+FN>0, TP/(TP+FN) if TP+FN else 0)
    s = None if prec is None or rec is None else prec+rec
    f1 = g(s is not None and s>0, 2*(prec*rec)/s if s else 0)
    spec = g(TN+FP>0, TN/(TN+FP) if TN+FP else 0)
    return dict(TP=TP,TN=TN,FP=FP,FN=FN,accuracy=acc,precision=prec,recall=rec,f1_score=f1,specificity=spec)
fmt = lambda v: "" if v is None else sas_best12(v)
bad=0
for name, sc, ref in [("real", R+"/scenarios/real_metrics", R+"/reference"),
                      ("a", R+"/scenarios/edge_metrics_a", R+"/reference/scenarios/edge_metrics_a"),
                      ("b", R+"/scenarios/edge_metrics_b", R+"/reference/scenarios/edge_metrics_b"),
                      ("c", R+"/scenarios/edge_metrics_c", R+"/reference/scenarios/edge_metrics_c")]:
    df = pl.read_csv(sc+"/risk_scores_validation.csv", infer_schema=False).select(
        pl.col("default_flag").cast(pl.Float64), pl.col("pd_logistic").cast(pl.Float64))
    reft = pl.read_csv(ref+"/threshold_analysis.csv", infer_schema=False).fill_null("")
    at = df.filter(pl.col("pd_logistic").is_in([0.3,0.4,0.5,0.6,0.7])).group_by("pd_logistic").len().sort("pd_logistic")
    print(name, "rows with pd exactly at a threshold:", at.rows())
    for i,t in enumerate([0.3,0.4,0.5,0.6,0.7]):
        m = metrics(df, pl.col("pd_logistic") >= t)
        row = reft.row(i, named=True)
        mine = {k: fmt(m[k]) for k in ["accuracy","precision","recall","f1_score","specificity"]}
        ok = all(mine[k]==row[k] for k in mine)
        bad += not ok
        print(f"  {t} TP={m['TP']} TN={m['TN']} FP={m['FP']} FN={m['FN']} {'OK' if ok else 'DIFF'} {mine if not ok else ''} {row if not ok else ''}")
# train-side: from reference risk_scores pred_logistic
ms = pl.read_csv(R+"/reference/model_summary.csv", infer_schema=False).row(0, named=True)
for part,f in [("train","risk_scores_train.csv"),("valid","risk_scores_validation.csv")]:
    df = pl.read_csv(R+"/reference/"+f, infer_schema=False).select(pl.col("default_flag").cast(pl.Float64), pl.col("pd_logistic").cast(pl.Float64), pl.col("pred_logistic").cast(pl.Float64))
    m = metrics(df, pl.col("pd_logistic") >= 0.5)
    print(part, {k: (f"{m[k]:.4f}", ms[f"{part}_{k}"]) for k in ["precision","recall","f1_score","accuracy"]}, "pred==recomputed:", (df["pred_logistic"]==(df["pd_logistic"]>=0.5).cast(pl.Float64)).all())
print("bad", bad)
