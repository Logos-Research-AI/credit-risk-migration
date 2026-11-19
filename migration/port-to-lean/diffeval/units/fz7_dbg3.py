import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz7_metrics_gen as g
import polars as pl, compare as cmp
V = pl.DataFrame({"credit_risk_score": [600.0, 650.0]})
for nt in (1, 2):
    T = pl.DataFrame({"credit_risk_score": pl.Series([None]*nt, dtype=pl.String)})
    Vv = V.with_columns(default_flag=pl.lit(0.0), pd_logistic=pl.lit(0.5))
    ns = dict(vars(g.mc)); ns.update(logit_scored_valid=Vv, logit_scored_train=T, valid_exists=True)
    g.ex(g.CC, ns)
    print(nt, ns["psi_calculation"].select("score_bin","train_pct","valid_pct").to_dicts()[::9], ns["psi_summary"].to_dicts())
    print("pr_frame2 (metrics_run_06_psi (let f_ : Pl.Frame Float := [(\"credit_risk_score\", (Pl.Col.str [%s]))]; f_) (let f_ : Pl.Frame Float := [(\"credit_risk_score\", (Pl.Col.f64 [some (Float.ofBits 4648488871632306176), some (Float.ofBits 4648928676283416576)]))]; f_))" % ", ".join(["none"]*nt))
