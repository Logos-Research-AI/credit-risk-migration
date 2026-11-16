"""Port of feature_engineering.sas (RULEBOOK v1.3, structure-preserving).

Loads cs-training.csv, imputes and engineers features, splits train / validation using an
EXTERNAL split (R§4, INV &data_path / &output_path) and exports the two model_features CSVs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from credit_risk import sas_compat


def run(
    data_dir: Path,
    output_dir: Path,
    *,
    split_ids: Path,
) -> None:
    # R§4 (S12, A27): create the output folder first
    output_dir.mkdir(parents=True, exist_ok=True)

    # feature_engineering.sas:23-34 Q27: remove the results of an earlier run first
    for fname in ("income_medians.csv", "model_features_train.csv", "model_features_validation.csv"):
        (output_dir / fname).unlink(missing_ok=True)

    # feature_engineering.sas:41-47  PROC IMPORT, guessingrows=max  # INV work.credit_raw
    # Q1 (726048a): every row sizes the columns, so a present income is not cut
    # A failed import leaves no table.
    credit_raw: pl.DataFrame | None
    try:
        credit_raw = sas_compat.proc_import_csv(data_dir / "cs-training.csv", guessingrows=None)
    except (OSError, ValueError, pl.exceptions.PolarsError):
        credit_raw = None

    # feature_engineering.sas:49-123 Q27: check the input conditions, stop with an error before
    # anything is exported
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
    known_incomes = 0
    if credit_raw is not None:
        # :68-79 the expected columns and no others (SAS names: any case)
        columns_ok = int(
            len(credit_raw.columns) == 12
            and sum(name.upper() in [c.upper() for c in EXPECTED] for name in credit_raw.columns) == 12
        )
        # SAS names are case-blind: the columns take the spelling the steps below use; a column
        # the check names and the table lacks is a numeric column of missing values
        by_upper = {c.upper(): c for c in EXPECTED}
        raw = credit_raw.rename({name: by_upper.get(name.upper(), name) for name in credit_raw.columns})
        raw = raw.with_columns(
            [pl.lit(None, dtype=pl.Float64).alias(c) for c in EXPECTED if c not in raw.columns]
        )
        if columns_ok == 1:
            credit_raw = raw

        # :50-61 %num: a numeric column as it is; a character column read as a number, missing
        # when the text is no number or is longer than 32 characters
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

        # :84-107 DATA input_check
        input_check = raw.select(
            pl.col("VAR1"),
            bad_row=sas_compat.flag(
                num("VAR1").is_null()
                | ~num("SeriousDlqin2yrs").is_in([0.0, 1.0]).fill_null(False)
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
            known_income=sas_compat.flag(num("MonthlyIncome").is_not_null()),
        )
        # :109-114 bad rows, repeated row ids (count(distinct) leaves a missing id out), known incomes
        bad_rows = int(input_check.get_column("bad_row").sum())
        duplicate_ids = input_check.height - input_check.get_column("VAR1").drop_nulls().n_unique()
        known_incomes = int(input_check.get_column("known_income").sum())

    # :116-123
    if credit_raw is None or columns_ok != 1 or bad_rows != 0 or duplicate_ids != 0 or known_incomes < 1:
        print(
            "ERROR: cs-training.csv does not meet the input conditions: "
            f"columns_ok={columns_ok} bad_rows={bad_rows} duplicate_ids={duplicate_ids} "
            f"known_incomes={known_incomes}."
        )
        print("ERROR: Feature engineering stopped. Nothing is exported.")
        raise ValueError("Feature engineering stopped. Nothing is exported.")

    # feature_engineering.sas:36-38
    # listing-only: PROC MEANS n nmiss mean std min max of credit_raw  # INV listing-only PROCs

    # feature_engineering.sas:45-56  # INV MonthlyIncome_num, NumberOfDependents_num
    # create the _num columns, drop the text columns, rename (numeric versions end last, as in the PDV)
    # input(v, best32.) reads text: a column imported as numeric (no row holds NA or other text) is
    # first written as BEST12. text, so a number that needs more than 12 characters is changed
    # (experiment x09_input_numeric: 1234567890123 is read back as 1234567900000)
    def input_best32(v: str) -> pl.Expr:
        if credit_raw.schema[v] != pl.String:
            return sas_compat.input_best32(
                pl.col(v).map_elements(sas_compat.sas_best12, return_dtype=pl.String)
            )
        return sas_compat.input_best32(pl.col(v))

    credit_raw_clean = (
        credit_raw.with_columns(
            MonthlyIncome_num=input_best32("MonthlyIncome"),
            NumberOfDependents_num=input_best32("NumberOfDependents"),
        )
        .drop("MonthlyIncome", "NumberOfDependents")
        .rename({"MonthlyIncome_num": "MonthlyIncome", "NumberOfDependents_num": "NumberOfDependents"})
    )

    # feature_engineering.sas:59-73  # INV work.income_medians; R§2 PROC SQL median
    income_medians = (
        credit_raw_clean.with_columns(
            # :62-68 PROC SQL CASE; R§2 chain, INV age_group: Int32 literals; SAS comparisons (finding P2)
            age_group=pl.when(sas_compat.lt(pl.col("age"), 30))
            .then(1)
            .when(sas_compat.lt(pl.col("age"), 40))
            .then(2)
            .when(sas_compat.lt(pl.col("age"), 50))
            .then(3)
            .when(sas_compat.lt(pl.col("age"), 60))
            .then(4)
            .otherwise(5)
        )
        .filter(pl.col("MonthlyIncome").is_not_null())
        .group_by("age_group", maintain_order=True)
        .agg(median_income=pl.col("MonthlyIncome").median())
    )

    # feature_engineering.sas:165-184  # work.age_groups, work.income_medians_all
    # one row per age group 1 to 5 (an age group with no known income has a missing median), with the
    # median of all known incomes on every row (the input check leaves at least one); ordered by
    # age_group
    age_groups = pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}, schema={"age_group": pl.Int32})
    income_medians_all = age_groups.join(
        income_medians, on="age_group", how="left", maintain_order="left"
    ).with_columns(
        overall_median_income=pl.lit(
            credit_raw_clean.get_column("MonthlyIncome").drop_nulls().median(), dtype=pl.Float64
        )
    )

    # feature_engineering.sas:75-94  # INV age_group, MonthlyIncome_missing, Dependents_missing
    credit_cleaned = credit_raw_clean.with_columns(
        # :79-83 R§2 if/else-if chain, INV age_group: Int32 literals; SAS comparisons (finding P2)
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
        # both expressions read the pre-imputation column (SAS evaluates missing() before the assignment)
        Dependents_missing=sas_compat.flag(pl.col("NumberOfDependents").is_null()),
        NumberOfDependents=pl.col("NumberOfDependents").fill_null(0.0),
    )

    # feature_engineering.sas:97-120  # INV work.credit_imputed; R§2 left join (A11), key Int32 on both sides
    # :214 Q1 (167dc38): the age group's median, else the median of all known incomes
    credit_imputed = credit_cleaned.join(
        income_medians_all, on="age_group", how="left", maintain_order="left"
    ).select(
        pl.col("VAR1").alias("row_id"),
        pl.col("SeriousDlqin2yrs").alias("default_flag"),
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

    # feature_engineering.sas:126-202  # R§2 DATA step: successive with_columns where a statement reads
    # an earlier assignment; plain comparisons because every operand is MISSING_NEVER (A2, INV rows)
    # :182-188  # INV financial_health; A30 nested expression applying the statements in order
    fh = pl.lit(100.0)
    fh = pl.when(pl.col("credit_utilization") > 30).then(fh - 15).otherwise(fh)
    fh = pl.when(pl.col("credit_utilization") > 75).then(fh - 15).otherwise(fh)
    fh = pl.when(pl.col("debt_ratio") > 43).then(fh - 20).otherwise(fh)
    fh = pl.when(pl.col("has_delinquency") != 0).then(fh - 20).otherwise(fh)  # R§2 truthiness (A29)
    fh = pl.when(pl.col("num_late_90_plus") > 0).then(fh - 30).otherwise(fh)

    credit_features = (
        credit_imputed.with_columns(
            # :130  # INV total_late_payments
            total_late_payments=sas_compat.sas_sum(
                pl.col("num_late_30_59"), pl.col("num_late_60_89"), pl.col("num_late_90_plus")
            ).alias("total_late_payments"),
        )
        .with_columns(
            # :133  # INV has_delinquency
            has_delinquency=sas_compat.flag(pl.col("total_late_payments") > 0),
            # :136  # INV has_serious_delinquency
            has_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
            # :139-142  # INV credit_util_category; SAS comparisons in the three chains (finding P4)
            credit_util_category=pl.when(sas_compat.lt(pl.col("credit_utilization"), 30))
            .then(1)
            .when(sas_compat.lt(pl.col("credit_utilization"), 50))
            .then(2)
            .when(sas_compat.lt(pl.col("credit_utilization"), 75))
            .then(3)
            .otherwise(4),
            # :145-148  # INV debt_category
            debt_category=pl.when(sas_compat.lt(pl.col("debt_ratio"), 30))
            .then(1)
            .when(sas_compat.lt(pl.col("debt_ratio"), 43))
            .then(2)
            .when(sas_compat.lt(pl.col("debt_ratio"), 60))
            .then(3)
            .otherwise(4),
            # :151-152  # INV income_per_dependent (plain `/`, column by column, divisor >= 2; A13)
            income_per_dependent=pl.when(pl.col("num_dependents") > 0)
            .then(pl.col("monthly_income") / (pl.col("num_dependents") + 1))
            .otherwise(pl.col("monthly_income")),
            # :155  # INV credit_lines_per_person (divisor >= 1)
            credit_lines_per_person=pl.col("num_credit_lines") / (pl.col("num_dependents") + 1),
            # :158-162  # INV age_category
            age_category=pl.when(sas_compat.lt(pl.col("age"), 25))
            .then(1)
            .when(sas_compat.lt(pl.col("age"), 35))
            .then(2)
            .when(sas_compat.lt(pl.col("age"), 50))
            .then(3)
            .when(sas_compat.lt(pl.col("age"), 65))
            .then(4)
            .otherwise(5),
            # :165-174  # INV flag_* rows; R§2 flag()
            flag_high_utilization=sas_compat.flag(pl.col("credit_utilization") > 75),
            flag_very_high_utilization=sas_compat.flag(pl.col("credit_utilization") > 100),
            flag_high_debt_ratio=sas_compat.flag(pl.col("debt_ratio") > 43),
            flag_very_high_debt_ratio=sas_compat.flag(pl.col("debt_ratio") > 60),
            flag_recent_late_payments=sas_compat.flag(pl.col("num_late_30_59") > 0),
            flag_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
            flag_multiple_delinquencies=sas_compat.flag(pl.col("total_late_payments") >= 3),
            flag_low_income=sas_compat.flag(sas_compat.lt(pl.col("monthly_income"), 2500)),
            flag_many_dependents=sas_compat.flag(pl.col("num_dependents") >= 3),
            flag_few_credit_lines=sas_compat.flag(sas_compat.le(pl.col("num_credit_lines"), 2)),
        )
        .with_columns(
            # :288-292  # INV total_risk_flags; Q7 (7b55ef1): the eight risk flags, in the SAS order
            total_risk_flags=sas_compat.sas_sum(
                pl.col("flag_high_utilization"),
                pl.col("flag_very_high_utilization"),
                pl.col("flag_high_debt_ratio"),
                pl.col("flag_serious_delinquency"),
                pl.col("flag_multiple_delinquencies"),
                pl.col("flag_low_income"),
                pl.col("flag_many_dependents"),
                pl.col("flag_few_credit_lines"),
            ).alias("total_risk_flags"),
            # :182-188  # INV financial_health; A30 one expression applying the statements in order
            financial_health=sas_compat.sas_max(pl.lit(0.0), fh).alias("financial_health"),
            # :191-193  # INV log_* rows; R§2 log()
            log_monthly_income=sas_compat.sas_log(pl.col("monthly_income") + 1).alias("log_monthly_income"),
            log_num_credit_lines=sas_compat.sas_log(pl.col("num_credit_lines") + 1).alias(
                "log_num_credit_lines"
            ),
            log_total_late_payments=sas_compat.sas_log(pl.col("total_late_payments") + 1).alias(
                "log_total_late_payments"
            ),
        )
        .with_columns(
            # :309-310  # INV age_income_interaction; Q9 (10f447e): age * log(income) when the income is
            # above 0, else age * log_monthly_income (assigned above); a missing income takes the else
            age_income_interaction=pl.when(pl.col("monthly_income") > 0)
            .then(pl.col("age") * sas_compat.sas_log(pl.col("monthly_income")))
            .otherwise(pl.col("age") * pl.col("log_monthly_income")),
            # :311  # INV utilization_debt_interaction; Q9 (10f447e): the product, no division by 100
            utilization_debt_interaction=pl.col("credit_utilization") * pl.col("debt_ratio"),
            # :200-201  # INV credit_utilization_capped, debt_ratio_capped; R§2 min()
            credit_utilization_capped=sas_compat.sas_min(pl.col("credit_utilization"), pl.lit(200.0)).alias(
                "credit_utilization_capped"
            ),
            debt_ratio_capped=sas_compat.sas_min(pl.col("debt_ratio"), pl.lit(500.0)).alias(
                "debt_ratio_capped"
            ),
        )
    )

    # feature_engineering.sas:209-221  # INV work.credit_split
    # RESOLVED (post-parity): the split is an explicit input (--split-ids), so row order cannot change it
    # (SAS drew a different split in judge run x_split_drift_m_metrics_threshold, judge/README.md:75-81)
    # the split is an INPUT (A27): selected = row_id is a training row_id in split_ids
    train_ids = (
        pl.read_csv(split_ids, columns=["row_id"], infer_schema=False)  # R§1 CSV I/O: all text
        .get_column("row_id")
        .cast(pl.Int64)
        .cast(pl.Float64)
    )
    credit_split = credit_features.with_columns(selected=pl.col("row_id").is_in(train_ids.implode()))
    credit_train = credit_split.filter(pl.col("selected")).drop("selected")
    credit_validation = credit_split.filter(~pl.col("selected")).drop("selected")

    # feature_engineering.sas:227-247
    # listing-only: PROC MEANS n mean std min max of credit_train
    # listing-only: PROC FREQ default_flag of credit_train
    # listing-only: PROC MEANS n mean std min max of credit_validation
    # listing-only: PROC FREQ default_flag of credit_validation

    # feature_engineering.sas:254-278  # INV model_features_train.csv, model_features_validation.csv
    # `format _numeric_ best12.` is the writer default (A31): the copy steps are kept as aliases
    credit_train_export = credit_train
    credit_validation_export = credit_validation
    # :380-391  income_medians.csv, always written and first: the training income medians per age group
    # and overall (format best32. on the two medians), from which predict imputes the test set
    income_medians_export = income_medians_all
    sas_compat.write_sas_csv(
        income_medians_export,
        output_dir / "income_medians.csv",
        formats={"median_income": "best32.", "overall_median_income": "best32."},
    )
    sas_compat.write_sas_csv(credit_train_export, output_dir / "model_features_train.csv", formats={})
    sas_compat.write_sas_csv(
        credit_validation_export, output_dir / "model_features_validation.csv", formats={}
    )

    # feature_engineering.sas:280-284  # R§2 %put
    print("NOTE: Feature engineering completed successfully")
    print(f"NOTE: Training set: exported to {output_dir}/model_features_train.csv")
    print(f"NOTE: Validation set: exported to {output_dir}/model_features_validation.csv")
    print("NOTE: Missing value imputation completed")
    print("NOTE: Ready for model training")


if __name__ == "__main__":  # R§4
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split-ids", type=Path, required=True)
    args = parser.parse_args()
    run(args.data_dir, args.output_dir, split_ids=args.split_ids)

# PORT STATUS: confidence=high todos=0
