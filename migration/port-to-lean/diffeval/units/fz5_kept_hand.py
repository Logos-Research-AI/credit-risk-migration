"""Hand-picked edge matrices for def:_kept (fifth diff fuzz): prints the Lean inputs (one per line) and the Python
result of the REAL sas_compat._kept on each (stand-ins as in fz5_kept_gen.py).  --inputs | --run"""
import json, sys, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import numpy as np
import fz5_kept_gen as g
NAN, INF = float("nan"), float("inf")
U = 2.0 ** -52
CASES = [
    [], [[1.0]], [[0.0]], [[-0.0]], [[NAN]], [[INF]], [[-1.0]], [[5e-324]], [[-INF]], [[1e-9]],
    [[1.0, 0.0], [0.0, NAN]], [[NAN, 0.0], [0.0, 1.0]], [[1.0, NAN], [NAN, 1.0]], [[INF, 0.0], [0.0, 1.0]],
    [[-0.0, 0.0], [0.0, 1.0]], [[1.0, 1.0], [1.0, 1.0]], [[1.0, 1.0], [1.0, 1.0 + U]], [[1.0, 0.0], [0.0, 5e-324]],
    [[1.0, 0.0], [0.0, 1e-9]], [[2.0, 1.0], [3.0, 1.5]], [[1.0, 0.0, 2.0], [0.0, 1.0, 0.0], [7.0, 0.0, 5.0]],
    [[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]], [[1e-9, 0.0], [0.0, 1.0]],
]
def run(m):
    n = len(m); arr = np.zeros((n, n))
    for i in range(n):
        for j in range(n): arr[i, j] = m[i][j]
    g.FLAG["zero_pivot"] = False
    o = np.linalg.solve; np.linalg.solve = g.solve_sa
    try:
        with np.errstate(all="ignore"): return g.sc._kept(arr.view(g.NA))
    finally: np.linalg.solve = o
def lean(m):
    return g.S_L + " " + g.D_L + " (Np.NDArray.d2 [" + ",".join("[" + ",".join(g.lit(v) for v in r) + "]" for r in m) + "])"
if sys.argv[1] == "--inputs": print("\n".join(lean(m) for m in CASES))
else: print(json.dumps([run(m) for m in CASES]))
