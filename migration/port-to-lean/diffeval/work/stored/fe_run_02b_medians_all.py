    age_groups = pl.DataFrame({"age_group": [1, 2, 3, 4, 5]}, schema={"age_group": pl.Int32})
    income_medians_all = age_groups.join(
        income_medians, on="age_group", how="left", maintain_order="left"
    ).with_columns(
        overall_median_income=pl.lit(
            credit_raw_clean.get_column("MonthlyIncome").drop_nulls().median(), dtype=pl.Float64
        )
    )
