import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz7_metrics_gen as g
import polars as pl, compare as cmp, leanterm as lt
def psi(T, V):
    V = V.with_columns(default_flag=pl.lit(0.0), pd_logistic=pl.lit(0.5))
    ns = dict(vars(g.mc)); ns.update(logit_scored_valid=V, logit_scored_train=T, valid_exists=True)
    g.ex(g.CC, ns); return ns
cases = {
 "f64 600 / [600,650]": (pl.DataFrame({"credit_risk_score": [600.0]}), pl.DataFrame({"credit_risk_score": [600.0, 650.0]})),
 "f64 600 / [600]": (pl.DataFrame({"credit_risk_score": [600.0]}), pl.DataFrame({"credit_risk_score": [600.0]})),
 "f64 none / [600]": (pl.DataFrame({"credit_risk_score": pl.Series([None], dtype=pl.Float64)}), pl.DataFrame({"credit_risk_score": [600.0]})),
}
for k,(T,V) in cases.items():
    ns = psi(T,V)
    print(k)
    print(ns["psi_calculation"].select("score_bin","train_pct","valid_pct","psi_component").to_dicts()[:10])
    print(ns["psi_summary"].to_dicts())
    lf = lambda d: lt.lean_frame(d)
    print("LEAN:", f"(pr_frame2 (metrics_run_06_psi {lf(T)} {lf(V.select('credit_risk_score'))}))")
    print("EXP:", cmp.tokens(g.canon(ns['psi_calculation']))+cmp.tokens(g.canon(ns['psi_summary'])))
