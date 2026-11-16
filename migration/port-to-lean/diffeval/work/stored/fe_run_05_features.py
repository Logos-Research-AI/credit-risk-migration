    fh = pl.lit(100.0)
    fh = pl.when(pl.col("credit_utilization") > 30).then(fh - 15).otherwise(fh)
    fh = pl.when(pl.col("credit_utilization") > 75).then(fh - 15).otherwise(fh)
    fh = pl.when(pl.col("debt_ratio") > 43).then(fh - 20).otherwise(fh)
    fh = pl.when(pl.col("has_delinquency") != 0).then(fh - 20).otherwise(fh)  # R§2 truthiness (A29)
    fh = pl.when(pl.col("num_late_90_plus") > 0).then(fh - 30).otherwise(fh)

    credit_features = (
        credit_imputed.with_columns(
            # :241  # INV total_late_payments
            total_late_payments=sas_compat.sas_sum(
                pl.col("num_late_30_59"), pl.col("num_late_60_89"), pl.col("num_late_90_plus")
            ).alias("total_late_payments"),
        )
        .with_columns(
            # :244  # INV has_delinquency
            has_delinquency=sas_compat.flag(pl.col("total_late_payments") > 0),
            # :247  # INV has_serious_delinquency
            has_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
            # :250-253  # INV credit_util_category; SAS comparisons in the three chains (finding P4)
            credit_util_category=pl.when(sas_compat.lt(pl.col("credit_utilization"), 30))
            .then(1)
            .when(sas_compat.lt(pl.col("credit_utilization"), 50))
            .then(2)
            .when(sas_compat.lt(pl.col("credit_utilization"), 75))
            .then(3)
            .otherwise(4),
            # :256-259  # INV debt_category
            debt_category=pl.when(sas_compat.lt(pl.col("debt_ratio"), 30))
            .then(1)
            .when(sas_compat.lt(pl.col("debt_ratio"), 43))
            .then(2)
            .when(sas_compat.lt(pl.col("debt_ratio"), 60))
            .then(3)
            .otherwise(4),
            # :262-263  # INV income_per_dependent (plain `/`, column by column, divisor >= 2; A13)
            income_per_dependent=pl.when(pl.col("num_dependents") > 0)
            .then(pl.col("monthly_income") / (pl.col("num_dependents") + 1))
            .otherwise(pl.col("monthly_income")),
            # :266  # INV credit_lines_per_person (divisor >= 1)
            credit_lines_per_person=pl.col("num_credit_lines") / (pl.col("num_dependents") + 1),
            # :269-273  # INV age_category
            age_category=pl.when(sas_compat.lt(pl.col("age"), 25))
            .then(1)
            .when(sas_compat.lt(pl.col("age"), 35))
            .then(2)
            .when(sas_compat.lt(pl.col("age"), 50))
            .then(3)
            .when(sas_compat.lt(pl.col("age"), 65))
            .then(4)
            .otherwise(5),
            # :276-285  # INV flag_* rows; R§2 flag()
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
            ),
            # :294-301  # INV financial_health; A30 one expression applying the statements in order
            financial_health=sas_compat.sas_max(pl.lit(0.0), fh).alias("financial_health"),
            # :304-306  # INV log_* rows; R§2 log()
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
            # :314-315  # INV credit_utilization_capped, debt_ratio_capped; R§2 min()
            credit_utilization_capped=sas_compat.sas_min(pl.col("credit_utilization"), pl.lit(200.0)).alias(
                "credit_utilization_capped"
            ),
            debt_ratio_capped=sas_compat.sas_min(pl.col("debt_ratio"), pl.lit(500.0)).alias(
                "debt_ratio_capped"
            ),
        )
    )
