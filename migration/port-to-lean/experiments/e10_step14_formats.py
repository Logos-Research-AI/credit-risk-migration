"""E10 (2026-11-17, port-translator-8): when does step 14 of train.run raise at an export?

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/e10_step14_formats.py > experiments/e10_step14_formats.out.txt

Lines 725-819 of credit_risk/train.py are read from the file and executed with the module's
globals (the real sas_compat.write_sas_csv, writing into a temporary folder) on small frames.
Base: every formatted column present and numeric -> five files. Then one change at a time:
the column a `formats` key names (train.py:730, 735, 759, 803-815; sas_compat.py:645-650) is
removed, or made text, in the frame it comes from. Both values of roc_valid_created.
"""
from __future__ import annotations
import datetime as dt, sys, tempfile, textwrap
from pathlib import Path
import polars as pl
from credit_risk import train

A, B = 725, 819
src = "".join(Path(train.__file__).read_text().splitlines(keepends=True)[A - 1:B])
assert src.lstrip().startswith("risk_scores_train_clean = risk_scores_train") and src.rstrip().endswith('"model_coefficients.csv", formats={})'), "line numbers moved"
CODE = compile(textwrap.dedent(src), f"train.py:{A}-{B}", "exec")
TM = ["train_precision", "train_recall", "train_f1_score", "train_accuracy"]
VM = ["valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy"]


def base() -> dict:
    rs = pl.DataFrame({"row_id": [1.0, 2.0], "default_flag": [0.0, 1.0], "pd_logistic": [0.2, 0.7], "interest_rate": [0.05, 0.12]})
    roc = lambda name: pl.DataFrame({"ROCModel": [name], "Area": [0.75]})
    return {"risk_scores_train": rs, "risk_scores_validation": rs.head(1), "roc_train": roc("Training Set"),
            "roc_valid": roc("Validation Set"), "training_metrics": pl.DataFrame({k: [0.5] for k in TM}),
            "validation_metrics": pl.DataFrame({k: [0.25] for k in VM}),
            "model_coefficients": pl.DataFrame({"Variable": ["Intercept"], "Estimate": ["-1.0"]})}


def run(env: dict, created: bool) -> str:
    ns = dict(vars(train))
    ns.update(env)
    ns["roc_valid_created"] = created
    with tempfile.TemporaryDirectory() as d:
        ns["output_dir"] = Path(d)
        try:
            exec(CODE, ns)
        except Exception as e:  # noqa: BLE001
            return f"RAISES {type(e).__name__}: {e}   (files written before: {sorted(p.name for p in Path(d).iterdir())})"
        return f"returns, files {sorted(p.name for p in Path(d).iterdir())}, model_summary {ns['model_summary'].height} row(s)"


def text(df: pl.DataFrame, c: str) -> pl.DataFrame:
    return df.with_columns(pl.col(c).cast(pl.String))


cases = [("base", lambda e: e)]
for fr in ("risk_scores_train", "risk_scores_validation"):
    cases.append((f"{fr}: no interest_rate", lambda e, fr=fr: {**e, fr: e[fr].drop("interest_rate")}))
    cases.append((f"{fr}: interest_rate text", lambda e, fr=fr: {**e, fr: text(e[fr], "interest_rate")}))
    cases.append((f"{fr}: interest_rate Int64", lambda e, fr=fr: {**e, fr: e[fr].with_columns(pl.col("interest_rate").cast(pl.Int64))}))
    cases.append((f"{fr}: interest_rate all null (Null dtype)", lambda e, fr=fr: {**e, fr: e[fr].with_columns(interest_rate=pl.lit(None))}))
for fr, keys in (("training_metrics", TM), ("validation_metrics", VM)):
    for k in keys:
        cases.append((f"{fr}: no {k}", lambda e, fr=fr, k=k: {**e, fr: e[fr].drop(k)}))
        cases.append((f"{fr}: {k} text", lambda e, fr=fr, k=k: {**e, fr: text(e[fr], k)}))
for fr, k in (("roc_train", "Train_AUC"), ("roc_valid", "Valid_AUC")):
    cases.append((f"{fr}: Area text ({k} text)", lambda e, fr=fr: {**e, fr: text(e[fr], "Area")}))
cases += [
    ("validation_metrics has a text column Train_AUC (overwrites the merged one)", lambda e: {**e, "validation_metrics": e["validation_metrics"].with_columns(Train_AUC=pl.lit("x"))}),
    ("training_metrics also holds valid_recall as text, validation_metrics numeric (later frame wins)", lambda e: {**e, "training_metrics": e["training_metrics"].with_columns(valid_recall=pl.lit("x"))}),
    ("training_metrics has a text column training_date (replaced by with_columns)", lambda e: {**e, "training_metrics": e["training_metrics"].with_columns(training_date=pl.lit("x"))}),
    ("training_metrics has a text column that no format names", lambda e: {**e, "training_metrics": e["training_metrics"].with_columns(note=pl.lit("x"))}),
    ("risk_scores_train has no row", lambda e: {**e, "risk_scores_train": e["risk_scores_train"].clear()}),
    ("training_metrics and validation_metrics have no row", lambda e: {**e, "training_metrics": e["training_metrics"].clear(), "validation_metrics": e["validation_metrics"].clear()}),
]
print("polars", pl.__version__, "python", sys.version.split()[0], dt.date.today().isoformat())
for name, f in cases:
    for created in (True, False):
        print(f"[{name}] roc_valid_created={created}: {run(f(base()), created)}")
