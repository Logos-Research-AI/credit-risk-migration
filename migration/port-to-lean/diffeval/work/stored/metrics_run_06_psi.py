    # metrics_calculation.sas:332-346 psi_cuts: the nine nearest-rank deciles of the training scores
    # R§2 PROC SORT (missing first); row ceil(k * n_train / 10) of the sorted scores, k = 1..9. An empty
    # training set leaves psi_cuts without a row
    train_scores_sorted = logit_scored_train.select("credit_risk_score").sort(
        "credit_risk_score", maintain_order=True
    )
    n_train = train_scores_sorted.height
    psi_cuts = [
        cast(float | None, train_scores_sorted.item(-(-k * n_train // 10) - 1, 0))
        for k in range(1, 10)
        if n_train > 0
    ]

    # metrics_calculation.sas:349-369 train_bins / valid_bins: both sets in the training bins; a score
    # equal to a cut belongs to the lower bin (SAS >, missing smallest). `if _n_ = 1 then set psi_cuts`
    # ends the step at once when psi_cuts has no row: both tables are then empty
    score_bin = pl.lit(0, pl.Int64)
    for cut in psi_cuts:
        score_bin = score_bin + sas_compat.flag(
            sas_compat.gt(pl.col("credit_risk_score"), pl.lit(cut, pl.Float64))
        )
    train_bins = (logit_scored_train if psi_cuts else logit_scored_train.clear()).with_columns(
        score_bin=score_bin
    )
    valid_bins = (logit_scored_valid if psi_cuts else logit_scored_valid.clear()).with_columns(
        score_bin=score_bin
    )

    # metrics_calculation.sas:371-375 psi_bins: always ten rows, bins 0 to 9
    psi_bins = pl.DataFrame({"score_bin": list(range(10))}, schema={"score_bin": pl.Int64})

    # metrics_calculation.sas:381-386 &psi_rows (whole number, format 32.) and &psi_floor = (0.5 / &psi_rows)
    # SQL division by 0 is missing (no row on either side)
    psi_rows = max(train_bins.height, valid_bins.height)
    psi_floor = pl.lit(0.5 / psi_rows if psi_rows > 0 else None, pl.Float64)

    # metrics_calculation.sas:389-406 psi_calculation
    # INV work.psi_calculation / psi_summary: shares = div(count, n) after aggregation (A7, A13); left
    # joins from psi_bins, an empty bin has share 0 and enters the component at the floor (SAS max ignores
    # missing)
    a = train_bins.group_by("score_bin", maintain_order=True).agg(cnt=pl.len().cast(pl.Int64))
    a = a.with_columns(train_pct=sas_compat.div(pl.col("cnt"), train_bins.height)).drop("cnt")
    b = valid_bins.group_by("score_bin", maintain_order=True).agg(cnt=pl.len().cast(pl.Int64))
    b = b.with_columns(valid_pct=sas_compat.div(pl.col("cnt"), valid_bins.height)).drop("cnt")
    psi_calculation = (
        psi_bins.join(a, on="score_bin", how="left", maintain_order="left")
        .join(b, on="score_bin", how="left", maintain_order="left")
        .with_columns(
            train_pct=pl.col("train_pct").fill_null(0.0),  # coalesce(a.train_pct, 0)
            valid_pct=pl.col("valid_pct").fill_null(0.0),  # coalesce(b.valid_pct, 0)
        )
        .with_columns(
            psi_component=(
                sas_compat.sas_max(pl.col("train_pct"), psi_floor)
                - sas_compat.sas_max(pl.col("valid_pct"), psi_floor)
            )
            * sas_compat.sas_log(  # R§2 log
                sas_compat.div(
                    sas_compat.sas_max(pl.col("train_pct"), psi_floor),
                    sas_compat.sas_max(pl.col("valid_pct"), psi_floor),
                )
            )
        )
        .sort("score_bin", maintain_order=True)  # order by s.score_bin
    )

    # metrics_calculation.sas:408-415 psi_summary (PSI format best12.: published unrounded)
    # R§2 SQL aggregates (S10): PSI is missing when every component is missing; INV work.psi_calculation /
    # psi_summary (S11)
    psi_summary = psi_calculation.select(PSI=sas_compat.sql_sum(pl.col("psi_component")))
    psi_summary = psi_summary.with_columns(
        PSI_interpretation=pl.when(sas_compat.lt(pl.col("PSI"), 0.1))
        .then(pl.lit("No significant change"))
        .when(sas_compat.lt(pl.col("PSI"), 0.25))
        .then(pl.lit("Some change"))
        .otherwise(pl.lit("Significant change"))
    )
