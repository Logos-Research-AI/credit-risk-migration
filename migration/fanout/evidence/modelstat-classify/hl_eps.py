import numpy as np, polars as pl, math, glob, os
import sys; sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/modelstat-classify"); from hl_lib import *
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
dirs = sorted({os.path.dirname(f) for f in glob.glob(f"{J}/runs/*/printed_hl_partition.csv")} | {f"{J}/reference", f"{J}/reference/scenarios/edge_predict"})
data = {}
for dd in dirs:
    p = np.sort(pl.read_csv(f"{dd}/risk_scores_train.csv", infer_schema_length=0)["pd_logistic"].cast(pl.Float64).to_numpy())
    data[dd.replace(J + "/", "")] = (p, pl.read_csv(f"{dd}/printed_hl_partition.csv")["Total"].to_list())
print(len(data), "datasets")
ok_eps = []
for eps in np.round(np.arange(0.50e-6, 2.0001e-6, 0.01e-6), 10):
    allok = all(doc(anchored_blocks(p, eps, False), len(p)) == ref for p, ref in data.values())
    if allok: ok_eps.append(eps)
print("eps reproducing ALL:", ok_eps[:1], "...", ok_eps[-1:], "count", len(ok_eps))
# chained / other rule at 1e-6 for contrast
for name, (p, ref) in data.items():
    g = doc(anchored_blocks(p, 1e-6, False), len(p))
    gl = lt(anchored_blocks(p, 1e-6, False), len(p))
    ge = doc(anchored_blocks(p, 0.0, False), len(p))
    print(f"{name:45s} doc+anch1e-6 {'OK' if g == ref else g}  | lt-rule {'OK' if gl == ref else 'differs'} | exact-ties {'OK' if ge == ref else 'differs'}")
