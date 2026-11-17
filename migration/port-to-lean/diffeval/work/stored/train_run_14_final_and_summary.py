    risk_scores_train_clean = risk_scores_train
    risk_scores_validation_clean = risk_scores_validation

    # train.sas:363-374 PROC EXPORT scored sets  # INV risk_scores_train.csv, risk_scores_validation.csv
    sas_compat.write_sas_csv(
        risk_scores_train_clean, output_dir / "risk_scores_train.csv", formats={"interest_rate": "percent8.2"}
    )
    sas_compat.write_sas_csv(
        risk_scores_validation_clean,
        output_dir / "risk_scores_validation.csv",
        formats={"interest_rate": "percent8.2"},
    )

    # train.sas:377-383 data work.final_model_output (keep keeps PDV order)
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

    # train.sas:385-389 PROC EXPORT final_model_output
    sas_compat.write_sas_csv(
        final_model_output, output_dir / "final_model_output.csv", formats={"interest_rate": "percent8.2"}
    )

    # train.sas:392-411 data work.model_summary (merge, no BY)  # R§2 merge (A6, S5), INV work.model_summary
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
    if not roc_valid_created:
        # the merge names a table that does not exist: the data step stops and leaves 0 rows and the
        # kept variables in the order it met them, Valid_AUC last; the export writes the header only
        model_summary = model_summary.clear().select(
            [c for c in model_summary.columns if c != "Valid_AUC"] + ["Valid_AUC"]
        )

    # train.sas:413-417 PROC EXPORT model_summary  # INV model_summary.csv
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

    # train.sas:420-424 PROC EXPORT model_coefficients  # INV model_coefficients.csv
    sas_compat.write_sas_csv(model_coefficients, output_dir / "model_coefficients.csv", formats={})
