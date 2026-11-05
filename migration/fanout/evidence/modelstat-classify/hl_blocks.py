"""Tie-block structure of the training pd around the HL group boundaries."""
import numpy as np
import polars as pl

J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
MODEL_VARS = ["credit_utilization_capped", "debt_ratio_capped", "has_delinquency", "has_serious_delinquency",
              "log_monthly_income", "num_real_estate_loans", "num_dependents", "income_per_dependent",
              "credit_lines_per_person", "flag_high_utilization", "flag_very_high_utilization",
              "flag_very_high_debt_ratio", "flag_recent_late_payments", "flag_multiple_delinquencies",
              "flag_few_credit_lines", "credit_util_category", "financial_health", "age_income_interaction"]
rs = pl.read_csv(f"{J}/reference/risk_scores_train.csv", infer_schema_length=0)
d = rs.select(pl.col("row_id"), pl.col("default_flag").cast(pl.Int64), pl.col("pd_logistic").alias("pd_txt"),
              pl.col("pd_logistic").cast(pl.Float64).alias("pd"),
              pl.concat_str([pl.col(c) for c in MODEL_VARS], separator="|").alias("cov"))
d = d.sort("pd", maintain_order=True)
n = d.height
pd_ = d["pd"].to_numpy()
cov = d["cov"].to_list()
print("N", n, "distinct pd", d["pd"].n_unique(), "distinct cov", d["cov"].n_unique())
# block = run of equal pd
new_block = np.r_[True, pd_[1:] != pd_[:-1]]
starts = np.flatnonzero(new_block)  # 0-based start index of each block
ends = np.r_[starts[1:], n]          # exclusive end
sizes = ends - starts
print("blocks", len(starts), "max block", sizes.max(), "blocks>1:", (sizes > 1).sum())
ref_cum = np.cumsum([10498, 10502, 10501, 10502, 10499, 10500, 10500, 10501, 10500, 10497])
for i in range(1, 10):
    t = i * 10500
    # block containing position t (1-based last item t -> index t-1)
    b = np.searchsorted(starts, t - 1, side="right") - 1
    print(f"target {t}: SAS boundary {ref_cum[i-1]}; block containing obs #{t}: [{starts[b]+1}, {ends[b]}] size {sizes[b]};"
          f" prev block end {starts[b]}, next block start {ends[b]+1}")
    for j in range(max(0, b - 2), min(len(starts), b + 3)):
        print(f"    block [{starts[j]+1},{ends[j]}] size {sizes[j]} pd={pd_[starts[j]]!r}")
