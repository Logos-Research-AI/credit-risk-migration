"""Credit Risk Scoring Model - Model Validation (port of metrics_calculation.sas).

RULEBOOK v1.3. Stage entry point: run(input_dir, output_dir) (R§4, A27).
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import cast

import polars as pl

from credit_risk import sas_compat


def _into_float(x: float | None) -> float | None:
    # R§2 select into (A9): BEST8. text; a missing aggregate stays missing (S10)
    v = sas_compat.sas_best(x, 8)
    return float(v) if v else None


# metrics_calculation.sas:122-158  %macro confusion_metrics(threshold, suffix)
# R§2 macro (A23): returns the datasets it creates (confusion, conf_matrix, metrics)
def confusion_metrics(
    threshold: float, suffix: str, logit_scored_valid: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    # R§2 macro: WORK dataset the body reads is a parameter; suffix only names SAS datasets (INV
    # confusion_metrics)
    _ = suffix
    # :123-126 predicted = (pd_logistic >= &threshold)
    confusion = logit_scored_valid.with_columns(
        predicted=sas_compat.flag(
            pl.col("pd_logistic") >= threshold
        )  # R§2 boolean assignment; INV predicted (MISSING_NEVER, plain >=)
    )
    # :128-130 PROC FREQ tables default_flag * predicted / out=conf_matrix
    # INV work.conf_matrix_&suffix: only occurring cells become rows
    conf_matrix = (
        confusion.group_by(["default_flag", "predicted"], maintain_order=True)
        .agg(COUNT=pl.len().cast(pl.Int64))
        .sort(["default_flag", "predicted"], maintain_order=True)
    )
    # :133-157 retain TP TN FP FN 0; set ... end=eof  (R§2 retain + end=eof -> aggregation)
    # INV work.metrics_&suffix: an absent cell keeps the retained 0 (empty sum is 0)
    counts = conf_matrix.select(
        TP=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("predicted") == 1)).sum(),
        TN=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("predicted") == 0)).sum(),
        FP=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("predicted") == 1)).sum(),
        FN=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("predicted") == 0)).sum(),
    ).cast(pl.Int64)
    # INV accuracy / precision / recall / specificity (plain guards, column / column division, A13)
    metrics = counts.with_columns(
        threshold=pl.lit(threshold, pl.Float64),
        accuracy=pl.when((pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")) > 0)
        .then((pl.col("TP") + pl.col("TN")) / (pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")))
        .otherwise(None),
        precision=pl.when((pl.col("TP") + pl.col("FP")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FP")))
        .otherwise(None),
        recall=pl.when((pl.col("TP") + pl.col("FN")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FN")))
        .otherwise(None),
        specificity=pl.when((pl.col("TN") + pl.col("FP")) > 0)
        .then(pl.col("TN") / (pl.col("TN") + pl.col("FP")))
        .otherwise(None),
    )
    # INV f1_score (MISSING_NULLABLE, A2): reads precision and recall assigned above
    metrics = metrics.with_columns(
        f1_score=pl.when(sas_compat.gt(pl.col("precision") + pl.col("recall"), 0))
        .then(2 * (pl.col("precision") * pl.col("recall")) / (pl.col("precision") + pl.col("recall")))
        .otherwise(None)
    )
    metrics = metrics.select("threshold", "accuracy", "precision", "recall", "f1_score", "specificity").cast(
        pl.Float64
    )  # keep list (:156); explicit Float64 so an all-null column is not dtype Null
    return confusion, conf_matrix, metrics


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)  # R§4, S12

    # metrics_calculation.sas:28-41 PROC IMPORT of the scored data
    # INV work.logit_scored_valid / logit_scored_train (R§2 PROC IMPORT, default guessingrows=20)
    logit_scored_valid = sas_compat.proc_import_csv(input_dir / "risk_scores_validation.csv", guessingrows=20)
    logit_scored_train = sas_compat.proc_import_csv(input_dir / "risk_scores_train.csv", guessingrows=20)

    # metrics_calculation.sas:48-54 PROC LOGISTIC nofit + roc (ROCAssociation)
    # INV printed_roc_metrics.csv; the roccontrast table is not ported
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

    # listing-only: PROC PRINT auc_summary (AUC and Gini)

    # metrics_calculation.sas:75-77 PROC SORT by pd_logistic (in place; stable, ties keep input order)
    logit_scored_valid = logit_scored_valid.sort("pd_logistic", maintain_order=True)  # R§2 PROC SORT

    # metrics_calculation.sas:80-84 select ... into :total_good_count, :total_bad_count
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

    # listing-only: PROC PRINT ks_statistic

    # metrics_calculation.sas:161-165 test multiple thresholds (call order)
    _confusion_03, _conf_matrix_03, metrics_03 = confusion_metrics(0.3, "03", logit_scored_valid)
    _confusion_04, _conf_matrix_04, metrics_04 = confusion_metrics(0.4, "04", logit_scored_valid)
    _confusion_05, _conf_matrix_05, metrics_05 = confusion_metrics(0.5, "05", logit_scored_valid)
    _confusion_06, _conf_matrix_06, metrics_06 = confusion_metrics(0.6, "06", logit_scored_valid)
    _confusion_07, _conf_matrix_07, metrics_07 = confusion_metrics(0.7, "07", logit_scored_valid)

    # metrics_calculation.sas:168-171 threshold_analysis (set = concatenation)
    threshold_analysis = pl.concat(
        [metrics_03, metrics_04, metrics_05, metrics_06, metrics_07], how="vertical"
    )

    # listing-only: PROC PRINT threshold_analysis (accuracy..specificity printed 8.4)

    # metrics_calculation.sas:183-188 PROC RANK groups=10 descending
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

    # listing-only: PROC PRINT decile_analysis

    # metrics_calculation.sas:213-217 select ... into :total_defaults, :overall_default_rate
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

    # listing-only: PROC SGPLOT cumulative_lift (cumulative lift by decile)

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

    # listing-only: PROC PRINT psi_summary

    # metrics_calculation.sas:299-304 PROC RANK groups=20
    # R§2 PROC RANK
    calibration_data = logit_scored_valid.with_columns(
        sas_compat.proc_rank_groups(logit_scored_valid.get_column("pd_logistic"), 20).alias("pred_bin")
    )

    # metrics_calculation.sas:306-316 calibration_plot
    # INV work.calibration_plot (calibration_plot.csv): means divided after aggregation (A7), only
    # occurring bins
    calibration_plot = (
        calibration_data.group_by("pred_bin", maintain_order=True)
        .agg(
            mean_predicted=sas_compat.sql_mean(pl.col("pd_logistic")),  # R§2 SQL aggregates (S10)
            mean_actual=sas_compat.sql_mean(pl.col("default_flag")),
            bin_count=pl.len().cast(pl.Int64),
        )
        .select("pred_bin", "mean_predicted", "mean_actual", "bin_count")
        .sort("pred_bin", maintain_order=True)
    )

    # listing-only: PROC SGPLOT calibration_plot (calibration scatter)

    # metrics_calculation.sas:331-345 validation_summary
    # R§2 merge (S5); INV work.validation_summary: status via helpers (AUC, KS, PSI can be missing on
    # extra rows)
    validation_summary = sas_compat.merge_one_to_one(auc_summary, ks_statistic, psi_summary)
    validation_summary = validation_summary.with_columns(
        model=pl.lit("Logistic Regression"),
        status=pl.when(
            sas_compat.ge(pl.col("AUC"), 0.7)
            & sas_compat.ge(pl.col("KS_Statistic"), 0.3)
            & sas_compat.lt(pl.col("PSI"), 0.25)
        )
        .then(pl.lit("Production Ready"))
        .when(sas_compat.ge(pl.col("AUC"), 0.65))
        .then(pl.lit("Requires Review"))
        .otherwise(pl.lit("Needs Improvement")),
    )

    # listing-only: PROC PRINT validation_summary

    # metrics_calculation.sas:356-387 PROC EXPORT validation_summary, decile_analysis, threshold_analysis,
    # ks_statistic, calibration_plot (INV validation_summary.csv, decile_analysis.csv, threshold_analysis.csv,
    # ks_statistic.csv, calibration_plot.csv for the stored formats)
    sas_compat.write_sas_csv(
        validation_summary,
        output_dir / "validation_summary.csv",
        formats={"AUC": "8.4", "Gini": "8.4", "KS_Statistic": "8.4", "KS_Cutoff": "8.4", "PSI": "best12."},
    )
    sas_compat.write_sas_csv(
        decile_analysis, output_dir / "decile_analysis.csv", formats=decile_analysis_formats
    )
    sas_compat.write_sas_csv(threshold_analysis, output_dir / "threshold_analysis.csv", formats={})
    sas_compat.write_sas_csv(
        ks_statistic, output_dir / "ks_statistic.csv", formats={"KS_Statistic": "8.4", "KS_Cutoff": "8.4"}
    )
    sas_compat.write_sas_csv(
        calibration_plot,
        output_dir / "calibration_plot.csv",
        formats={"mean_predicted": "8.4", "mean_actual": "8.4"},
    )

    # metrics_calculation.sas:391-413 model_performance_metrics
    # INV work.model_performance_metrics: where=(threshold=0.5) (plain, never missing) + dataset rename
    # and RENAME
    # statement composed; R§2 merge (S5); validation_date = today() (A16 at export)
    at_50 = threshold_analysis.filter(pl.col("threshold") == 0.5).rename(
        {
            "accuracy": "accuracy_at_50",
            "precision": "precision_at_50",
            "recall": "recall_at_50",
            "f1_score": "f1_score_at_50",
            "specificity": "specificity_at_50",
        }
    )
    model_performance_metrics = sas_compat.merge_one_to_one(auc_summary, ks_statistic, psi_summary, at_50)
    model_performance_metrics = model_performance_metrics.with_columns(
        model_name=pl.lit("Logistic Regression"),
        validation_date=pl.lit(dt.date.today()),
        dataset=pl.lit("Kaggle Give Me Some Credit"),
    ).drop("threshold", "ROCModel")

    # metrics_calculation.sas:416-420 PROC EXPORT model_performance_metrics
    # INV model_performance_metrics.csv: *_at_50 columns carry no format (BEST12.)
    sas_compat.write_sas_csv(
        model_performance_metrics,
        output_dir / "model_performance_metrics.csv",
        formats={
            "AUC": "8.4",
            "Gini": "8.4",
            "KS_Statistic": "8.4",
            "KS_Cutoff": "8.4",
            "PSI": "best12.",
            "validation_date": "date9.",
        },
    )

    # listing-only: PROC PRINT model_performance_metrics

    # Judge-instrumented exports of datasets the SAS code only prints (R§2, A21; judge/run_sas.py
    # EXPORT_AFTER):
    # roc_stats, cumulative_lift, psi_calculation -> printed_<name>.csv (INV printed_roc_metrics.csv,
    # printed_cumulative_lift.csv, printed_psi_calculation.csv)
    printed_roc_metrics = pl.DataFrame(
        {
            c: [
                roc_stats.item(0, c)
                if c == "ROCModel"
                else sas_compat.sas_d8(
                    cast(float | None, roc_stats.item(0, c))
                )  # D8. on all seven numbers (A20)
            ]
            for c in roc_stats.columns
        },
        schema={c: pl.String for c in roc_stats.columns},
    )
    sas_compat.write_sas_csv(printed_roc_metrics, output_dir / "printed_roc_metrics.csv", formats={})
    sas_compat.write_sas_csv(
        cumulative_lift,
        output_dir / "printed_cumulative_lift.csv",
        formats={
            **decile_analysis_formats,
            "cum_capture_rate": "percent8.2",
            "cum_lift": "8.2",
        },
    )
    sas_compat.write_sas_csv(psi_calculation, output_dir / "printed_psi_calculation.csv", formats={})

    # metrics_calculation.sas:427-430
    print("NOTE: Model validation completed successfully")
    print("NOTE: Validation metrics calculated and exported")
    print(f"NOTE: Results saved to: {output_dir}")
    print("NOTE: Check validation_summary.csv for overall performance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Credit risk model validation (metrics_calculation.sas)")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)

# PORT STATUS: confidence=high todos=0
