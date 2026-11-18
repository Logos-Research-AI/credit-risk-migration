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
- metrics: PROC IMPORT cannot read the header-only risk_scores_validation.csv and WORK.LOGIT_SCORED_VALID does
  not exist; SAS writes validation_summary.csv, model_performance_metrics.csv, threshold_analysis.csv and
  printed_cumulative_lift.csv as a header only and printed_psi_calculation.csv in full, and no
  decile_analysis.csv, ks_statistic.csv, calibration_plot.csv or printed_roc_metrics.csv;
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
from credit_risk import metrics_calculation, predict, sas_compat, train  # noqa: E402

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


METRICS_FILES = (
    "validation_summary.csv",
    "decile_analysis.csv",
    "threshold_analysis.csv",
    "ks_statistic.csv",
    "calibration_plot.csv",
    "model_performance_metrics.csv",
    "printed_roc_metrics.csv",
    "printed_cumulative_lift.csv",
    "printed_psi_calculation.csv",
)
SAS_METRICS_FILES = {
    "validation_summary.csv",
    "model_performance_metrics.csv",
    "threshold_analysis.csv",
    "printed_cumulative_lift.csv",
    "printed_psi_calculation.csv",
}


def test_metrics_writes_what_sas_writes() -> None:
    # on SAS's score files (the metrics line of the contract) and on the port's own (the end-to-end line)
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "train"
            _train(case, scores)
            for source in (DATA / case, scores):
                out = Path(tmp) / "metrics"
                metrics_calculation.run(source, out)
                written = {f for f in METRICS_FILES if (out / f).exists()}
                assert written == SAS_METRICS_FILES, (case, source, written ^ SAS_METRICS_FILES)
                for f in sorted(SAS_METRICS_FILES):
                    assert (out / f).read_bytes() == (DATA / case / f).read_bytes(), (case, source, f)


def test_threshold_metrics_have_no_row_without_a_row_read() -> None:
    # retain + end=eof: a table read with no row gives no row
    empty = pl.DataFrame(schema={"default_flag": pl.Float64, "pd_logistic": pl.Float64})
    _, conf_matrix, metrics = metrics_calculation.confusion_metrics(0.5, "05", empty)
    assert conf_matrix.height == 0 and metrics.height == 0
    assert metrics.columns == ["threshold", "accuracy", "precision", "recall", "f1_score", "specificity"]


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
