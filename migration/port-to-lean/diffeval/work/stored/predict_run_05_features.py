    test_features = test_imputed.with_columns(
        total_late_payments=sas_compat.sas_sum(  # INV total_late_payments
            pl.col("num_late_30_59"), pl.col("num_late_60_89"), pl.col("num_late_90_plus")
        ),
    )
    test_features = test_features.with_columns(
        # predict.sas:276-280 INV has_delinquency / has_serious_delinquency (plain: MISSING_NEVER)
        has_delinquency=sas_compat.flag(pl.col("total_late_payments") > 0),
        has_serious_delinquency=sas_compat.flag(pl.col("num_late_90_plus") > 0),
        # predict.sas:282-286 INV credit_util_category; SAS comparisons in the three chains (finding P5)
        credit_util_category=pl.when(sas_compat.lt(pl.col("credit_utilization"), 30))
        .then(1)
        .when(sas_compat.lt(pl.col("credit_utilization"), 50))
        .then(2)
        .when(sas_compat.lt(pl.col("credit_utilization"), 75))
        .then(3)
        .otherwise(4),
        # predict.sas:288-292 INV debt_category
        debt_category=pl.when(sas_compat.lt(pl.col("debt_ratio"), 30))
        .then(1)
        .when(sas_compat.lt(pl.col("debt_ratio"), 43))
        .then(2)
        .when(sas_compat.lt(pl.col("debt_ratio"), 60))
        .then(3)
        .otherwise(4),
        # predict.sas:294-296 INV log_monthly_income / age_income_interaction / income_per_dependent
        # num_dependents never missing, so plain comparison; null monthly_income propagates
        income_per_dependent=pl.when(pl.col("num_dependents") > 0)
        .then(pl.col("monthly_income") / (pl.col("num_dependents") + 1))
        .otherwise(pl.col("monthly_income")),
        # predict.sas:298-299 INV credit_lines_per_person (divisor >= 1, plain `/`)
        credit_lines_per_person=pl.col("num_credit_lines") / (pl.col("num_dependents") + 1),
        # predict.sas:301-306 INV age_category
        age_category=pl.when(sas_compat.lt(pl.col("age"), 25))
        .then(1)
        .when(sas_compat.lt(pl.col("age"), 35))
        .then(2)
        .when(sas_compat.lt(pl.col("age"), 50))
        .then(3)
        .when(sas_compat.lt(pl.col("age"), 65))
        .then(4)
        .otherwise(5),
        # predict.sas:308-318 risk flags; INV flag_* (plain comparisons, MISSING_NEVER)
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
    # predict.sas:320-334 INV total_risk_flags, INV financial_health (A30: one nested expression)
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
        # predict.sas:336-339 INV log_* (R§2 log)
        log_monthly_income=sas_compat.sas_log(pl.col("monthly_income") + 1),
        log_num_credit_lines=sas_compat.sas_log(pl.col("num_credit_lines") + 1),
        log_total_late_payments=sas_compat.sas_log(pl.col("total_late_payments") + 1),
    )
    test_features = test_features.with_columns(
        # predict.sas:341-348
        # Q9 (10f447e): age * log(income) when income is above 0, else age * log(income + 1)
        age_income_interaction=pl.when(pl.col("monthly_income") > 0)
        .then(pl.col("age") * sas_compat.sas_log(pl.col("monthly_income")))
        .otherwise(pl.col("age") * pl.col("log_monthly_income")),
        # Q9 (10f447e): utilization * debt ratio, no division by 100
        utilization_debt_interaction=pl.col("credit_utilization") * pl.col("debt_ratio"),
        credit_utilization_capped=sas_compat.sas_min(pl.col("credit_utilization"), pl.lit(200.0)),
        debt_ratio_capped=sas_compat.sas_min(pl.col("debt_ratio"), pl.lit(500.0)),
    )
