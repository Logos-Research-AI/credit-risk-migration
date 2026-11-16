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
