# Evaluation of def:run_py_py_py after the fifth port diff (2026-11-18): runs the real train.run on
# small inputs with no fit (one response value among the rows used) and prints the frames passed to
# write_sas_csv in call order, model.json, the stepwise result and the Lean input terms of the two
# imported tables (printed only, never saved).
#   cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/u5_run_py_py_py_nofit.py
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "diffeval")
import leanterm as lt  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

FIX = Path("../../port/tests/data/one_row_training")
written = []
orig = sc.write_sas_csv


def rec(df, path, formats=None):
    written.append((Path(path).name, df))
    return orig(df, path, formats=formats)


sc.write_sas_csv = rec
orig_sw = sc.stepwise_logistic
cap = {}


def sw(*a, **k):
    r = orig_sw(*a, **k)
    cap["sw"] = r
    return r


sc.stepwise_logistic = sw


def case(name, tr_text, va_text, lean=True):
    d = Path(tempfile.mkdtemp())
    i = d / "in"
    o = d / "out"
    i.mkdir()
    if tr_text is not None:
        (i / "model_features_train.csv").write_text(tr_text)
    if va_text is not None:
        (i / "model_features_validation.csv").write_text(va_text)
    written.clear()
    cap.clear()
    try:
        train.run(i, o)
        res = "completed"
    except Exception as e:  # noqa: BLE001
        res = f"raised {type(e).__name__}: {e}"
    print("=== CASE", name, res)
    sw_ = cap.get("sw")
    print("stepwise:", None if sw_ is None else (len(sw_.steps), sw_.final, sw_.intercept_only))
    for n, df in written:
        print("FILE", n, df.shape, df.columns)
        print("  ", df.to_dicts())
    mj = o / "model.json"
    print("model.json:", mj.read_text() if mj.exists() else "absent")
    if lean and tr_text is not None and va_text is not None:
        tr = sc.proc_import_csv(i / "model_features_train.csv", guessingrows=None)
        va = sc.proc_import_csv(i / "model_features_validation.csv", guessingrows=None)
        print("LEAN_TR", lt.lean_table(tr) if tr.height else "[]")
        print("LEAN_VA", lt.lean_table(va) if va.height else "[]")
    shutil.rmtree(d)


c0 = (FIX / "n1_class0" / "model_features_train.csv").read_text().splitlines()
c1 = (FIX / "n1_class1" / "model_features_train.csv").read_text().splitlines()
hdr = c0[0]
case("stop_no_train_file", None, hdr + "\n", lean=False)
case("n1_class0", "\n".join(c0) + "\n", hdr + "\n")
# two rows of one class in training (the row of n1_class0 with ids 1 and 2), one row in validation
# (the row of n1_class1, default_flag 1)
r2 = "2" + c0[1][c0[1].index(","):]
case("two_rows_class0_valid1", "\n".join([hdr, c0[1], r2]) + "\n", "\n".join([hdr, c1[1]]) + "\n")
