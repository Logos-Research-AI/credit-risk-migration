import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
args = sys.argv[1:]; sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz7_metrics_gen as g
import polars as pl, compare as cmp, leanterm as lt
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(20)
s = int(args[0])
V = g.V_of(s)
ns = dict(vars(g.mc)); ns.update(logit_scored_valid=V, logit_scored_train=g.T_of(s), valid_exists=V.height>0)
g.ex(g.CA, ns)
Vs = ns["logit_scored_valid"].select("default_flag", "pd_logistic")
print(Vs)
print(ns["decile_analysis"])
open(HERE.parent/"work"/"fz7_dbg4.in.txt","w").write("(let V := " + lt.lean_frame(Vs) + "; let r := metrics_run_04_deciles V; pr_frame2 (r.1, r.2))")
exp = cmp.tokens(g.canon(ns['decile_data'])) + cmp.tokens(g.canon(ns['decile_analysis']))
open(HERE.parent/"work"/"fz7_dbg4.exp.json","w").write(str(exp))
print(len(open(HERE.parent/"work"/"fz7_dbg4.in.txt").read()))
