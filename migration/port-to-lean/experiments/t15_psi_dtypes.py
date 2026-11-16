"""T15: what the lines 325-401 of metrics_calculation.py do when credit_risk_score is not Float64.
PYTHONPATH=../../port uv run --project ../../port python experiments/t15_psi_dtypes.py"""
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diffeval" / "units"))
sys.argv = [sys.argv[0]]
import t15_gen as g  # noqa: E402

F = pl.DataFrame({"credit_risk_score": [600.0, 700.0, 800.0]})
S = pl.DataFrame({"credit_risk_score": ["600", "700", "800"]})
I = pl.DataFrame({"credit_risk_score": [600, 700, 800]})
N = pl.DataFrame({"x": [1.0]})
for name, t, v in [("String training", S, F), ("String validation", F, S), ("Int64 training", I, F), ("Int64 validation", F, I),
                   ("column missing in training", N, F), ("column missing in validation", F, N)]:
    try:
        pc, ps = g.run_slice(t, v)
        print(f"{name}: no raise; PSI {ps.item(0, 'PSI')!r}; score_bin dtype {pc.schema['score_bin']}")
    except Exception as e:  # noqa: BLE001
        print(f"{name}: {type(e).__name__}: {str(e).splitlines()[0][:110]}")
