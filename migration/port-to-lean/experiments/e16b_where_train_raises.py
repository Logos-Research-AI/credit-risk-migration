"""E16b (2026-11-16): where train.run raises when the validation set is empty (R6), and what it had written by then.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e16b_where_train_raises.py > experiments/e16b_where_train_raises.out.txt
"""
from __future__ import annotations
import contextlib, io, tempfile, traceback
from pathlib import Path
from credit_risk import feature_engineering as fe, sas_compat as sc, train as tr
from e13_common import REAL, head_rows

for n in (2, 100, 2000):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "data").mkdir()
        t = head_rows(REAL / "cs-training.csv", n)
        (d / "data" / "cs-training.csv").write_text(t, newline="")
        (d / "split.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in range(1, n + 1)))
        out = d / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(d / "data", out, split_ids=d / "split.csv")
        v = sc.proc_import_csv(out / "model_features_validation.csv", None)
        print(f"\n== first {n} data lines, every id in the split file")
        print(f"   model_features_validation.csv: {(out / 'model_features_validation.csv').read_bytes().count(10)} line(s); read by proc_import_csv: {v.height} rows x {v.width} columns, kinds {sorted({str(x) for x in v.schema.values()})}")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                tr.run(out, out)
            print("   train completed")
        except Exception as e:  # noqa: BLE001
            fr = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.endswith("train.py")]
            print(f"   train raised {type(e).__name__} at train.py:{fr[-1].lineno}: {fr[-1].line}")
            print(f"   first line of the message: {str(e).splitlines()[0][:200]}")
        print("   output folder after train:", sorted(p.name for p in out.glob("*")))
        print("   the five files train removes at its start and exports at its end are present:",
              {f: (out / f).exists() for f in ("risk_scores_train.csv", "risk_scores_validation.csv", "final_model_output.csv", "model_summary.csv", "model_coefficients.csv")})
