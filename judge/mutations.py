"""Deliberate breakages of the ORIGINAL SAS code, used to prove the judge catches them.

Each mutation is a list of exact text replacements: (script, old, new, expected_count).
expected_count guards against a mutation silently not applying (or applying twice).
Every mutation targets a behavior that reaches an exported output. Verdicts use PORT
mode (strict mode fails every mutation trivially). validate_judge.py classifies each run:
CAUGHT (port mode fails), EQUIVALENT (outputs byte-identical to the reference, so no
judge could see it), or MISSED (outputs differ but port mode passes: a judge bug).
Edge-scenario mutations (EDGE_SCENARIO) are judged against a scenario reference, because
the real data never reaches them (e.g. grade F only occurs when pd is missing).
"""

from __future__ import annotations

MUTATIONS: dict[str, list[tuple[str, str, str, int]]] = {
    # Feature engineering: change a scoring rule (flip a constant).
    "fe_health_penalty": [
        ("feature_engineering.sas",
         "if credit_utilization > 30 then financial_health = financial_health - 15;",
         "if credit_utilization > 30 then financial_health = financial_health - 10;", 1),
    ],
    # Feature engineering: wrong imputation statistic.
    "fe_impute_mean": [
        ("feature_engineering.sas",
         "median(MonthlyIncome) as median_income",
         "mean(MonthlyIncome) as median_income", 1),
    ],
    # Training: variable-selection entry threshold.
    "train_slentry": [
        ("train.sas", "slentry=0.05", "slentry=0.10", 1),
    ],
    # Training: flip a comparison boundary in risk grading (train + validation blocks).
    "train_grade_cutoff": [
        ("train.sas",
         "if credit_risk_score >= 750 then risk_grade = 'A';",
         "if credit_risk_score > 750 then risk_grade = 'A';", 2),
    ],
    # Training: rounding rule (round half away from zero -> floor).
    "train_round_floor": [
        ("train.sas",
         "credit_risk_score = round(base_score + score_range * (1 - pd_logistic));",
         "credit_risk_score = floor(base_score + score_range * (1 - pd_logistic));", 2),
    ],
    # Training: output format change only (percent8.2 -> percent8.1).
    "train_rate_format": [
        ("train.sas", "format interest_rate percent8.2;", "format interest_rate percent8.1;", 2),
    ],
    # Metrics: decile grouping.
    "metrics_decile_groups": [
        ("metrics_calculation.sas", "groups=10 descending;", "groups=5 descending;", 1),
    ],
    # Metrics: one evaluation threshold.
    "metrics_threshold": [
        ("metrics_calculation.sas", "%confusion_metrics(0.3, 03);", "%confusion_metrics(0.35, 03);", 1),
    ],
    # Prediction: drop the dependents-imputation path (missing stays missing).
    "predict_no_dep_impute": [
        ("predict.sas", "        NumberOfDependents = 0;\n", "", 1),
    ],
    # Training: stepwise REMOVAL rule (age p=0.0802 and num_credit_lines p=0.0512 stay in).
    "train_slstay": [
        ("train.sas", "slstay=0.05", "slstay=0.10", 1),
    ],
    # Feature engineering: PROC IMPORT type guessing. Today MonthlyIncome is read as $5.
    # (guessingrows=20 default), truncating 77 incomes >= 100,000; this removes that.
    "fe_import_guessingrows": [
        ("feature_engineering.sas",
         "    out=work.credit_raw\n    dbms=csv\n    replace;\n    getnames=yes;\nrun;",
         "    out=work.credit_raw\n    dbms=csv\n    replace;\n    getnames=yes;\n    guessingrows=max;\nrun;", 1),
    ],
    # Feature engineering: imputation join misalignment (SQL age groups != data-step groups).
    "fe_median_group_misaligned": [
        ("feature_engineering.sas", "            when age < 40 then 2\n", "            when age < 45 then 2\n", 1),
    ],
    # Feature engineering: integer exactness on a flag that is NOT a model input.
    "fe_low_income_boundary": [
        ("feature_engineering.sas",
         "flag_low_income = (monthly_income < 2500);", "flag_low_income = (monthly_income <= 2500);", 1),
    ],
    # Prediction: grade boundary (41 test rows at score 700 move B -> C).
    "predict_grade_b_boundary": [
        ("predict.sas",
         "    else if credit_risk_score >= 700 then risk_grade = 'B';",
         "    else if credit_risk_score > 700 then risk_grade = 'B';", 1),
    ],
    # ---- Edge-scenario mutations: only observable on scenarios/ inputs (EDGE_SCENARIO) ----
    # Prediction: pricing constant for grade F (F only occurs when pd is missing).
    "predict_rate_f": [
        ("predict.sas", "else interest_rate = base_rate + 0.15;", "else interest_rate = base_rate + 0.16;", 1),
    ],
    # Prediction: Python/polars null semantics (null < 2500 is False; in SAS . < 2500 is 1).
    "predict_null_compare_false": [
        ("predict.sas", "flag_low_income = (monthly_income < 2500);",
         "flag_low_income = (monthly_income < 2500 and not missing(monthly_income));", 1),
    ],
    # Metrics: PROC RANK tie handling (default TIES=MEAN) in the decile ranking.
    "metrics_rank_ties": [
        ("metrics_calculation.sas", "groups=10 descending;", "groups=10 descending ties=low;", 1),
    ],
    # Metrics: PSI formula sign (PSI is 0 by construction on the real data).
    "metrics_psi_sign": [
        ("metrics_calculation.sas", "(a.train_pct - b.valid_pct) * log(a.train_pct / b.valid_pct)",
         "(b.valid_pct - a.train_pct) * log(a.train_pct / b.valid_pct)", 1),
    ],
    # Metrics: status branch threshold ("Requires Review" never occurs on the real data).
    "metrics_status_threshold": [
        ("metrics_calculation.sas", "else if AUC >= 0.65 then", "else if AUC >= 0.70 then", 1),
    ],
    # ---- Mutations of the CORRECTED SAS (2026-11-16): the score is no longer rounded (Q15) and the
    # grade is cut on the probability (Q18), so train_round_floor, train_grade_cutoff and
    # predict_grade_b_boundary above no longer find their text. These three stand in for them and
    # validate the score and grade rules of the judge.
    # Training: the score rounded again (train + validation blocks).
    "train_score_rounded": [
        ("train.sas",
         "credit_risk_score = base_score + score_range * (1 - pd_logistic);",
         "credit_risk_score = round(base_score + score_range * (1 - pd_logistic));", 2),
    ],
    # Training: the A/B cut moved from 10 % to 11 % (train + validation blocks).
    "train_grade_cut_pd": [
        ("train.sas",
         "    else if pd_logistic < 0.10 then risk_grade = 'A';",
         "    else if pd_logistic < 0.11 then risk_grade = 'A';", 2),
    ],
    # Prediction: the B/C cut moved from 15 % to 16 %.
    "predict_grade_b_cut_pd": [
        ("predict.sas",
         "    else if pd_logistic < 0.15 then risk_grade = 'B';",
         "    else if pd_logistic < 0.16 then risk_grade = 'B';", 1),
    ],
}

# Mutations validated against an edge scenario instead of the real data:
# mutation -> (scenario reference run-id, run_sas.py arguments for that scenario)
EDGE_SCENARIO: dict[str, str] = {
    "predict_rate_f": "edge_predict",
    "predict_null_compare_false": "edge_predict",
    "metrics_rank_ties": "edge_metrics_a",
    "metrics_psi_sign": "edge_metrics_b",
    "metrics_status_threshold": "edge_metrics_c",
    # staged on the REAL reference risk scores (metrics stage only; immune to SAS split drift)
    "metrics_decile_groups": "real_metrics",
    "metrics_threshold": "real_metrics",
}


def apply_mutation(sources: dict[str, str], name: str) -> dict[str, str]:
    out = dict(sources)
    for script, old, new, expected in MUTATIONS[name]:
        found = out[script].count(old)
        if found != expected:
            raise RuntimeError(f"mutation {name}: expected {expected}x in {script}, found {found}")
        out[script] = out[script].replace(old, new)
    return out
