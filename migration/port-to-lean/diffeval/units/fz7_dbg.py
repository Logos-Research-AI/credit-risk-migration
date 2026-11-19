import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE))
import fz7_metrics_gen as g
import polars as pl
pl.Config.set_tbl_rows(50); pl.Config.set_tbl_cols(20)
s = 41055
V, T = g.V_of(s), g.T_of(s)
print(V); print(T)
ns = dict(vars(g.mc)); ns.update(logit_scored_valid=V, logit_scored_train=T, valid_exists=True)
g.ex(g.CA, ns); g.ex(g.CC, ns)
print(ns["psi_calculation"]); print(ns["psi_summary"]); print(ns["psi_cuts"])
