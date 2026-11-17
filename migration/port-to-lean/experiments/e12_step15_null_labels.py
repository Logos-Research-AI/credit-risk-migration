"""E12 (2026-11-17, port-translator-8): what lines 823-842 of credit_risk/train.py do with a ROC
frame whose ROCModel labels are all null (the narrowing of def:train_run_15_printed_roc_precond).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/e12_step15_null_labels.py
"""
import tempfile
import textwrap
from pathlib import Path

import polars as pl

from credit_risk import sas_compat, train

A, B = 823, 842
src = "".join(Path(train.__file__).read_text().splitlines(keepends=True)[A - 1:B])
assert src.lstrip().startswith("roc_cols = [") and "printed_confusion_validation.csv" in src.splitlines()[-1], "line numbers moved"
CODE = compile(textwrap.dedent(src), f"train.py:{A}-{B}", "exec")
RC = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
CM = pl.DataFrame({"default_flag": [0.0], "pred_logistic": [0], "COUNT": [1], "PERCENT": [100.0]})


def roc(labels):
    return pl.DataFrame({"ROCModel": pl.Series(labels, dtype=pl.String), **{c: [0.5] * len(labels) for c in RC}})


def run(name, rt, rv, created):
    seen = {}
    real = sas_compat.write_sas_csv

    def rec(df, path, formats):
        seen[Path(path).name] = df
        return real(df, path, formats=formats)

    ns = dict(vars(train))
    ns.update(confusion_matrix_train=CM, confusion_matrix=CM, roc_train=rt, roc_valid=rv, roc_valid_created=created)
    ns["sas_compat"] = type("S", (), {"write_sas_csv": staticmethod(rec), "sas_d8": staticmethod(sas_compat.sas_d8)})
    with tempfile.TemporaryDirectory() as d:
        ns["output_dir"] = Path(d)
        exec(CODE, ns)
        files = {p.name: p.read_text() for p in sorted(Path(d).iterdir())}
    print(f"--- {name} (roc_valid_created={created})")
    print("    built: printed_roc_train ROCModel", ns["printed_roc_train"].schema["ROCModel"],
          "| printed_roc_validation ROCModel", ns["printed_roc_validation"].schema["ROCModel"])
    for f in ("printed_roc_train.csv", "printed_roc_validation.csv"):
        if f in seen:
            print(f"    written {f}: ROCModel dtype {seen[f].schema['ROCModel']}, file text {files[f]!r}")
        else:
            print(f"    {f}: not written")


ok, tr = roc(["Validation Set"]), roc(["Training Set"])
run("labels present", tr, ok, True)
run("roc_valid: one row, label null", tr, roc([None]), True)
run("roc_valid: one row, label null", tr, roc([None]), False)
run("roc_train: two rows, labels null", roc([None, None]), ok, True)
run("roc_valid: two rows, one label null", tr, roc([None, "x"]), True)
run("roc_valid: no row", tr, roc([]), True)
