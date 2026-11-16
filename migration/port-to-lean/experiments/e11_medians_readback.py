"""E11 (2026-11-16): income_medians.csv written by the real feature_engineering.run and read by the
reader predict uses (sas_compat.proc_import_csv, default guessingrows=20), on training files where
an age group has no known income, and on every valid scenario: written frame against read frame.
  PYTHONPATH=../../port uv run --project ../../port python experiments/e11_medians_readback.py > experiments/e11_medians_readback.out.txt
"""
import contextlib, io, struct, tempfile
from pathlib import Path
import polars as pl
from credit_risk import feature_engineering as fe, sas_compat as sc
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
b = lambda x: None if x is None else struct.unpack("<Q", struct.pack("<d", float(x)))[0]
for name in ("legacy/data", "judge/scenarios/fix_Q1", "judge/scenarios/fix_Q14", "judge/scenarios/fix_Q13", "judge/scenarios/fix2/good",
             "judge/scenarios/fix2/q13_median_width", "judge/scenarios/fix_G34/income_zero", "judge/scenarios/fix_round5/good",
             "judge/scenarios/fix_Q27_textid/good", "judge/scenarios/fix_Q7", "judge/scenarios/fix_Q9"):
    got = {}
    o = sc.write_sas_csv
    def w(df, path, formats=None):
        got[Path(path).name] = df.clone()
        return o(df, path, formats)
    with tempfile.TemporaryDirectory() as d:
        sc.write_sas_csv = w
        err = None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ROOT / name, Path(d), split_ids=HERE.parent / "inputs/split_ids.csv")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        finally:
            sc.write_sas_csv = o
        if err:
            print(f"{name}: {err}")
            continue
        W = got["income_medians.csv"]
        R = sc.proc_import_csv(Path(d) / "income_medians.csv")
        text = (Path(d) / "income_medians.csv").read_text()
    same = W.columns == R.columns and all([b(x) for x in W[c].to_list()] == [b(x) for x in R[c].to_list()] for c in W.columns)
    print(f"{name}: written {dict(W.schema)} {W.rows()} | file {text!r} | read {dict(R.schema)} {R.rows()} | equal cell for cell: {same}")
