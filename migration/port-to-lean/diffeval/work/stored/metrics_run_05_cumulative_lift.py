    # metrics_calculation.sas:286-290 select ... into :total_defaults, :overall_default_rate
    # R§2 select into (A9): BEST8. text, later arithmetic sees the rounded value; INV &total_defaults /
    # &overall_default_rate
    into = decile_data.select(
        total_defaults=sas_compat.sql_sum(pl.col("default_flag")),  # R§2 SQL aggregates (S10)
        overall_default_rate=sas_compat.sql_mean(pl.col("default_flag")),
    )
    total_defaults = _into_float(cast(float | None, into.item(0, "total_defaults")))
    overall_default_rate = _into_float(cast(float | None, into.item(0, "overall_default_rate")))

    # metrics_calculation.sas:293-314 cumulative_lift (retain cum_defaults cum_count)
    # INV work.cumulative_lift: running totals in ascending decile order; scalar divisors -> div (A13).
    # :306-312 with no defaulter (&total_defaults / &overall_default_rate not above 0, or missing) both
    # are 0; cum_lift stays missing while the deciles so far are empty
    cumulative_lift = (
        decile_analysis.sort("decile", maintain_order=True)
        .with_columns(
            cum_defaults=pl.col("defaults").cum_sum().forward_fill(),  # sum statement skips missing (P7)
            cum_count=pl.col("total_count").cum_sum(),
        )
        .with_columns(
            cum_capture_rate=pl.when(sas_compat.gt(pl.lit(total_defaults, pl.Float64), 0))
            .then(sas_compat.div(pl.col("cum_defaults"), pl.lit(total_defaults, pl.Float64)))
            .otherwise(0.0),
            cum_lift=pl.when(sas_compat.gt(pl.col("cum_count"), 0)).then(
                pl.when(sas_compat.gt(pl.lit(overall_default_rate, pl.Float64), 0))
                .then(
                    sas_compat.div(
                        pl.col("cum_defaults") / pl.col("cum_count"), pl.lit(overall_default_rate, pl.Float64)
                    )
                )
                .otherwise(0.0)
            ),
        )
    )
