"""Review by port-translator-7 of def:train_run_14_final_and_summary_precond as it stands after rule G30
(blueprint 5365851c): the precondition rendered in Python against what the port does (lines 725-819
executed verbatim, td_gen.run_slice), on the inputs of a real run with one thing changed, and on the
2,400 generated inputs of fz_td_gen (suite fz_td14).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/rv_td_pre14.py

Rendering: fz_td_gen.pre14 (ROC frames, merge clause) and the two new clauses: interest_rate is a
column and not String in both scored sets; each of the ten formatted names is a column, not String,
of sas_compat.merge_one_to_one on the four frames as the unit builds them.
"""
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz_td_gen as fz  # noqa: E402
import rv_td_gen as rv  # noqa: E402
import td_gen as td  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

TEN = ["Train_AUC", "Valid_AUC", "train_precision", "train_recall", "train_f1_score", "train_accuracy",
       "valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy"]


def pre(e: dict) -> bool:
    for f in (e["roc_train"], e["roc_valid"]):
        if f.schema.get("ROCModel") != pl.String or "Area" not in f.columns:
            return False
    if not fz.pre14(e):
        return False
    for f in (e["risk_scores_train"], e["risk_scores_validation"]):
        if "interest_rate" not in f.columns or f.schema["interest_rate"] == pl.String:
            return False
    m = sc.merge_one_to_one(
        e["roc_train"].filter(pl.col("ROCModel") == "Training Set").select(Train_AUC=pl.col("Area")),
        e["roc_valid"].filter(pl.col("ROCModel") == "Validation Set").select(Valid_AUC=pl.col("Area")),
        e["training_metrics"], e["validation_metrics"])
    return all(k in m.columns and m.schema[k] != pl.String for k in TEN)


def returns(e: dict):
    try:
        td.run_slice("s14", e)
        return True, ""
    except Exception as ex:  # noqa: BLE001
        return False, f"{type(ex).__name__}: {str(ex)[:70]}"


def main():
    base = dict(td.traced(rv.WORK / "rv_td_data" / "rb")[0]["s14", "in"])
    rst, rsv, tm, vm, rt, rvv = (base[k] for k in ("risk_scores_train", "risk_scores_validation", "training_metrics",
                                                    "validation_metrics", "roc_train", "roc_valid"))
    null = lambda n: pl.lit(None).alias(n)  # noqa: E731
    V = {
        "as run": {},
        # the nine inputs of the review (Python raises)
        "1 risk_scores_train without interest_rate": {"risk_scores_train": rst.drop("interest_rate")},
        "2 risk_scores_validation without interest_rate": {"risk_scores_validation": rsv.drop("interest_rate")},
        "3 interest_rate as text in risk_scores_train": {"risk_scores_train": rst.with_columns(interest_rate=pl.lit("5%"))},
        "4 training_metrics without train_recall": {"training_metrics": tm.drop("train_recall")},
        "5 validation_metrics with no column": {"validation_metrics": pl.DataFrame()},
        "6 train_f1_score as text": {"training_metrics": tm.with_columns(train_f1_score=pl.lit("x"))},
        "7 Area of roc_valid as text": {"roc_valid": rvv.with_columns(Area=pl.lit("0.9"))},
        "8 Area of roc_train as text, created false": {"roc_train": rt.with_columns(Area=pl.lit("0.9")), "roc_valid_created": False},
        "9 a text column Valid_AUC in training_metrics": {"training_metrics": tm.with_columns(Valid_AUC=pl.lit("x"))},
        "4b training_metrics without train_recall, created false": {"training_metrics": tm.drop("train_recall"), "roc_valid_created": False},
        "3b interest_rate as text in risk_scores_validation": {"risk_scores_validation": rsv.with_columns(interest_rate=pl.lit("5%"))},
        # inputs the port may accept
        "interest_rate Int64": {"risk_scores_train": rst.with_columns(interest_rate=pl.lit(1))},
        "interest_rate Boolean": {"risk_scores_validation": rsv.with_columns(interest_rate=pl.lit(True))},
        "interest_rate Null dtype": {"risk_scores_train": rst.with_columns(null("interest_rate"))},
        "interest_rate all null Float64, scored set with no row": {"risk_scores_train": rst.clear()},
        "model_coefficients with no column": {"model_coefficients": pl.DataFrame()},
        "train_recall Int64": {"training_metrics": tm.with_columns(train_recall=pl.lit(1))},
        "train_recall Boolean": {"training_metrics": tm.with_columns(train_recall=pl.lit(True))},
        "train_recall Null dtype": {"training_metrics": tm.with_columns(null("train_recall"))},
        "Area of roc_valid Int64": {"roc_valid": rvv.with_columns(Area=pl.lit(1))},
        "Area of roc_valid Null dtype": {"roc_valid": rvv.with_columns(null("Area"))},
        "train_recall only in validation_metrics": {"training_metrics": tm.drop("train_recall"),
                                                    "validation_metrics": vm.with_columns(train_recall=pl.lit(0.5))},
        "valid_* columns in training_metrics, validation_metrics with no column": {
            "training_metrics": pl.concat([tm, vm], how="horizontal"), "validation_metrics": pl.DataFrame()},
        "a Float64 column Valid_AUC in training_metrics": {"training_metrics": tm.with_columns(Valid_AUC=pl.lit(0.5))},
        "an Int64 column Train_AUC in validation_metrics": {"validation_metrics": vm.with_columns(Train_AUC=pl.lit(1))},
        "metrics with no row": {"training_metrics": tm.clear(), "validation_metrics": vm.clear()},
        "roc frames with no row": {"roc_train": rt.clear(), "roc_valid": rvv.clear()},
        "roc_valid labelled otherwise": {"roc_valid": rvv.with_columns(ROCModel=pl.lit("x"))},
        "a text column `note` in both metrics frames": {"training_metrics": tm.with_columns(note=pl.lit("a")),
                                                         "validation_metrics": vm.with_columns(note=pl.lit("b"))},
        "interest_rate text in risk_scores_train with no row": {"risk_scores_train": rst.clear().with_columns(interest_rate=pl.lit("x"))},
    }
    bad = 0
    for name, ch in V.items():
        e = dict(base)
        e.update(ch)
        p = pre(e)
        r, msg = returns(e)
        verdict = "ok" if p == r else ("ADMITS, PYTHON RAISES" if p else "excluded, Python returns (narrowing)")
        bad += p != r
        print(f"{verdict:38s} pre={p!s:5s} returns={r!s:5s} {name}  {msg}")
    n = adm = both = 0
    for s in range(fz.S14, fz.S14 + fz.NBLOCK * fz.BLOCK):
        e = fz.env14(s)
        p, (r, _) = pre(e), returns(e)
        n += 1
        adm += p
        both += (p and not r)
        assert r, s
    print(f"fz_td14 inputs: {n}; admitted by the precondition as it stands {adm}; admitted by the earlier rendering "
          f"{sum(fz.pre14(fz.env14(s)) for s in range(fz.S14, fz.S14 + fz.NBLOCK * fz.BLOCK))}; admitted and raising {both}")


if __name__ == "__main__":
    main()
