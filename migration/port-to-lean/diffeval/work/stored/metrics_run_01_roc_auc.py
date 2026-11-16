    # metrics_calculation.sas:71-77 PROC LOGISTIC nofit + roc (ROCAssociation)
    # INV printed_roc_metrics.csv; the roccontrast table is not ported. With one response level among the
    # usable rows (or no usable row) PROC LOGISTIC stops with an ERROR and WORK.ROC_STATS is not created:
    # the Area is then missing here
    # listing-only: PROC LOGISTIC roccontrast (ROC Model Information / contrast coefficients)
    roc_stats = sas_compat.roc_association(
        logit_scored_valid.get_column("default_flag"),
        logit_scored_valid.get_column("pd_logistic"),
        "Logistic Model",
    )

    # metrics_calculation.sas:82-91 auc_pairs: one row per distinct non-missing probability
    # R§2 SQL aggregates: sum of a comparison counts the rows where it holds (never missing in a group)
    auc_pairs = (
        logit_scored_valid.filter(pl.col("pd_logistic").is_not_null())
        .group_by("pd_logistic", maintain_order=True)
        .agg(
            n_bad=sas_compat.flag(pl.col("default_flag") == 1).sum(),
            n_good=sas_compat.flag(pl.col("default_flag") == 0).sum(),
        )
        .sort("pd_logistic", maintain_order=True)  # order by pd_logistic
    )

    # metrics_calculation.sas:93-113 auc_summary (retain concordant tied cum_good cum_bad 0; end=eof ->
    # aggregation): the exact pairwise AUC. concordant adds n_bad * cum_good BEFORE cum_good takes the row;
    # AUC and Gini stay missing with no defaulter or no non-defaulter; no row when auc_pairs has none.
    # Formats 8.4 applied at export
    auc_totals = auc_pairs.select(
        concordant=(pl.col("n_bad") * (pl.col("n_good").cum_sum() - pl.col("n_good"))).sum(),
        tied=(pl.col("n_bad") * pl.col("n_good")).sum(),
        cum_good=pl.col("n_good").sum(),
        cum_bad=pl.col("n_bad").sum(),
    ).cast(pl.Float64)
    auc_summary = (
        auc_totals.with_columns(
            ROCModel=pl.lit("Logistic Model"),
            AUC=pl.when(pl.col("cum_bad") * pl.col("cum_good") > 0).then(
                (pl.col("concordant") + pl.col("tied") / 2) / (pl.col("cum_bad") * pl.col("cum_good"))
            ),
        )
        .with_columns(Gini=2 * pl.col("AUC") - 1)
        .select("ROCModel", "AUC", "Gini")  # keep list (:111)
        .head(min(auc_pairs.height, 1))
    )
