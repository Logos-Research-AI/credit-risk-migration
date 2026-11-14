import numpy as np, polars as pl, math, sys
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/modelstat-classify")
runs = ["baseline_v2", "m_fe_health_penalty", "m_fe_import_guessingrows", "m_fe_impute_mean", "m_fe_median_group_misaligned", "m_train_slstay", "x_split_drift_m_metrics_threshold"]
def doc(bs, N, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or (c < M and c + math.floor(0.5 * nj) <= M): c += nj
        else: groups.append(c); c = nj
    groups.append(c)
    if groups[-1] <= math.floor(0.05 * N) and len(groups) > 1: groups[-2] += groups.pop()
    return groups
for r in runs:
    d = pl.read_csv(f"{J}/runs/{r}/risk_scores_train.csv", infer_schema_length=0).select(pl.col("pd_logistic").cast(pl.Float64)).sort("pd_logistic")
    p = d["pd_logistic"].to_numpy(); N = len(p)
    st = np.flatnonzero(np.r_[True, p[1:] != p[:-1]]); bs = np.diff(np.r_[st, N])
    ref = pl.read_csv(f"{J}/runs/{r}/printed_hl_partition.csv")["Total"].to_list()
    g = doc(bs, N)
    print(r, "N", N, "maxblock", bs.max(), "\n  SAS ", ref, "\n  doc ", g)
    cum = np.cumsum(ref)[:-1]
    # block sizes around each SAS boundary
    out = []
    for b in cum:
        i = np.searchsorted(st, b, side="right") - 1  # block containing obs index b (0-based = obs b+1)
        out.append((int(b), int(st[i]), int(bs[i])))
    print("  boundaries (cum, start of block containing next obs, its size):", out)
