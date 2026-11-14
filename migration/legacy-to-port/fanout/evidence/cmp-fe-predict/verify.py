import polars as pl
R="/Users/cristophersalvi/GitHub/sas-migration/"
J=R+"judge/reference/"
def raw(p):
    df=pl.read_csv(p,infer_schema=False)
    df=df.rename({"":"VAR1"})
    f=lambda c: pl.col(c).cast(pl.Float64)
    return df.select(
        row_id=f("VAR1").cast(pl.Int64), age=f("age"),
        credit_utilization=f("RevolvingUtilizationOfUnsecuredLines")*100,
        debt_ratio=f("DebtRatio")*100,
        num_late_30_59=f("NumberOfTime30-59DaysPastDueNotWorse"),
        num_late_60_89=f("NumberOfTime60-89DaysPastDueNotWorse"),
        num_late_90_plus=f("NumberOfTimes90DaysLate"),
        num_credit_lines=f("NumberOfOpenCreditLinesAndLoans"),
        num_dependents=pl.when(pl.col("NumberOfDependents")=="NA").then(0.0).otherwise(f("NumberOfDependents")),
        MonthlyIncome=pl.when(pl.col("MonthlyIncome")=="NA").then(None).otherwise(f("MonthlyIncome")),
    )
def chain(x, cuts):
    e=pl.when(x<cuts[0]).then(1)
    for i,c in enumerate(cuts[1:],2): e=e.when(x<c).then(i)
    return e.otherwise(len(cuts)+1)
def feats(df):
    df=df.with_columns(total_late_payments=pl.col("num_late_30_59")+pl.col("num_late_60_89")+pl.col("num_late_90_plus"))
    cu,dr,a=pl.col("credit_utilization"),pl.col("debt_ratio"),pl.col("age")
    df=df.with_columns(
        age_group=chain(a,[30,40,50,60]),
        has_delinquency=(pl.col("total_late_payments")>0).cast(pl.Int64),
        has_serious_delinquency=(pl.col("num_late_90_plus")>0).cast(pl.Int64),
        credit_util_category=chain(cu,[30,50,75]),
        debt_category=chain(dr,[30,43,60]),
        age_category=chain(a,[25,35,50,65]),
        flag_high_utilization=(cu>75).cast(pl.Int64),
        flag_very_high_utilization=(cu>100).cast(pl.Int64),
        flag_high_debt_ratio=(dr>43).cast(pl.Int64),
        flag_very_high_debt_ratio=(dr>60).cast(pl.Int64),
        flag_recent_late_payments=(pl.col("num_late_30_59")>0).cast(pl.Int64),
        flag_serious_delinquency=(pl.col("num_late_90_plus")>0).cast(pl.Int64),
        flag_multiple_delinquencies=(pl.col("total_late_payments")>=3).cast(pl.Int64),
        flag_many_dependents=(pl.col("num_dependents")>=3).cast(pl.Int64),
        flag_few_credit_lines=(pl.col("num_credit_lines")<=2).cast(pl.Int64),
    )
    df=df.with_columns(fh_raw=100-15*(cu>30).cast(pl.Int64)-15*(cu>75).cast(pl.Int64)-20*(dr>43).cast(pl.Int64)
        -20*(pl.col("has_delinquency")!=0).cast(pl.Int64)-30*(pl.col("num_late_90_plus")>0).cast(pl.Int64))
    return df.with_columns(financial_health=pl.max_horizontal(pl.lit(0),pl.col("fh_raw")))
INT=["age_group","has_delinquency","has_serious_delinquency","credit_util_category","debt_category","age_category",
 "flag_high_utilization","flag_very_high_utilization","flag_high_debt_ratio","flag_very_high_debt_ratio",
 "flag_recent_late_payments","flag_serious_delinquency","flag_multiple_delinquencies","flag_many_dependents","flag_few_credit_lines","financial_health"]
