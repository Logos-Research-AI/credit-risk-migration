import polars as pl, glob
R="/Users/cristophersalvi/GitHub/sas-migration/judge"
files = sorted(glob.glob(R+"/reference/model_features_*.csv")+glob.glob(R+"/reference/risk_scores_*.csv")
  +glob.glob(R+"/scenarios/*/risk_scores_*.csv")+glob.glob(R+"/scenarios/*/model_features_*.csv")
  +glob.glob(R+"/reference/scenarios/*/risk_scores_*.csv"))
for f in files:
    df = pl.read_csv(f, infer_schema=False)
    out=[f.replace(R+"/",""), df.height]
    for c in ["default_flag","pd_logistic","pred_logistic","risk_grade","recommendation","interest_rate","credit_risk_score"]:
        if c in df.columns:
            s=df[c]
            out.append(f"{c}: empty={(s.is_null()|(s=='')).sum()} uniq={sorted(s.unique().drop_nulls().to_list())[:8] if s.n_unique()<10 else s.n_unique()}")
    print(*out, sep=" | ")
