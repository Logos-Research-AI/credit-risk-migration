"""Port of predict.sas: score the Kaggle test set with the model trained by train.sas."""

import argparse
import json
from pathlib import Path

import polars as pl

from credit_risk import sas_compat

# predict.sas:19-20 %let data_path / output_path -> run() parameters (R§4, A27)
# INV &data_path / &output_path


def run(
    input_dir: Path,
    output_dir: Path,
    *,
    data_dir: Path,
    fix_train_medians: bool = False,
    medians: Path | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)  # R§4 S12

    # predict.sas:27-33 PROC IMPORT, guessingrows=max
    # INV work.test_raw; R§2 PROC IMPORT (None = all rows, A31)
    test_raw = sas_compat.proc_import_csv(data_dir / "cs-test.csv", guessingrows=None)

    # predict.sas:36-38
    # listing-only: PROC CONTENTS of test_raw

    # predict.sas:45-56 DATA test_raw_clean
    # INV work.test_raw_clean; R§2 input(s, best32.) (S2); keep/drop/rename
    test_raw_clean = (
        test_raw.with_columns(
            MonthlyIncome_num=sas_compat.input_best32(pl.col("MonthlyIncome")),
            NumberOfDependents_num=sas_compat.input_best32(pl.col("NumberOfDependents")),
        )
        .drop("MonthlyIncome", "NumberOfDependents")
        .rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"})
    )

    # predict.sas:59-73 PROC SQL test_income_medians
    # BUG(port): medians come from the TEST set, not training. Repro: cs-test.csv gives
    # {1: 2516, 2: 4667, 3: 6000, 4: 6260.5, 5: 5395}; edge_predict age group 1 has no median.
    # INV work.test_income_medians; age never missing so plain comparisons (MISSING_NEVER)
    # The WHERE runs before the group by, so an all-missing age group gets no row (INV test_income_medians).
    test_income_medians = (
        test_raw_clean.filter(pl.col("MonthlyIncome").is_not_null())
        .with_columns(
            age_group=pl.when(pl.col("age") < 30)
            .then(1)
            .when(pl.col("age") < 40)
            .then(2)
            .when(pl.col("age") < 50)
            .then(3)
            .when(pl.col("age") < 60)
            .then(4)
            .otherwise(5)
        )
        .group_by("age_group", maintain_order=True)
        .agg(median_income=pl.col("MonthlyIncome").median())
    )

    # FIXED(post-parity, flag --fix-train-medians): impute from the TRAINING medians (income_medians.csv)
    if fix_train_medians:
        if medians is None:
            raise ValueError("--fix-train-medians requires --medians <income_medians.csv>")
        test_income_medians = pl.read_csv(
            medians, schema_overrides={"age_group": pl.Int32, "median_income": pl.Float64}
        )
        if set(test_income_medians.get_column("age_group").to_list()) != {1, 2, 3, 4, 5}:
            raise ValueError(f"{medians}: age_group must cover exactly 1-5")

    # predict.sas:75-94 DATA test_cleaned
    # INV age_group; INV MonthlyIncome_missing
    # INV NumberOfDependents / Dependents_missing
    # R§2 `data out; set in;` -- Dependents_missing and the imputation both read the pre-imputation column
    test_cleaned = test_raw_clean.with_columns(
        age_group=pl.when(pl.col("age") < 30)
        .then(1)
        .when(pl.col("age") < 40)
        .then(2)
        .when(pl.col("age") < 50)
        .then(3)
        .when(pl.col("age") < 60)
        .then(4)
        .otherwise(5),
        MonthlyIncome_missing=sas_compat.flag(pl.col("MonthlyIncome").is_null()),
        Dependents_missing=sas_compat.flag(pl.col("NumberOfDependents").is_null()),
        NumberOfDependents=pl.col("NumberOfDependents").fill_null(0.0),
    )

    # predict.sas:97-119 PROC SQL test_imputed
    # INV work.test_imputed; R§2 PROC SQL left join (A11 not needed: keys never missing)
    # BUG(port): imputes from TEST-set medians. Repro: edge_predict under-30 rows get null monthly_income.
    # (FIXED(post-parity, flag --fix-train-medians): test_income_medians above is the training table)
    # monthly_income stays null where the age group has no median row (INV monthly_income (test_imputed)).
    test_imputed = test_cleaned.join(
        test_income_medians, on="age_group", how="left", maintain_order="left"
    ).select(
        pl.col("VAR1").alias("row_id"),
        pl.col("age"),
        pl.when(pl.col("MonthlyIncome_missing") == 1)
        .then(pl.col("median_income"))
        .otherwise(pl.col("MonthlyIncome"))
        .alias("monthly_income"),
        pl.col("MonthlyIncome_missing"),
        pl.col("NumberOfDependents").alias("num_dependents"),
        pl.col("Dependents_missing"),
        pl.col("age_group"),
        pl.col("NumberOfTime30-59DaysPastDueNotW").alias("num_late_30_59"),
        pl.col("NumberOfTime60-89DaysPastDueNotW").alias("num_late_60_89"),
        pl.col("NumberOfTimes90DaysLate").alias("num_late_90_plus"),
        (pl.col("RevolvingUtilizationOfUnsecuredL") * 100).alias("credit_utilization"),
        (pl.col("DebtRatio") * 100).alias("debt_ratio"),
        pl.col("NumberOfOpenCreditLinesAndLoans").alias("num_credit_lines"),
        pl.col("NumberRealEstateLoansOrLines").alias("num_real_estate_loans"),
    )

    # predict.sas:125-201 DATA test_features
    # (duplicated feature engineering stays duplicated, R§0). Split into successive with_columns
    # wherever a statement reads a variable assigned earlier in the step (R§2 data step).
    # predict.sas:129
    test_features = test_imputed.with_columns(
        total_late_payments=sas_compat.sas_sum(  # INV total_late_payments
            pl.col("num_late_30_59"), pl.col("num_late_60_89"), pl.col("num_late_90_plus")
        ),
    )
    test_features = test_features.with_columns(
        # predict.sas:132-135 INV has_delinquency / has_serious_delinquency (plain: MISSING_NEVER)
        has_delinquency=sas_compat.flag(pl.col("total_late_payments") > 0),
        has_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
        # predict.sas:138-141 INV credit_util_category
        credit_util_category=pl.when(pl.col("credit_utilization") < 30)
        .then(1)
        .when(pl.col("credit_utilization") < 50)
        .then(2)
        .when(pl.col("credit_utilization") < 75)
        .then(3)
        .otherwise(4),
        # predict.sas:144-147 INV debt_category
        debt_category=pl.when(pl.col("debt_ratio") < 30)
        .then(1)
        .when(pl.col("debt_ratio") < 43)
        .then(2)
        .when(pl.col("debt_ratio") < 60)
        .then(3)
        .otherwise(4),
        # predict.sas:150-151 INV log_monthly_income / age_income_interaction / income_per_dependent
        # num_dependents never missing, so plain comparison; null monthly_income propagates
        income_per_dependent=pl.when(pl.col("num_dependents") > 0)
        .then(pl.col("monthly_income") / (pl.col("num_dependents") + 1))
        .otherwise(pl.col("monthly_income")),
        # predict.sas:154 INV credit_lines_per_person (divisor >= 1, plain `/`)
        credit_lines_per_person=pl.col("num_credit_lines") / (pl.col("num_dependents") + 1),
        # predict.sas:157-161 INV age_category
        age_category=pl.when(pl.col("age") < 25)
        .then(1)
        .when(pl.col("age") < 35)
        .then(2)
        .when(pl.col("age") < 50)
        .then(3)
        .when(pl.col("age") < 65)
        .then(4)
        .otherwise(5),
        # predict.sas:164-173 risk flags; INV flag_* (plain comparisons, MISSING_NEVER)
        flag_high_utilization=sas_compat.flag(pl.col("credit_utilization") > 75),
        flag_very_high_utilization=sas_compat.flag(pl.col("credit_utilization") > 100),
        flag_high_debt_ratio=sas_compat.flag(pl.col("debt_ratio") > 43),
        flag_very_high_debt_ratio=sas_compat.flag(pl.col("debt_ratio") > 60),
        flag_recent_late_payments=sas_compat.flag(pl.col("num_late_30_59") > 0),
        flag_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
        flag_multiple_delinquencies=sas_compat.flag(pl.col("total_late_payments") >= 3),
        # INV flag_low_income: MISSING_NULLABLE, missing < 2500 is true (R§2 comparison, A1/A2)
        flag_low_income=sas_compat.flag(sas_compat.lt(pl.col("monthly_income"), 2500)),
        flag_many_dependents=sas_compat.flag(pl.col("num_dependents") >= 3),
        flag_few_credit_lines=sas_compat.flag(pl.col("num_credit_lines") <= 2),
    )
    # predict.sas:176-187 INV total_risk_flags, INV financial_health (A30: one nested expression)
    financial_health = pl.lit(100.0)
    for cond, k in (
        (pl.col("credit_utilization") > 30, 15.0),
        (pl.col("credit_utilization") > 75, 15.0),
        (pl.col("debt_ratio") > 43, 20.0),
        (pl.col("has_delinquency") != 0, 20.0),  # R§2 numeric truthiness (A29)
        (pl.col("num_late_90_plus") > 0, 30.0),
    ):
        financial_health = pl.when(cond).then(financial_health - k).otherwise(financial_health)
    test_features = test_features.with_columns(
        total_risk_flags=sas_compat.sas_sum(
            pl.col("flag_high_utilization"),
            pl.col("flag_high_debt_ratio"),
            pl.col("flag_serious_delinquency"),
            pl.col("flag_multiple_delinquencies"),
            pl.col("flag_low_income"),
        ),
        financial_health=sas_compat.sas_max(pl.lit(0.0), financial_health),
    )
    test_features = test_features.with_columns(
        # predict.sas:190-192 INV log_* (R§2 log)
        log_monthly_income=sas_compat.sas_log(pl.col("monthly_income") + 1),
        log_num_credit_lines=sas_compat.sas_log(pl.col("num_credit_lines") + 1),
        log_total_late_payments=sas_compat.sas_log(pl.col("total_late_payments") + 1),
    )
    test_features = test_features.with_columns(
        # predict.sas:195-200
        age_income_interaction=pl.col("age") * pl.col("log_monthly_income"),
        # INV utilization_debt_interaction: product first, then div by the literal (A13)
        utilization_debt_interaction=sas_compat.div(pl.col("credit_utilization") * pl.col("debt_ratio"), 100),
        credit_utilization_capped=sas_compat.sas_min(pl.col("credit_utilization"), pl.lit(200.0)),
        debt_ratio_capped=sas_compat.sas_min(pl.col("debt_ratio"), pl.lit(500.0)),
    )

    # predict.sas:208-212 PROC PLM restore ... score predicted=predicted_logit
    # INV work.test_scored (pd_logistic); R§2 store/restore: model.json from input_dir (R§4, A27)
    model = json.loads((input_dir / "model.json").read_text())
    intercept = float(model["intercept"])
    coefficients: dict[str, float] = {str(k): float(v) for k, v in model["coefficients"].items()}
    # TODO(port): rulebook silent on a model variable absent at scoring (SAS PLM errors) —
    # keys are full names per RULEBOOK §2 PLM
    absent = [k for k in coefficients if k not in test_features.columns]
    if absent:
        raise ValueError(f"model.json coefficient variables absent from the scoring frame: {absent}")
    predicted_logit = pl.lit(intercept)
    # eta sums in model.json key order, which is MODEL order (intercept first)
    for name, beta in coefficients.items():
        predicted_logit = predicted_logit + pl.col(name) * beta  # null if any x_i null
    test_scored_temp = test_features.with_columns(predicted_logit=predicted_logit)

    # predict.sas:215-222 DATA test_scored
    # R§2 exp(x): sas_exp, overflow -> missing (S1); divisor is a column and is >= 1, plain `/`
    test_scored = test_scored_temp.with_columns(
        # R§2 arithmetic: literal / column is column-wise (A13 note)
        pd_logistic=1 / (1 + sas_compat.sas_exp(-pl.col("predicted_logit")))
    ).drop("predicted_logit")

    # predict.sas:228-262 DATA test_predictions
    # INV credit_risk_score / risk_grade / recommendation / interest_rate / pred_logistic (MISSING_NULLABLE)
    test_predictions = test_scored.with_columns(
        pred_logistic=sas_compat.flag(sas_compat.ge(pl.col("pd_logistic"), 0.5)),
        base_score=pl.lit(600.0),
        score_range=pl.lit(250.0),
    )
    test_predictions = test_predictions.with_columns(
        # R§2 round(x): sas_round, null stays null
        credit_risk_score=sas_compat.sas_round(
            pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
        )
    )
    test_predictions = test_predictions.with_columns(
        # R§2 if/else chain; sas_compat.ge is false for missing so a missing score gets 'F'
        risk_grade=pl.when(sas_compat.ge(pl.col("credit_risk_score"), 750))
        .then(pl.lit("A"))
        .when(sas_compat.ge(pl.col("credit_risk_score"), 700))
        .then(pl.lit("B"))
        .when(sas_compat.ge(pl.col("credit_risk_score"), 650))
        .then(pl.lit("C"))
        .when(sas_compat.ge(pl.col("credit_risk_score"), 600))
        .then(pl.lit("D"))
        .when(sas_compat.ge(pl.col("credit_risk_score"), 550))
        .then(pl.lit("E"))
        .otherwise(pl.lit("F"))
    )
    test_predictions = test_predictions.with_columns(
        recommendation=pl.when(pl.col("risk_grade").is_in(["A", "B"]))
        .then(pl.lit("Approve"))
        .when(pl.col("risk_grade") == "C")
        .then(pl.lit("Review"))
        .otherwise(pl.lit("Decline")),
        base_rate=pl.lit(0.05),
    )
    test_predictions = test_predictions.with_columns(
        interest_rate=pl.when(pl.col("risk_grade") == "A")
        .then(pl.col("base_rate"))
        .when(pl.col("risk_grade") == "B")
        .then(pl.col("base_rate") + 0.02)
        .when(pl.col("risk_grade") == "C")
        .then(pl.col("base_rate") + 0.04)
        .when(pl.col("risk_grade") == "D")
        .then(pl.col("base_rate") + 0.07)
        .when(pl.col("risk_grade") == "E")
        .then(pl.col("base_rate") + 0.10)
        .otherwise(pl.col("base_rate") + 0.15)
    )  # format interest_rate percent8.2 -> applied at export below (R§2 format attach)

    # predict.sas:269-272 DATA kaggle_submission; R§2 keep keeps input column order (A12)
    KEEP_KAGGLE = {"row_id", "pd_logistic"}
    kaggle_submission = test_predictions.select([c for c in test_predictions.columns if c in KEEP_KAGGLE])

    # predict.sas:275-281 DATA test_predictions_full
    KEEP_FULL = {
        "row_id",
        "pd_logistic",
        "pred_logistic",
        "credit_risk_score",
        "risk_grade",
        "recommendation",
        "interest_rate",
        "age",
        "monthly_income",
        "credit_utilization",
        "debt_ratio",
        "total_late_payments",
        "num_credit_lines",
        "financial_health",
        "total_risk_flags",
    }
    test_predictions_full = test_predictions.select([c for c in test_predictions.columns if c in KEEP_FULL])

    # predict.sas:288-292 PROC EXPORT kaggle_submission
    # R§2 PROC EXPORT; INV kaggle_submission.csv
    sas_compat.write_sas_csv(kaggle_submission, output_dir / "kaggle_submission.csv", formats={})
    # predict.sas:295-299 PROC EXPORT test_predictions_full
    # R§2 PROC EXPORT; INV test_predictions.csv
    sas_compat.write_sas_csv(
        test_predictions_full, output_dir / "test_predictions.csv", formats={"interest_rate": "percent8.2"}
    )

    # predict.sas:302-305
    # listing-only: PROC FREQ risk_grade recommendation
    # predict.sas:307-310
    # listing-only: PROC MEANS pd_logistic credit_risk_score
    # predict.sas:313-316
    # listing-only: PROC PRINT first 20 rows of test_predictions_full

    # predict.sas:318-321 %put (INV &data_path / &output_path)
    print("NOTE: Test set scoring completed successfully")
    print(f"NOTE: Kaggle submission file: {output_dir / 'kaggle_submission.csv'}")
    print(f"NOTE: Full predictions: {output_dir / 'test_predictions.csv'}")
    print("NOTE: Total records scored: 101,503")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score the test set (predict.sas)")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--fix-train-medians",
        action="store_true",
        help="post-parity fix: impute MonthlyIncome from the training medians",
    )
    parser.add_argument("--medians", type=Path, help="income_medians.csv from feature_engineering")
    args = parser.parse_args()
    if args.fix_train_medians and args.medians is None:
        parser.error("--fix-train-medians requires --medians")
    if args.medians is not None and not args.fix_train_medians:
        parser.error("--medians requires --fix-train-medians")
    run(
        args.input_dir,
        args.output_dir,
        data_dir=args.data_dir,
        fix_train_medians=args.fix_train_medians,
        medians=args.medians,
    )

# PORT STATUS: confidence=high todos=1
