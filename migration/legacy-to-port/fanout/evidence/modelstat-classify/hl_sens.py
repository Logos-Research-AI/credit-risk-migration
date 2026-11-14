import sys, glob, os
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/modelstat-classify")
from hl_lib import *
import numpy as np, polars as pl
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
dirs = sorted({os.path.dirname(f) for f in glob.glob(f"{J}/runs/*/printed_hl_partition.csv")} | {f"{J}/reference"})
data = {}
for dd in dirs:
    p = np.sort(pl.read_csv(f"{dd}/risk_scores_train.csv", infer_schema_length=0)["pd_logistic"].cast(pl.Float64).to_numpy())
    data[dd] = (p, pl.read_csv(f"{dd}/printed_hl_partition.csv")["Total"].to_list())
for eps in [0.99e-6, 0.995e-6, 0.999e-6, 0.9999e-6, 1e-6, 1.0001e-6, 1.001e-6, 1.005e-6, 1.01e-6]:
    nok = sum(doc(anchored_blocks(p, eps), len(p)) == ref for p, ref in data.values())
    print(f"eps={eps:.6g}: {nok}/{len(data)} exact")
# strict '<' variant
def anch_strict(v, eps):
    out = []; i = 0
    while i < len(v):
        j = int(np.searchsorted(v, v[i] + eps, side="left")); j = max(j, i + 1); out.append(j - i); i = j
    return out
print("strict < 1e-6:", sum(doc(anch_strict(p, 1e-6), len(p)) == ref for p, ref in data.values()))
# converged fixture
pc = np.sort(pl.read_csv(f"{J}/fixtures/converged/risk_scores_train.csv", infer_schema_length=0)["pd_logistic"].cast(pl.Float64).to_numpy())
ref = data[f"{J}/reference"][1]
g = doc(anchored_blocks(pc, 1e-6), len(pc))
print("converged fixture totals:", g, "\nreference              :", ref, "\nmax |diff|", max(abs(a - b) for a, b in zip(g, ref)))
