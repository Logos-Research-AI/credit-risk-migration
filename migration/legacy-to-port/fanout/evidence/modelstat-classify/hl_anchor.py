import numpy as np, polars as pl, math
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
runs = ["baseline_v2", "m_fe_health_penalty", "m_fe_import_guessingrows", "m_fe_impute_mean", "m_fe_median_group_misaligned", "m_train_slstay", "x_split_drift_m_metrics_threshold"]
data = {}
for r in runs:
    p = np.sort(pl.read_csv(f"{J}/runs/{r}/risk_scores_train.csv", infer_schema_length=0)["pd_logistic"].cast(pl.Float64).to_numpy())
    ref = pl.read_csv(f"{J}/runs/{r}/printed_hl_partition.csv")["Total"].to_list()
    data[r] = (p, ref)

def anchored_blocks(v, eps, rel):
    out = []; i = 0; n = len(v)
    while i < n:
        lim = v[i] * (1 + eps) if rel else v[i] + eps
        j = np.searchsorted(v, lim, side="right")
        out.append(j - i); i = j
    return out

def chained_blocks(v, eps, rel):
    d = np.diff(v)
    thr = eps * v[:-1] if rel else eps
    st = np.flatnonzero(np.r_[True, d > thr])
    return list(np.diff(np.r_[st, len(v)]))

def doc(bs, N, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or (c < M and c + math.floor(0.5 * nj) <= M): c += nj
        else: groups.append(c); c = nj
    groups.append(c)
    if groups[-1] <= math.floor(0.05 * N) and len(groups) > 1: x = groups.pop(); groups[-1] += x
    return groups

def lt(bs, N, G=10):
    M = math.floor(N / G + 0.5); groups = []; c = 0
    for nj in bs:
        if c == 0 or c < M: c += nj
        else: groups.append(c); c = nj
    groups.append(c); return groups

def key(v, kind, eps, rel):
    return anchored_blocks(v, eps, rel) if kind == "anch" else chained_blocks(v, eps, rel)

best = []
for kind in ("anch", "chain"):
    for rel in (False, True):
        grid = [m * 10.0 ** k for k in range(-9, -2) for m in (1, 2, 3, 5)]
        for eps in grid:
            for rn, rule in (("doc", doc), ("lt", lt)):
                score = 0; exact = 0
                for r, (p, ref) in data.items():
                    g = rule(key(p, kind, eps, rel), len(p))
                    if len(g) == len(ref):
                        dev = sum(abs(a - b) for a, b in zip(g, ref)); score += dev; exact += dev == 0
                    else:
                        score += 10**6
                best.append((score, exact, kind, rel, eps, rn))
best.sort()
for b in best[:15]: print(b)
