"""A training part of one outcome: SAS fits nothing and runs on (RULEBOOK R46 of migration/legacy-to-lean;
experiment migration/legacy-to-lean/experiments/x27_one_class_roc, cases C60 and E60; owner's decision (2) of
2026-11-18).

C60: the first 60 rows of legacy/data/cs-training.csv, defaulters only among the 18 rows SAS's split puts in
the validation part; E60: the same rows, no defaulter. The files under data/x27_one_class/<case> are SAS's,
from judge/runs/x27_<case>_full (all four scripts in one session, run_sas.py) and x27_<case>_metrics
(metrics_calculation.sas alone on those score files: the same five files, byte for byte):

- train: PROC LOGISTIC stops ("All observations have the same response"), every pd_logistic is missing,
  neither ROC table is created; SAS writes risk_scores_train.csv, final_model_output.csv and
  printed_confusion_train.csv in full, risk_scores_validation.csv and model_summary.csv as a header only,
  and no model_coefficients.csv and no printed table of the fit;
- predict: stops on its own check (no model_coefficients.csv) and writes nothing.

cd port && uv run python tests/test_one_class_training.py        (or: uv run pytest tests)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import predict, sas_compat, train  # noqa: E402

DATA = HERE / "data" / "x27_one_class"
CASES = ("C60", "E60")
# the train stage's files (judge/compare.py STAGES["train"]) and the port's item store
TRAIN_FILES = (
    "risk_scores_train.csv",
    "risk_scores_validation.csv",
    "final_model_output.csv",
    "model_summary.csv",
    "model_coefficients.csv",
    "stepwise_summary.csv",
    "printed_fit_statistics.csv",
    "printed_global_tests.csv",
    "printed_rsquare.csv",
    "printed_association.csv",
    "printed_odds_ratios.csv",
    "printed_hl_partition.csv",
    "printed_hosmer_lemeshow.csv",
    "printed_classification.csv",
    "printed_roc_train.csv",
    "printed_roc_validation.csv",
    "printed_confusion_train.csv",
    "printed_confusion_validation.csv",
    "model.json",
)
SAS_TRAIN_FILES = {
    "risk_scores_train.csv",
    "risk_scores_validation.csv",
    "final_model_output.csv",
    "model_summary.csv",
    "printed_confusion_train.csv",
}


def _train(case: str, out: Path) -> None:
    train.run(DATA / case, out)


def test_stepwise_fits_nothing_on_one_outcome() -> None:
    frame = pl.DataFrame({"y": [0.0, 0.0, 0.0, 0.0], "x": [1.0, 2.0, 3.0, 5.0]})
    res = sas_compat.stepwise_logistic(frame, "y", ["x"])
    assert res.final is None and res.intercept_only is None and res.steps == []


def test_train_writes_what_sas_writes() -> None:
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            _train(case, out)
            written = {f for f in TRAIN_FILES if (out / f).exists()}
            assert written == SAS_TRAIN_FILES, (case, written ^ SAS_TRAIN_FILES)
            for f in sorted(SAS_TRAIN_FILES):
                assert (out / f).read_bytes() == (DATA / case / f).read_bytes(), (case, f)


def test_train_scores_every_row_without_probability() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        _train("C60", out)
        scores = pl.read_csv(out / "risk_scores_train.csv", infer_schema=False)
        assert scores.height == 42
        assert scores.get_column("pd_logistic").is_null().all()
        assert scores.get_column("credit_risk_score").is_null().all()
        assert set(scores.get_column("pred_logistic").to_list()) == {"0"}
        assert set(scores.get_column("risk_grade").to_list()) == {"F"}
        header = (out / "model_summary.csv").read_text().splitlines()
        assert len(header) == 1 and header[0].endswith(",Train_AUC,Valid_AUC")


def test_predict_stops_after_a_training_without_model() -> None:
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            _train(case, out)
            try:
                predict.run(out, out, data_dir=DATA / case, income_medians=DATA / case / "income_medians.csv")
            except ValueError as e:
                assert "Test set scoring stopped" in str(e)
            else:
                raise AssertionError("predict did not stop")
            assert not (out / "kaggle_submission.csv").exists()
            assert not (out / "test_predictions.csv").exists()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
