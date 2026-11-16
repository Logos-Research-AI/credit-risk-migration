"""Review of T5 / T9 by port-translator-7: def:fe_run_05_features (feature_engineering.py:234-336)
and def:predict_run_05_features (predict.py:277-372) on the reviewer's own inputs.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_t5t9_gen.py
      -> diffeval/work/rv_t5t9.json, rv_t5t9.inputs.json

Python side: the source lines of the step are executed verbatim (read from the module file,
dedented) on a hand-made frame; nothing is retyped. Inputs, all inside the two preconditions:
  edge   14 rows: every threshold of the step exactly and just beside it, nulls, NaN, infinities,
         zeros of both signs, negative and fractional counts, a divisor of 0.5 and of -1 after
         `+ 1` is never 0; plus columns the step CREATES already present in the input with
         another dtype (has_delinquency and total_risk_flags as text, log_monthly_income,
         age_category, total_late_payments as numbers) and one it does not touch
  empty  the same columns, no row
  one    the first row only; zeros (every input 0.0); negzeros (every input -0.0)
Lean side: digest of the result without the four columns that hold a logarithm (the last bit of
log is outside the model, RULEBOOK §6), for full = true and false; the four log columns of `edge`
are compared as tokens with a tolerance of 2 ulps.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat  # noqa: E402

nan, inf = float("nan"), float("inf")
EDGE = pl.DataFrame(
    {
        "VAR1": [float(i) for i in range(1, 15)],
        "has_delinquency": ["x"] * 14,
        "age": [24.0, 25.0, 34.999, 35.0, 50.0, 65.0, 64.5, None, nan, inf, -1.0, 0.0, -0.0, 49.0],
        "log_monthly_income": [7.0] * 14,
        "monthly_income": [2500.0, 2499.99, 0.0, -0.0, None, nan, inf, -5.0, 1e-320, 1.0, 2500.0, 3000.0, 0.5, 1e308],
        "num_dependents": [0.0, 1.0, 3.0, 2.5, None, nan, inf, -0.5, -2.0, 0.0, -0.0, 3.0, 20.0, 1e-17],
        "num_late_30_59": [0.0, 1.0, None, nan, 2.0, 0.0, 0.0, None, 3.0, 0.0, -1.0, 98.0, 0.0, 0.0],
        "total_risk_flags": ["y"] * 14,
        "num_late_60_89": [0.0, 0.0, None, 1.0, 0.0, 0.0, 0.0, None, 0.0, 0.0, 1.0, 98.0, 0.0, 0.0],
        "num_late_90_plus": [0.0, 0.0, None, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 98.0, 0.0, nan],
        "age_category": [9.5] * 14,
        "credit_utilization": [30.0, 30.0000001, 50.0, 75.0, 75.5, 100.0, 100.5, 200.0, 250.0, None, nan, -0.0, inf, 29.9],
        "debt_ratio": [30.0, 43.0, 43.5, 60.0, 60.5, 500.0, 501.0, None, nan, -1.0, 0.0, inf, 29.0, 42.99],
        "total_late_payments": [1.0] * 14,
        "num_credit_lines": [2.0, 2.5, 3.0, None, nan, 0.0, -1.0, 1.0, 2.0, 10.0, 0.0, -0.0, inf, 5.0],
        "untouched": ["k"] * 14,
    }
)
NUMS = ["age", "monthly_income", "num_dependents", "num_late_30_59", "num_late_60_89", "num_late_90_plus",
        "credit_utilization", "debt_ratio", "num_credit_lines"]
FRAMES = {
    "edge": EDGE,
    "empty": EDGE.clear(),
    "one": EDGE.head(1),
    "zeros": EDGE.head(1).with_columns([pl.lit(0.0).alias(c) for c in NUMS]),
    "negzeros": EDGE.head(1).with_columns([pl.lit(-0.0).alias(c) for c in NUMS]),
}
LOGS = ["log_monthly_income", "log_num_credit_lines", "log_total_late_payments", "age_income_interaction"]
UNITS = [  # unit, carrier, module, first line, last line, input name, output name
    ("fe_run_05_features", "zz_carrier_f", fe, 234, 336, "credit_imputed", "credit_features"),
    ("predict_run_05_features", "zz_carrier_p", pr, 277, 372, "test_imputed", "test_features"),
]


def slice_run(mod, a: int, b: int, inp: str, out: str, df: pl.DataFrame) -> pl.DataFrame:
    src = textwrap.dedent("\n".join(Path(mod.__file__).read_text().splitlines()[a - 1:b]))
    env = {"pl": pl, "sas_compat": sas_compat, inp: df}
    exec(compile(src, f"{mod.__name__}:{a}-{b}", "exec"), env)
    return env[out]


def main():
    s = Suite("rv_t5t9")
    lets = "".join(lt.lean_frame_let(f"f_{k}", v) for k, v in FRAMES.items())
    drop = "[" + ", ".join(lt.lean_str(c) for c in LOGS) + "]"
    for unit, carrier, mod, a, b, inp, out in UNITS:
        s.item, s.decl, s.carrier = f"def:{carrier}", carrier, "identity"
        res = {k: slice_run(mod, a, b, inp, out, v) for k, v in FRAMES.items()}
        for k, r in res.items():
            print(unit, k, r.shape, [c for c in r.columns][:6], "...")
        cases = []
        for k in FRAMES:
            for full in ("true", "false"):
                cases.append((f"{unit} {k} full={full} (without the log columns)", unit,
                              f"tR (({unit} {full} f_{k}).drop {drop})", cmp.canon_frame(res[k].drop(LOGS))))
        s.digest(lets, cases, gen=False, table=False)
        s.tokens(lt.lean_frame_let("f_edge", EDGE), f"{unit} edge: the four log columns (2 ulps)", unit,
                 f"tR (({unit} true f_edge).cols {drop})", "frame", cmp.canon_frame(res["edge"].select(LOGS)),
                 gen=False, ulp_tol=2)
    s.notes = {u[0]: "review by port-translator-7: source lines executed verbatim on hand-made frames (thresholds, nulls, NaN, "
                     "infinities, signed zeros, created columns already present with another dtype; no row; one row)" for u in UNITS}
    s.write()


if __name__ == "__main__":
    main()
