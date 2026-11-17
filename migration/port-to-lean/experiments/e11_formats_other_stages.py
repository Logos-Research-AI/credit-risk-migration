"""E11 (2026-11-17, port-translator-8): the dtype of every column a non-empty `formats` names, at
each write_sas_csv call of the four stages, on a real chained run; then the same with hostile
caller columns (text columns named like the formatted ones) in the stage's input files.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/e11_formats_other_stages.py > experiments/e11_formats_other_stages.out.txt

Run A: feature_engineering.run on the first 3,000 data lines of legacy/data/cs-training.csv with
migration/port-to-lean/inputs/split_ids.csv, then train.run, metrics_calculation.run, predict.run (first 300 lines
of cs-test.csv). sas_compat.write_sas_csv is wrapped: it records (file, key, dtype) for every key
of a non-empty `formats` and then calls the real function.
Run B (metrics): the two score files get text columns named like every formatted column of the
stage; metrics_calculation.run again.
Run C (feature engineering / predict): a text column named like a formatted one added to
cs-training.csv / cs-test.csv.
"""
from __future__ import annotations
import contextlib, io, tempfile
from pathlib import Path
import polars as pl
from credit_risk import feature_engineering as fe, metrics_calculation as mc, predict, sas_compat as sc, train

REPO = Path(__file__).resolve().parents[3]
DATA = REPO / "legacy" / "data"
SPLIT = Path(__file__).resolve().parents[1] / "inputs" / "split_ids.csv"
real = sc.write_sas_csv
rec: list = []


def wrapped(df, path, formats=None):
    for k in (formats or {}):
        rec.append((Path(path).name, k, str(df.schema.get(k, "ABSENT")), df.height))
    return real(df, path, formats)


def call(label, f):
    rec.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            f()
        out = "returns"
    except Exception as e:  # noqa: BLE001
        out = f"RAISES {type(e).__name__}: {e}"
    print(f"== {label}: {out}")
    for r in rec:
        print(f"   {r[0]:32s} {r[1]:22s} {r[2]:8s} rows={r[3]}")
    bad = [r for r in rec if r[2] in ("String", "ABSENT")]
    print(f"   formatted columns: {len(rec)}; text or absent: {len(bad)}")


def head(path: Path, n: int) -> str:
    return "".join(path.read_text().splitlines(keepends=True)[: n + 1])


def add_text_cols(path: Path, names: list[str]):
    df = pl.read_csv(path, infer_schema=False)
    df.with_columns([pl.lit("x").alias(n) for n in names if n not in df.columns]).write_csv(path)


sc.write_sas_csv = wrapped
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    data, out = d / "data", d / "out"
    data.mkdir()
    (data / "cs-training.csv").write_text(head(DATA / "cs-training.csv", 3000))
    (data / "cs-test.csv").write_text(head(DATA / "cs-test.csv", 300))
    print("polars", pl.__version__)
    call("A feature_engineering.run", lambda: fe.run(data, out, split_ids=SPLIT))
    call("A train.run", lambda: train.run(out, out))
    call("A metrics_calculation.run", lambda: mc.run(out, out))
    call("A predict.run", lambda: predict.run(out, out, data_dir=data, income_medians=out / "income_medians.csv"))
    keys = ["AUC", "Gini", "KS_Statistic", "KS_Cutoff", "PSI", "validation_date", "default_rate", "avg_pd", "min_pd", "max_pd",
            "capture_rate", "lift", "cum_capture_rate", "cum_lift", "mean_predicted", "mean_actual"]
    hostile = d / "hostile"
    hostile.mkdir()
    for f in ("risk_scores_train.csv", "risk_scores_validation.csv"):
        (hostile / f).write_text((out / f).read_text())
        add_text_cols(hostile / f, keys)
    print("hostile score files: columns", pl.read_csv(hostile / "risk_scores_validation.csv", n_rows=1).columns[-len(keys):])
    call("B metrics_calculation.run on score files with text columns named like the formatted ones", lambda: mc.run(hostile, d / "out_b"))
    data_c = d / "data_c"
    data_c.mkdir()
    (data_c / "cs-training.csv").write_text(head(DATA / "cs-training.csv", 50))
    add_text_cols(data_c / "cs-training.csv", ["median_income", "overall_median_income"])
    (data_c / "cs-test.csv").write_text(head(DATA / "cs-test.csv", 50))
    add_text_cols(data_c / "cs-test.csv", ["interest_rate"])
    call("C feature_engineering.run, cs-training.csv with text columns median_income / overall_median_income",
         lambda: fe.run(data_c, d / "out_c", split_ids=SPLIT))
    call("C predict.run, cs-test.csv with a text column interest_rate",
         lambda: predict.run(out, d / "out_c2", data_dir=data_c, income_medians=out / "income_medians.csv"))
sc.write_sas_csv = real
