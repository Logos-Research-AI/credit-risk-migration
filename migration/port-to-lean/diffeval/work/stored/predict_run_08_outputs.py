    KEEP_KAGGLE = {"row_id", "pd_logistic"}
    kaggle_submission = test_predictions.select([c for c in test_predictions.columns if c in KEEP_KAGGLE])

    # predict.sas:423-430 DATA test_predictions_full
    KEEP_FULL = {
        "row_id",
        "pd_logistic",
        "pred_logistic",
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
        "financial_health",
        "total_risk_flags",
    }
    test_predictions_full = test_predictions.select(
        [c for c in test_predictions.columns if c in KEEP_FULL]
    ).rename({"age": age_name})  # SAS names are case-blind and keep the spelling of the test file
