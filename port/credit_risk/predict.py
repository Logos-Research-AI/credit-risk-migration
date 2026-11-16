"""Port of predict.sas: score the Kaggle test set with the model trained by train.sas."""

import argparse
import json
import re
import tempfile
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
    income_medians: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)  # R§4 S12

    # predict.sas:22-32 Q27 (b40a55d): remove the results of an earlier run first
    for fname in ("kaggle_submission.csv", "test_predictions.csv"):
        (output_dir / fname).unlink(missing_ok=True)

    # predict.sas:34-42 Q27 (b40a55d): stop when the step before did not produce its result
    if not income_medians.exists() or not (input_dir / "model_coefficients.csv").exists():
        print(
            "ERROR: The training medians or the model are not in the output folder: "
            "the training steps did not complete."
        )
        print("ERROR: Test set scoring stopped. Nothing is exported.")
        raise ValueError("Test set scoring stopped. Nothing is exported.")

    # predict.sas:48-71 Q27 (G44): how many lines the test file has (counted up to two); the first
    # line with one made-up applicant under it: NA under the three names that may hold NA, 1 under
    # every other, the same line end
    test_lines = 0
    header_copy_text = b""
    try:
        with (data_dir / "cs-test.csv").open("rb") as fh:
            for _n_ in (1, 2):
                infile = fh.readline()
                if infile == b"":
                    break
                infile = infile.removesuffix(b"\n")
                if _n_ == 1:
                    made_up = b",".join(
                        b"NA"
                        if re.sub(rb"[^0-9A-Za-z_]", b"", name).upper()
                        in (b"SERIOUSDLQIN2YRS", b"MONTHLYINCOME", b"NUMBEROFDEPENDENTS")
                        else b"1"
                        for name in infile.split(b",")
                    )
                    line_end = b"\r\n" if infile.endswith(b"\r") else b"\n"
                    header_copy_text = infile + b"\n" + made_up + line_end
                test_lines = _n_
    except OSError:
        pass

    # predict.sas:73-112 PROC IMPORT, guessingrows=max
    # INV work.test_raw; R§2 PROC IMPORT (None = all rows, A31)
    # Q27 (G44): a file with its header line and no applicant is read from the copy, and the
    # made-up applicant is removed, which leaves an empty table. A failed import leaves no table.
    test_raw: pl.DataFrame | None
    try:
        if test_lines == 1:
            with tempfile.TemporaryDirectory() as work:
                header_copy = Path(work) / "cs-test-header.csv"
                header_copy.write_bytes(header_copy_text)
                test_raw = sas_compat.proc_import_csv(header_copy, guessingrows=None).clear()
        else:
            test_raw = sas_compat.proc_import_csv(data_dir / "cs-test.csv", guessingrows=None)
    except (OSError, ValueError, pl.exceptions.PolarsError):
        test_raw = None

    # predict.sas:114-187 Q27: check the input conditions, stop with an error before anything is exported
    EXPECTED = (
        "VAR1",
        "SeriousDlqin2yrs",
        "age",
        "MonthlyIncome",
        "NumberOfDependents",
        "RevolvingUtilizationOfUnsecuredL",
        "DebtRatio",
        "NumberOfTime30-59DaysPastDueNotW",
        "NumberOfTime60-89DaysPastDueNotW",
        "NumberOfTimes90DaysLate",
        "NumberOfOpenCreditLinesAndLoans",
        "NumberRealEstateLoansOrLines",
    )
    columns_ok = 0
    bad_rows = 1
    duplicate_ids = 1
    age_name = "age"
    if test_raw is not None:
        # predict.sas:132-143 the expected columns and no others (SAS names: any case)
        # SAS names are case-blind, so a table cannot hold two names that differ only in case:
        # PROC IMPORT names the later one VARn, n its place (ev10 header_variants 10: VAR12)
        test_raw_names = test_raw.columns
        upper_names = [name.upper() for name in test_raw_names]
        sas_names = [
            f"VAR{i + 1}" if name.upper() in upper_names[:i] else name
            for i, name in enumerate(test_raw.columns)
        ]
        columns_ok = int(
            len(sas_names) == 12
            and sum(name.upper() in [c.upper() for c in EXPECTED] for name in sas_names) == 12
        )
        # SAS names are case-blind: the columns take the spelling the steps below use (the first
        # column of each name; a column of no expected name is not read below); a column
        # the check names and the table lacks is a numeric column of missing values
        by_upper = {c.upper(): c for c in EXPECTED}
        raw = test_raw.select(
            [
                pl.col(name).alias(by_upper[name.upper()])
                for i, name in enumerate(test_raw.columns)
                if name.upper() in by_upper and name.upper() not in upper_names[:i]
            ]
        )
        raw = raw.with_columns(
            [pl.lit(None, dtype=pl.Float64).alias(c) for c in EXPECTED if c not in raw.columns]
        )
        if columns_ok == 1:
            test_raw = raw
            # the test file's spelling of age, which the export below writes (predict.sas:246 a.age
            # keeps the imported name: ev11_round5_before 14 writes AGE)
            age_name = test_raw_names[upper_names.index("AGE")]

        # predict.sas:117-126 %num: a numeric column as it is; a character column read as a number,
        # missing when the text is no number or is longer than 32 characters
        def num(v: str) -> pl.Expr:
            if raw.schema[v] != pl.String:
                return pl.col(v)
            text = pl.col(v).str.strip_chars(" ")
            return pl.when(text.str.len_chars() <= 32).then(sas_compat.input_best32(text))

        # upcase(cats(v)) not in ('', '.', 'NA'): the cell states a value
        def stated(v: str) -> pl.Expr:
            if raw.schema[v] != pl.String:
                return pl.col(v).is_not_null()
            return ~pl.col(v).fill_null("").str.strip_chars(" ").str.to_uppercase().is_in(["", ".", "NA"])

        # x >= 0 and x = int(x): a whole number, zero or more (a missing x is not)
        def count_ok(x: pl.Expr) -> pl.Expr:
            return sas_compat.ge(x, 0) & sas_compat.eq(x, pl.when(x >= 0).then(x.floor()).otherwise(x.ceil()))

        # predict.sas:148-171 DATA input_check
        input_check = raw.select(
            pl.col("VAR1"),
            bad_row=sas_compat.flag(
                num("VAR1").is_null()
                | (stated("SeriousDlqin2yrs") & ~num("SeriousDlqin2yrs").is_in([0.0, 1.0]).fill_null(False))
                | num("age").is_null()
                | num("RevolvingUtilizationOfUnsecuredL").is_null()
                | num("DebtRatio").is_null()
                | num("NumberRealEstateLoansOrLines").is_null()
                | ~count_ok(num("NumberOfTime30-59DaysPastDueNotW"))
                | ~count_ok(num("NumberOfTime60-89DaysPastDueNotW"))
                | ~count_ok(num("NumberOfTimes90DaysLate"))
                | ~count_ok(num("NumberOfOpenCreditLinesAndLoans"))
                | (stated("MonthlyIncome") & num("MonthlyIncome").is_null())
                | (num("MonthlyIncome").is_not_null() & sas_compat.lt(num("MonthlyIncome"), 0))
                | (stated("NumberOfDependents") & ~count_ok(num("NumberOfDependents")))
            ),
        )
        # predict.sas:173-178 bad rows, repeated row ids (count(distinct) leaves a missing id out)
        bad_rows = int(input_check.get_column("bad_row").sum())
        duplicate_ids = input_check.height - input_check.get_column("VAR1").drop_nulls().n_unique()

    # predict.sas:180-187
    if test_raw is None or columns_ok != 1 or bad_rows != 0 or duplicate_ids != 0:
        print(
            "ERROR: cs-test.csv does not meet the input conditions: "
            f"columns_ok={columns_ok} bad_rows={bad_rows} duplicate_ids={duplicate_ids}."
        )
        print("ERROR: Test set scoring stopped. Nothing is exported.")
        raise ValueError("Test set scoring stopped. Nothing is exported.")

    # predict.sas:36-38
    # listing-only: PROC CONTENTS of test_raw

    # predict.sas:45-56 DATA test_raw_clean
    # INV work.test_raw_clean; R§2 input(s, best32.) (S2); keep/drop/rename
    # input(v, best32.) reads text: a column imported as numeric (no row holds NA or other text) is
    # first written as BEST12. text, so a number that needs more than 12 characters is changed
    # (experiment x09_input_numeric: 1234567890123 is read back as 1234567900000)
    def input_best32(v: str) -> pl.Expr:
        if test_raw.schema[v] != pl.String:
            return sas_compat.input_best32(
                pl.col(v).map_elements(sas_compat.sas_best12, return_dtype=pl.String)
            )
        return sas_compat.input_best32(pl.col(v))

    test_raw_clean = (
        test_raw.with_columns(
            MonthlyIncome_num=input_best32("MonthlyIncome"),
            NumberOfDependents_num=input_best32("NumberOfDependents"),
        )
        .drop("MonthlyIncome", "NumberOfDependents")
        .rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"})
    )

    # predict.sas:212-218 PROC IMPORT income_medians.csv (default guessingrows)
    # Q13 (2d4fdef): the training income medians by age group, exported by feature_engineering
    # INV work.train_income_medians; R§2 PROC IMPORT
    train_income_medians = sas_compat.proc_import_csv(income_medians)
    # SAS names are case-blind: the three columns the join reads take the spelling it uses
    medians_upper = [name.upper() for name in train_income_medians.columns]
    train_income_medians = train_income_medians.rename(
        {
            name: name.lower()
            for i, name in enumerate(train_income_medians.columns)
            if name.upper() in ("AGE_GROUP", "MEDIAN_INCOME", "OVERALL_MEDIAN_INCOME")
            and name.upper() not in medians_upper[:i]
            and (name.lower() == name or name.lower() not in train_income_medians.columns)
        }
    )

    # predict.sas:75-94 DATA test_cleaned
    # INV age_group; INV MonthlyIncome_missing
    # INV NumberOfDependents / Dependents_missing
    # R§2 `data out; set in;` -- Dependents_missing and the imputation both read the pre-imputation column
    test_cleaned = test_raw_clean.with_columns(
        age_group=pl.when(sas_compat.lt(pl.col("age"), 30))
        .then(1)
        .when(sas_compat.lt(pl.col("age"), 40))
        .then(2)
        .when(sas_compat.lt(pl.col("age"), 50))
        .then(3)
        .when(sas_compat.lt(pl.col("age"), 60))
        .then(4)
        .otherwise(5),
        MonthlyIncome_missing=sas_compat.flag(pl.col("MonthlyIncome").is_null()),
        Dependents_missing=sas_compat.flag(pl.col("NumberOfDependents").is_null()),
        NumberOfDependents=pl.col("NumberOfDependents").fill_null(0.0),
    )

    # predict.sas:241-264 PROC SQL test_imputed
    # INV work.test_imputed; R§2 PROC SQL left join (A11 not needed: keys never missing)
    # Q13 (2d4fdef): imputes from the training medians. Q14 (12a28e4), Q1 (167dc38): an age group
    # with no median falls back to the overall training median (coalesce).
    test_imputed = test_cleaned.join(
        train_income_medians,
        left_on=pl.col("age_group").cast(pl.Float64),
        right_on="age_group",
        how="left",
        maintain_order="left",
    ).select(
        pl.col("VAR1").alias("row_id"),
        pl.col("age"),
        pl.when(pl.col("MonthlyIncome_missing") == 1)
        .then(pl.coalesce(pl.col("median_income"), pl.col("overall_median_income")))
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
        # predict.sas:138-141 INV credit_util_category; SAS comparisons in the three chains (finding P5)
        credit_util_category=pl.when(sas_compat.lt(pl.col("credit_utilization"), 30))
        .then(1)
        .when(sas_compat.lt(pl.col("credit_utilization"), 50))
        .then(2)
        .when(sas_compat.lt(pl.col("credit_utilization"), 75))
        .then(3)
        .otherwise(4),
        # predict.sas:144-147 INV debt_category
        debt_category=pl.when(sas_compat.lt(pl.col("debt_ratio"), 30))
        .then(1)
        .when(sas_compat.lt(pl.col("debt_ratio"), 43))
        .then(2)
        .when(sas_compat.lt(pl.col("debt_ratio"), 60))
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
        age_category=pl.when(sas_compat.lt(pl.col("age"), 25))
        .then(1)
        .when(sas_compat.lt(pl.col("age"), 35))
        .then(2)
        .when(sas_compat.lt(pl.col("age"), 50))
        .then(3)
        .when(sas_compat.lt(pl.col("age"), 65))
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
        flag_few_credit_lines=sas_compat.flag(sas_compat.le(pl.col("num_credit_lines"), 2)),
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
        # Q7 (7b55ef1): the total counts the eight risk flags
        total_risk_flags=sas_compat.sas_sum(
            pl.col("flag_high_utilization"),
            pl.col("flag_very_high_utilization"),
            pl.col("flag_high_debt_ratio"),
            pl.col("flag_serious_delinquency"),
            pl.col("flag_multiple_delinquencies"),
            pl.col("flag_low_income"),
            pl.col("flag_many_dependents"),
            pl.col("flag_few_credit_lines"),
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
        # Q9 (10f447e): age * log(income) when income is above 0, else age * log(income + 1)
        age_income_interaction=pl.when(pl.col("monthly_income") > 0)
        .then(pl.col("age") * sas_compat.sas_log(pl.col("monthly_income")))
        .otherwise(pl.col("age") * pl.col("log_monthly_income")),
        # Q9 (10f447e): utilization * debt ratio, no division by 100
        utilization_debt_interaction=pl.col("credit_utilization") * pl.col("debt_ratio"),
        credit_utilization_capped=sas_compat.sas_min(pl.col("credit_utilization"), pl.lit(200.0)),
        debt_ratio_capped=sas_compat.sas_min(pl.col("debt_ratio"), pl.lit(500.0)),
    )

    # predict.sas:208-212 PROC PLM restore ... score predicted=predicted_logit
    # INV work.test_scored (pd_logistic); R§2 store/restore: model.json from input_dir (R§4, A27)
    model = json.loads((input_dir / "model.json").read_text())
    intercept = float(model["intercept"])
    coefficients: dict[str, float] = {str(k): float(v) for k, v in model["coefficients"].items()}
    # RESOLVED (post-parity): ValueError matches PROC PLM's ERROR; model.json keys are full names.
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
        # Q15 (b7b1cd4): the score is not rounded
        credit_risk_score=pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
    )
    test_predictions = test_predictions.with_columns(
        # Q18 (e1df983): the grade is cut on the probability; a missing probability is graded F
        risk_grade=pl.when(pl.col("pd_logistic").is_null())
        .then(pl.lit("F"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.10))
        .then(pl.lit("A"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.15))
        .then(pl.lit("B"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.25))
        .then(pl.lit("C"))
        .when(sas_compat.lt(pl.col("pd_logistic"), 0.35))
        .then(pl.lit("D"))
        .when(sas_compat.le(pl.col("pd_logistic"), 0.50))
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
    test_predictions_full = test_predictions.select(
        [c for c in test_predictions.columns if c in KEEP_FULL]
    ).rename({"age": age_name})  # SAS names are case-blind and keep the spelling of the test file

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
        "--income-medians",
        type=Path,
        required=True,
        help="income_medians.csv written by feature_engineering",
    )
    args = parser.parse_args()
    run(
        args.input_dir,
        args.output_dir,
        data_dir=args.data_dir,
        income_medians=args.income_medians,
    )

# PORT STATUS: confidence=high todos=0
