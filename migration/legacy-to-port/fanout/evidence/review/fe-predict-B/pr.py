import sys
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/migration/fanout/evidence/arith")
from fe import build, cmp, R
import polars as pl
cols = ["monthly_income","credit_utilization","debt_ratio","num_credit_lines","total_late_payments","total_risk_flags","financial_health"]
for name, src, ref in [("real", f"{R}/data/cs-test.csv", f"{R}/judge/reference/test_predictions.csv"), ("edge", f"{R}/judge/scenarios/edge_predict/cs-test.csv", f"{R}/judge/reference/scenarios/edge_predict/test_predictions.csv")]:
    df = build(src, None)
    print(name, "median rows by group:", df.group_by("age_group").agg(pl.col("median_income").first(), pl.len(), pl.col("MonthlyIncome").null_count().alias("na")).sort("age_group").rows())
    print("  null counts", {c: df[c].null_count() for c in cols+["log_num_credit_lines","log_total_late_payments","credit_lines_per_person","utilization_debt_interaction","credit_utilization_capped","debt_ratio_capped","num_dependents"]}, "fh_pre min", df["fh_pre"].min())
    cmp(df, ref, cols)
