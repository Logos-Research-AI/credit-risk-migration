    # metrics_calculation.sas:124-126 PROC SORT by pd_logistic (in place; stable, ties keep input order)
    logit_scored_valid = logit_scored_valid.sort("pd_logistic", maintain_order=True)  # R§2 PROC SORT

    # metrics_calculation.sas:129-133 select ... into :total_good_count, :total_bad_count
    # R§2 select into (A9): BEST8. text; INV work.ks_calculation / ks_statistic: exact integers here
    totals = logit_scored_valid.select(
        good=sas_compat.sql_sum(sas_compat.flag(pl.col("default_flag") == 0)),  # R§2 SQL aggregates (S10)
        bad=sas_compat.sql_sum(sas_compat.flag(pl.col("default_flag") == 1)),
    )
    total_good_count = _into_float(cast(float | None, totals.item(0, "good")))
    total_bad_count = _into_float(cast(float | None, totals.item(0, "bad")))

    # metrics_calculation.sas:136-153 ks_calculation (by pd_logistic; retain cum_good cum_bad)
    # INV work.ks_calculation: cum_bad counts every row that is not default_flag = 0; scalar divisors ->
    # div (A13)
    ks_calculation = logit_scored_valid.with_columns(
        cum_good=sas_compat.flag(pl.col("default_flag") == 0).cum_sum(),
        cum_bad=(1 - sas_compat.flag(pl.col("default_flag") == 0)).cum_sum(),  # else branch (:146-147)
    )
    ks_calculation = ks_calculation.with_columns(
        cum_pct_good=sas_compat.div(pl.col("cum_good"), pl.lit(total_good_count, pl.Float64)),
        cum_pct_bad=sas_compat.div(pl.col("cum_bad"), pl.lit(total_bad_count, pl.Float64)),
    )
    # :152 if last.pd_logistic: the last row of each run of equal probabilities (missing is one BY group);
    # ks_value stays missing on the other rows
    last_pd_logistic = (pl.int_range(pl.len()) == pl.len() - 1) | pl.col("pd_logistic").ne_missing(
        pl.col("pd_logistic").shift(-1)
    )
    ks_calculation = ks_calculation.with_columns(
        ks_value=pl.when(last_pd_logistic).then((pl.col("cum_pct_good") - pl.col("cum_pct_bad")).abs())
    )

    # metrics_calculation.sas:156-162 ks_statistic (one row: the maximum and the lowest cutoff attaining it)
    # R§2 SQL aggregates (S10): one row also over no rows; INV work.ks_calculation / ks_statistic
    max_ks_value = ks_calculation.select(sas_compat.sql_max(pl.col("ks_value")))  # R§2 SQL aggregates (S10)
    ks_statistic = ks_calculation.filter(
        sas_compat.eq(pl.col("ks_value"), pl.lit(max_ks_value.item(0, 0), pl.Float64))  # SQL: . = . is true
    ).select(
        KS_Statistic=sas_compat.sql_max(pl.col("ks_value")),
        KS_Cutoff=sas_compat.sql_min(pl.col("pd_logistic")),
    )
