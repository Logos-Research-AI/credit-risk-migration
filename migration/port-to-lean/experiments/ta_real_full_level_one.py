"""T-A 2026-11-17: does the classification table of the full real data change with the second
diff (level printed 1.000 compared with 1 + 1e-12 on every fit)? The real train.run on the full
feature files of legacy/data (tc_gen.full_features); the arguments of classification_table are
captured and the leave-one-out probabilities recomputed (sc:1277-1295)."""
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diffeval" / "units"))
sys.path.insert(0, str(HERE.parent / "diffeval"))
import tc_gen as tc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

calls = []
o = sc.classification_table
sc.classification_table = lambda *a, **k: (calls.append((a, k)), o(*a, **k))[1]
r = tc.real_run(tc.full_features(), False)
sc.classification_table = o
assert r["raised"] is None, r["raised"]
(y, x), pd = calls[0][0], calls[0][1]["pd"]
p = np.asarray(pd, dtype=np.float64)
eta = np.log(p) - np.log1p(-p)
w = p * (1.0 - p)
v = np.linalg.inv(x.T @ (x * w[:, None]))
q = np.einsum("ij,jk,ik->i", x, v, x)
ps = sc._expit(eta - (y - p) * q / (1.0 - w * q))
khi = math.ceil(float(ps.max()) / 0.02)
t = o(y, x, pd=pd)
print("rows", len(y), "columns", x.shape[1], "names", r["locals"]["final"].names)
print("max ps", float(ps.max()), "khi", khi, "levels", t.height, "last level", t["ProbLevel"][-1])
print("ps >= 1.0:", int(np.count_nonzero(ps >= 1.0)), "-> the table", "CHANGES" if khi == 50 and np.count_nonzero(ps >= 1.0) else "does not change", "with the second diff")
