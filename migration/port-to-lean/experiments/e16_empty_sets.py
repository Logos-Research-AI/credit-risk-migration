"""E16 (2026-11-16): R6, four-stage runs with an empty validation set, and with a header-only test file.

  PYTHONPATH=../../port uv run --project ../../port python experiments/e16_empty_sets.py > experiments/e16_empty_sets.out.txt

Real stages, in sequence, each in a fresh folder. Per stage: completed or what it raised, and the files that
appeared or changed in the output folder during it (name: number of lines).
"""
from __future__ import annotations
import tempfile
from pathlib import Path
from e13_common import REAL, ROOT, SPLIT, head_rows, new_files, run_stages

SC = ROOT / "judge" / "scenarios"
TRAIN = (REAL / "cs-training.csv").read_text()
TEST = (REAL / "cs-test.csv").read_text()
TEST_HEAD = TEST.splitlines(keepends=True)[0]


def ids_of(train_text):
    return [ln.split(",", 1)[0] for ln in train_text.splitlines()[1:]]


def run(label, train_text, test_text, split_text=None, show=()):
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        sp = SPLIT
        if split_text is not None:
            sp = d / "split.csv"
            sp.write_text(split_text)
        status, locs, files = run_stages(d, train_text, test_text, sp)
    print(f"\n== {label}")
    nf = new_files(files)
    for s in ("fe", "train", "metrics", "predict"):
        print(f"   {s:8}: {status[s]}")
        print(f"             wrote {nf[s]}")
    F = locs.get("fe", {})
    if F.get("credit_train") is not None:
        print(f"   fe: credit_train {F['credit_train'].height} rows, credit_validation {F['credit_validation'].height} rows")
    last = files["predict"]
    for name in show:
        if name in last:
            t = last[name].decode()
            print(f"   {name} ({t.count(chr(10))} lines): {t[:700]!r}")
        else:
            print(f"   {name}: not in the output folder at the end")
    T = locs.get("train", {})
    for k in ("valid_data", "train_data"):
        if T.get(k) is not None:
            v = T[k]
            print(f"   train.run {k}: {v.height} rows x {v.width} columns, kinds {sorted({str(t) for t in v.schema.values()})}")
    return status


def all_ids(train_text):
    return "row_id\n" + "".join(f"{i}\n" for i in ids_of(train_text))


SHOW = ("validation_summary.csv", "ks_statistic.csv", "model_performance_metrics.csv", "decile_analysis.csv", "threshold_analysis.csv", "calibration_plot.csv")
print("#### A. validation set empty: the split file names every applicant")
run("A1 real training file, every id in the split file, real test file", TRAIN, TEST, all_ids(TRAIN), show=SHOW + ("risk_scores_validation.csv", "model_features_validation.csv"))
for n in (2, 20, 100, 500, 2000, 10000):
    t = head_rows(REAL / "cs-training.csv", n)
    run(f"A2 first {n} data lines of the real training file, every id in the split file, real test file", t, TEST, all_ids(t))
for s in ("fix_Q1", "fix2/good", "fix_Q13"):
    t = (SC / s / "cs-training.csv").read_text()
    te = (SC / s / "cs-test.csv").read_text()
    n = len(ids_of(t))
    run(f"A3 scenario {s} ({n} data lines) with the real split file", t, te)
    run(f"A3 scenario {s} ({n} data lines), every id in the split file", t, te, all_ids(t))

print("\n#### B. for comparison, the same small files with the real split file (validation set not empty when n >= 3)")
for n in (2, 20, 100, 500, 2000, 10000):
    run(f"B first {n} data lines of the real training file, real split file, real test file", head_rows(REAL / "cs-training.csv", n), TEST)

print("\n#### C. header-only test file")
run("C1 real training file, real split file, test file = header line + line end", TRAIN, TEST_HEAD, show=("kaggle_submission.csv", "test_predictions.csv"))
run("C2 same, header line with no line end", TRAIN, TEST_HEAD.rstrip("\r\n"), show=("kaggle_submission.csv", "test_predictions.csv"))
run("C3 same, header line with CRLF", TRAIN, TEST_HEAD.rstrip("\r\n") + "\r\n", show=("kaggle_submission.csv", "test_predictions.csv"))
print("\n#### D. both: validation set empty and header-only test file")
run("D real training file, every id in the split file, header-only test file", TRAIN, TEST_HEAD, all_ids(TRAIN), show=("kaggle_submission.csv", "test_predictions.csv"))
print("\n#### E. the other end: training set empty (split file with no id)")
run("E real training file, split file header only, real test file", TRAIN, TEST, "row_id\n")
