import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
runs = ["baseline_v2", "m_fe_health_penalty", "m_fe_import_guessingrows", "m_fe_impute_mean", "m_fe_median_group_misaligned", "m_train_slstay", "x_split_drift_m_metrics_threshold"]
for r in runs:
    p = np.sort(pl.read_csv(f"{J}/runs/{r}/risk_scores_train.csv", infer_schema_length=0)["pd_logistic"].cast(pl.Float64).to_numpy())
    N = len(p)
    newv = np.r_[True, p[1:] != p[:-1]]
    ndist_cum = np.cumsum(newv)  # distinct count up to obs i
    K = ndist_cum[-1]
    ref = pl.read_csv(f"{J}/runs/{r}/printed_hl_partition.csv")["Total"].to_numpy()
    cum = np.cumsum(ref)
    print(r, "N", N, "K distinct", K, "K/10", K / 10)
    print("   distinct up to SAS boundary:", [int(ndist_cum[c - 1]) for c in cum])
