import sys
from pathlib import Path
import polars as pl
from credit_risk import sas_compat as sc
R = Path("../../judge/scenarios")
for n in ["real_metrics","fix_Q23_nodefaulter","fix_G43","edge_metrics_a","edge_metrics_b","edge_metrics_c"]:
    v = sc.proc_import_csv(R/n/"risk_scores_validation.csv", guessingrows=20)
    d, p = v["default_flag"], v["pd_logistic"]
    txt = pl.read_csv(R/n/"risk_scores_validation.csv", infer_schema=False)["pd_logistic"].to_list()
    ml = max(len(t or "") for t in txt)
    odd = [t for t in txt if t is None or "e" in t.lower() or not t.startswith("0.")][:8]
    print(n, v.height, d.dtype, p.dtype, "flag nulls", d.null_count(), d.unique().to_list()[:5], "pd nulls", p.null_count(), "nan", p.is_nan().sum(), "maxlen", ml, "odd", odd, "uniq pd", p.n_unique())
