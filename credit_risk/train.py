"""train.sas -> polars: train the logistic model, score, grade, evaluate and export.

Structure-preserving translation (RULEBOOK §0). Entry point: run(input_dir, output_dir) (§4, A27).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from credit_risk import sas_compat


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)  # R§4 S12

    # train.sas:19 %let output_path -> input_dir (features) and output_dir (exports)  # INV &output_path

    # train.sas:26-41 PROC IMPORT of the two feature files
    # R§2 PROC IMPORT, INV work.model_features_train: guessingrows=max -> None, all 42 columns Float64
    model_features_train = sas_compat.proc_import_csv(
        input_dir / "model_features_train.csv", guessingrows=None
    )
    model_features_validation = sas_compat.proc_import_csv(
        input_dir / "model_features_validation.csv", guessingrows=None
    )

    # train.sas:48-96 PROC LOGISTIC stepwise, ODS tables, OUTPUT OUT=, STORE
    # MODEL statement order (train.sas:51-80)
    candidates = [
        "credit_utilization_capped",
        "debt_ratio_capped",
        "num_late_30_59",
        "num_late_60_89",
        "num_late_90_plus",
        "total_late_payments",
        "has_delinquency",
        "has_serious_delinquency",
        "age",
        "monthly_income",
        "log_monthly_income",
        "num_credit_lines",
        "num_real_estate_loans",
        "log_num_credit_lines",
        "num_dependents",
        "income_per_dependent",
        "credit_lines_per_person",
        "flag_high_utilization",
        "flag_very_high_utilization",
        "flag_high_debt_ratio",
        "flag_very_high_debt_ratio",
        "flag_recent_late_payments",
        "flag_serious_delinquency",
        "flag_multiple_delinquencies",
        "flag_low_income",
        "flag_many_dependents",
        "flag_few_credit_lines",
        "total_risk_flags",
        "credit_util_category",
        "debt_category",
        "age_category",
        "financial_health",
        "age_income_interaction",
        "utilization_debt_interaction",
        "MonthlyIncome_missing",
        "Dependents_missing",
    ]
    # R§2 PROC LOGISTIC selection=stepwise, A5
    # INV work.logit_scored_train / model_coefficients / stepwise path
    # SAS fits on complete cases only: a row with a missing MODEL variable or response is excluded
    # (RULEBOOK §2 stepwise); the fit frame feeds the fit and every fit statistic below
    fit_mask = (
        model_features_train.select(pl.all_horizontal(pl.col(*candidates, "default_flag").is_not_null()))
        .to_series()
        .to_numpy()
    )
    fit_frame = model_features_train.filter(pl.Series(fit_mask))
    stepwise = sas_compat.stepwise_logistic(fit_frame, "default_flag", candidates, 0.05, 0.05)
    final = stepwise.final
    intercept_only = stepwise.intercept_only
    if final is None or intercept_only is None:
        raise RuntimeError("stepwise_logistic returned no final model")
    n_obs = fit_frame.height
    y_train = np.asarray(fit_frame.get_column("default_flag").to_numpy(), dtype=np.float64)
    m2ll0 = -2.0 * intercept_only.loglik  # -2 Log L of the intercept-only fit
    ybar = float(y_train.mean())

    # ODS StepwiseSummary (ModelBuildingSummary) -> stepwise_summary.csv
    # INV stepwise_summary.csv, R§2 ODS tables
    # stored formats: Step best8., Effect $20., DF 4., NumberInModel best8.,
    # ScoreChiSq/WaldChiSq 10.4, ProbChiSq pvalue6.4 (S7)
    ss_step: list[str] = []
    ss_entered: list[str] = []
    ss_removed: list[str] = []
    ss_df: list[str] = []
    ss_number: list[str] = []
    ss_score: list[str] = []
    ss_wald: list[str] = []
    ss_prob: list[str] = []
    for st in stepwise.steps:
        ss_step.append(str(st.step))
        ss_entered.append("" if st.entered is None else st.entered[:20])
        ss_removed.append("" if st.removed is None else st.removed[:20])
        ss_df.append(str(st.df))
        ss_number.append(str(st.number_in_model))
        ss_score.append(
            "_" if st.score_chisq is None else sas_compat.fmt_wd(st.score_chisq, 10, 4)
        )  # '_' = ODS ._
        ss_wald.append("_" if st.wald_chisq is None else sas_compat.fmt_wd(st.wald_chisq, 10, 4))
        ss_prob.append(sas_compat.sas_pvalue(st.p_value))
    stepwise_summary = pl.DataFrame(
        {
            "Step": ss_step,
            "EffectEntered": ss_entered,
            "EffectRemoved": ss_removed,
            "DF": ss_df,
            "NumberInModel": ss_number,
            "ScoreChiSq": ss_score,
            "WaldChiSq": ss_wald,
            "ProbChiSq": ss_prob,
        }
    )
    sas_compat.write_sas_csv(stepwise_summary, output_dir / "stepwise_summary.csv", formats={})

    # ODS FitStatistics -> printed_fit_statistics.csv  # INV printed_fit_statistics.csv
    # (complete cases only: x_k, n_obs and y_train come from fit_frame)
    # stored formats: RowId $8., Criterion $8., Equals $1., InterceptOnly d12.3,
    # InterceptAndCovariates 9.3 (S7)
    fs_step: list[str] = ["0"]
    fs_rowid: list[str] = ["M2LOGL0"]
    fs_criterion: list[str] = ["-2 Log L"]
    fs_equals: list[str] = ["="]
    fs_only: list[str] = [sas_compat.sas_d12_3(m2ll0)]  # R§2 S6: the one D12.3 helper
    fs_cov: list[str] = [sas_compat.fmt_wd(m2ll0, 9, 3)]
    # ODS GlobalTests -> printed_global_tests.csv  # INV printed_global_tests.csv
    # (complete cases only: the global tests come from the fit on fit_frame)
    # stored formats: Test $16., ChiSq 10.4, DF 4., ProbChiSq pvalue6.4 (S7)
    gt_step: list[str] = []
    gt_test: list[str] = []
    gt_chisq: list[str] = []
    gt_df: list[str] = []
    gt_prob: list[str] = []
    # ODS RSquare -> printed_rsquare.csv  # INV printed_rsquare.csv
    # stored formats: cValue $6., nValue d12.3 (S7)
    rs_step: list[str] = []
    rs_label1: list[str] = []
    rs_cvalue1: list[str] = []
    rs_nvalue1: list[str] = []
    rs_label2: list[str] = []
    rs_cvalue2: list[str] = []
    rs_nvalue2: list[str] = []
    for st in stepwise.steps:
        names_k = st.fit.names
        q = len(names_k) - 1  # effects in the model, intercept not counted
        m2ll = -2.0 * st.fit.loglik
        x_k = np.column_stack(
            [
                np.ones(n_obs),
                *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]],
            ]
        )
        # fit statistics: AIC, SC, -2 Log L for each step
        fs_step.extend([str(st.step)] * 3)
        fs_rowid.extend(["AIC", "SBC", "M2LOGL"])
        fs_criterion.extend(["AIC", "SC", "-2 Log L"])
        fs_equals.extend(["", "", ""])
        fs_only.extend(
            [
                sas_compat.sas_d12_3(m2ll0 + 2.0),
                sas_compat.sas_d12_3(m2ll0 + math.log(n_obs)),
                sas_compat.sas_d12_3(m2ll0),
            ]
        )
        fs_cov.extend(
            [
                sas_compat.fmt_wd(m2ll + 2.0 * (q + 1), 9, 3),
                sas_compat.fmt_wd(m2ll + (q + 1) * math.log(n_obs), 9, 3),
                sas_compat.fmt_wd(m2ll, 9, 3),
            ]
        )
        # global tests: likelihood ratio, score (at the intercept-only fit), Wald
        lr = m2ll0 - m2ll
        u0 = x_k.T @ (y_train - ybar)
        i0 = ybar * (1.0 - ybar) * (x_k.T @ x_k)
        score = float(u0 @ np.linalg.solve(i0, u0))
        b_slope = st.fit.beta[1:]
        wald = float(b_slope @ np.linalg.solve(st.fit.cov[1:, 1:], b_slope))
        for test, stat in (("Likelihood Ratio", lr), ("Score", score), ("Wald", wald)):
            gt_step.append(str(st.step))
            gt_test.append(test)
            gt_chisq.append(sas_compat.fmt_wd(stat, 10, 4))
            gt_df.append(str(q))
            gt_prob.append(sas_compat.sas_pvalue(sas_compat.chi2_sf(stat, q)))
        # R-square: Cox-Snell and Nagelkerke (max-rescaled)
        cox_snell = 1.0 - math.exp(-lr / n_obs)
        nagelkerke = cox_snell / (1.0 - math.exp(-m2ll0 / n_obs))
        rs_step.append(str(st.step))
        rs_label1.append("R-Square")
        rs_cvalue1.append(sas_compat.fmt_wd(cox_snell, 6, 4))
        rs_nvalue1.append(sas_compat.sas_d12_3(cox_snell))
        rs_label2.append("Max-rescaled R-Square")
        rs_cvalue2.append(sas_compat.fmt_wd(nagelkerke, 6, 4))
        rs_nvalue2.append(sas_compat.sas_d12_3(nagelkerke))
    printed_fit_statistics = pl.DataFrame(
        {
            "Step": fs_step,
            "RowId": fs_rowid,
            "Criterion": fs_criterion,
            "Equals": fs_equals,
            "InterceptOnly": fs_only,
            "InterceptAndCovariates": fs_cov,
        }
    )
    sas_compat.write_sas_csv(printed_fit_statistics, output_dir / "printed_fit_statistics.csv", formats={})
    printed_global_tests = pl.DataFrame(
        {"Step": gt_step, "Test": gt_test, "ChiSq": gt_chisq, "DF": gt_df, "ProbChiSq": gt_prob}
    )
    sas_compat.write_sas_csv(printed_global_tests, output_dir / "printed_global_tests.csv", formats={})
    printed_rsquare = pl.DataFrame(
        {
            "Step": rs_step,
            "Label1": rs_label1,
            "cValue1": rs_cvalue1,
            "nValue1": rs_nvalue1,
            "Label2": rs_label2,
            "cValue2": rs_cvalue2,
            "nValue2": rs_nvalue2,
        }
    )
    sas_compat.write_sas_csv(printed_rsquare, output_dir / "printed_rsquare.csv", formats={})

    # OUTPUT OUT=work.logit_scored_train PREDICTED=pd_logistic  # R§2 `output out= predicted=`
    # final model effects in MODEL statement order (ParameterEstimates order), Intercept first
    final_effects = [c for c in candidates if c in final.names]
    final_index = [final.names.index(c) for c in final_effects]
    intercept = float(final.beta[0])
    coefficients = {c: float(final.beta[i]) for c, i in zip(final_effects, final_index, strict=True)}
    eta_train = pl.lit(intercept)
    for c, b in coefficients.items():
        eta_train = eta_train + b * pl.col(c)
    logit_scored_train = model_features_train.with_columns(
        pd_logistic=1
        / (
            1 + (-eta_train).exp()
        )  # R§2 output out= predicted=: pd per training row, final model (no SAS exp() call, S1 n/a)
    )

    # ODS Association -> printed_association.csv  # INV printed_association.csv, R§2 A8
    # stored formats: Label1 $18., cValue1 $9., nValue1 d12.3, Label2 $9., cValue2 $5., nValue2 d12.3 (S7)
    assoc = sas_compat.association_table(
        logit_scored_train.get_column("default_flag"), logit_scored_train.get_column("pd_logistic")
    )
    printed_association = pl.DataFrame(
        {
            "Label1": ["Percent Concordant", "Percent Discordant", "Percent Tied", "Pairs"],
            "cValue1": [
                sas_compat.fmt_wd(assoc.concordant_pct, 9, 1),
                sas_compat.fmt_wd(assoc.discordant_pct, 9, 1),
                sas_compat.fmt_wd(assoc.tied_pct, 9, 1),
                str(assoc.pairs),
            ],
            "nValue1": [
                sas_compat.sas_d12_3(assoc.concordant_pct),
                sas_compat.sas_d12_3(assoc.discordant_pct),
                sas_compat.sas_d12_3(assoc.tied_pct),
                sas_compat.sas_d12_3(float(assoc.pairs)),
            ],
            "Label2": ["Somers' D", "Gamma", "Tau-a", "c"],
            "cValue2": [
                sas_compat.fmt_wd(assoc.somers_d, 5, 3),
                sas_compat.fmt_wd(assoc.gamma, 5, 3),
                sas_compat.fmt_wd(assoc.tau_a, 5, 3),
                sas_compat.fmt_wd(assoc.c, 5, 3),
            ],
            "nValue2": [
                sas_compat.sas_d12_3(assoc.somers_d),
                sas_compat.sas_d12_3(assoc.gamma),
                sas_compat.sas_d12_3(assoc.tau_a),
                sas_compat.sas_d12_3(assoc.c),
            ],
        }
    )
    sas_compat.write_sas_csv(printed_association, output_dir / "printed_association.csv", formats={})

    # ODS ParameterEstimates -> work.model_coefficients (exported at train.sas:395)
    # INV model_coefficients.csv
    # stored formats: Variable $20., DF 2., Estimate d8., StdErr d8., WaldChiSq 10.4,
    # ProbChiSq pvalue6.4, _ESTTYPE_ $4. (S7)
    mc_variable: list[str] = ["Intercept"]
    mc_estimate: list[str] = [sas_compat.sas_d8(intercept)]
    mc_stderr: list[str] = []
    mc_wald: list[str] = []
    mc_prob: list[str] = []
    # odds ratios: final model only, no Intercept  # INV printed_odds_ratios.csv, R§2 Z975
    or_effect: list[str] = []
    or_est: list[str] = []
    or_lower: list[str] = []
    or_upper: list[str] = []
    for idx, name in [(0, "Intercept"), *zip(final_index, final_effects, strict=True)]:
        b = float(final.beta[idx])
        se = math.sqrt(float(final.cov[idx, idx]))
        wald_b = (b / se) ** 2
        if idx != 0:
            mc_variable.append(name[:20])
            mc_estimate.append(sas_compat.sas_d8(b))
            or_effect.append(name[:20])
            # R§2 ODS stored widths (S7)
            or_est.append(sas_compat.fmt_oddsr(math.exp(b), 8, 3))
            or_lower.append(sas_compat.fmt_oddsr(math.exp(b - sas_compat.Z975 * se), 8, 3))
            or_upper.append(sas_compat.fmt_oddsr(math.exp(b + sas_compat.Z975 * se), 8, 3))
        mc_stderr.append(sas_compat.sas_d8(se))
        mc_wald.append(sas_compat.fmt_wd(wald_b, 10, 4))
        mc_prob.append(sas_compat.sas_pvalue(sas_compat.chi2_sf(wald_b, 1)))
    model_coefficients = pl.DataFrame(
        {
            "Variable": mc_variable,
            "DF": ["1"] * len(mc_variable),
            "Estimate": mc_estimate,
            "StdErr": mc_stderr,
            "WaldChiSq": mc_wald,
            "ProbChiSq": mc_prob,
            "_ESTTYPE_": ["MLE"] * len(mc_variable),
        }
    )
    printed_odds_ratios = pl.DataFrame(
        {"Effect": or_effect, "OddsRatioEst": or_est, "LowerCL": or_lower, "UpperCL": or_upper}
    )
    # stored formats: Effect $20., OddsRatioEst/LowerCL/UpperCL oddsr8.3 (S7)
    sas_compat.write_sas_csv(printed_odds_ratios, output_dir / "printed_odds_ratios.csv", formats={})

    # LACKFIT -> printed_hl_partition.csv and printed_hosmer_lemeshow.csv  # INV printed_hl_partition.csv
    # stored formats: Group/Total/Observed 8., Expected 8.2; ChiSq 10.4, DF 4.,
    # ProbChiSq pvalue6.4, NGroups best8. (S7)
    hl_table, hl_chisq, hl_df, hl_p = sas_compat.hosmer_lemeshow(
        logit_scored_train.get_column("default_flag"), logit_scored_train.get_column("pd_logistic")
    )
    printed_hl_partition = pl.DataFrame(
        {
            "Group": [str(v) for v in hl_table.get_column("Group").to_list()],
            "Total": [sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("Total").to_list()],
            "EventsObserved": [
                sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("EventsObserved").to_list()
            ],
            "EventsExpected": [
                sas_compat.fmt_wd(v, 8, 2) for v in hl_table.get_column("EventsExpected").to_list()
            ],
            "NoneventsObserved": [
                sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("NoneventsObserved").to_list()
            ],
            "NoneventsExpected": [
                sas_compat.fmt_wd(v, 8, 2) for v in hl_table.get_column("NoneventsExpected").to_list()
            ],
        }
    )
    sas_compat.write_sas_csv(printed_hl_partition, output_dir / "printed_hl_partition.csv", formats={})
    printed_hosmer_lemeshow = pl.DataFrame(
        {
            "ChiSq": [sas_compat.fmt_wd(hl_chisq, 10, 4)],
            "DF": [str(hl_df)],
            "ProbChiSq": [sas_compat.sas_pvalue(hl_p)],
            "NGroups": [str(hl_table.height)],
        }
    )
    sas_compat.write_sas_csv(printed_hosmer_lemeshow, output_dir / "printed_hosmer_lemeshow.csv", formats={})

    # CTABLE -> printed_classification.csv  # INV printed_classification.csv
    # stored formats: ProbLevel 5.3, counts 5., percentages 5.1 (S7)
    x_final = np.column_stack(
        [
            np.ones(n_obs),
            *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in final.names[1:]],
        ]
    )
    # CTABLE uses the complete cases only: x_final, y_train and pd_train are all on the fit frame
    pd_train = np.asarray(logit_scored_train.get_column("pd_logistic").to_numpy(), dtype=np.float64)[fit_mask]
    ctable = sas_compat.classification_table(y_train, x_final, pd=pd_train)
    printed_classification = pl.DataFrame(
        {
            "ProbLevel": [sas_compat.fmt_wd(v, 5, 3) for v in ctable.get_column("ProbLevel").to_list()],
            "CorrectEvents": [
                sas_compat.fmt_wd(v, 5, 0) for v in ctable.get_column("CorrectEvents").to_list()
            ],
            "CorrectNonevents": [
                sas_compat.fmt_wd(v, 5, 0) for v in ctable.get_column("CorrectNonevents").to_list()
            ],
            "IncorrectEvents": [
                sas_compat.fmt_wd(v, 5, 0) for v in ctable.get_column("IncorrectEvents").to_list()
            ],
            "IncorrectNonevents": [
                sas_compat.fmt_wd(v, 5, 0) for v in ctable.get_column("IncorrectNonevents").to_list()
            ],
            "Correct": [sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("Correct").to_list()],
            "Sensitivity": [sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("Sensitivity").to_list()],
            "Specificity": [sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("Specificity").to_list()],
            "FalsePositive": [
                sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("FalsePositive").to_list()
            ],
            "FalseNegative": [
                sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("FalseNegative").to_list()
            ],
            "PPV": [sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("PPV").to_list()],
            "NPV": [sas_compat.fmt_wd(v, 5, 1) for v in ctable.get_column("NPV").to_list()],
        }
    )
    sas_compat.write_sas_csv(printed_classification, output_dir / "printed_classification.csv", formats={})

    # STORE work.logit_model -> model.json  # R§2 PROC LOGISTIC store / PROC PLM restore, RULEBOOK §0
    with (output_dir / "model.json").open("w", encoding="utf-8") as fh:
        json.dump({"intercept": intercept, "coefficients": coefficients}, fh)

    # title "Logistic Regression Model - Credit Default Prediction"  # R§2 title dropped

    # train.sas:103-106 add binary prediction variable
    logit_scored_train = logit_scored_train.with_columns(
        pred_logistic=sas_compat.flag(
            pl.col("pd_logistic") >= 0.5
        )  # INV credit_risk_score: MISSING_NEVER, plain
    )

    # train.sas:109-111 PROC FREQ out=work.confusion_matrix_train
    # R§2 PROC FREQ tables a*b / out=, INV printed_confusion_train.csv
    confusion_matrix_train = (
        logit_scored_train.group_by(["default_flag", "pred_logistic"], maintain_order=True)
        .agg(COUNT=pl.len().cast(pl.Int64))
        .sort(["default_flag", "pred_logistic"], maintain_order=True)
        .with_columns(PERCENT=sas_compat.div(100 * pl.col("COUNT"), pl.col("COUNT").sum()))
    )

    # train.sas:113-115
    # listing-only: PROC PRINT confusion_matrix_train

    # train.sas:118-139 data work.training_metrics (retain + end=eof)
    # R§2 retain + end=eof, INV work.training_metrics
    training_metrics = confusion_matrix_train.select(
        TP=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("pred_logistic") == 1)).sum(),
        TN=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("pred_logistic") == 0)).sum(),
        FP=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("pred_logistic") == 1)).sum(),
        FN=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("pred_logistic") == 0)).sum(),
    ).with_columns(
        train_precision=pl.when((pl.col("TP") + pl.col("FP")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FP")))
        .otherwise(None),
        train_recall=pl.when((pl.col("TP") + pl.col("FN")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FN")))
        .otherwise(None),
        train_accuracy=pl.when((pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")) > 0)
        .then((pl.col("TP") + pl.col("TN")) / (pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")))
        .otherwise(None),
    )
    training_metrics = training_metrics.with_columns(
        train_f1_score=pl.when(
            sas_compat.gt(pl.col("train_precision") + pl.col("train_recall"), 0)
        )  # INV train_f1_score: A2
        .then(
            2
            * (pl.col("train_precision") * pl.col("train_recall"))
            / (pl.col("train_precision") + pl.col("train_recall"))
        )
        .otherwise(None)
    )
    training_metrics = training_metrics.select(
        "train_precision", "train_recall", "train_f1_score", "train_accuracy"
    ).cast(pl.Float64)

    # train.sas:141-144
    # listing-only: PROC PRINT training_metrics

    # train.sas:151-155 PROC PLM restore ... score -> eta = intercept + sum(b_i x_i)
    # INV work.logit_scored_valid_temp (PROC PLM in train): in-memory model, same as model.json
    eta_valid = pl.lit(intercept)
    for c, b in coefficients.items():
        eta_valid = eta_valid + b * pl.col(c)
    logit_scored_valid_temp = model_features_validation.with_columns(predicted_logit=eta_valid)

    # train.sas:158-168 inverse logit and binary prediction
    logit_scored_valid = (
        logit_scored_valid_temp.with_columns(
            pd_logistic=1
            / (
                1 + sas_compat.sas_exp(-pl.col("predicted_logit"))
            )  # R§2 exp(x) -> sas_exp (S1), as predict.py
        )
        .with_columns(pred_logistic=sas_compat.flag(sas_compat.ge(pl.col("pd_logistic"), 0.5)))
        .drop("predicted_logit")
    )

    # train.sas:171-173 PROC FREQ out=work.confusion_matrix
    # R§2 PROC FREQ, INV printed_confusion_validation.csv
    confusion_matrix = (
        logit_scored_valid.group_by(["default_flag", "pred_logistic"], maintain_order=True)
        .agg(COUNT=pl.len().cast(pl.Int64))
        .sort(["default_flag", "pred_logistic"], maintain_order=True)
        .with_columns(PERCENT=sas_compat.div(100 * pl.col("COUNT"), pl.col("COUNT").sum()))
    )

    # train.sas:175-177
    # listing-only: PROC PRINT confusion_matrix

    # train.sas:180-201 data work.validation_metrics (retain + end=eof)  # INV work.validation_metrics
    validation_metrics = confusion_matrix.select(
        TP=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("pred_logistic") == 1)).sum(),
        TN=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("pred_logistic") == 0)).sum(),
        FP=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("pred_logistic") == 1)).sum(),
        FN=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("pred_logistic") == 0)).sum(),
    ).with_columns(
        valid_precision=pl.when((pl.col("TP") + pl.col("FP")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FP")))
        .otherwise(None),
        valid_recall=pl.when((pl.col("TP") + pl.col("FN")) > 0)
        .then(pl.col("TP") / (pl.col("TP") + pl.col("FN")))
        .otherwise(None),
        valid_accuracy=pl.when((pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")) > 0)
        .then((pl.col("TP") + pl.col("TN")) / (pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")))
        .otherwise(None),
    )
    validation_metrics = validation_metrics.with_columns(
        valid_f1_score=pl.when(
            sas_compat.gt(pl.col("valid_precision") + pl.col("valid_recall"), 0)
        )  # INV valid_f1_score: A2
        .then(
            2
            * (pl.col("valid_precision") * pl.col("valid_recall"))
            / (pl.col("valid_precision") + pl.col("valid_recall"))
        )
        .otherwise(None)
    )
    validation_metrics = validation_metrics.select(
        "valid_precision", "valid_recall", "valid_f1_score", "valid_accuracy"
    ).cast(pl.Float64)

    # train.sas:203-206
    # listing-only: PROC PRINT validation_metrics

    # train.sas:213-244 data work.risk_scores_train
    risk_scores_train = logit_scored_train.with_columns(
        base_score=pl.lit(600.0),
        score_range=pl.lit(250.0),
    ).with_columns(
        credit_risk_score=sas_compat.sas_round(  # R§2 round(x), INV credit_risk_score
            pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
        )
    )
    risk_scores_train = risk_scores_train.with_columns(
        risk_grade=pl.when(pl.col("credit_risk_score") >= 750)
        .then(pl.lit("A"))
        .when(pl.col("credit_risk_score") >= 700)
        .then(pl.lit("B"))
        .when(pl.col("credit_risk_score") >= 650)
        .then(pl.lit("C"))
        .when(pl.col("credit_risk_score") >= 600)
        .then(pl.lit("D"))
        .when(pl.col("credit_risk_score") >= 550)
        .then(pl.lit("E"))
        .otherwise(pl.lit("F"))
    )
    risk_scores_train = risk_scores_train.with_columns(
        recommendation=pl.when(pl.col("risk_grade").is_in(["A", "B"]))
        .then(pl.lit("Approve"))
        .when(pl.col("risk_grade") == "C")
        .then(pl.lit("Review"))
        .otherwise(pl.lit("Decline")),
        base_rate=pl.lit(0.05),
    )
    risk_scores_train = risk_scores_train.with_columns(
        interest_rate=pl.when(pl.col("risk_grade") == "A")
        .then(pl.col("base_rate"))
        .when(pl.col("risk_grade") == "B")
        .then(pl.col("base_rate") + 0.02)
        .when(pl.col("risk_grade") == "C")
        .then(pl.col("base_rate") + 0.04)
        .when(pl.col("risk_grade") == "D")
        .then(pl.col("base_rate") + 0.07)
        .when(pl.col("risk_grade") == "E")
        .then(pl.col("base_rate") + 0.10)
        .otherwise(pl.col("base_rate") + 0.15)
    )  # format interest_rate percent8.2 -> applied at export

    # train.sas:247-275 data work.risk_scores_validation
    risk_scores_validation = logit_scored_valid.with_columns(
        base_score=pl.lit(600.0),
        score_range=pl.lit(250.0),
    ).with_columns(
        credit_risk_score=sas_compat.sas_round(  # R§2 round(x), INV credit_risk_score
            pl.col("base_score") + pl.col("score_range") * (1 - pl.col("pd_logistic"))
        )
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        risk_grade=pl.when(pl.col("credit_risk_score") >= 750)
        .then(pl.lit("A"))
        .when(pl.col("credit_risk_score") >= 700)
        .then(pl.lit("B"))
        .when(pl.col("credit_risk_score") >= 650)
        .then(pl.lit("C"))
        .when(pl.col("credit_risk_score") >= 600)
        .then(pl.lit("D"))
        .when(pl.col("credit_risk_score") >= 550)
        .then(pl.lit("E"))
        .otherwise(pl.lit("F"))
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        recommendation=pl.when(pl.col("risk_grade").is_in(["A", "B"]))
        .then(pl.lit("Approve"))
        .when(pl.col("risk_grade") == "C")
        .then(pl.lit("Review"))
        .otherwise(pl.lit("Decline")),
        base_rate=pl.lit(0.05),
    )
    risk_scores_validation = risk_scores_validation.with_columns(
        interest_rate=pl.when(pl.col("risk_grade") == "A")
        .then(pl.col("base_rate"))
        .when(pl.col("risk_grade") == "B")
        .then(pl.col("base_rate") + 0.02)
        .when(pl.col("risk_grade") == "C")
        .then(pl.col("base_rate") + 0.04)
        .when(pl.col("risk_grade") == "D")
        .then(pl.col("base_rate") + 0.07)
        .when(pl.col("risk_grade") == "E")
        .then(pl.col("base_rate") + 0.10)
        .otherwise(pl.col("base_rate") + 0.15)
    )  # format interest_rate percent8.2 -> applied at export

    # train.sas:278-286
    # listing-only: PROC FREQ risk_grade x default_flag of risk_scores_train
    # listing-only: PROC FREQ risk_grade x default_flag of risk_scores_validation

    # train.sas:293-306 PROC LOGISTIC nofit + roc (train and validation)
    # R§2 PROC LOGISTIC nofit + roc, INV printed_roc_train.csv / printed_roc_validation.csv
    roc_train = sas_compat.roc_association(
        risk_scores_train.get_column("default_flag"),
        risk_scores_train.get_column("pd_logistic"),
        label="Training Set",
    )
    roc_valid = sas_compat.roc_association(
        risk_scores_validation.get_column("default_flag"),
        risk_scores_validation.get_column("pd_logistic"),
        label="Validation Set",
    )

    # train.sas:309-319
    # listing-only: PROC PRINT Area of roc_train (Training Set AUC)
    # listing-only: PROC PRINT Area of roc_valid (Validation Set AUC)

    # train.sas:326-335 drop IP_: XP_: _FROM_ _INTO_ _LEVEL_  # INV work.risk_scores_train_clean: identity
    risk_scores_train_clean = risk_scores_train
    risk_scores_validation_clean = risk_scores_validation

    # train.sas:338-349 PROC EXPORT scored sets  # INV risk_scores_train.csv, risk_scores_validation.csv
    sas_compat.write_sas_csv(
        risk_scores_train_clean, output_dir / "risk_scores_train.csv", formats={"interest_rate": "percent8.2"}
    )
    sas_compat.write_sas_csv(
        risk_scores_validation_clean,
        output_dir / "risk_scores_validation.csv",
        formats={"interest_rate": "percent8.2"},
    )

    # train.sas:352-358 data work.final_model_output (keep keeps PDV order)
    # R§2 keep, A12, INV final_model_output.csv
    keep = {
        "row_id",
        "default_flag",
        "pd_logistic",
        "credit_risk_score",
        "risk_grade",
        "recommendation",
        "interest_rate",
        "age",
        "monthly_income",
        "credit_utilization",
        "debt_ratio",
        "total_late_payments",
        "num_credit_lines",
    }
    final_model_output = risk_scores_train.select([c for c in risk_scores_train.columns if c in keep])

    # train.sas:360-364 PROC EXPORT final_model_output
    sas_compat.write_sas_csv(
        final_model_output, output_dir / "final_model_output.csv", formats={"interest_rate": "percent8.2"}
    )

    # train.sas:367-386 data work.model_summary (merge, no BY)  # R§2 merge (A6, S5), INV work.model_summary
    model_summary = sas_compat.merge_one_to_one(
        roc_train.filter(pl.col("ROCModel") == "Training Set").select(Train_AUC=pl.col("Area")),
        roc_valid.filter(pl.col("ROCModel") == "Validation Set").select(Valid_AUC=pl.col("Area")),
        training_metrics,
        validation_metrics,
    )
    model_summary = model_summary.with_columns(
        model_name=pl.lit("Logistic Regression"),
        training_date=pl.lit(dt.date.today()),  # INV training_date: DATE9. at export, A16
        training_records=pl.lit(105000),  # Approximate 70% of 150K
        validation_records=pl.lit(45000),  # Approximate 30% of 150K
    )
    summary_keep = {
        "model_name",
        "training_date",
        "training_records",
        "validation_records",
        "Train_AUC",
        "Valid_AUC",
        "train_precision",
        "train_recall",
        "train_f1_score",
        "train_accuracy",
        "valid_precision",
        "valid_recall",
        "valid_f1_score",
        "valid_accuracy",
    }
    model_summary = model_summary.select([c for c in model_summary.columns if c in summary_keep])

    # train.sas:388-392 PROC EXPORT model_summary  # INV model_summary.csv
    sas_compat.write_sas_csv(
        model_summary,
        output_dir / "model_summary.csv",
        formats={
            "Train_AUC": "8.4",
            "Valid_AUC": "8.4",
            "train_precision": "8.4",
            "train_recall": "8.4",
            "train_f1_score": "8.4",
            "train_accuracy": "8.4",
            "valid_precision": "8.4",
            "valid_recall": "8.4",
            "valid_f1_score": "8.4",
            "valid_accuracy": "8.4",
            "training_date": "date9.",
        },
    )

    # train.sas:395-399 PROC EXPORT model_coefficients  # INV model_coefficients.csv
    sas_compat.write_sas_csv(model_coefficients, output_dir / "model_coefficients.csv", formats={})

    # judge-instrumented exports of printed datasets (EXPORT_AFTER)  # R§2 datasets the judge exports (A21)
    # ROC tables: stored formats ROCModel $12./$14., seven statistics d8. (S7)
    roc_cols = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
    printed_roc_train = pl.DataFrame(
        {
            "ROCModel": roc_train.get_column("ROCModel").to_list(),
            **{c: [sas_compat.sas_d8(v) for v in roc_train.get_column(c).to_list()] for c in roc_cols},
        }
    )
    sas_compat.write_sas_csv(printed_roc_train, output_dir / "printed_roc_train.csv", formats={})
    printed_roc_validation = pl.DataFrame(
        {
            "ROCModel": roc_valid.get_column("ROCModel").to_list(),
            **{c: [sas_compat.sas_d8(v) for v in roc_valid.get_column(c).to_list()] for c in roc_cols},
        }
    )
    sas_compat.write_sas_csv(printed_roc_validation, output_dir / "printed_roc_validation.csv", formats={})
    sas_compat.write_sas_csv(confusion_matrix_train, output_dir / "printed_confusion_train.csv", formats={})
    sas_compat.write_sas_csv(confusion_matrix, output_dir / "printed_confusion_validation.csv", formats={})

    # train.sas:401-407 %put
    print("NOTE: Model training completed successfully")
    print("NOTE: Model stored as work.logit_model")
    print(f"NOTE: Training set scored: {output_dir}/risk_scores_train.csv")
    print(f"NOTE: Validation set scored: {output_dir}/risk_scores_validation.csv")
    print(f"NOTE: Model summary: {output_dir}/model_summary.csv")
    print(f"NOTE: Model coefficients: {output_dir}/model_coefficients.csv")
    print("NOTE: Ready for validation metrics calculation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="train.sas -> Python")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.input_dir, args.output_dir)

# PORT STATUS: confidence=medium todos=0
