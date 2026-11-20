"""Fidelity pass 2026-11-20 (label stale-compositions): the real-data inputs of def:run and def:run_py_py,
Python side at port HEAD 4a757fb.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_real_gen.py
      -> diffeval/work/fz10_real.expected.json

The REAL feature_engineering.run on legacy/data/cs-training.csv with inputs/split_ids.csv, then the REAL
train.run on its feature files (only to obtain model.json / model_coefficients.csv), then the REAL
predict.run on legacy/data/cs-test.csv. write_sas_csv is wrapped (the real writer still writes) to
record each frame in call order. Recorded per file of the two compositions: name, columns, height, and
the digest compare.digest(tok_str(name) + tokens(canon_table(df))) used by fz_run_gen (without the four
log columns for feature engineering, as there) and by fz_run_py_py_gen's file_digest for predict.
Also recorded: whether the split file fits ((7n+9)//10 distinct present ids: used as given) or the run
draws.
The Lean side is NOT evaluated (no carrier on 5365851c; eval_decl refuses def:run / def:run_py_py at
call level, 2026-11-20). A whole-file input (150,000 / 101,503 rows) would in any case exceed an
eval_decl input by far: the earlier real-data checks of these compositions used slices (t6, t11, runs_r2).
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import compare as cmp  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train as tr  # noqa: E402

ROOT = HERE.parents[3]
DATA = ROOT / "legacy" / "data"
SPLIT = HERE.parents[1] / "inputs" / "split_ids.csv"
LOGS = ["log_monthly_income", "log_num_credit_lines", "log_total_late_payments", "age_income_interaction"]


def fe_digest(name, df):
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df.drop([c for c in LOGS if c in df.columns]))))


def full_digest(name, df):
    toks = cmp.tok_str(name) + [len(df.columns)]
    for c in df.columns:
        toks += cmp.tok_str(c)
    return cmp.digest(toks + cmp.tokens(cmp.canon_table(df)))


def main() -> None:
    rec: list = []
    orig = sc.write_sas_csv

    def w(df, path, formats=None):
        rec.append((Path(path).name, df))
        return orig(df, path, formats=formats)

    out: dict = {"port_head": "4a757fb", "split_file": str(SPLIT.relative_to(HERE.parents[1]))}
    with tempfile.TemporaryDirectory() as d:
        o = Path(d) / "out"
        sc.write_sas_csv = w
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(DATA, o, split_ids=SPLIT)
            fe_files = list(rec)
            rec.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                tr.run(o, o)
            rec.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                pr.run(o, o, data_dir=DATA, income_medians=o / "income_medians.csv")
            pr_files = list(rec)
        finally:
            sc.write_sas_csv = orig
        model = json.loads((o / "model.json").read_text())
    tr_rows = fe_files[1][1].height
    n = tr_rows + fe_files[2][1].height
    ids = pl.read_csv(SPLIT, columns=["row_id"], infer_schema=False).select(sc.input_best32(pl.col("row_id"))).get_column("row_id").to_list()
    nt = (7 * n + 9) // 10
    out["split"] = {"n": n, "n_train": nt, "file_ids": len(ids), "distinct": len(set(ids)),
                    "fits": len(ids) == nt and len(set(ids)) == nt, "train_rows": tr_rows}
    out["run"] = [{"file": f, "columns": df.columns, "height": df.height, "digest_without_logs": fe_digest(f, df),
                   "digest_full": full_digest(f, df)} for f, df in fe_files]
    out["run_py_py"] = [{"file": f, "columns": df.columns, "height": df.height, "digest": full_digest(f, df)} for f, df in pr_files]
    out["model"] = {"intercept": model["intercept"], "n_coefficients": len(model["coefficients"]), "names": list(model["coefficients"])}
    (HERE.parent / "work" / "fz10_real.expected.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "model"}, indent=0)[:3000])
    print(out["model"])


if __name__ == "__main__":
    main()
