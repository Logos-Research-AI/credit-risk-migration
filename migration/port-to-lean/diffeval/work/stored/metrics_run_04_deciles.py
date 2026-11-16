    # metrics_calculation.sas:234-239 PROC RANK groups=10 descending
    # R§2 PROC RANK; INV work.decile_data / decile_analysis
    decile_data = logit_scored_valid.with_columns(
        sas_compat.proc_rank_groups(logit_scored_valid.get_column("pd_logistic"), 10, descending=True).alias(
            "decile"
        )
    )

    # metrics_calculation.sas:242-246 decile_list: always ten rows, deciles 1 to 10
    decile_list = pl.DataFrame({"decile": list(range(1, 11))}, schema={"decile": pl.Int64})

    # metrics_calculation.sas:251-279 decile_analysis (decile_list left join the grouped data)
    # INV work.decile_data / decile_analysis: the :273-274 subqueries run at FULL precision (not the
    # BEST8. INTO values); a decile with no applicant, and 0/0 with no defaulter, give capture rate and
    # lift 0 (coalesce); a missing decile is in no row of the list
    subquery = decile_data.select(
        total_defaults=sas_compat.sql_sum(pl.col("default_flag")),  # R§2 SQL aggregates (S10)
        overall_default_rate=sas_compat.sql_mean(pl.col("default_flag")),
    )
    sq_total_defaults = cast(float | None, subquery.item(0, "total_defaults"))
    sq_overall_default_rate = cast(float | None, subquery.item(0, "overall_default_rate"))
    decile_grouped = (
        decile_data.group_by("decile", maintain_order=True)
        .agg(
            total_count=pl.len().cast(pl.Int64),
            defaults=sas_compat.sql_sum(pl.col("default_flag")),
            default_rate=sas_compat.sql_mean(pl.col("default_flag")),  # SAS mean ignores missing
            avg_pd=sas_compat.sql_mean(pl.col("pd_logistic")),
            min_pd=sas_compat.sql_min(pl.col("pd_logistic")),
            max_pd=sas_compat.sql_max(pl.col("pd_logistic")),
        )
        .with_columns(decile=pl.col("decile") + 1)  # decile + 1 as decile
        .with_columns(
            capture_rate=sas_compat.div(
                pl.col("defaults"), pl.lit(sq_total_defaults, pl.Float64)
            ),  # A13: scalar divisor
            lift=sas_compat.div(
                pl.col("default_rate"), pl.lit(sq_overall_default_rate, pl.Float64)
            ),  # calculated default_rate, A13
        )
    )
    decile_analysis = (
        decile_list.join(decile_grouped, on="decile", how="left", maintain_order="left")
        .with_columns(
            total_count=pl.col("total_count").fill_null(0),  # coalesce(d.total_count, 0)
            defaults=pl.col("defaults").fill_null(0),  # coalesce(d.defaults, 0)
            capture_rate=pl.col("capture_rate").fill_null(0.0),  # coalesce(d.capture_rate, 0)
            lift=pl.col("lift").fill_null(0.0),  # coalesce(d.lift, 0)
        )
        .sort("decile", maintain_order=True)  # order by l.decile
        .select(
            "decile",
            "total_count",
            "defaults",
            "default_rate",
            "avg_pd",
            "min_pd",
            "max_pd",
            "capture_rate",
            "lift",
        )
    )
    decile_analysis_formats = {
        "default_rate": "percent8.2",
        "avg_pd": "8.4",
        "min_pd": "8.4",
        "max_pd": "8.4",
        "capture_rate": "percent8.2",
        "lift": "8.2",
    }