# boundary counts
tr=feats(raw(R+"data/cs-training.csv"))
te=feats(raw(R+"data/cs-test.csv"))
for nm,d in [("train",tr),("test",te)]:
    print(nm,"null counts:",{c:d[c].null_count() for c in d.columns if d[c].null_count()})
    for col,cs in [("credit_utilization",[30,50,75,100]),("debt_ratio",[30,43,60]),("age",[25,30,35,40,50,60,65]),("total_late_payments",[0,3]),("num_dependents",[0,3]),("num_credit_lines",[2])]:
        print("  ",col,{c:d.filter(pl.col(col)==c).height for c in cs}, "min",d[col].min(),"max",d[col].max())
    print("   fh_raw<0 rows:",d.filter(pl.col("fh_raw")<0).height)
mf=pl.concat([pl.read_csv(J+"model_features_train.csv"),pl.read_csv(J+"model_features_validation.csv")])
m=mf.join(tr,on="row_id",suffix="_py")
print("FE rows",mf.height,"joined",m.height)
for c in INT:
    print("  FE",c,"mismatch",m.filter(pl.col(c)!=pl.col(c+"_py")).height)
# total_risk_flags FE
m=m.with_columns(trf=pl.col("flag_high_utilization_py")+pl.col("flag_high_debt_ratio_py")+pl.col("flag_serious_delinquency_py")+pl.col("flag_multiple_delinquencies_py")+(pl.col("monthly_income")<2500).cast(pl.Int64))
print("  FE total_risk_flags mismatch",m.filter(pl.col("trf")!=pl.col("total_risk_flags")).height)
# income_per_dependent branch
m=m.with_columns(ipd=pl.when(pl.col("num_dependents_py")>0).then(pl.col("monthly_income")/(pl.col("num_dependents_py")+1)).otherwise(pl.col("monthly_income")))
print("  FE income_per_dependent max rel diff",((pl.col("ipd")-pl.col("income_per_dependent")).abs()/pl.col("income_per_dependent").abs().clip(1e-9)).max().alias("x").__repr__() if False else m.select((((pl.col("ipd")-pl.col("income_per_dependent")).abs())/(pl.col("income_per_dependent").abs()+1e-9)).max()).item())
# predict
for scen,p,out in [("ref",R+"data/cs-test.csv",J+"test_predictions.csv"),("edge",R+"judge/scenarios/edge_predict/cs-test.csv",J+"scenarios/edge_predict/test_predictions.csv")]:
    d=feats(raw(p))
    med=d.filter(pl.col("MonthlyIncome").is_not_null()).group_by("age_group",maintain_order=True).agg(median_income=pl.col("MonthlyIncome").median()).sort("age_group")
    print(scen,"medians",med.to_dicts())
    d=d.join(med,on="age_group",how="left",maintain_order="left").with_columns(
        MonthlyIncome_missing=pl.col("MonthlyIncome").is_null().cast(pl.Int64))
    d=d.with_columns(monthly_income=pl.when(pl.col("MonthlyIncome_missing")==1).then(pl.col("median_income")).otherwise(pl.col("MonthlyIncome")))
    print("  null monthly_income",d["monthly_income"].null_count(), "by age_group", d.filter(pl.col("monthly_income").is_null())["age_group"].value_counts().to_dicts())
    # sas lt: null < 2500 true
    d=d.with_columns(fli=(pl.col("monthly_income").is_null()|(pl.col("monthly_income")<2500)).cast(pl.Int64))
    d=d.with_columns(trf=pl.col("flag_high_utilization")+pl.col("flag_high_debt_ratio")+pl.col("flag_serious_delinquency")+pl.col("flag_multiple_delinquencies")+pl.col("fli"))
    o=pl.read_csv(out,schema_overrides={"monthly_income":pl.Float64})
    x=o.join(d,on="row_id",suffix="_py")
    print("  rows",o.height,x.height)
    for c in ["financial_health","total_late_payments"]:
        print("  ",c,"mismatch",x.filter(pl.col(c)!=pl.col(c+"_py")).height)
    print("   total_risk_flags mismatch",x.filter(pl.col("total_risk_flags")!=pl.col("trf")).height)
    print("   monthly_income null mismatch",x.filter(pl.col("monthly_income").is_null()!=pl.col("monthly_income_py").is_null()).height,
          "value maxdiff",x.select((pl.col("monthly_income")-pl.col("monthly_income_py")).abs().max()).item())
    print("   age mismatch", x.filter(pl.col("age")!=pl.col("age_py")).height)
