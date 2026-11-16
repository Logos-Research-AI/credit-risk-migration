import polars as pl, sys
from pathlib import Path
from credit_risk import sas_compat as sc
R = Path("../../judge/scenarios")
for d in ["fix_Q26_small","fix_Q26_ties","fix_Q26_nodefaulter","fix_Q23_alldefaulters","fix_Q23_tie","fix_Q23_nodefaulter","real_metrics","edge_metrics_a","edge_metrics_b","edge_metrics_c"]:
    f = sc.proc_import_csv(R/d/"risk_scores_validation.csv", guessingrows=20)
    y, s = f.get_column("default_flag"), f.get_column("pd_logistic")
    print(d, f.height, y.dtype, s.dtype, "nulls", y.null_count(), s.null_count(), "yvals", sorted(set(map(str, y.unique().to_list())))[:6], "nuniq s", s.n_unique(), "min/max", s.min(), s.max())
    sl = s.drop_nulls().to_list()
    for k in (2, 4, 10):
        ok = all(x == round(x * 10**k) / 10**k for x in sl)
        print("   decimals", k, ok)
    r = sc.roc_association(y, s, "Logistic Model")
    print("  ", r.row(0))
